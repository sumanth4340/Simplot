"""Grade base or adapter on the 12-task eval set (Modal, GPU).

Loads Muse-Glimmer-30B 4-bit and attaches /out/adapter when the
trained LoRA is present, else grades the base and says so loudly.
Each eval task is rendered with the same thinker message builders the
endpoint path uses (build_system_prompt / build_dispatch_prompt +
build_user_content), greedy-generated, and graded with eval/score.py.
Report lands at /out/eval_report_<base|adapter>.json.

Usage:
  modal run action-reasoner/modal/grade_adapter.py   # base or adapter, auto
"""
import importlib.util
import json
import sys
from pathlib import Path

import modal

MODEL_ID = "meta-models/Muse-Glimmer-30B"
GPU = "A100-40GB"
MAX_SEQ_LEN = 4096
GEN_TOKENS = 256

HERE = Path(__file__).resolve().parent
AR = HERE.parent

# Same pins as train_glimmer.py (source of truth; re-probe there first).
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch==2.15.0", "torchvision==0.29.2", "pillow==13.0.0",
    "transformers==5.22.1", "datasets==5.1.0", "peft==0.21.2",
    "bitsandbytes==0.50.2", "trl==1.17.1", "accelerate==1.15.0",
    "huggingface_hub[hf_transfer]==2.4.0",
).env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
image = image.add_local_dir(str(AR / "eval"), "/grade/eval")
image = image.add_local_dir(
    str(AR / "ext" / "isaacsim.action.reasoner.executor"),
    "/grade/ext/isaacsim.action.reasoner.executor")
image = image.add_local_file(str(AR / "actions_compact.json"),
                             "/grade/actions_compact.json")
image = image.add_local_file(str(AR / "skills_routing.json"),
                             "/grade/skills_routing.json")

app = modal.App("action-reasoner-grade")
out_vol = modal.Volume.from_name("reasoner-sft", create_if_missing=True)
hf_vol = modal.Volume.from_name("reasoner-hf-cache", create_if_missing=True)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(f"argrade_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_reasoner(root):
    """Load the shipped reasoner modules from a tree root.

    ``root`` is the repo checkout locally, /grade in the container.
    Returns (thinker, protocol, handlers, dispatcher, score, catalog,
    routing, signatures, roster) — the same pieces run_eval wires.
    """
    root = Path(root)
    ext_py = (root / "ext" / "isaacsim.action.reasoner.executor"
              / "isaacsim" / "action" / "reasoner" / "executor")
    thinker = _load("thinker", ext_py / "thinker.py")
    protocol = _load("protocol", ext_py / "protocol.py")
    handlers = _load("handlers", ext_py / "handlers.py")
    dispatcher = _load("dispatcher", ext_py / "dispatcher.py")
    score = _load("score", root / "eval" / "score.py")
    catalog = protocol.load_catalog(root / "actions_compact.json")
    routing = json.loads((root / "skills_routing.json").read_text(
        encoding="utf-8"))
    signatures = [protocol.help_line(k, catalog[k])
                  for k in handlers.HANDLED_ACTIONS if k in catalog]
    roster = dispatcher.describe_roster()
    return (thinker, protocol, handlers, dispatcher, score, catalog,
            routing, signatures, roster)


def build_messages(task, thinker, signatures, roster, routing):
    """Eval task -> [system, user] messages, exactly like run_eval's
    endpoint path (same builders, same inputs). Pure: tested offline,
    executed on the GPU worker."""
    skills = thinker.select_skills(task["task"], routing)
    if task["kind"] == "dispatch":
        system = thinker.build_dispatch_prompt(list(roster),
                                               list(skills))
    else:
        system = thinker.build_system_prompt(list(signatures),
                                             list(skills))
    content, _, _ = thinker.build_user_content(task["task"],
                                               task["snapshot"], ())
    assert isinstance(content, str), task["id"]
    return [{"role": "system", "content": system},
            {"role": "user", "content": content}]


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/out": out_vol, "/root/.cache/huggingface": hf_vol},
    timeout=3600,
)
def grade():
    import torch
    from peft import PeftModel
    from transformers import (AutoModelForImageTextToText,
                              AutoTokenizer, BitsAndBytesConfig)

    (thinker, protocol, handlers, dispatcher, score, catalog,
     routing, signatures, roster) = load_reasoner("/grade")

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True)
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID, quantization_config=bnb, trust_remote_code=True,
        device_map="auto")
    adapter_cfg = Path("/out/adapter/adapter_config.json")
    if adapter_cfg.is_file():
        model = PeftModel.from_pretrained(model, "/out/adapter")
        label = "adapter"
        print("adapter attached: /out/adapter")
    else:
        label = "base"
        print("NO ADAPTER at /out/adapter: grading the base model")
    model.eval()

    def render(messages):
        if getattr(tok, "chat_template", None):
            return tok.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=True)
        parts = [f"<{m['role']}>\n{m['content']}" for m in messages]
        return "\n".join(parts) + tok.eos_token

    def generate(task):
        try:
            text = render(build_messages(task, thinker, signatures,
                                         roster, routing))
            ids = tok(text, return_tensors="pt", truncation=True,
                      max_length=MAX_SEQ_LEN - GEN_TOKENS)
            in_len = ids["input_ids"].shape[1]
            ids = {k: v.to(model.device) for k, v in ids.items()}
            with torch.no_grad():
                out = model.generate(**ids, max_new_tokens=GEN_TOKENS,
                                     do_sample=False,
                                     pad_token_id=tok.pad_token_id)
            return tok.decode(out[0][in_len:], skip_special_tokens=True)
        except Exception as exc:
            print(f"GEN FAILED {task['id']}: {exc!r}")
            return None

    report = score.run_suite(generate, catalog, routing)
    report["backend"] = f"grade:{label}"
    report["model"] = MODEL_ID
    summary = report["summary"]
    print(f"backend: grade:{label}")
    print(f"action valid-line rate: {summary['action_valid_rate']:.3f} "
          f"({summary['action_lines']} lines)")
    print(f"dispatch accept rate:   {summary['dispatch_accept_rate']:.3f} "
          f"({summary['dispatch_tasks']} tasks)")
    print(f"skill hit rate:         {summary['skill_hit_rate']:.3f}")
    print(f"unsupported:            {summary['unsupported']}")
    for entry in report["tasks"]:
        if entry.get("supported") is False:
            print(f"  {entry['id']}: unsupported ({entry.get('error', '')})")
        elif entry["kind"] == "action":
            print(f"  {entry['id']}: valid {entry['valid']}/{entry['total']} "
                  f"skill_hit={entry.get('skill_hit')} "
                  f"prose={entry['prose']}")
        else:
            print(f"  {entry['id']}: accepted={entry['accepted']}" +
                  (f" ({entry.get('error')})" if not entry["accepted"]
                   else f" deploys={entry['deploys']} "
                        f"steps={entry['steps']}"))
    name = f"/out/eval_report_{label}.json"
    with open(name, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    out_vol.commit()
    print(f"report: {name}")
    return {"label": label, "summary": summary, "report": name}


@app.local_entrypoint()
def main():
    res = grade.remote()
    print(f"grade done: {res['label']} {res['summary']}")
