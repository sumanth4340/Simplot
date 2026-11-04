# gpunuc G1+G2 -- Notes (live-verified, Isaac Sim 6.0 / Kit 110)

## Scope bound (hardware)
- Single GPU box: 1x RTX 3050 Laptop 4GB (2.5GB free during drills).
  Multi-GPU DISTRIBUTION is not runnable here; G1 verifies honest
  device reporting + selection instead of pretending otherwise.

## G1 devices (7/7)
- torch/warp agree: cuda available, exactly [cpu, cuda:0].
- `SimulationManager` default device is cpu/numpy on a fresh sim;
  `set_device("cuda")` -> cuda:0 (backend label stays numpy -- that
  is the tensor frontend label, not an error).
- Negative test: `set_device("cuda:1")` raises clean
  `ValueError(Invalid device specification...)` and the sim stays
  healthy on cuda:0. No phantom devices.
- `/renderer/activeGpuIndex` setting reads None (not a usable signal;
  torch/warp enumeration is the source of truth). Not gated.

## G2 asset root (6/6)
- No `ISAACSIM_ASSET_ROOT` / `ISAACSIM_ASSET_REGION_PROFILE` overrides:
  default hosted profile, remote S3-backed root
  (`.../Assets/Isaac/6.0`). Resolved via public API only.
- Known assets (TI radar USD, Example_Rotary_2D USDA) resolve in ~1ms
  (cached); a bogus path returns False in 889ms -- clean miss, no hang.
  Per skill: never hardcode the endpoint; always
  `get_assets_root_path()` + `path_join`.
- R1/N2 already proved end-to-end loads from this root (config
  references); G2 pins the resolution layer beneath them.
