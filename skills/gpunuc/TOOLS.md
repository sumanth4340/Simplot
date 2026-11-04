# GPUNUC Tool Knowledge (2026-11-04)

> Full detail: `TOOLS_REF.md` — 8 tools, 22 functions, ~25 knobs, 29 limits, 31 unknowns (5 scripts + 2 evidence JSON read full; no discovery.md in pack).

## Tools

### torch.cuda (PyTorch CUDA device query)
- DOES: Reports CUDA availability, device count, and device name on the sim host.
- FUNCTIONS USED:
  - `torch.cuda.is_available()`
  - `torch.cuda.device_count()`
  - `torch.cuda.get_device_name(0)`
- LIMITS-live-verified:
  - Single-GPU box only: reports exactly 1 device (RTX 3050 Laptop); multi-GPU distribution unrunnable here (failures.md scope bound).
- UNKNOWN:
  - Behavior on multi-GPU boxes (counts > 1, name indexing beyond 0) not drill-proven.

### warp (NVIDIA Warp device enumeration)
- DOES: Enumerates compute devices as source-of-truth cross-check against torch.
- FUNCTIONS USED:
  - `warp.get_devices()` (as `wp.get_devices()`)
- LIMITS-live-verified:
  - Must agree with torch: exactly `[cpu, cuda:0]` (failures.md G1; evidence/g1_devices.json).
- UNKNOWN:
  - Warp device list on multi-GPU or CPU-only hosts not drill-proven.

### isaacsim.core.simulation_manager.SimulationManager (device selection)
- DOES: Reports and selects the sim compute device; reports tensor backend and active physics engine.
- FUNCTIONS USED:
  - `SimulationManager.get_device()`
  - `SimulationManager.set_device("cuda")` / `set_device("cuda:1")`
  - `SimulationManager.get_backend()`
  - `SimulationManager.get_active_physics_engine()`
- LIMITS-live-verified:
  - Fresh sim defaults to `cpu` device / `numpy` backend (failures.md G1).
  - After `set_device("cuda")`, device is `cuda:0` but backend label stays `numpy` — tensor frontend label, not an error (failures.md G1).
  - Phantom id `set_device("cuda:1")` raises clean `ValueError(Invalid device specification...)`; sim stays healthy on `cuda:0` (failures.md G1; evidence/g1_devices.json cuda1_err).
  - Active engine observed `physx` only (evidence/g1_devices.json).
- UNKNOWN:
  - `set_device` with other spec strings (`"cpu"`, `"cuda:0"` explicit, torch.device objects) not drill-proven.
  - Behavior of get_backend under non-numpy frontends not drill-proven.

### carb.settings (Kit settings read)
- DOES: Reads renderer settings keys.
- FUNCTIONS USED:
  - `carb.settings.get_settings()`
  - `settings.get("/renderer/active")`
  - `settings.get("/renderer/activeGpuIndex")`
- LIMITS-live-verified:
  - `/renderer/activeGpuIndex` reads None — not a usable signal, never gate on it; torch/warp enumeration is source of truth (failures.md G1).
  - `/renderer/active` observed `rtx` (evidence/g1_devices.json).
- UNKNOWN:
  - Whether activeGpuIndex ever yields a valid index on other configs not drill-proven.

### isaacsim.storage.native (public asset-root API)
- DOES: Returns the configured asset root and joins relative asset paths without hardcoded endpoints.
- FUNCTIONS USED:
  - `get_assets_root_path()`
  - `path_join(root, rel)`
- LIMITS-live-verified:
  - Default hosted profile only here: remote S3-backed root (`.../Assets/Isaac/6.0`), no `ISAACSIM_ASSET_ROOT`/`..._REGION_PROFILE` overrides (failures.md G2).
  - Root resolution fast (~0 ms cached); known assets resolve in ~1 ms (failures.md G2; evidence/g2_assets.json).
  - Never hardcode endpoints; always `get_assets_root_path()` + `path_join` (failures.md G2).
- UNKNOWN:
  - Regional profiles, local packs, and availability manifests not built here (SKILL.md Limitations; upstream `isaac-sim-assets` workflows).
  - Cold-cache / first-fetch latency not drill-proven.

### pxr.Ar (USD asset resolver)
- DOES: Resolves joined asset URLs to confirm they exist.
- FUNCTIONS USED:
  - `Ar.GetResolver()`
  - `resolver.Resolve(path)`
- LIMITS-live-verified:
  - Known assets (TI radar USD, Example_Rotary_2D USDA) resolve True in ~1 ms (failures.md G2).
  - Bogus path returns False in ~889 ms: clean miss, no hang (failures.md G2; evidence/g2_assets.json missing.ms=888.6).
- UNKNOWN:
  - Resolver behavior on malformed URLs, network outage, or non-USD files not drill-proven.

### os.environ (env override check)
- DOES: Checks for asset-root env overrides.
- FUNCTIONS USED:
  - `os.environ.get("ISAACSIM_ASSET_ROOT")`
  - `os.environ.get("ISAACSIM_ASSET_REGION_PROFILE")`
- LIMITS-live-verified:
  - Both must be None for the default-hosted-profile drill (failures.md G2; verify_g2.py default-profile gate).
- UNKNOWN:
  - Effect of setting either override not drill-proven in this pack.

### Local evidence verifiers (stdlib-only gates: json/sys/time)
- DOES: Gate recorded evidence JSON offline without a live sim (G1 7 gates, G2 6 gates).
- FUNCTIONS USED:
  - `json.load` / `json.dump`
  - `sys.exit(0/1)`
  - `time.time()` (latency measurement in g2_probe.py)
- LIMITS-live-verified:
  - G1 gates: single-gpu, warp-cuda0, cuda-select, cuda1-rejected, healthy-after, engine-physx, renderer-rtx (verify_g1.py; G1 7/7 green).
  - G2 gates: default-profile, root-remote, root-fast (<5000 ms), ti-resolves, lidar-resolves, missing-clean (verify_g2.py; G2 6/6 green).
- UNKNOWN:
  - None; pure local gating logic.

## Unverified

- Multi-GPU device reporting/selection/distribution (out of scope: single-GPU box).
- Regional asset profiles, local asset packs, availability manifests (deferred to `isaac-sim-assets`).
- Cold-cache asset fetch latency and offline/network-failure resolver behavior.
- `SimulationManager.set_device` variants beyond `"cuda"` and phantom `"cuda:1"`.
- Non-PhysX engines and non-RTX renderers through this probe path.
- Whether `/renderer/activeGpuIndex` is ever a valid signal on other configs.

## Sources-read

- action-reasoner/skills/gpunuc/SKILL.md (full)
- action-reasoner/skills/gpunuc/failures.md (full)
- action-reasoner/skills/gpunuc/scripts/g1_probe.py (full)
- action-reasoner/skills/gpunuc/scripts/g1_drive.py (full)
- action-reasoner/skills/gpunuc/scripts/g2_probe.py (full)
- action-reasoner/skills/gpunuc/scripts/verify_g1.py (full)
- action-reasoner/skills/gpunuc/scripts/verify_g2.py (full)
- action-reasoner/skills/gpunuc/evidence/g1_devices.json (full)
- action-reasoner/skills/gpunuc/evidence/g2_assets.json (full)
