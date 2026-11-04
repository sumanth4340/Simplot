"""CPU probe: inspect Glimmer-30B repo config before the GPU run.

Downloads only config + tokenizer (megabytes, no GPU) and reports the
architecture, model type, vision tower presence, and chat-template
status the training script depends on. Run first; costs ~nothing.

Launch:
    modal run action-reasoner/modal/probe_glimmer.py
"""

import modal

MODEL_ID = "meta-models/Muse-Glimmer-30B"

# Pinned 2026-11-04 via probe_versions.py; re-probe before changing.
image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "torch==2.15.0", "transformers==5.22.1",
    "huggingface_hub[hf_transfer]==2.4.0",
).env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})

app = modal.App("action-reasoner-probe")


@app.function(image=image, timeout=900)
def probe():
    from transformers import AutoConfig, AutoTokenizer

    import inspect

    from transformers import MuseGlimmerForConditionalGeneration

    cfg = AutoConfig.from_pretrained(MODEL_ID, trust_remote_code=True)
    tok = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    sig = inspect.signature(MuseGlimmerForConditionalGeneration.forward)
    pix = sig.parameters.get("pixel_values")
    print("forward pixel_values default:",
          pix.default if pix is not None else "NO-PARAM")
    report = {
        "architectures": getattr(cfg, "architectures", None),
        "model_type": getattr(cfg, "model_type", None),
        "has_vision_config": getattr(cfg, "vision_config", None) is not None,
        "has_text_config": getattr(cfg, "text_config", None) is not None,
        "vocab_size": getattr(cfg, "vocab_size", None),
        "tokenizer_class": type(tok).__name__,
        "has_chat_template": bool(getattr(tok, "chat_template", None)),
        "pad_token": str(getattr(tok, "pad_token", None)),
        "eos_token": str(getattr(tok, "eos_token", None)),
    }
    for key, value in report.items():
        print(f"{key}: {value}")
    return report


@app.local_entrypoint()
def main():
    report = probe.remote()
    print("probe done:", report)
