---
name: gpunuc
description: Device honesty (G1) and asset-root resolution (G2) drills — single-GPU enumeration/selection with phantom-id negative test, and public-API asset resolution with clean-miss diagnosis. Use when checking GPU visibility, selecting sim devices, or diagnosing missing assets.
metadata:
  validated: 2026-11-04
  validated_by: G1 7/7 + G2 6/6 green on Isaac Sim 6.0.0/Kit 110
---

# gpunuc

## Purpose

Pin the platform layer beneath every drill: honest device reporting
and selection on a single-GPU box (G1), and asset-root resolution
through the public storage API with clean-miss behavior (G2).
Validated live on Isaac Sim 6.0.0 / Kit 110 + one RTX 3050 4 GB
(G1-PASS 7/7, G2-PASS 6/6).

## Prerequisites

- `isaac-sim-assets` (root precedence, profiles, local packs).

## Limitations

- Single-GPU scope bound: multi-GPU DISTRIBUTION is not runnable
  here; G1 verifies reporting/selection, nothing more.
- Default hosted (remote) profile only; regional profiles and
  local packs follow the `isaac-sim-assets` workflows, unbuilt here.

## Key procedures

### Device honesty check (G1)

Enumerate via torch AND warp (agree: exactly `[cpu, cuda:0]`);
`SimulationManager` default device is cpu/numpy on a fresh sim;
`set_device("cuda")` -> cuda:0 (backend label stays numpy: tensor
frontend label, not an error). Negative-test phantom ids:
`set_device("cuda:1")` must raise clean `ValueError` with the sim
healthy after. `/renderer/activeGpuIndex` reads None: not a usable
signal, never gate on it. See `scripts/g1_probe.py`,
`scripts/g1_drive.py`, `evidence/g1_devices.json`.

### Asset-root resolution (G2)

Resolve ONLY via `get_assets_root_path()` + `path_join` (never
hardcode endpoints). Known assets (TI radar USD,
Example_Rotary_2D USDA) resolve in ~1 ms cached; a bogus path
returns False in <1 s: clean miss, no hang. No
`ISAACSIM_ASSET_ROOT`/`..._REGION_PROFILE` overrides here
(default hosted profile). This pins the resolution layer beneath
the R1/N2 config-reference loads. See `scripts/g2_probe.py`,
`evidence/g2_assets.json`.

## Related skills

- RECEIVES from: `isaac-sim-assets` (profiles, precedence).
- PRODUCES for: all packs (platform preflight).

## Failure index

`failures.md` (scope bound, G1/G2 notes).

## References

- Scripts: `scripts/g1_probe.py`, `g1_drive.py`, `verify_g1.py`,
  `scripts/g2_probe.py`, `verify_g2.py`.
- Upstream: `docs/.../installation/accessing_assets.html` (profiles,
  manifests, packs) via `isaac-sim-assets`.

## Iteration Log

- v0.1 2026-11-04: distilled from G1/G2 drills (MSF Capture).
