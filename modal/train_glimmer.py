"""QLoRA SFT of Muse-Glimmer-30B on Action Reasoner traces (Modal).

What it trains: chat SFT mapping TASK + snapshot -> catalog action
lines. Phase A: text-only rows (protocol + skills). Phase B: live
screenshot rows (15 vis captures) through the vision tower, same adapter.

Data: finetune traces_mock + traces_drills + traces_dispatch +
traces_live + traces_vision (451 traces; missing files are skipped).
8 stratified held out for a post-train check. Phase B vision SFT runs
on rows with images (same adapter, 1 epoch).

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
VIS_EVAL_ROWS = 2  # first N vision rows held out (stable as data grows)


def split_vision_eval(vis_rows, n_eval=VIS_EVAL_ROWS):
    """Split vision rows into (train, eval); eval = first rows, stable."""
    vis_rows = list(vis_rows)
    if len(vis_rows) <= n_eval:
        return vis_rows, []
    return vis_rows[n_eval:], vis_rows[:n_eval]
TRACE_FILES = ("traces_mock.jsonl", "traces_drills.jsonl",
               "traces_dispatch.jsonl", "traces_live.jsonl",
               "traces_vision.jsonl")

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


# Plain helper (NOT a Modal function): phase B runs in-process inside
# train()'s GPU container, sharing the loaded model. A decorator here
# would only mislead — remote execution could never receive `model`.
def _vision_phase(model, vis_rows, tok):
    """Phase B: vision SFT over live-captured rows (1 epoch, low LR).

    Formats each row as image + chat text via the model processor,
    masks the prompt, and trains with plain transformers.Trainer
    (avoids TRL multimodal quirks). Raises on any failure so the
    caller can skip loudly with phase A intact.
    """
    import torch
    from PIL import Image
    from torch.utils.data import Dataset as TorchDataset
    from transformers import (AutoProcessor, Trainer, TrainingArguments,
                              default_data_collator)

    processor = AutoProcessor.from_pretrained(MODEL_ID,
                                              trust_remote_code=True)
    if getattr(processor, "tokenizer", None) is not None:
        if processor.tokenizer.pad_token is None:
            processor.tokenizer.pad_token = processor.tokenizer.eos_token
    pad_id = processor.tokenizer.pad_token_id

    train_rows, eval_rows = split_vision_eval(vis_rows)

    def _encode(subset):
        sub = []
        for r in subset:
            img_rel = r["meta"]["image_files"][0]
            im = Image.open(os.path.join("/data", img_rel)).convert("RGB")
            sys_c, usr_c, asst_c = (m["content"] for m in r["messages"])
            msgs = [
                {"role": "system",
                 "content": [{"type": "text", "text": sys_c}]},
                {"role": "user", "content": [
                    {"type": "image"},
                    {"type": "text", "text": usr_c}]},
                {"role": "assistant",
                 "content": [{"type": "text", "text": asst_c}]},
            ]
            full = processor.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=False)
            pre = processor.apply_chat_template(
                msgs[:2], tokenize=False, add_generation_prompt=True)
            enc = processor(text=full, images=im, return_tensors="pt",
                            truncation=True, max_length=MAX_SEQ_LEN)
            enc_pre = processor(text=pre, images=im, return_tensors="pt",
                                truncation=True, max_length=MAX_SEQ_LEN)
            input_ids = enc["input_ids"][0]
            labels = input_ids.clone()
            labels[:enc_pre["input_ids"].shape[1]] = -100
            item = {"input_ids": input_ids,
                    "attention_mask": enc["attention_mask"][0],
                    "labels": labels}
            for _k, _v in enc.items():
                if _k not in ("input_ids", "attention_mask"):
                    item[_k] = _v[0]  # pixel_values, image_grid_thw, ...
            sub.append(item)
        return sub

    train_items = _encode(train_rows)
    eval_items = _encode(eval_rows)
    max_len = max(int(t["input_ids"].numel())
                  for t in train_items + eval_items)
    import torch.nn.functional as F
    for t in train_items + eval_items:
        pad = max_len - int(t["input_ids"].numel())
        if pad:
            t["input_ids"] = F.pad(t["input_ids"], (0, pad),
                                   value=pad_id)
            t["attention_mask"] = F.pad(t["attention_mask"], (0, pad),
                                        value=0)
            t["labels"] = F.pad(t["labels"], (0, pad), value=-100)

    class _DS(TorchDataset):
        def __init__(self, rows):
            self._rows = rows

        def __len__(self):
            return len(self._rows)

        def __getitem__(self, i):
            return self._rows[i]

    vargs = TrainingArguments(
        output_dir="/out/adapter_phase_b", num_train_epochs=1,
        per_device_train_batch_size=2, per_device_eval_batch_size=2,
        gradient_accumulation_steps=2,
        learning_rate=5e-5, lr_scheduler_type="cosine",
        logging_steps=1, save_strategy="no", bf16=True,
        eval_strategy="epoch",
        report_to="none", seed=42, remove_unused_columns=False)
    vtrainer = Trainer(model=model, args=vargs, train_dataset=_DS(train_items),
                       eval_dataset=_DS(eval_items) if eval_items else None,
                       data_collator=default_data_collator)
    vtrainer.train()
    return {"rows": len(vis_rows), "n_train": len(train_items),
            "n_eval": len(eval_items), "status": "trained",
            "loss": [float(x["loss"]) for x in vtrainer.state.log_history
                     if "loss" in x],
            "eval_loss": [float(x["eval_loss"])
                          for x in vtrainer.state.log_history
                          if "eval_loss" in x]}


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

    # Phase A trains text-only rows; vision rows (whose tasks need
    # pixels) train in phase B below.
    text_rows = [r for r in rows if not r["meta"].get("images")]
    vis_rows = [r for r in rows if r["meta"].get("images")]
    print(f"text rows: {len(text_rows)}, vision rows: {len(vis_rows)}")
    rows = text_rows
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
    # loss, generate() for the held-out check, pixel_values path for
    # phase B. Plain AutoModel gives the headless base; CausalLM auto
    # class has no MuseGlimmerConfig mapping at all.
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

    # ---- Phase B: vision SFT on live-captured rows (same adapter). ----
    # Any failure here skips loudly; phase A artifacts are already saved.
    phase_b = {"rows": len(vis_rows), "status": "skipped: no vision rows"}
    if vis_rows:
        try:
            phase_b = _vision_phase(model, vis_rows, tok)
            trainer.save_model("/out/adapter")
            out_vol.commit()
        except Exception as exc:
            print(f"VISION PHASE SKIPPED: {exc!r}")
            phase_b = {"rows": len(vis_rows),
                       "status": "skipped: %r" % (exc,)}

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
           "n_train": len(train_texts), "n_eval": len(eval_texts),
           "phase_b": phase_b}
    with open("/out/train_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    out_vol.commit()
    print(json.dumps({k: (v if k != "held_out_gens" else "...")
                      for k, v in log.items()}, indent=1)[:1500])
    return log


@app.local_entrypoint()
def main():
    import pathlib
    # Stage the two jsonl files into the data volume (remove-then-put:
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
        img_dir = pathlib.Path(LOCAL_DATA) / "images"
        if img_dir.is_dir():
            for png in sorted(img_dir.glob("*.png")):
                try:
                    data_vol.remove_file(f"/images/{png.name}")
                except Exception:
                    pass
                batch.put_file(str(png), f"/images/{png.name}")
            print("images staged:",
                  len(list(img_dir.glob("*.png"))))
    print("uploaded:", upload_data.remote())
    print("launching QLoRA SFT on", GPU)
    log = train.remote()
    print("train done. eval_loss:", log.get("eval_loss"))
