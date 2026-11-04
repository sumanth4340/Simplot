"""Run any shell command inside the serve container spec (no script edits).

Windows can't use `modal shell`, so this is the equivalent: one generic
runner, new commands pass via --cmd, the file never changes.

Usage:
    modal run action-reasoner/modal/exec.py --cmd 'ls /model'
    modal run action-reasoner/modal/exec.py --cmd 'du -sh /model/*' --gpu   # A100 attached
    modal run action-reasoner/modal/exec.py --cmd 'python -c "import vllm; print(vllm.__version__)"'

Notes:
  - Same image, volumes (/model, /adapter) and secrets as serve_glimmer.py.
  - CPU by default (cheap); --gpu attaches the A100 (billed while running).
  - This is a FRESH container per run, not the live vLLM process: it sees the
    same volumes but cannot touch the running server. Kill output with Ctrl-C;
    the container stops when the command ends.
"""

import modal

GPU = "A100-80GB"
MODEL_DIR = "/model"
ADAPTER_DIR = "/adapter"

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.1-devel-ubuntu22.04", add_python="3.12")
    .pip_install("vllm==0.32.0", "huggingface_hub[hf_transfer]==2.4.0")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

app = modal.App("action-reasoner-exec")
volume = modal.Volume.from_name("glimmer-weights", create_if_missing=True)
adapter_vol = modal.Volume.from_name("reasoner-sft", create_if_missing=True)


@app.function(
    image=image,
    volumes={MODEL_DIR: volume, ADAPTER_DIR: adapter_vol},
    secrets=[
        modal.Secret.from_name("glimmer-api-key"),
        modal.Secret.from_name("huggingface-secret"),
    ],
    timeout=3600,
)
def run_cpu(cmd: str) -> str:
    return _run(cmd)


@app.function(
    image=image,
    gpu=GPU,
    volumes={MODEL_DIR: volume, ADAPTER_DIR: adapter_vol},
    secrets=[
        modal.Secret.from_name("glimmer-api-key"),
        modal.Secret.from_name("huggingface-secret"),
    ],
    timeout=3600,
)
def run_gpu(cmd: str) -> str:
    return _run(cmd)


def _run(cmd: str) -> str:
    import subprocess

    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3300)
    out = f"$ {cmd}\n[exit {p.returncode}]\n{p.stdout}"
    if p.stderr:
        out += f"\n[stderr]\n{p.stderr}"
    return out


@app.local_entrypoint()
def main(cmd: str, gpu: bool = False):
    fn = run_gpu if gpu else run_cpu
    print(fn.remote(cmd))
