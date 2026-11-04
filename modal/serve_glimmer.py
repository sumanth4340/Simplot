"""Serve Glimmer 30B (BF16) on Modal as an OpenAI-compatible endpoint.

Setup (once, in your terminal):
    pip install modal
    modal setup                                   # links your Modal account
    modal secret create glimmer-api-key GLIMMER_API_KEY=<pick-any-long-random-string>
    modal secret create huggingface-secret HF_TOKEN=<your-hf-token>   # only if the model is gated

Deploy:
    modal run action-reasoner/modal/serve_glimmer.py     # downloads weights to a Volume (once)
    modal deploy action-reasoner/modal/serve_glimmer.py  # serves /v1/chat/completions (dedicated, always-on)

Test:
    curl https://<your-modal-url>/v1/chat/completions \
      -H "Authorization: Bearer <same-GLIMMER_API_KEY>" \
      -H "Content-Type: application/json" \
      -d '{"model": "glimmer-30b", "messages": [{"role": "user", "content": "say ok"}]}'
"""

import modal

# Verified 2026-11-04: public Apache-2.0 repo, BF16 safetensors (2 shards),
# processor_config (multimodal) + tokenizer. No HF token needed.
MODEL_ID = "meta-models/Muse-Glimmer-30B"

SERVED_NAME = "glimmer-30b"  # stable name our Isaac client sends as "model"
ADAPTER_NAME = "glimmer-sft"  # LoRA adapter from train (point "model" here to use it)
GPU = "A100-80GB"  # BF16 30B needs ~60GB for weights; 80GB leaves room for KV cache.
# NVFP4 weights would need Blackwell ("B200") instead; they cannot run on A100.
MAX_MODEL_LEN = 16384  # raise toward 32768 only if stable; VRAM is tight at 80GB
MAX_LORA_RANK = 16  # must cover train LORA_R
VLLM_PORT = 8000
MODEL_DIR = "/model"
ADAPTER_DIR = "/adapter"  # reasoner-sft volume root (train writes /out/adapter)

# Pinned 2026-11-04 via probe_versions.py; re-probe before changing.
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.32.0", "huggingface_hub[hf_transfer]==2.4.0")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("action-reasoner-glimmer")
volume = modal.Volume.from_name("glimmer-weights", create_if_missing=True)
adapter_vol = modal.Volume.from_name("reasoner-sft", create_if_missing=True)


@app.function(
    image=image,
    volumes={MODEL_DIR: volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=7200,
)
def download_model():
    import os

    from huggingface_hub import snapshot_download

    snapshot_download(repo_id=MODEL_ID, local_dir=MODEL_DIR,
                      token=os.environ.get("HF_TOKEN"))
    volume.commit()


@app.function(
    image=image,
    gpu=GPU,
    volumes={MODEL_DIR: volume, ADAPTER_DIR: adapter_vol},
    secrets=[modal.Secret.from_name("glimmer-api-key")],
    min_containers=1,  # dedicated: always-on GPU, no cold starts
    timeout=24 * 3600,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=VLLM_PORT, startup_timeout=30 * 60)
def serve():
    import os
    import pathlib
    import subprocess

    cmd = [
        "vllm", "serve", MODEL_DIR,
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--served-model-name", SERVED_NAME,
        "--max-model-len", str(MAX_MODEL_LEN),
        "--api-key", os.environ["GLIMMER_API_KEY"],
        "--trust-remote-code",
    ]
    # LoRA only when the trained adapter is on the volume, so the same
    # deploy serves the base model before training and glimmer-sft after.
    if (pathlib.Path(ADAPTER_DIR) / "adapter").is_dir():
        cmd += ["--enable-lora",
                "--max-lora-rank", str(MAX_LORA_RANK),
                "--lora-modules", f"{ADAPTER_NAME}={ADAPTER_DIR}/adapter"]
    subprocess.Popen(cmd)


@app.local_entrypoint()
def main():
    download_model.remote()
    print("weights cached; now run: modal deploy action-reasoner/modal/serve_glimmer.py")
