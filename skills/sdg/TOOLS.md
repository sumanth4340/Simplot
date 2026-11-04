# SDG Tool Knowledge (2026-11-04)

> Exhaustive per-tool reference: `TOOLS_REF.md` (15 tools,
> 60 functions, 34 knobs, 31 limits, 23 unknowns, every
> claim tagged verified/probable/theoretical).

Tool/API/CLI surface used by the `sdg` pack (base S1-S4/V12/X12 + adv
A1-A3/VA), all live-verified on Isaac Sim 6.0.0 / Kit 110, windowed GUI,
Windows. In-sim scripts run via the bridge (top-level `await` supported,
`--file` takes no args — multi-leg scripts hardcode legs, e.g. a2_run).

## Tools

### omni.replicator.core orchestrator + camera + render product
- DOES: drives stepped capture: manual stepping, camera creation/posing,
  render-product creation.
- FUNCTIONS USED:
  - `rep.orchestrator.set_capture_on_play(False)` — manual step control
    before every capture
  - `await rep.orchestrator.step_async()` — advance one frame in Kit
  - `await rep.orchestrator.wait_until_complete_async()` — drain backend
    before reading files
  - `rep.create.camera()` + `with cam: rep.modify.pose(position=, look_at=)`
    — camera pose via context manager only
  - `rep.create.render_product(cam, (320, 240))` — RP from camera ITEM
- LIMITS-live-verified:
  - Sync `step()`/`wait` raise OrchestratorError in Kit — always
    `step_async` (failures.md base R1-F3).
  - Direct `rep.modify.pose(cam, ...)` raises TypeError ("multiple values
    for 'position'") — use the `with cam:` pattern (base R1-F1).
  - `rep.create.render_product(cam.GetPath(), ...)` fails —
    ReplicatorItem has no GetPath; pass the item (base R1-F2).
  - First-frame reads on a fresh sim are empty until the renderer warms
    up — 120 app updates first (failures.md adv ruled-out list).
- UNKNOWN:
  - Behavior in headless/standalone flows (pack ran interactive Kit only).
  - Resolutions other than 320x240; multi-RP capture (2-RP black-RGB
    check in R3 suggests multi-RP runs, but no drill gates it).

### rep.AnnotatorRegistry + rgb / bbox_2d_tight / semantic_segmentation
- DOES: per-frame tensor readback attached to a render product.
- FUNCTIONS USED:
  - `rep.AnnotatorRegistry.get_annotator("rgb" | "bounding_box_2d_tight" | "semantic_segmentation")`
  - `ann.attach(rp)`, `ann.get_data()`, `ann.detach(rp)`
  - rgb payload: bare (H,W,4) uint8 array; bbox: dict
    `data=[(semId,x0,y0,x1,y1,...)]` + `info{idToLabels, primPaths}`;
    semseg: dict `data=(H,W)` uint32 + `info{idToLabels}`
- LIMITS-live-verified:
  - Bbox annotators freeze the labeled INSTANCE set at first capture:
    later-labeled prims invisible (n=1 then n=0 with the one hidden),
    new instances never join, removed never return — label everything
    before the first capture; restart sim to reset (base R5, adv R7;
    A2/A3/VA share one frozen `abox` set by design).
  - `semantic_segmentation` stays live per-frame (exempt from the
    freeze) (base R5, adv R7 note).
  - Adv bbox `data` is a 1-D STRUCTURED array (fields
    semId,x0,y0,x1,y1): index rows (`r[0..4]`), never `[:, i]`
    (discovery.md adv; a2_run.py).
  - After a USD pose edit, the first step absorbs the edit — read boxes
    from the second step (a2_run.py two-step pattern).
- UNKNOWN:
  - `bounding_box_2d_loose` payload details (only named in R5 as equally
    frozen; no drill gates its boxes).
  - `instance_segmentation` / `depth` direct-read take (R8 prescribes
    it, but no drill demonstrates it).
  - Whether the bbox freeze also applies to re-added prims at the same
    path vs new paths.

### BasicWriter (via rep.WriterRegistry)
- DOES: writes structured annotation files (bbox .npy + labels/prim-path
  JSONs) to a flat output dir.
- FUNCTIONS USED:
  - `rep.WriterRegistry.get("BasicWriter")`
  - `bw.initialize(output_dir=, rgb=False, bounding_box_2d_tight=True)`
  - `bw.attach(rp)`, `bw.detach()`
  - `rep.WriterRegistry.detach_all()` at every capture start
- LIMITS-live-verified:
  - RGB path writes pure-black PNGs in interactive Kit (0.00 across 8
    frames/2 RPs) while direct rgb reads give 63.69 — OPEN, use
    BasicWriter for structured data + direct reads for pixels
    (base R3 OPEN; evidence/base/probe_bw, s3_out).
  - Layout is FLAT: `rgb_NNNN.png`, `bounding_box_2d_tight_NNNN.npy`,
    `_labels/_prim_paths` JSONs, `metadata.txt` — no per-modality
    subdirs; glob flat patterns (base R2).
  - Bbox file content matches direct reads exactly (117,79,202,164,
    class s2cube) — bbox path CORRECT in Kit (base R3).
- UNKNOWN:
  - Whether BasicWriter RGB works in headless/standalone (hypothesis in
    R3 says writers are validated for those flows — not drilled here).
  - Other BasicWriter modalities (normals, depth, semantic) through this
    writer.

### KittiWriter (via rep.WriterRegistry)
- DOES: writes KITTI-format datasets: images, label txt, semantic maps.
- FUNCTIONS USED:
  - `rep.WriterRegistry.get("KittiWriter")`
  - `kw.initialize(output_dir=, use_kitti_dir_names=True, omit_semantic_type=True, mapping_dict={lowercase: RGBA})`
  - `kw.attach(rp)`, `kw.detach()`, `kw.num_written`
  - `inspect.signature(kw.initialize)` to print the init signature
    (probe_kitti.py)
- LIMITS-live-verified:
  - `instance/` + `depth/` (uint16 PNG backend) are silently missing —
    not even dirs, no log errors; gate rgb/labels/semantic only, take
    instance/depth via direct reads (adv R8; evidence/a1_out, a3_out).
  - Default labels embed a dict REPR WITH A SPACE
    (`"{'class': 'kboxa'}"`) — naive `.split()` shifts every field; use
    `omit_semantic_type=True` for plain tokens (adv R9).
  - Class names are case-FOLDED (`kboxA` -> `kboxa`); mapping_dict keys
    MUST be lowercase or nothing matches (all-zero sem map) (adv R9).
  - Semantic ids are 0-based with background folded into 0
    (bg+kboxa=0, kboxb=1): first class inseparable from bg in the sem
    map — separate via instance/semrgb (adv R9).
  - Label rows carry boxes only: `class 0.00 occ 0.00 x0 y0 x1 y1` + 7x
    `0.00` (alpha/dims/location/rot/score unsupported); boxes <25px tall
    discarded (discovery.md adv).
  - Attach AFTER warmup: a pre-warmup attach writes frame 0 during
    warmup (51 files for a 50-frame sweep) (adv R10).
  - KittiWriter RGB is NOT black in Kit (mean 63.7) — base R3 does not
    apply to it (adv ruled-out list).
- UNKNOWN:
  - Full `initialize` signature text (probe prints KITTI-SIG but the
    value is not recorded in the pack).
  - More than 2 mapped classes; behavior of unmapped classes beyond
    "render as unlabelled" (discovery.md adv, single-sample).
  - Sweeps longer than 50 frames; warm-vs-cold fps beyond 13.7/2.2.

### rep.Writer subclass (custom writer pattern)
- DOES: user-defined writer attached to a render product (documented
  "direct access to annotator tensors" pattern).
- FUNCTIONS USED:
  - `rep.Writer` subclass with `write()` override; `self._frame_id = 0`
    in `__init__` (frame counters are per-instance)
- LIMITS-live-verified:
  - Blocking `get_data()`+`np.save` inside `write()` killed the WHOLE
    capture for ALL writers (zero files from either writer, only
    metadata.txt) — writers must only schedule backend work, never
    block (base R4).
- UNKNOWN:
  - Any SAFE custom-writer `write()` body: R3 names the direct-tensor
    subclass as the workaround, but R4 proves `get_data()` in `write()`
    kills capture — contested, drill pattern avoids custom writers
    entirely (BasicWriter + direct reads saved in-script).

### isaacsim.core.experimental.utils.semantics (add_labels)
- DOES: attaches semantic class labels to USD prims for bbox/semseg.
- FUNCTIONS USED:
  - `add_labels(prim, labels=[...])` — labels keyword-only; dedups on
    re-run; `get_labels` returns `{taxonomy: [...]}` (discovery.md base)
- LIMITS-live-verified:
  - Labels added AFTER the first bbox capture are invisible to bbox
    annotators (freeze, base R5) — label-before-first-capture discipline.
  - Class-name regexes in verifiers must allow digits (`[\w+]+`, not
    `[a-z+]`) (discovery.md base).
- UNKNOWN:
  - Multi-taxonomy labeling; label removal/relabel mid-session effects.

### isaacsim.core.experimental.utils.app (update_app_async)
- DOES: renderer warmup without orchestrator steps.
- FUNCTIONS USED:
  - `await app_utils.update_app_async(steps=120)` before the first
    capture step
- LIMITS-live-verified:
  - 120 updates + 1 step verified: zero boxes before, 3 boxes every
    step after (a2_run.py; adv ruled-out list).
- UNKNOWN:
  - Minimum sufficient step count (120 is proven, not minimal).

### omni.usd stage access
- DOES: reaches the live USD stage from in-sim scripts.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`; `stage.GetPrimAtPath(path)`;
    `stage.RemovePrim(path)` (probe setup teardown)
- LIMITS-live-verified: none (no failures implicate it).
- UNKNOWN:
  - Behavior on an empty/unstaged context; multi-context handling.

### pxr USD authoring (UsdGeom, UsdLux, Gf)
- DOES: scripted scene building + per-frame pose variation.
- FUNCTIONS USED:
  - `UsdGeom.Cube.Define(stage, path)`, `GetSizeAttr().Set()`
  - `UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(...))`
  - `GetOrderedXformOps()[0].Set(...)` for per-frame pose updates
  - `UsdLux.DomeLight.Define(stage, path)`, `GetIntensityAttr().Set(3000.0)`
- LIMITS-live-verified:
  - Scripted USD translates + seeded rng give bit-identical layouts
    across runs (A2 leg0==leg1 exact; evidence/a2_layouts_*.npy).
- UNKNOWN:
  - Non-cube/light prim types; material/shader authoring for SDG.

### numpy
- DOES: layout RNG, tensor math, evidence persistence, verification.
- FUNCTIONS USED:
  - `np.random.default_rng(seed)` + `uniform(-2.0, 2.0, (N, 2))` for poses
  - `np.save` / `np.load` (.npy layouts, direct rgb/sem dumps)
  - `np.asarray`, `np.unique`, `==` pixel counts, `.mean()`
- LIMITS-live-verified:
  - `np default_rng(seed)` ALONE gives deterministic layouts; do NOT use
    `rep.set_global_seed` for this (SKILL.md seeded-determinism; adv
    ruled-out list).
- UNKNOWN: none — stdlib-grade usage, fully covered by drills.

### PIL (Pillow Image)
- DOES: PNG pixel stats for writer-output verification.
- FUNCTIONS USED:
  - `Image.open(f)` + `np.asarray` in adv/scripts/pngstats.py: prints
    `path shape mean nunique` per file
- LIMITS-live-verified:
  - PIL exists ONLY under `$ISAAC_SIM_DIR/python.bat` — missing in
    system AND pixi pythons (adv ruled-out list).
- UNKNOWN: none.

### C:/isaacsim/python.bat CLI
- DOES: the only python that runs pixel checks (has PIL).
- FUNCTIONS USED:
  - `C:/isaacsim/python.bat adv/scripts/pngstats.py <files...>` (also
    invoked via subprocess from verify_a1/a3/va)
- LIMITS-live-verified:
  - Verifier-side dependency: verify_a1/a3/va shell out to it
    (adv/scripts imports: subprocess+sys).
- UNKNOWN: none.

### rep.set_global_seed (negative knowledge)
- DOES: purported global RNG seed for randomized Replicator runs.
- FUNCTIONS USED: none — deliberately NOT called.
- LIMITS-live-verified:
  - Suspected of detaching annotators (empty reads); dropping it changed
    nothing — real causes were R7 + warmup. `np default_rng` alone
    suffices (adv ruled-out list; a2_run.py NOTE).
- UNKNOWN:
  - Whether it has ANY safe use (discovery.md base still notes it "for
    randomized runs" — undrilled, do not trust).

### stdlib file/test helpers (os, shutil, glob, json, re, subprocess, sys, time, inspect)
- DOES: output-dir hygiene, file counting, report parsing, timing.
- FUNCTIONS USED:
  - `shutil.rmtree(OUT, ignore_errors=True)` + `os.makedirs(OUT)` per run
  - `os.walk` + relpath-prefix counting (`Camera/image_02`, `Camera/label_02`)
  - `json`/`re` report parsing in verify_s1/s2/s4/v12; `glob` in
    verify_s3/v12/a1/a3/va; `time.time()` fps in a3_run
- LIMITS-live-verified: none (no failures implicate them).
- UNKNOWN: none.

### Bridge send transport (top-level await, --file no-args)
- DOES: executes the in-sim scripts inside Kit.
- FUNCTIONS USED: top-level `await` in sent scripts; multi-leg scripts
  hardcode legs because `--file` takes no args (a2_run.py docstring).
- LIMITS-live-verified:
  - 50 orchestrator steps fit the bridge timeout (~3 min) (a3_run.py).
  - Stale writers survive sends — detach_all at every capture start
    (base R4 hygiene); a crashed mid-teardown detach wedges the NEXT
    capture (writer silently idle, zero files), the run after recovers —
    guard detach_all in try/except + explicit `detach()` per capture
    (adv R6).
  - 1 transient bridge hiccup seen (WinError 121, port stayed up)
    (discovery.md base session notes).
- UNKNOWN:
  - Exact bridge timeout value; max script size/duration.

## Unverified

- Headless/standalone Replicator flows (all drills interactive-Kit; R3
  hypothesizes writers behave better there — no evidence either way).
- Custom-writer safe pattern (R3 workaround vs R4 kill contradict; no
  green drill with a custom writer).
- `bounding_box_2d_loose` payload and `instance_segmentation`/`depth`
  direct-read takes (named but ungated).
- KittiWriter full init signature, 3+ classes, >50-frame sweeps.
- `rep.set_global_seed` any-safe-use (noted for randomized runs, ruled
  out for seeded layouts).
- Non-320x240 resolutions, multi-RP capture, non-cube prims, material
  authoring, multi-taxonomy labels.
- Exact bridge timeout / script limits.

## Sources-read

- action-reasoner/skills/sdg/SKILL.md (full)
- action-reasoner/skills/sdg/failures.md (full)
- action-reasoner/skills/sdg/discovery.md (full)
- action-reasoner/skills/sdg/base/scripts/s3_run.py (full)
- action-reasoner/skills/sdg/base/scripts/s2_run.py (full)
- action-reasoner/skills/sdg/base/scripts/v12_run.py (full)
- action-reasoner/skills/sdg/adv/scripts/a1_run.py (full)
- action-reasoner/skills/sdg/adv/scripts/a2_run.py (full)
- action-reasoner/skills/sdg/adv/scripts/a3_run.py (full)
- action-reasoner/skills/sdg/adv/scripts/probe_kitti.py (full)
- action-reasoner/skills/sdg/adv/scripts/pngstats.py (full)
- Skimmed by name + imports only (29 scripts): base probe_bb3/bw/chain/
  hide/rep/sem/wr, s1_build/s1_run, s2_build, s4_run, v12_build,
  verify_s1/s2/s3/s4/v12; adv a1_build, a2_build, a3_build, probe_ann/
  join/labset/warmup, va_run, verify_a1/a2/a3/va.
