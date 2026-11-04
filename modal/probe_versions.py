"""CPU probe: record today's resolved pip versions for image pinning.

Builds the same images train/serve use, then prints installed
versions as JSON. Re-run before editing pins; paste the output into
the pip_install lists it names. CPU-only, costs ~nothing.

Launch:
    modal run action-reasoner/modal/probe_versions.py
"""
import modal

# NOTE: this probe intentionally floats (no == pins) — it reports
# what a fresh resolve installs so the other images can pin to it.
TRAIN_PKGS = ["torch", "torchvision", "pillow", "transformers",
              "datasets", "peft", "bitsandbytes", "trl", "accelerate",
              "huggingface_hub[hf_transfer]"]
SERVE_PKGS = ["vllm", "huggingface_hub[hf_transfer]"]

train_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    *TRAIN_PKGS)
serve_image = modal.Image.debian_slim(python_version="3.12").pip_install(
    *SERVE_PKGS)

app = modal.App("action-reasoner-versions")


def _versions():
    import importlib.metadata as md
    out = {}
    for dist in ("torch", "torchvision", "pillow", "transformers",
                 "datasets", "peft", "bitsandbytes", "trl",
                 "accelerate", "huggingface_hub", "vllm"):
        try:
            out[dist] = md.version(dist)
        except md.PackageNotFoundError:
            out[dist] = None
    return out


@app.function(image=train_image, timeout=600)
def train_versions():
    return _versions()


@app.function(image=serve_image, timeout=1800)
def serve_versions():
    return _versions()


@app.local_entrypoint()
def main():
    import json
    print("train-image:")
    print(json.dumps(train_versions.remote(), indent=1))
    print("serve-image:")
    print(json.dumps(serve_versions.remote(), indent=1))
