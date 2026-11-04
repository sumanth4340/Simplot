---
name: sdg
description: >
  Synthetic data generation on Isaac Sim 6 — Replicator basics (rgb, bbox,
  semseg, writers, variation) plus KITTI datasets, seeded deterministic
  layouts, and 50-frame volume sweeps. Use when capturing annotated
  frames, writing KITTI datasets, seeding deterministic scenes, or
  running volume sweeps.
metadata:
  validated: 2026-11-04
  validated_by: S1-S4/V12/X12 + A1/A2/A3/VA all green on Isaac Sim 6.0.0/Kit 110
---

# sdg

## Purpose

Two layers, validated live on Isaac Sim 6.0.0 / Kit 110
(windowed GUI, Windows):

- `base/` — Replicator basics: rgb (S1), bbox + semseg (S2),
  writers (S3), variation (S4) + V12 exam + X12 cross-val.
- `adv/` — KittiWriter datasets (A1), seeded deterministic
  layouts (A2), 50-frame volume sweeps (A3) + VA re-sweep exam.

Merged 2026-11-04 from the `sdg` and `sdg-adv` packs; drill
tags are namespaced per part (base S1-S4/V12, adv A1-A3/VA).

## Routing

| Signal | Part | Drills |
|---|---|---|
| rgb/bbox/semseg annotators, BasicWriter, variation | `base/` | S1-S4, V12, X12 |
| KITTI format, seeded layouts, volume capture | `adv/` | A1-A3, VA |

## Prerequisites

- `base/` procedures before `adv/` (A-drills build on S1-S4).
- Pixel checks run under `$ISAAC_SIM_DIR/python.bat` (PIL
  lives only there): `adv/scripts/pngstats.py`.

## Limitations

- BasicWriter RGB is pure black in interactive Kit while bbox
  is correct (base R3 OPEN); drill pattern = BasicWriter for
  structured data + DIRECT annotator reads saved in-script.
- KittiWriter `instance/` + `depth/` uint16 outputs are
  silently missing in Kit; take them via direct reads.
- Bbox instance set freezes at first capture per sim boot
  (restart to reset); plan multi-drill captures around one
  frozen set. `semantic_segmentation` stays live (exempt).

## Key procedures

### Interactive-Kit chain (base)

rep.create.camera + `with cam: rep.modify.pose(position,
look_at)` + rep.create.render_product (camera ITEM, not path)
+ AnnotatorRegistry annotators + `await
rep.orchestrator.step_async()` (sync step is standalone-only).
Annotator payloads: rgb bare (240,320,4) uint8 array; bbox
dict {data:[(id,x0,y0,x1,y1,...)], info:{idToLabels,
primPaths}}; semseg dict {data:(240,320) uint32, info}.
add_labels(prim, labels=[...]) — labels keyword-only.
BasicWriter: FLAT layout (rgb_NNNN.png, *_NNN.npy,
_labels/_prim_paths JSONs, metadata.txt) — no subdirs.

### Writer discipline (base + adv)

Never block in Writer.write(): get_data()+np.save killed the
whole capture for all writers (R4); detach_all() at every
capture start (stale writers survive sends). Warm up FIRST
(120 app updates + 1 step), attach the writer AFTER (attach
counts warmup steps as frame 0), detach EXPLICITLY
(`writer.detach()`) at each capture's end. Guard every
`detach_all()` in try/except: a skipped detach survives, a
crashed one poisons the next run.

### Label-before-first-capture (adv)

Bbox annotators freeze the labeled INSTANCE set at first
capture: new instances never join, removed ones never return.
Procedure: label everything before the first capture; share
one frozen set across drills by design (A2/A3/VA share
`abox`); restart the sim to reset.

### KittiWriter contract (adv)

`initialize(output_dir, use_kitti_dir_names=True,
omit_semantic_type=True, mapping_dict={lowercase: RGBA})`.
Layout: `Camera/image_02/`, `label_02/`, `semantic/`,
`semantic_rgb/`. Label rows carry boxes only; boxes <25px
tall are discarded. `mapping_dict` keys MUST be lowercase.
Semantic ids are 0-based with background folded into 0:
separate class 0 from bg via instance/semrgb, never the map.

### Seeded determinism (adv)

Seeded `np.default_rng` poses + scripted USD translates give
bit-identical layouts across runs (A2 leg0==leg1 exact; do
NOT use `rep.set_global_seed` for this). Bbox annotator data
is a 1-D STRUCTURED array (`semId,x0,y0,x1,y1`): index rows,
never `[:, i]`. Volume reference: 50-frame KITTI sweep, 23 s
cold (2.2 fps incl. material warmup), ~4 s warm (13.7 fps).

## Drills

| Drill | Claim | Verifier |
|---|---|---|
| base S1 rgb | 5/5, (240,320,4) uint8, mean 63.66 | `base/scripts/verify_s1.py` |
| base S2 bbox+semseg | 7/7, 1 box area 7225, 5847 cube px | `base/scripts/verify_s2.py` |
| base S3 writers | 9/9, 3 rgb + 3 bbox npy + labels JSONs | `base/scripts/verify_s3.py` |
| base S4 variation | 4/4, xmins monotonic, spread 117 | `base/scripts/verify_s4.py` |
| base V12 exam | 13/13, 2 props x 3 poses x 3 modalities | `base/scripts/verify_v12.py` |
| adv A1 KittiWriter | 4-frame set, 2-row labels, rgb, sem maps | `adv/scripts/verify_a1.py` |
| adv A2 seeded | same seed identical, diff seed different | `adv/scripts/verify_a2.py` |
| adv A3 sweep | 50-frame capture + fps report | `adv/scripts/verify_a3.py` |
| adv VA exam | 12-frame re-sweep, new seed, live re-attach | `adv/scripts/verify_va.py` |

Cross-val: base X12 (8/8 across stage/model/sense/rig/sem/sdg).

## Related skills

- RECEIVES from: `data-collection-sim` (headless SDG patterns).
- PRODUCES for: dataset consumers (training pipelines),
  `rendering-lighting` (capture quality).

## Failure index

Details, bisection logs, and ruled-out causes: `failures.md`
(base R1-R5, R3 open; adv R6-R10 + ruled-out list).

## References

- Base tools: `base/scripts/s1_build/s1_run`,
  `s2_build/s2_run`, `s3_run`, `s4_run`, `v12_build/v12_run`,
  `probe_rep/chain/sem/wr/bw/bb3/hide`, `verify_sN/verify_v12`.
- Adv tools: `adv/scripts/a1_build.py`, `a1_run.py`, `a2_*`,
  `a3_*`, `va_run.py`, `verify_a1/a2/a3/va.py`, `pngstats.py`.
- Evidence: `base/evidence/`, `adv/evidence/`
  (`a1_out`, `a2_layouts_*.npy`, `a3_out`, `va_out`).

## Iteration Log

- v1.0 2026-11-04: merged `sdg` + `sdg-adv` packs into `sdg`
  (base/adv); drill scripts and evidence unchanged apart from
  path updates.
- v0.1 2026-11-04: `sdg-adv` distilled from A1/A2/A3/VA (MSF Capture).
