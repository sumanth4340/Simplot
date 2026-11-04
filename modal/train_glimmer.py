"""QLoRA SFT of Muse-Glimmer-30B on Action Reasoner traces (Modal).

What it trains: chat SFT mapping TASK + snapshot -> catalog action
lines. Text-only rows (protocol + skills); stage awareness comes
from the sense watchdog's event lines, not screenshots.

Data: finetune traces_mock + traces_drills + traces_dispatch +
traces_live (458 traces; missing files are skipped).
8 stratified held out for a post-train check.

GPU: A100-80GB (4-bit 30B base + LoRA adapters + 4k context).
Time: rough estimate under ~2h for 3 epochs; watch the Modal dashboard
for actual spend. Nothing runs locally except the data upload.

Setup (once):
    modal secret create glimmer-api-key GLIMMER_API_KEY=<any-long-string>
    # no HF token needed: meta-models/Muse-Glimmer-30B is public Apache-2.0

Launch:
    modal run action-reasoner/modal/train_glimmer.py        # upload + train
Outputs (Modal Volume "reasoner-sft"):
    /out/adapter/          - LoRA adapter (use with the base for serving)
    /out/train_log.json    - loss curve + held-out generations
"""

import json
import os

import modal

MODEL_ID = "meta-models/Muse-Glimmer-30B"
GPU = "A100-80GB"
MAX_SEQ_LEN = 4096
EPOCHS = 3
LORA_R = 16
LORA_ALPHA = 32
HELD_OUT = 8
TRACE_FILES = ("traces_mock.jsonl", "traces_drills.jsonl",
               "traces_dispatch.jsonl", "traces_live.jsonl")

# Pinned 2026-11-04 via probe_versions.py; re-probe before changing.
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch==2.15.0", "torchvision==0.29.2", "pillow==13.0.0",
    "transformers==5.22.1", "datasets==5.1.0", "peft==0.21.2",
    "bitsandbytes==0.50.2", "trl==1.17.1", "accelerate==1.15.0",
    "huggingface_hub[hf_transfer]==2.4.0",
).env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})

app = modal.App("action-reasoner-train")
data_vol = modal.Volume.from_name("reasoner-sft-data", create_if_missing=True)
out_vol = modal.Volume.from_name("reasoner-sft", create_if_missing=True)
hf_vol = modal.Volume.from_name("reasoner-hf-cache", create_if_missing=True)

LOCAL_DATA = os.path.join(os.path.dirname(__file__), "..", "finetune")


@app.function(image=image, volumes={"/data": data_vol}, timeout=600)
def upload_data():
    # Files are mounted read-write; the local entrypoint writes them.
    return sorted(os.listdir("/data"))


@app.function(
    image=image,
    gpu=GPU,
    volumes={"/data": data_vol, "/out": out_vol,
             "/root/.cache/huggingface": hf_vol},
    timeout=6 * 3600,
)
def train():
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (AutoModelForImageTextToText,
                              AutoTokenizer, BitsAndBytesConfig)
    from trl import SFTConfig, SFTTrainer

    rows = []
    for name in TRACE_FILES:
        path = os.path.join("/data", name)
        if not os.path.exists(path):
            print(f"skip missing {name}")
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    assert len(rows) >= 50, f"too few traces: {len(rows)}"
    print(f"loaded {len(rows)} traces")

    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    def render(messages):
        if getattr(tok, "chat_template", None):
            return tok.apply_chat_template(messages, tokenize=False,
                                           add_generation_prompt=False)
        # Fallback when the tokenizer ships no chat template.
        parts = []
        for m in messages:
            parts.append(f"<{m['role']}>\n{m['content']}")
        return "\n".join(parts) + tok.eos_token

    # All rows are text-only (stage awareness via watchdog events).
    print(f"text rows: {len(rows)}")
    texts = [render(r["messages"]) for r in rows]
    # Stratified held-out: round-robin over (backend, drill) groups so eval
    # covers drill skills, not just the mock head of the file order.
    _groups = {}
    for _i, _r in enumerate(rows):
        _key = (_r["meta"]["backend"], _r["meta"].get("drill", "-"))
        _groups.setdefault(_key, []).append(_i)
    _eval_idx, _left = [], HELD_OUT
    _order = sorted(_groups, key=lambda k: (k[0] != "mock", k))
    while _left > 0 and any(_groups.values()):
        for _key in _order:
            if _groups[_key] and _left > 0:
                _eval_idx.append(_groups[_key].pop(0))
                _left -= 1
    _eval_set = set(_eval_idx)
    eval_texts = [t for i, t in enumerate(texts) if i in _eval_set]
    train_texts = [t for i, t in enumerate(texts) if i not in _eval_set]
    train_ds = Dataset.from_dict({"text": train_texts})
    eval_ds = Dataset.from_dict({"text": eval_texts})

    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True)
    # VLM auto class -> MuseGlimmerForConditionalGeneration (verified in
    # the local transformers mapping; has generate()). LM head for SFT
    # loss, generate() for the held-out check. Plain AutoModel gives
    # the headless base; CausalLM auto class has no MuseGlimmerConfig
    # mapping at all.
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID, quantization_config=bnb, trust_remote_code=True,
        device_map="auto")
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)
    # task_type=None: PEFT's CAUSAL_LM wrapper requires
    # prepare_inputs_for_generation, which MuseGlimmerModel lacks
    # (AttributeError, first launch). The base PeftModel + TRL loss
    # forward need only labels, which the model supports.
    peft_cfg = LoraConfig(
        r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=0.05,
        bias="none", task_type=None,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    # Filter kwargs against the installed TRL signature: SFTConfig
    # pass-through args drift across versions (e.g. warmup_ratio
    # rejected here). Prefer eval_strategy, fall back to
    # evaluation_strategy on older TRL.
    import inspect as _inspect
    _sig = _inspect.signature(SFTConfig.__init__).parameters
    _want = dict(
        output_dir="/out/adapter",
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=5,
        save_strategy="epoch",
        save_total_limit=2,
        max_seq_length=MAX_SEQ_LEN,
        packing=False,
        bf16=True,
        report_to="none",
        seed=42,
    )
    if "eval_strategy" in _sig:
        _want["eval_strategy"] = "epoch"
    elif "evaluation_strategy" in _sig:
        _want["evaluation_strategy"] = "epoch"
    _want = {k: v for k, v in _want.items() if k in _sig}
    print("SFTConfig keys:", sorted(_want))
    args = SFTConfig(**_want)
    trainer = SFTTrainer(model=model, train_dataset=train_ds,
                         eval_dataset=eval_ds, args=args)
    trainer.train()
    trainer.save_model("/out/adapter")
    tok.save_pretrained("/out/adapter")
    out_vol.commit()

    # Held-out generation check (greedy, short).
    model.eval()
    gens = []
    for text in eval_texts[:4]:
        ids = tok(text, return_tensors="pt",
                  truncation=True, max_length=MAX_SEQ_LEN - 128)
        ids = {k: v.to(model.device) for k, v in ids.items()}
        with torch.no_grad():
            out = model.generate(**ids, max_new_tokens=128, do_sample=False,
                                 pad_token_id=tok.pad_token_id)
        gens.append(tok.decode(out[0][-128:], skip_special_tokens=True))
    log = {"loss": [float(x["loss"]) for x in trainer.state.log_history
                    if "loss" in x],
           "eval_loss": [float(x["eval_loss"]) for x in trainer.state.log_history
                         if "eval_loss" in x],
           "held_out_gens": gens,
           "n_train": len(train_texts), "n_eval": len(eval_texts)}
    with open("/out/train_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    out_vol.commit()
    print(json.dumps({k: (v if k != "held_out_gens" else "...")
                      for k, v in log.items()}, indent=1)[:1500])
    return log


@app.local_entrypoint()
def main():
    import pathlib
    # Stage the jsonl trace files into the data volume (remove-then-put:
    # batch_upload has no force flag in this Modal version).
    for name in TRACE_FILES:
        try:
            data_vol.remove_file(f"/{name}")
        except Exception:
            pass
    with data_vol.batch_upload() as batch:
        for name in TRACE_FILES:
            src = pathlib.Path(LOCAL_DATA) / name
            if not src.exists():
                print(f"skip missing local {src}")
                continue
            batch.put_file(str(src), f"/{name}")
    print("uploaded:", upload_data.remote())
    print("launching QLoRA SFT on", GPU)
    log = train.remote()
    print("train done. eval_loss:", log.get("eval_loss"))
