# sdg TOOLS_REF — exhaustive tool reference (2026-11-04)

Companion to [TOOLS.md](TOOLS.md). One section per tool: DOES /
every function used (full call shape as observed in-pack) / every
knob + effect-of-change / EKB rules (IF/THEN/BECAUSE) / LIMITS with
cites / UNKNOWN. Claim tags: [verified] = gated by a green drill
verifier or on-disk evidence; [probable] = single-sample probe or
consistent-but-ungated observation; [theoretical] = hypothesis only.

Covers 15 tools, 60 functions, 34 knobs, 31 limits, 23 unknowns.
Scripts: 20 fully read, 17 skimmed (see Sources-read at end).
DATATYPE pass (2026-11-04): 60/60 signatures typed, 34/34 knobs
typed. Format — SIG: `name(params) -> return` with units +
defaults; TYPE (knobs): attr type + unit + default. Every slot
is grounded to `script:line` or tagged [probable]/[theoretical].
Zero bare params and zero elided signatures remain.

## 1. omni.replicator.core orchestrator + camera + render product

DOES: drives stepped capture in interactive Kit: manual step
control, camera creation/posing, render-product creation
[verified: every *_run.py + probe in the pack].

FUNCTIONS (call shapes as used in-pack):

- `rep.orchestrator.set_capture_on_play(False)` — SIG:
  `set_capture_on_play(capture_on_play: bool) -> None`.
  Units: unitless flag. Defaults: none observed — always
  passed explicitly as `False`; default value
  [theoretical-unknown]. Return value unused at every call
  site. Called once before every capture [verified:
  s1_run:9, s2_run:11, s3_run:17, s4_run:14, v12_run:17,
  probe_bw:6, probe_wr:7, a1_run:20, a2_run:20, a3_run:26,
  va_run:26, probe_kitti:42, probe_warmup:7].
- `await rep.orchestrator.step_async()` — SIG:
  `step_async() -> Coroutine[Any, Any, None]`
  [probable-return-type: awaited at top level, result never
  used]. Units: advances exactly 1 orchestrator frame/step.
  Defaults: n/a (no params) [verified: s1_run:16,
  s2_run:20, s3_run:28, s4_run:26, v12_run:34, a2_run:32,
  a3_run:49, probe_bb3:11, probe_warmup:18].
- `await rep.orchestrator.wait_until_complete_async()` —
  SIG: `wait_until_complete_async() -> Coroutine[Any, Any,
  None]` [probable-return-type: result never used]. Units:
  drains pending writer frames (count = steps since
  attach). Defaults: n/a (no params). Called after the step
  loop, before reading files or detaching [verified:
  s3_run:31, v12_run:48, probe_bw:16, probe_wr:21,
  a1_run:36, a3_run:50, va_run:50, probe_kitti:51].
- `rep.create.camera()` — SIG: `create_camera() ->
  ReplicatorItem` as used (zero args at every call site;
  any further params/defaults [theoretical-unknown]).
  Units: n/a. Returns camera item used as `with` target and
  render-product source [verified: s1_run:10, probe_bb3:3,
  probe_chain:2, v12_run:18, a1_run:21, a2_run:21].
- `rep.modify.pose(position=(x, y, z), look_at=(x, y, z))` —
  MUST be called inside `with cam:` (context binds the item).
  SIG: `pose(position: tuple[float, float, float],
  look_at: tuple[float, float, float]) -> None`. Units:
  stage distance units (meters on the default USD stage)
  [probable]. Defaults: none — both kwargs passed at every
  call site [verified: s1_run:12, s4_run:17, v12_run:33
  (position=pos var), a2_run:23, probe_bb3:5].
- `rep.create.render_product(cam, (w, h))` — SIG:
  `create_render_product(camera: ReplicatorItem,
  resolution: tuple[int, int]) -> RenderProduct`. Units:
  resolution in pixels (w, h). Defaults: none — both
  positionals passed at every call site. Only resolution
  ever passed: `(320, 240)` [verified: s1_run:13,
  probe_bb3:6, s3_run:21, v12_run:19, a1_run:24].

KNOBS + effect-of-change:

- `capture_on_play` — TYPE: `bool` | unitless |
  default [theoretical-unknown] (in-pack value always
  `False`). Effect: manual stepping — steps only advance via
  `step_async`; writers/annotators fire per explicit step
  [verified]. `True` undrilled [theoretical].
- `position` — TYPE: `tuple[float, float, float]` (XYZ) |
  meters [probable] | no default (required kwarg). Effect:
  changes framing 1:1; V12's 3 positions give 3 distinct
  views (pxa differs all frames) [verified: v12_run +
  verify_v12 "views differ"].
- `look_at` — TYPE: `tuple[float, float, float]` (XYZ
  target) | meters [probable] | no default (required
  kwarg). Effect: re-aims without moving [verified: same
  scripts; (0,0,0.5)/(0,0,0.4) used].
- Resolution — TYPE: `tuple[int, int]` (w, h) | pixels |
  no default (required positional; in-pack value always
  `(320, 240)`). Effect: rgb arrays are (240,320,4); all
  box gates assume x<=320, y<=240 [verified]. Any other
  resolution undrilled [theoretical].

EKB RULES:

- IF inside Kit THEN always `step_async`, never sync `step()`
  BECAUSE sync step raises OrchestratorError in Kit
  [verified: failures.md base R1-F3].
- IF posing a camera THEN use `with cam:
  rep.modify.pose(position=..., look_at=...)` BECAUSE a
  direct call passing the camera as first arg raises
  TypeError ("multiple values for 'position'")
  [verified: R1-F1].
- IF creating a render product THEN pass the camera ITEM
  BECAUSE ReplicatorItem has no GetPath; path-passing fails
  [verified: R1-F2].
- IF reading writer files THEN call
  `wait_until_complete_async()` first BECAUSE the backend
  lags the step loop [verified: all writer runs].
- IF first capture on a fresh sim THEN warm up (120 app
  updates + 1 step) before trusting reads BECAUSE
  first-frame reads are empty until the renderer warms up
  [verified: probe_warmup, a2_run, adv ruled-out list].

LIMITS (cites):

- L1: sync `step()`/`wait` raise OrchestratorError in Kit
  (failures.md base R1-F3) [verified].
- L2: direct pose call raises TypeError (R1-F1) [verified].
- L3: `render_product(cam.GetPath(), ...)` fails (R1-F2)
  [verified].
- L4: fresh-sim first-frame reads empty until warmup
  (adv ruled-out list; probe_warmup) [verified].

UNKNOWN:

- U1: headless/standalone stepping behavior [theoretical].
- U2: resolutions other than 320x240 [theoretical].
- U3: multi-RP capture (2-RP black-RGB check in R3 suggests
  it runs; no drill gates it) [probable-exists,
  theoretical-details].

## 2. rep.AnnotatorRegistry + rgb / bbox_2d_tight / semantic_segmentation

DOES: per-frame tensor readback attached to a render product
[verified: s1/s2/s4/v12_run, a2_run, all bbox probes].

FUNCTIONS:

- `rep.AnnotatorRegistry.get_annotator(name)` — SIG:
  `get_annotator(name: str) -> Annotator`. Units: n/a.
  Defaults: none — `name` required positionally. Names
  used: `"rgb"`, `"bounding_box_2d_tight"`,
  `"bounding_box_2d_loose"` (probe_bb3:8 only),
  `"semantic_segmentation"` [verified: s1_run:14,
  s2_run:16-17, v12_run:23-25, a2_run:25, probe_bb3:7,
  probe_sem:11-12]. Probe-only names (existence checked, no
  data gated): `"bounding_box_2d_tight_fast"`,
  `"bounding_box_2d_loose_fast"`,
  `"instance_segmentation_fast"`, `"distance_to_camera"`,
  `"camera_params"` (probe_ann:5-10; results not recorded in
  pack) [probable].
- `ann.attach(rp)` — SIG: `attach(render_product:
  RenderProduct) -> None` [probable-return: value unused].
  Units: n/a. Defaults: none — RP required positionally
  (the object returned by `rep.create.render_product`).
  Binds annotator to RP; multiple annotators per RP allowed
  (V12 attaches rgb+seg+box to one RP) [verified:
  s1_run:15, s2_run:18-19, v12_run:26-28, probe_bb3:9-10,
  probe_chain:7, a2_run:26].
- `ann.get_data()` — SIG: `get_data() -> Payload` where
  Payload = `np.ndarray[(H,W,4), uint8]` for rgb |
  `dict{data, info}` for bbox_2d_tight |
  `dict{data: (H,W) uint32, info}` for semantic_segmentation
  (schemas in PAYLOADS below). Units: pixels / class ids /
  0-255 channel values. Defaults: n/a (no params). Called
  AFTER a step; result is per-that-step [verified:
  s1_run:17, s2_run:21+26, v12_run:35-37, a2_run:51,
  probe_bb3:12, probe_warmup:19-20].
- `ann.detach(rp)` — SIG: `detach(render_product:
  RenderProduct) -> None` [probable-return: value unused].
  Units: n/a. Defaults: none — RP required positionally.
  Unbinds; called at every capture end [verified: s1_run:20,
  s2_run:32-33, s4_run:31, v12_run:50-52, a2_run:65,
  probe_wr:23, probe_warmup:22-23].

PAYLOADS (this build, 6.0.0/Kit 110):

- rgb: bare `(H,W,4)` uint8 array, observed (240,320,4);
  mean ~63.7 on lit scenes [verified: s1_run,
  evidence/s1_run.json, verify_s1/s3/v12].
- bbox_2d_tight: dict `{"data": [...], "info":
  {"bboxIds", "idToLabels", "primPaths"}}`. `data` rows are
  `(semId,x0,y0,x1,y1,...)`; `idToLabels` keys are STRINGS
  (`idToLabels[str(semId)]["class"]`); `primPaths` lists
  source prim paths [verified: s2_run, v12_run,
  evidence/s2_run.json]. In adv (A2) `data` arrives as a
  1-D STRUCTURED numpy array (fields semId,x0,y0,x1,y1),
  NOT (N,5) [verified: a2_run NOTE; discovery.md adv].
- semantic_segmentation: dict `{"data": (H,W) uint32,
  "info": {"idToLabels": {0: BACKGROUND, 1: UNLABELLED,
  2+: labels}}}` [verified: s2_run (uniq=[1,2],
  npix2=5847), v12_run, discovery.md base].

KNOBS + effect-of-change:

- Annotator `name` — TYPE: `str` (modality token) |
  n/a | no default (required positional). Effect: selects
  modality + payload schema; wrong name raises (MISS branch
  in probe_ann:13-14) [probable]; tight vs loose both gated
  only for row counts/paths in probe_bb3:13-14 [probable].
- Attach target RP — TYPE: `RenderProduct` (from
  `rep.create.render_product`) | n/a | no default (required
  positional). Effect: selects which camera view is read;
  reads follow the RP's current pose (V12 re-pose then read
  per frame) [verified: v12_run:32-37].
- Row indexing style — TYPE: code-pattern choice (`row[k]`
  ints vs `arr[:, i]` slices) | pixels (box coords) | n/a
  (caller-side). Effect: `[:, i]` FAILS on structured
  arrays; row indexing works for both list and structured
  forms [verified: a2_run:57-60 vs probe_labset:20].

EKB RULES:

- IF reading adv bbox data THEN index rows (`r[0..4]`),
  never `[:, i]` BECAUSE the array is 1-D structured
  [verified: a2_run, discovery.md adv].
- IF the USD pose was just edited THEN step TWICE and read
  the second BECAUSE the first step absorbs the edit
  (render catches up) [verified: a2_run two-step pattern].
- IF bbox rows are needed THEN label everything BEFORE the
  first bbox capture BECAUSE the labeled INSTANCE set
  freezes at first capture (new never join, removed never
  return; sim restart resets) [verified: failures.md
  R5/R7, probe_join].
- IF per-frame-fresh labels are needed THEN prefer
  semantic_segmentation BECAUSE it stays live (exempt from
  the freeze) [verified: R5, R7 note].
- IF resolving class names THEN `str()` the semId key
  BECAUSE idToLabels keys are strings [verified: s2_run,
  v12_run].

LIMITS (cites):

- L1: bbox instance set freezes at first capture per sim
  boot; restart to reset (R5, R7; A2/A3/VA share one
  frozen `abox` set by design) [verified].
- L2: `semantic_segmentation` exempt from freeze (R5, R7
  note) [verified].
- L3: adv bbox `data` is 1-D structured; `[:, i]`
  invalid (discovery.md adv; a2_run) [verified].
- L4: post-USD-edit first step yields stale boxes; read
  the second step (a2_run) [verified].
- L5: fresh-sim bbox reads return zero boxes until warmup
  (120 updates + steps; probe_warmup, a2_run) [verified].

UNKNOWN:

- U1: `bounding_box_2d_loose` payload details (only row
  counts/paths probed; equally frozen per R5) [probable].
- U2: `instance_segmentation` / `depth` direct-read takes
  (R8 prescribes; no drill demonstrates) [theoretical].
- U3: whether freeze also covers re-added prims at the
  SAME path vs new paths [theoretical].
- U4: `_fast` annotators + `distance_to_camera` /
  `camera_params` data shapes (existence probe only)
  [theoretical].

## 3. BasicWriter (via rep.WriterRegistry)

DOES: writes structured annotation files (bbox .npy +
labels/prim-path JSONs, optional RGB PNGs) to a FLAT output
dir [verified: probe_bw, probe_wr, s3_run, v12_run,
evidence/probe_bw, probe_w, s3_out, v12_out].

FUNCTIONS:

- `rep.WriterRegistry.get("BasicWriter")` — SIG:
  `get(name: str) -> BasicWriter`. Units: n/a. Defaults:
  none — `name` required positionally [verified:
  probe_bw:11, s3_run:22, v12_run:20, probe_wr:14].
- `bw.initialize(output_dir=OUT, rgb=False,
  bounding_box_2d_tight=True)` — SIG (observed kwargs
  only; further params [theoretical-unknown]):
  `initialize(output_dir: str, rgb: bool = ?,
  bounding_box_2d_tight: bool = ?) -> None`
  [probable-return: value unused]. Units: `output_dir` is
  a filesystem path (str); flags unitless. Defaults:
  `output_dir` required [probable: passed at every call
  site]; `rgb` default [theoretical-unknown: never
  omitted — False in probe_bw:12, s3_run:23, v12_run:21,
  True in probe_wr:15]; `bounding_box_2d_tight` default
  behaves as False [probable: omitted in probe_wr:15 and
  no bbox files land in probe_w/] [verified-calls,
  probable-incomplete].
- `bw.attach(rp)` — SIG: `attach(render_product:
  RenderProduct) -> None` [probable-return: value unused].
  Units: n/a. Defaults: none — RP required positionally.
  Starts per-step capture to output_dir [verified:
  probe_bw:13, s3_run:24, v12_run:22, probe_wr:16].
- `bw.detach()` — SIG: `detach() -> None`
  [probable-return: value unused]. Units: n/a. Defaults:
  n/a (no params). Ends capture; called after
  `wait_until_complete_async()` [verified: probe_bw:17,
  s3_run:32, v12_run:49, probe_wr:22].
- `rep.WriterRegistry.detach_all()` — SIG: `detach_all()
  -> None` [probable-return: value unused]. Units: n/a.
  Defaults: n/a (no params). Detaches all writers; called
  at every capture start (base, unguarded) because stale
  writers survive sends [verified: s3_run:14, s4_run:13,
  v12_run:14, probe_bb3:2, probe_hide:6, R4 hygiene].

OUTPUT LAYOUT (flat, no subdirs):

- `rgb_NNNN.png` (only when rgb=True; 5 files in
  probe_w for 5 steps) [verified: probe_wr,
  evidence/probe_w].
- `bounding_box_2d_tight_NNNN.npy` (one per step)
  [verified: s3_out has 0000-0002].
- `bounding_box_2d_tight_labels_NNNN.json`:
  `{"0": {"class": "<name>"}, ...}` (semId->class map)
  [verified: s3_out labels json on disk].
- `bounding_box_2d_tight_prim_paths_NNNN.json`
  [verified: s3_out].
- `metadata.txt` (always written, even on killed
  captures — R4's only artifact) [verified: R4,
  evidence/probe_w].
- Frame counter NNNN is per-writer-instance (starts
  0000 per initialize) [verified: discovery.md base;
  stale-writer 0003/0004 continuation in R4].

KNOBS + effect-of-change:

- `output_dir` — TYPE: `str` (filesystem path) |
  n/a | required [probable: passed at every call site].
  Effect: where files land; must be pre-cleaned (`rmtree`
  + `makedirs`) or old frames mix with new [verified:
  every writer run: probe_bw:4-5, s3_run:15-16].
- `rgb` — TYPE: `bool` | unitless | default
  [theoretical-unknown] (in-pack: False in
  probe_bw:12/s3_run:23/v12_run:21, True in probe_wr:15).
  Effect: toggles PNG output — True adds `rgb_NNNN.png`
  per step, but in interactive Kit they are pure black
  (0.00); use direct rgb reads instead [verified: R3
  OPEN, probe_wr].
- `bounding_box_2d_tight` — TYPE: `bool` | unitless |
  default behaves as False [probable: omitted in
  probe_wr:15, no bbox files in probe_w/]. Effect: toggles
  bbox .npy + JSONs; file content matches direct reads
  exactly (117,79,202,164, class s2cube) [verified: R3,
  verify_s3 "bbox has box"].

EKB RULES:

- IF capturing structured data in Kit THEN use
  BasicWriter for bbox + direct annotator reads saved
  in-script for pixels BECAUSE BasicWriter RGB is black
  in Kit while bbox is correct [verified: R3, s3_run
  docstring].
- IF starting any capture THEN `detach_all()` first
  BECAUSE stale writers survive sends and keep firing
  (frame counters 0003/0004 observed) [verified: R4].
- IF globbing outputs THEN use flat patterns
  (`rgb_*.png`, `*_*.npy`) BECAUSE there are no
  per-modality subdirs [verified: R2].

LIMITS (cites):

- L1: RGB path writes pure-black PNGs in interactive
  Kit (0.00 across 8 frames/2 RPs) while direct reads
  give 63.69 — OPEN (R3; evidence/probe_bw, s3_out,
  probe_w) [verified].
- L2: layout is FLAT (R2) [verified].
- L3: bbox file content == direct reads exactly (R3)
  [verified].

UNKNOWN:

- U1: whether BasicWriter RGB works in
  headless/standalone (R3 hypothesis: writers validated
  for those flows) [theoretical].
- U2: other modalities through BasicWriter (normals,
  depth, semantic) [theoretical].

## 4. KittiWriter (via rep.WriterRegistry)

DOES: writes KITTI-format datasets: images, label txt,
semantic maps (+colorized). The adv workhorse [verified:
probe_kitti, a1/a3/va_run, evidence/a1_out, a3_out,
va_out, probe_kitti].

FUNCTIONS:

- `rep.WriterRegistry.get("KittiWriter")` — SIG:
  `get(name: str) -> KittiWriter`. Units: n/a. Defaults:
  none — `name` required positionally [verified:
  a1_run:25, a3_run:31, va_run:31, probe_kitti:12].
- `kw.initialize(output_dir=OUT,
  use_kitti_dir_names=True, omit_semantic_type=True,
  mapping_dict={lowercase: RGBA})` — SIG (observed kwargs
  only; further params [theoretical-unknown]):
  `initialize(output_dir: str, use_kitti_dir_names: bool
  = ?, omit_semantic_type: bool = ?, mapping_dict:
  dict[str, tuple[int, int, int, int]] = ?) -> None`
  [probable-return: value unused]. Units: `output_dir` a
  filesystem path (str); flags unitless; mapping values
  RGBA 0-255 ints. Defaults: `output_dir` required
  [probable: passed at every call site];
  `use_kitti_dir_names` default behaves as False
  [probable: bare init in probe_kitti:47 lands non-KITTI
  dirs `Camera/rgb`, `Camera/object_detection`];
  `omit_semantic_type` default False [verified: bare-init
  default labels embed the spaced dict repr — R9];
  `mapping_dict` default [theoretical-unknown: bare-init
  sem-map behavior not recorded]. Full call e.g.
  a1_run:29-32 (`{"kboxa": (255,0,0,255), "kboxb":
  (0,255,0,255)}`), a3_run:32-34, va_run:32-34
  (`{"abox": (0,0,255,255)}`). Full signature printed via
  `inspect.signature` (probe_kitti:13) but value NOT
  recorded [verified-calls, theoretical-full-signature].
- `kw.attach(rp)` / `kw.detach()` — SIG:
  `attach(render_product: RenderProduct) -> None` /
  `detach() -> None` [probable-returns: values unused].
  Units: n/a. Defaults: none / n/a. Same contract as
  BasicWriter, but attach AFTER warmup (R10) and detach
  explicitly at each capture end (R6) [verified:
  a1_run:33+38, a3_run:39+53, va_run:39+53,
  probe_kitti:48+58].
- `kw.num_written` — SIG (read-only property):
  `num_written: int`. Units: frames written. Read after
  `wait_until_complete_async()` [verified: a1_run:37,
  a3_run:52, va_run:52, probe_kitti:52 print it].
- `kw.get_data()` — SIG: `get_data() -> dict | None`
  [probable: `kw.get_data() or {}` then `sorted(_d.keys())`
  in probe_kitti:54-55 implies dict-like-or-None]. Units:
  n/a. Defaults: n/a (no params). Probed in try/except
  (`PAYLOAD-KEYS`/`PAYLOAD-ERR`); result not recorded in
  pack [probable-exists, theoretical-payload].

OUTPUT LAYOUT (with use_kitti_dir_names=True):

- `Camera/image_02/*.png` — RGB frames, NOT black in
  Kit (mean 63.7) [verified: A1/A3/VA, ruled-out list].
- `Camera/label_02/*.txt` — one row per box:
  `class 0.00 occ 0.00 x0 y0 x1 y1 + 7x 0.00`
  (alpha/dims/location/rot/score always 0) [verified:
  on-disk a1 label file, discovery.md adv].
- `Camera/semantic/*.png` — class-index map, 0-based
  with background folded into 0 (bg+kboxa=0, kboxb=1;
  A1 sem has nunique=2) [verified: R9, verify_a1].
- `Camera/semantic_rgb/*.png` — colorized map with
  mapping colors (A1 nunique=3: bg+red+green)
  [verified: verify_a1].
- `instance/` + `depth/` SILENTLY MISSING (not even
  dirs, no log errors) — uint16 PNG backend dropped
  [verified: R8; evidence/a1_out, a3_out].

KNOBS + effect-of-change:

- `use_kitti_dir_names` — TYPE: `bool` | unitless |
  default behaves as False [probable: bare probe_kitti:47
  init lands non-KITTI dirs]. Effect: KITTI tree layout —
  True gives `Camera/image_02`-style dirs; False undrilled
  beyond the bare-init probe [verified-True,
  theoretical-False].
- `omit_semantic_type` — TYPE: `bool` | unitless |
  default False [verified: bare-init labels embed dict
  repr — R9]. Effect: True gives plain class tokens;
  False (default) embeds a dict REPR WITH A SPACE
  (`"{'class': 'kboxa'}"`) which breaks naive `.split()`
  parsing (field shift by one) [verified: R9, probe_kitti
  default-labels probe].
- `mapping_dict` — TYPE: `dict[str, tuple[int, int, int,
  int]]` (lowercase class -> RGBA 0-255) | color channel
  values 0-255 | default [theoretical-unknown].
  Effect: keys MUST be lowercase (writer case-folds
  classes: `kboxA`->`kboxa`); CamelCase keys never
  match -> all-zero sem map. Unmapped classes render
  as unlabelled (zeroed sem, single-sample) [verified:
  R9 (a1_run:29-32, a3_run:32-34); probable-unmapped].
- `output_dir` — TYPE: `str` (filesystem path) | n/a |
  required [probable: passed at every call site]. Effect:
  dataset root; pre-clean per run [verified: a1_run:18-19,
  a3_run:24-25, va_run:24-25].

EKB RULES:

- IF writing KITTI in Kit THEN gate rgb/labels/semantic
  only and take instance/depth via direct reads BECAUSE
  uint16 outputs are silently dropped (R8) [verified].
- IF parsing labels THEN set `omit_semantic_type=True`
  BECAUSE default labels embed a spaced dict repr
  [verified: R9].
- IF building mapping_dict THEN lowercase every key
  BECAUSE the writer case-folds class names [verified:
  R9, a1_run NOTE].
- IF separating class 0 from background THEN use
  instance/semrgb, never the sem map BECAUSE bg folds
  into id 0 [verified: R9].
- IF attaching the writer THEN attach AFTER warmup
  BECAUSE a pre-warmup attach writes frame 0 during
  warmup (51 files for 50 frames) [verified: R10].
- IF counting outputs THEN expect boxes >=25px tall
  only BECAUSE smaller boxes are discarded by the
  writer [verified: discovery.md adv; verify_a1/a3/va
  gate h>=25].

LIMITS (cites):

- L1: `instance/`+`depth/` silently missing (R8)
  [verified].
- L2: default labels embed spaced dict repr (R9)
  [verified].
- L3: class names case-folded; mapping keys lowercase
  (R9) [verified].
- L4: sem ids 0-based, bg folded into 0 (R9) [verified].
- L5: label rows carry boxes only (+7x 0.00);
  boxes <25px tall discarded (discovery.md adv)
  [verified].
- L6: pre-warmup attach writes frame 0 during warmup
  (R10) [verified].
- L7: KittiWriter RGB is NOT black (mean 63.7); base
  R3 does not apply (ruled-out list) [verified].

UNKNOWN:

- U1: full `initialize` signature text (KITTI-SIG
  printed, value not recorded) [theoretical].
- U2: 3+ mapped classes; unmapped-class behavior
  beyond single-sample "render as unlabelled"
  [probable].
- U3: sweeps >50 frames; warm-vs-cold fps beyond
  13.7/2.2 [theoretical].

## 5. rep.Writer subclass (custom writer pattern)

DOES: user-defined writer attached to a render product
(documented "direct access to annotator tensors" pattern).
NO surviving script in-pack implements one — knowledge is
entirely from the R4 kill report [probable].

FUNCTIONS (as described in failures.md/discovery.md):

- `class MyWriter(rep.Writer)` with `write()` override —
  SIG: `write(self) -> None` [theoretical: NO call site
  or implementation survives in-pack; shape inferred from
  the failures.md R4 kill report only]. Units: invoked
  once per graph frame [probable]. Defaults: n/a (no
  params beyond self) — graph-triggered per frame
  [probable].
- `self._frame_id = 0` in `__init__` — SIG:
  `__init__(self) -> None` [theoretical: no surviving
  implementation; any further params [theoretical-unknown]];
  attr `_frame_id: int`, units frames, init value 0.
  Frame counters are per-instance [verified: discovery.md
  base].

KNOBS + effect-of-change:

- `write()` body — TYPE: method body / callable code
  (override of `rep.Writer.write`) | per-frame | no
  default (must be authored). THE contested knob.
  Blocking `get_data()`+`np.save` inside `write()` killed
  the WHOLE capture for ALL writers (zero files from
  either writer, only metadata.txt) [verified: R4]. Any
  SAFE body is unknown [theoretical].

EKB RULES:

- IF pixels are needed THEN use BasicWriter for
  structured data + direct annotator reads saved
  in-script BECAUSE blocking in `write()` kills the
  capture (writers must only schedule backend work,
  never block) [verified: R4, s3_run docstring].
- IF tempted by the documented direct-tensor subclass
  THEN do not trust it BECAUSE R3 names it as the
  workaround but R4 proves `get_data()` in `write()`
  kills capture — contested, no green drill [verified].

LIMITS (cites):

- L1: blocking `get_data()`+`np.save` in `write()`
  kills the whole capture for all writers (R4)
  [verified].

UNKNOWN:

- U1: ANY safe custom-writer `write()` body
  [theoretical].

## 6. isaacsim.core.experimental.utils.semantics (add_labels)

DOES: attaches semantic class labels to USD prims for
bbox/semseg [verified: s2_build, v12_build, probe_sem,
a1/a2/a3_build, probe_join, probe_kitti].

FUNCTIONS:

- `add_labels(prim, labels=[...])` — SIG:
  `add_labels(prim: UsdPrim, *, labels: list[str]) ->
  None` [probable-return: value unused] (any further
  params such as taxonomy [theoretical-unknown]).
  Units: n/a. Defaults: none — `prim` required
  positionally, `labels` required KEYWORD-ONLY (every
  call passes `labels=[...]`). Dedups on re-run (safe to
  re-apply) [verified: s2_build:12, v12_build:29+34,
  a1_build:29, a2_build:38-39, a3_build:30-31,
  probe_join:20-21, probe_kitti:33-34, probe_sem:6;
  discovery.md base, s2_build docstring].
- `get_labels(prim)` — SIG: `get_labels(prim: UsdPrim)
  -> dict[str, list[str]]` [probable-param-type: only
  ever passed prims from `GetPrimAtPath`/`GetPrim`].
  Units: n/a. Defaults: none — `prim` required
  positionally. Returns `{taxonomy: [...]}` (e.g.
  `{'class': ['s2cube']}`-ish; exact repr in build
  reports) [verified: s2_build:13, v12_build:39 prints].

KNOBS + effect-of-change:

- `labels` — TYPE: `list[str]` (class names) | n/a |
  required keyword (no default). Effect: feeds bbox
  idToLabels + semseg ids; case preserved at label time
  (`kboxA`) but KittiWriter folds to lowercase (`kboxa`)
  [verified: a1_build:22-29 + R9].
- Re-run — TYPE: behavior flag (re-apply same call) |
  n/a | n/a (caller-side). Effect: dedups, no duplicate
  accumulation [verified: s2_build docstring].

EKB RULES:

- IF labeling for bbox THEN label before the FIRST
  bbox capture in the session BECAUSE later labels are
  invisible to bbox annotators (freeze) [verified: R5].
- IF matching class names in verifiers THEN allow
  digits (`[\w+]+`, not `[a-z+]`) BECAUSE classes like
  v12a/v12b contain digits [verified: discovery.md
  base; verify_v12 regex].
- IF running an exam THEN build a SELF-CONTAINED scene
  (own lights/ground/props/labels) on a fresh sim
  BECAUSE piggybacking on earlier drills' stages hits
  the freeze [verified: R5, v12_build docstring].

LIMITS (cites):

- L1: labels added after first bbox capture invisible
  to bbox (R5) [verified].

UNKNOWN:

- U1: multi-taxonomy labeling [theoretical].
- U2: label removal / relabel mid-session effects
  [theoretical].

## 7. isaacsim.core.experimental.utils.app (update_app_async)

DOES: renderer warmup without orchestrator steps
[verified: probe_warmup, a2/a3/va_run].

FUNCTIONS:

- `await app_utils.update_app_async(steps=120)` —
  SIG: `update_app_async(steps: int) -> Coroutine[Any,
  Any, None]` [probable-return-type: awaited at top level,
  result never used]; 120 is the only value ever passed.
  Units: app-update ticks (renderer updates, no
  orchestrator step). Defaults: `steps` default
  [theoretical-unknown: always passed as 120] [verified:
  a2_run:31, a3_run:37, va_run:37, probe_warmup:16].

KNOBS + effect-of-change:

- `steps` — TYPE: `int` (update count) | app-update
  ticks | default [theoretical-unknown] (in-pack value
  always 120). Effect: 120 + 1 step verified (zero boxes
  before, 3 boxes every step after); smaller counts
  undrilled [verified: a2_run:31-32, probe_warmup:16-18,
  ruled-out list; theoretical-minimum].

EKB RULES:

- IF capturing on a fresh sim THEN warm up (120 app
  updates + 1 step) BEFORE attaching writers / trusting
  reads BECAUSE the renderer returns empty until warm
  [verified: probe_warmup, a2_run].
- IF attaching a writer THEN attach after the warmup
  step BECAUSE the warmup step would otherwise be
  captured as frame 0 (R10) [verified].

LIMITS (cites):

- L1: 120 updates + 1 step verified sufficient (a2_run;
  ruled-out list) [verified].

UNKNOWN:

- U1: minimum sufficient step count (120 proven, not
  minimal) [theoretical].

## 8. omni.usd stage access

DOES: reaches the live USD stage from in-sim scripts
[verified: every *_build.py, s4_run, a2/a3/va_run,
probe_hide/rep/sem/join/kitti].

FUNCTIONS:

- `omni.usd.get_context()` — SIG: `get_context() ->
  UsdContext` [probable-type-name: object with
  `.get_stage()`]. Units: n/a. Defaults: n/a (no params).
  Returns the USD context [verified: s1_build:9,
  probe_hide:4, probe_rep:3, s2_build:10, a1_build:11,
  a2_build:11, a3_build:12].
- `context.get_stage()` — SIG: `get_stage() -> Usd.Stage`
  [probable-type-name: object with `GetPrimAtPath` /
  `RemovePrim`]. Units: n/a. Defaults: n/a (no params).
  Returns live stage [verified: same call sites, chained
  as `omni.usd.get_context().get_stage()`].
- `stage.GetPrimAtPath(path)` — SIG: `GetPrimAtPath(path:
  str) -> UsdPrim`. Units: n/a (`path` is an Sdf scene
  address, e.g. `/World/S1Cube`). Defaults: none — `path`
  required positionally. Returns prim (check `.IsValid()`)
  [verified: s1_build:11+23, s2_build:11, s4_run:21,
  v12_build:16+36, a1_build:14+30, probe_join:13].
- `stage.RemovePrim(path)` — SIG: `RemovePrim(path: str)
  -> bool` [probable-return: USD convention; value unused
  in-pack]. Units: n/a. Defaults: none — `path` required
  positionally. Teardown of build outputs before rebuild;
  also used to remove competing labeled prims (a2_build)
  and freeze-test instance removal (probe_join) [verified:
  s1_build:13, v12_build:18, a1_build:16, a2_build:22+26,
  probe_join:14, probe_kitti:20].
- `prim.IsValid()` — SIG: `IsValid() -> bool`. Units:
  n/a. Defaults: n/a (no params). Validity check before
  remove / in build reports [verified: s1_build:12+23,
  v12_build:17+36, a1_build:15+30, a2_build:21+25,
  probe_kitti:19].

KNOBS + effect-of-change:

- Prim path strings — TYPE: `str` (Sdf path, e.g.
  `/World/S1Cube`) | scene address (n/a units) | no
  default (required positional). Effect: wrong path ->
  invalid prim; `RemovePrim` on labeled prims does NOT
  unfreeze bbox instances (removed never return)
  [verified: probe_join:13-14, R7].

EKB RULES:

- IF rebuilding THEN remove-then-define each path
  BECAUSE Define on an existing prim is not the pack
  pattern (every build removes first) [verified: all
  builds].
- IF removing labeled prims THEN expect no bbox change
  mid-session BECAUSE the instance set is frozen (R7)
  [verified].

LIMITS: none (no failures implicate it) [verified].

UNKNOWN:

- U1: empty/unstaged context behavior [theoretical].
- U2: multi-context handling [theoretical].

## 9. pxr USD authoring (UsdGeom, UsdLux, Gf)

DOES: scripted scene building + per-frame pose variation
[verified: all builds, s4_run, a2/a3/va_run,
probe_hide/join/kitti].

FUNCTIONS:

- `UsdGeom.Cube.Define(stage, path)` — SIG:
  `Define(stage: Usd.Stage, path: str) -> UsdGeomCube`
  [probable-type-names]. Units: `path` an Sdf scene
  address (n/a units). Defaults: none — both positionals
  required [verified: s1_build:17+20, v12_build:22+25+30,
  a1_build:20+25, a2_build:30+34, a3_build:22+26,
  probe_join:16, probe_kitti:23+27].
- `cube.GetSizeAttr().Set(size)` — SIG:
  `GetSizeAttr() -> UsdAttribute; Set(size: float) ->
  None` [probable-return]. Units: stage length units
  (meters on the default stage) [probable]. Defaults:
  none for `Set` (value required); the attr's unset USD
  default never read in-pack [theoretical-unknown].
  Sizes used: 10.0 ground, 1.0 S1/A1/K cubes, 0.8
  V12/A2/A3 cubes [verified: s1_build:18+21,
  v12_build:23+26+31, a1_build:21+26, a2_build:31+35,
  a3_build:23+27, probe_kitti:24+28].
- `UsdGeom.Xformable(prim).AddTranslateOp().Set(
  Gf.Vec3d(x, y, z))` — SIG: `Xformable(prim: UsdPrim)
  -> Xformable; AddTranslateOp() -> UsdGeomXformOp;
  Set(value: Gf.Vec3d) -> None` [probable-type-names /
  probable-return]. Units: meters XYZ [probable].
  Defaults: none — prim and value required. Initial
  placement [verified: s1_build:19+22, v12_build:24+27-28,
  a1_build:22+27-28, probe_kitti:25+29-30].
- `UsdGeom.Xformable(prim).GetOrderedXformOps()[0].Set(
  value)` — SIG: `GetOrderedXformOps() ->
  list[UsdGeomXformOp]` [probable]; `[0]` indexes the
  first (translate) op; `Set(value: Gf.Vec3d) -> None`
  [probable-return]. Units: meters XYZ [probable].
  Defaults: none — prim and value required. Per-frame
  pose updates (tops[] pattern, cached once) [verified:
  s4_run:22+25+30, a2_run:33-34+45-46, a3_run:40-41+48,
  va_run:40-41+48].
- `UsdLux.DomeLight.Define(stage, path)` +
  `dome.GetIntensityAttr().Set(3000.0)` — SIG:
  `Define(stage: Usd.Stage, path: str) -> UsdLuxDomeLight`
  [probable-type-names]; `GetIntensityAttr() ->
  UsdAttribute; Set(intensity: float) -> None`
  [probable-return]. Units: light intensity units
  (renderer-dependent scale) [probable]. Defaults: none
  for `Set`; unset default never read [theoretical-
  unknown]. Scene light; 3000.0 is the only intensity
  ever used [verified: s1_build:15-16, v12_build:20-21,
  a1_build:18-19, a2_build:28-29, a3_build:20-21,
  probe_kitti:21-22].
- `UsdGeom.Imageable(prim).MakeInvisible()` /
  `.MakeVisible()` — SIG: `Imageable(prim: UsdPrim) ->
  Imageable; MakeInvisible() -> None; MakeVisible() ->
  None` [probable-type-names/returns]. Units: n/a.
  Defaults: n/a (no params beyond prim). Visibility
  toggle (freeze test: hidden S1Cube -> n=0) [verified:
  probe_hide:5+16, R5].
- `Gf.Vec3d(x, y, z)` — SIG: `Vec3d(x: float, y: float,
  z: float) -> Gf.Vec3d` (plain ints also accepted, e.g.
  `Gf.Vec3d(0, 0, -0.05)` in s1_build:19, `Gf.Vec3d(-1,
  0, 0.4)` in v12_build:28 — so `int | float` per
  component [verified]). Units: inherit from use (meters
  for translates) [probable]. Defaults: none — all three
  required. Translate value [verified: s1_build:19+22,
  s4_run:25, a2_run:45-46, a3_run:48].

KNOBS + effect-of-change:

- Cube `size` — TYPE: `float` | meters [probable] |
  always `Set` explicitly (unset default
  [theoretical-unknown]). Effect: object scale — V12 0.8
  cubes at given poses yield px>100/frame; S2 1.0 cube
  yields area 7225 [verified: evidence reports].
- Translate XYZ — TYPE: `Gf.Vec3d` (3 doubles) | meters
  [probable] | no default (required `Set` value). Effect:
  placement — S4 x=-1.5/0/+1.5 gives strictly monotonic
  xmins with spread 117px; restore-after-variation keeps
  the stage clean [verified: s4_run:24-30, verify_s4].
- Dome intensity — TYPE: `float` | light intensity units
  [probable] | unset default [theoretical-unknown]
  (in-pack value always 3000.0). Effect: brightness —
  with it, rgb mean ~63.7 (non-black gates >30 pass);
  other values undrilled [verified-value,
  theoretical-others].

EKB RULES:

- IF varying poses THEN script USD translates
  (seeded rng or fixed list) BECAUSE scripted
  variation beats RNG-graph randomize for determinism
  [verified: discovery.md base; S4/V12/A2/A3].
- IF moving a prim per frame THEN cache
  `GetOrderedXformOps()[0]` once BECAUSE repeated
  Xformable wrapping per frame is wasteful (tops[]
  pattern) [verified: s4/a2/a3/va_run].
- IF combining with seeded rng THEN scripted USD
  translates + `np.default_rng(seed)` give bit-identical
  layouts across runs (A2 leg0==leg1 exact) [verified].

LIMITS (cites):

- L1: scripted USD translates + seeded rng give
  bit-identical layouts (evidence/a2_layouts_*.npy)
  [verified].

UNKNOWN:

- U1: non-cube/light prim types [theoretical].
- U2: material/shader authoring for SDG [theoretical].

## 10. numpy

DOES: layout RNG, tensor math, evidence persistence,
verification [verified: s1/s2/s3/s4/v12_run (reads),
a2/a3/va_run (rng+layouts), pngstats, verify_*
(stat math)].

FUNCTIONS:

- `np.random.default_rng(seed)` — SIG:
  `default_rng(seed: int) -> np.random.Generator`
  (SeedSequence/array-like seed forms undrilled
  [theoretical]). Units: n/a. Defaults: `seed` always
  passed positionally; unseeded default undrilled
  [theoretical]. Seeds used: 7, 8 (A2 legs), 11 (A3), 99
  (VA) [verified: a2_run:39-40, a3_run:43, va_run:43].
- `rng.uniform(-2.0, 2.0, (N, 2))` — SIG:
  `uniform(low: float, high: float, size: tuple[int,
  int]) -> np.ndarray[float64]` [probable-dtype].
  Units: meters (pose scatter; fed into `Gf.Vec3d`
  translates). Defaults: all three positionals always
  passed; defaults [theoretical-unknown]. N=3 (A2) / N=2
  (A3/VA) pose samples [verified: a2_run:43, a3_run:46,
  va_run:46].
- `np.save(path, array)` / `np.load(path,
  allow_pickle=...)` — SIG: `save(file: str, arr:
  np.ndarray) -> None`; `load(file: str, allow_pickle:
  bool = ?) -> np.ndarray`. Units: n/a (payloads are
  pixels/boxes). Defaults: `allow_pickle` default
  [probable-False: omitted at verify_s3:15,
  verify_v12:20, verify_a2:17 for plain numeric arrays;
  passed True only for object bbox .npy at
  verify_s3:16]. Layouts (`a2_layouts_%d.npy`, (6,3,4)
  int32), direct rgb/sem dumps (`direct_rgb_*.npy`,
  `rgb_*.npy`, `sem_*.npy`) [verified: s3_run:29-30,
  v12_run:38-39, a2_run:63 saves; verify_s3:15-16,
  verify_v12:20, verify_a2:17 loads].
- `np.asarray(payload)` — SIG: `asarray(a: array_like,
  dtype = None [probable: never passed, inferred],
  order = ? [theoretical-unknown]) -> np.ndarray`.
  Units: inherit (pixels/ids/channels). Wraps rgb/bbox/
  semseg reads (bare array OR dict field) [verified:
  s1_run:17, s3_run:30, v12_run:35+39+41, a2_run:52,
  probe_chain:10, probe_sem:22, probe_warmup:19-20,
  probe_join:33, probe_labset:17, pngstats:11].
- `np.unique(a)` / `(a == id).sum()` / `.mean()` /
  `.max()` / `len(np.unique(flat, axis=0))` — SIG:
  `unique(ar: np.ndarray, axis: int | None = None)
  -> np.ndarray` [probable-default: `axis` omitted
  everywhere except pngstats:15 (`axis=0`)];
  `(a: np.ndarray == id: int) -> bool array; .sum() ->
  np.int64` count; `.mean() -> np.float64`;
  `.max() -> scalar`; `len(x) -> int`. Units: pixels /
  counts / 0-255 channel stats. Pixel/box stats
  [verified: s2_run:27-28, v12_run:41, s1_run:19
  (mean+max), probe_chain:11, pngstats:14-15,
  verify_s3:23].
- `np.zeros((6, 3, 4), dtype=np.int32)` — SIG:
  `zeros(shape: tuple[int, int, int], dtype: np.dtype)
  -> np.ndarray`. Units: box pixels in layout slots
  (frames x cubes x box). Defaults: both always passed;
  `dtype` default [theoretical-unknown]. Layout
  accumulator [verified: a2_run:41].

KNOBS + effect-of-change:

- `seed` — TYPE: `int` | n/a | always passed (unseeded
  default undrilled [theoretical]). Effect: layout stream
  — same seed -> bit-identical layouts (leg0==leg1
  exact); different seed -> differs [verified: a2_run:39,
  verify_a2].
- Pose range — TYPE: `low: float, high: float` + `size:
  tuple[int, int]` | meters (scatter area) | no defaults
  (all required positionally). In-pack value `(-2.0,
  2.0)`. Effect: boxes stay in-frame at 320x240 with the
  A-pose camera (all in-range gates pass); wider ranges
  undrilled [verified-range: a2_run:43, a3_run:46,
  theoretical-others].
- Layout shape/dtype — TYPE: `shape: tuple[int,int,int]`
  + `dtype: np.dtype` | frames x cubes x box-pixels | no
  defaults (in-pack `(6,3,4)/int32`). Effect:
  verifier-gated exact [verified: a2_run:41, verify_a2
  "shapes"].

EKB RULES:

- IF seeding layouts THEN use `np.default_rng(seed)`
  ALONE BECAUSE it suffices for determinism while
  `rep.set_global_seed` is suspected of detaching
  annotators [verified: a2_run NOTE, ruled-out list].
- IF comparing layouts THEN exact `==` (not tolerance)
  BECAUSE seeded runs are bit-identical [verified:
  verify_a2].

LIMITS (cites):

- L1: `default_rng(seed)` alone gives deterministic
  layouts; do NOT use `rep.set_global_seed` for this
  (SKILL.md; ruled-out list) [verified].

UNKNOWN: none — stdlib-grade usage, fully covered
[verified].

## 11. PIL (Pillow Image)

DOES: PNG pixel stats for writer-output verification
[verified: pngstats.py + verify_a1/a3/va].

FUNCTIONS:

- `Image.open(f)` — SIG: `open(fp: str, mode: str = ?
  [theoretical-unknown: never passed; only the path
  positional is used]) -> PIL.Image.Image`. Units: n/a.
  Defaults: `fp` required (a `sys.argv` path) [verified:
  pngstats:11].
- `np.asarray(img)` + reshape + `np.unique(flat,
  axis=0)` — SIG: `asarray(img: PIL.Image.Image) ->
  np.ndarray`; `reshape(-1, C: int) | reshape(-1) ->
  np.ndarray` (branch on `a.ndim == 3`, pngstats:12);
  `unique(flat: np.ndarray, axis: int = 0) -> np.ndarray`.
  Units: pixels / channel values; `len` of the result
  is the distinct-color count. Per-file `shape / mean /
  nunique` line [verified: pngstats:11-15].

KNOBS + effect-of-change:

- File args — TYPE: `list[str]` (PNG paths from
  `sys.argv[1:]`, pngstats:10) | n/a | no default (argv
  required). Effect: which PNGs — one stats line per
  file; verifiers match lines by path prefix [verified:
  verify_a1/a3/va parsing].

EKB RULES:

- IF stats are needed THEN run under
  `C:/isaacsim/python.bat` BECAUSE PIL exists ONLY
  there (missing in system AND pixi pythons) [verified:
  ruled-out list, pngstats docstring].

LIMITS (cites):

- L1: PIL only under `$ISAAC_SIM_DIR/python.bat`
  (ruled-out list) [verified].

UNKNOWN: none [verified].

## 12. C:/isaacsim/python.bat CLI

DOES: the only python that runs pixel checks (has PIL)
[verified: verify_a1/a3/va, pngstats docstring].

FUNCTIONS:

- `C:/isaacsim/python.bat
  adv/scripts/pngstats.py <files...>` — SIG:
  `subprocess.run(args: list[str], capture_output: bool
  = True, text: bool = True, timeout: float = 240) ->
  CompletedProcess` (further `run` params undrilled
  [theoretical]). Units: `timeout` in seconds; `args[0]`
  is the interpreter path, `args[1]` the script,
  `args[2:]` PNG paths. Defaults: all three kwargs always
  passed explicitly (stdlib defaults undrilled in-pack).
  `p.stdout: str` parsed with `re.search(r"mean=([\d.]+)")`
  / `r"nunique=(\d+)"` per path-prefixed line [verified:
  verify_a1:49-53, verify_a3:48-52, verify_va:47-51].

KNOBS + effect-of-change:

- Script + file list — TYPE: `list[str]` (argv: exe +
  script + PNG paths) | n/a | no default (required).
  Effect: stats targets — A1 checks img+sem+semrgb of
  frame 0; A3 samples frames 0/24/49 rgb; VA samples
  0/5/11 rgb [verified: verify_a1:45-47, verify_a3:44,
  verify_va:43].
- `timeout` — TYPE: `int` (seconds) | seconds | always
  passed as 240 (stdlib default undrilled in-pack
  [theoretical]). Effect: subprocess cap bounding pixel
  checks; no timeout observed [verified-call,
  probable-sufficient].

EKB RULES:

- IF a pixel gate fails to run THEN check the isaacsim
  python path first BECAUSE system/pixi pythons lack
  PIL [verified: ruled-out list].

LIMITS (cites):

- L1: verifier-side dependency of verify_a1/a3/va
  (subprocess+sys imports) [verified].

UNKNOWN: none [verified].

## 13. rep.set_global_seed (negative knowledge)

DOES: purported global RNG seed for randomized
Replicator runs. Deliberately NOT called anywhere
[verified: a2_run NOTE].

FUNCTIONS: none — never invoked in-pack (its only
in-pack mention is the a2_run:36-38 NOTE recording its
absence). 0 signatures to type [verified].

KNOBS: none. 0 knobs to type.

EKB RULES:

- IF seeding layouts THEN do NOT call it BECAUSE it
  was suspected of detaching annotators (empty reads)
  and `np.default_rng` alone suffices [verified:
  ruled-out list; a2_run NOTE]. (Dropping it changed
  nothing — real causes were R7 + warmup — but it
  remains banned for seeded layouts.)

LIMITS (cites):

- L1: suspected annotator-detach; dropping changed
  nothing; np rng suffices (ruled-out list; a2_run)
  [verified].

UNKNOWN:

- U1: whether it has ANY safe use (discovery.md base
  still notes it "for randomized runs" — undrilled,
  do not trust) [theoretical].

## 14. stdlib file/test helpers (os, shutil, glob, json, re, subprocess, sys, time, inspect)

DOES: output-dir hygiene, file counting, report parsing,
timing [verified: all writer runs + all verifiers].

FUNCTIONS:

- `shutil.rmtree(OUT, ignore_errors=True)` +
  `os.makedirs(OUT, exist_ok=True)` — SIG:
  `rmtree(path: str, ignore_errors: bool = True) ->
  None`; `makedirs(path: str, exist_ok: bool = True) ->
  None`. Units: n/a. Defaults: both flags always passed
  True; stdlib defaults (False) never observed in-pack
  [probable-stdlib]. Per-run dir reset [verified:
  probe_bw:4-5, probe_wr:5-6, s3_run:15-16, v12_run:15-16,
  a1_run:18-19, a3_run:24-25, va_run:24-25,
  probe_kitti:40-41].
- `os.walk(OUT)` + `os.path.join` + `os.path.relpath` +
  backslash normalize + `startswith("Camera/image_02" |
  "Camera/label_02")` — SIG: `walk(top: str) ->
  Iterator[tuple[str, list[str], list[str]]]` (root,
  dirs, files); `join(a: str, p: str) -> str`;
  `relpath(path: str, start: str) -> str`;
  `str.replace(old: str, new: str) -> str` (always
  `("\\", "/")`); `str.startswith(prefix: str) -> bool`;
  `str.endswith(suffix: str) -> bool`. Units: n/a.
  Defaults: all positionals required as used (further
  `walk`/`relpath` params undrilled [theoretical]).
  KITTI prefix counting [verified: a1_run:40-46,
  a3_run:55-61, va_run:55-61, probe_kitti:59-66].
- `os.listdir(OUT)` + startswith/endswith filters — SIG:
  `listdir(path: str) -> list[str]`; filters as above
  (`str -> bool`). Units: n/a. Defaults: `path` required.
  Flat-dir counting [verified: probe_bw:18, probe_wr:24,
  s3_run:34-38].
- `glob.glob(OUT + pattern)` — SIG: `glob(pathname: str,
  *, recursive: bool = ? [theoretical-unknown: never
  passed]) -> list[str]` (caller sorts). Units: n/a.
  Defaults: `pathname` required (a `str + str` pattern).
  Verifier-side file sets (`direct_rgb_*.npy`,
  `bounding_box_*.npy/json`, `rgb_*.npy`, `sem_*.npy`,
  `Camera/*/*`) [verified: verify_s3:12-14,
  verify_v12:17-19, verify_a1:23-26, verify_a3:22-23,
  verify_va:21-22].
- `json.load(open(evidence/*.json))["output"]` — SIG:
  `open(file: str, mode: str = "r" [probable: never
  passed, read-mode behavior]) -> TextIO`;
  `json.load(fp: TextIO) -> dict`; `d["output"] -> str`
  (bridge stdout text). Units: n/a. Bridge report
  extraction [verified: verify_s1:4-5, verify_s2:4-5,
  verify_s4:4, verify_v12:7-8, verify_s3:10].
- `re.search` / `re.finditer` — SIG: `search(pattern:
  str, string: str) -> Match | None`;
  `finditer(pattern: str, string: str) ->
  Iterator[Match]`; `Match.group(i: int) -> str`;
  `Match.groups() -> tuple[str, ...]` (further params
  such as flags undrilled [theoretical]). Units: n/a
  (parsed ints/floats are pixels/counts/channel stats).
  Report parsing (`mean=`, `xmins=`, `fN:nbox=` frames)
  [verified: verify_s1:8, verify_s2:8+17, verify_s4:6-7,
  verify_v12:12, verify_a1:59-60, verify_a3:57,
  verify_va:56].
- `subprocess.run(args, capture_output=True, text=True,
  timeout=240)` — SIG: same contract as tool 12:
  `run(args: list[str], capture_output: bool = True,
  text: bool = True, timeout: float = 240) ->
  CompletedProcess`; `p.stdout: str`. Units: `timeout`
  seconds. pngstats shell-out [verified: verify_a1:49-53,
  verify_a3:48-52, verify_va:47-51].
- `time.time()` — SIG: `time() -> float`. Units: seconds
  (epoch wall clock; differences `dt` in seconds, `N/dt`
  in fps). Defaults: n/a (no params). Sweep wall/fps
  (`N/dt`; 50-frame cold 23s/2.2fps, warm ~4s/13.7fps)
  [verified: a3_run:44+51+64-65, va_run:44+51,
  discovery.md adv].
- `inspect.signature(kw.initialize)` — SIG:
  `signature(obj: Callable) -> inspect.Signature`
  (printed via `print`, str form). Units: n/a. Defaults:
  `obj` required positionally. KITTI-SIG print
  [verified-call: probe_kitti:13; value not recorded].
- `sys.argv[1:]` / `sys.exit(1 if fails else 0)` — SIG:
  `argv: list[str]`; slice `argv[1:] -> list[str]` (PNG
  paths); `exit(code: int) -> NoReturn` (raises
  SystemExit; in-pack codes 0/1). Units: n/a. pngstats
  args / verifier exit codes [verified: pngstats:10,
  verify_a1:74, verify_a2:29, verify_a3:63, verify_va:62].

KNOBS + effect-of-change:

- `ignore_errors` / `exist_ok` — TYPE: `bool` | unitless |
  always passed True (stdlib default False
  [probable-stdlib]). Effect: idempotent reset — re-runs
  never crash on missing dirs [verified: every writer
  run].
- `timeout` — TYPE: `int` (seconds) | seconds | always
  passed as 240 (stdlib default undrilled in-pack
  [theoretical]). Pixel-check cap [verified-call,
  probable-sufficient].
- `capture_output` / `text` — TYPE: `bool` | unitless |
  always passed True (stdlib defaults undrilled in-pack
  [theoretical]). Effect: parseable `str` stdout
  [verified: verify_a1:49-53].
- Label-row parse — TYPE: contract over `list[str]` row
  (`ln.split() -> list[str]`: `r[0]: str` class with
  `strip("'\"")`, `r[4:8]: list[str]` box parsed via
  `float()`) | box in pixels | n/a (caller-side). KITTI
  row contract. Effect: requires `omit_semantic_type=True`
  labels; dict-repr labels shift fields [verified:
  verify_a1:31-41, verify_a3:29-38 + R9].

EKB RULES:

- IF resetting an output dir THEN `rmtree(ignore_errors)
  + makedirs(exist_ok)` BECAUSE re-runs must be
  idempotent [verified: every writer run].
- IF parsing KITTI labels THEN `split()` + class at
  [0] + box at [4:8] BECAUSE that is the omit-type row
  contract [verified: verifiers].
- IF a verifier reads bridge output THEN `["output"]`
  of the evidence json BECAUSE that key holds stdout
  [verified: base verifiers].

LIMITS: none (no failures implicate them) [verified].

UNKNOWN: none [verified].

## 15. Bridge send transport (top-level await, --file no-args)

DOES: executes the in-sim scripts inside Kit [verified:
every in-sim script; evidence/*.json envelopes].

FUNCTIONS (transport behaviors, not callables):

- Top-level `await` in sent scripts — SIG: behavior,
  not a callable: `await coro` where `coro:
  Coroutine[Any, Any, None]` [probable] (the orchestrator/
  app async calls above). Units: n/a. Defaults: n/a. All
  run scripts await orchestrator/app calls at module top
  level [verified: s1_run:16, s3_run:28+31, a2_run:31-32,
  a3_run:37-38+49-50, probe_warmup:16+18].
- `--file` takes no args — SIG: transport constraint, no
  callable and no params (empty argv by construction).
  Units: n/a. Defaults: n/a. Multi-leg scripts hardcode
  legs (a2_run:39: seeds (7,7,8) in one call) [verified].
- Evidence envelope — SIG (record shape):
  `{"status": str ("ok"), "output": str (full stdout),
  "result": None}` per send [probable-field-types: every
  on-disk envelope matches; other `result` shapes
  [theoretical-unknown]], saved as `evidence/*.json`
  [verified: on-disk s1/s2_run.json, read at
  verify_s1:4-5, verify_s2:4-5].

KNOBS + effect-of-change:

- Hardcoded legs/seeds — TYPE: `tuple[int, ...]` (in-pack
  `(7, 7, 8)`, a2_run:39) | unitless (seed stream ids) |
  n/a (source-level constant). The no-args workaround.
  Effect: A2 runs 3 legs x 6 frames x 2 steps in one send
  [verified: a2_run:39-63].
- Step budget per send — TYPE: `int` (step count; in-pack
  max N=50, a3_run) | orchestrator steps (~3 min wall) |
  n/a (caller-side loop bound). 50 orchestrator steps fit
  the bridge timeout (~3 min) [verified: a3_run docstring
  + a3_run:45 loop].

EKB RULES:

- IF sending a capture THEN `detach_all()` at capture
  start BECAUSE stale writers survive sends (R4)
  [verified].
- IF calling `detach_all()` in adv flows THEN guard in
  try/except + `detach()` explicitly per capture
  BECAUSE a crashed mid-teardown detach wedges the NEXT
  capture (silently idle, zero files; run after
  recovers) — a skipped detach survives, a crashed one
  poisons [verified: R6; a1/a2/a3/va_run,
  probe_kitti print DETACH-ALL-SKIPPED].
- IF a capture is silently idle with zero files THEN
  suspect a wedged writer from a prior crashed detach
  and re-run BECAUSE the run after recovers [verified:
  R6].

LIMITS (cites):

- L1: 50 orchestrator steps fit the bridge timeout
  (~3 min) (a3_run) [verified].
- L2: stale writers survive sends; detach_all at every
  start (R4) [verified].
- L3: crashed mid-teardown detach wedges next capture;
  run after recovers; guard + explicit detach (R6)
  [verified].
- L4: 1 transient bridge hiccup seen (WinError 121,
  port stayed up) (discovery.md base session notes)
  [verified-single-sample].

UNKNOWN:

- U1: exact bridge timeout value [theoretical].
- U2: max script size/duration [theoretical].

## Sources-read

- action-reasoner/skills/sdg/SKILL.md (full)
- action-reasoner/skills/sdg/failures.md (full)
- action-reasoner/skills/sdg/discovery.md (full)
- action-reasoner/skills/sdg/TOOLS.md (full)
- Fully read (20): base s1_run, s1_build, s2_run,
  s2_build, s3_run, s4_run, v12_run, v12_build,
  probe_bb3, probe_bw, probe_chain, probe_hide,
  probe_rep, probe_sem, probe_wr; adv a1_run, a2_run,
  a3_run, probe_kitti, va_run.
- Skimmed (17): base verify_s1/s2/s3/s4/v12; adv
  a1_build, a2_build, a3_build, probe_ann, probe_join,
  probe_labset, probe_warmup, pngstats,
  verify_a1/a2/a3/va.
- Evidence sampled: base s3_out/ (flat layout, labels
  json), probe_w/ (rgb_*.png + metadata.txt),
  s2_run.json (S2-REPORT); adv a1_out/Camera/ (4 dirs,
  no instance/depth), a1 label file (2 rows).




