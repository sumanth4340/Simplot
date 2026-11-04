# sdg — Failure Catalog (live-verified)

Failure IDs are namespaced per part: base R1-R5 (R3 open), adv R6-R10. Script paths below are relative to each part dir.

---

# Part: base (merged from `sdg`)

# SDG — Failure Catalog (live-verified)

## R5: bbox annotators freeze the semantic set at first capture
- FAILURE: V12 boxes labeled AFTER S2's first bbox step were
  invisible to bbox_2d_tight AND _loose (n=1, only S1Cube) —
  even with S1Cube hidden (n=0). Semseg saw all three live.
- CAUSE: bbox annotators enumerate labeled prims once (first
  capture) and never refresh; semseg reads per-pixel labels
  fresh every frame.
- RECOVERY: Label EVERYTHING before the first bbox capture in
  a session. Exams must be SELF-CONTAINED scenes (own lights/
  ground/props/labels) run on a fresh sim, never piggybacking
  on earlier drills' stages.

## R4: blocking IO in Writer.write() kills the capture (all writers)
- FAILURE: Custom writer doing get_data()+np.save inside
  write(), dual-attached with BasicWriter: ZERO files from
  EITHER writer (only metadata.txt). BasicWriter-alone on the
  same scene works (2/2 bbox files).
- CAUSE (hypothesis): Blocking call inside the graph-triggered
  write() stalls/poisons the shared backend batch; possibly
  get_data() reentrancy during capture.
- RECOVERY: Writer subclasses must only schedule backend work,
  never block. Drill pattern: BasicWriter for structured data
  + DIRECT annotator reads saved in-script for pixels.
- HYGIENE: Stale writers survive sends (frame counter 0003/
  0004 kept firing in a later send) — call
  WriterRegistry.detach_all() at every capture start.

## R3: BasicWriter RGB is pure black in interactive Kit (OPEN)
- FAILURE: BasicWriter rgb_*.png all exactly 0.00/0.00 across 8
  frames and 2 RPs, while direct rgb annotator reads on the
  SAME RP/steps give 63.69 and bbox_2d_tight writes correctly
  (same box as direct: 117,79,202,164, class s2cube).
- CAUSE (hypothesis): OgnWriter graph payload path delivers a
  zeroed RGB buffer in Kit-interactive; writers are validated
  for headless/standalone flows. Kit log shows only an
  unrelated WriterSyncGate cycle warning.
- WORKAROUND: Custom rep.Writer subclass pulling tensors via
  annotator.get_data() directly in write() (documented
  "direct access to annotator tensors" pattern); saves .npy.
  BasicWriter kept for bbox (proven working).

## R2: BasicWriter uses a FLAT layout (no per-modality subdirs)
- FAILURE: Gated OUT/rgb/*.png — dir missing, rgb_files=-1.
- CAUSE: Assumed nested layout; writer emits rgb_NNNN.png,
  bounding_box_2d_tight_NNNN.npy + _labels/_prim_paths JSONs
  + metadata.txt, all flat in output_dir.
- RECOVERY: Glob flat patterns (rgb_*.png, *_*.npy).

## R1: interactive-Kit Replicator API corrections (3x)
- FAILURE 1: rep.modify.pose(cam, position=..., ...) raised
  "got multiple values for argument 'position'".
  FIX: Context pattern — `with cam: rep.modify.pose(...)`.
- FAILURE 2: rep.create.render_product(cam.GetPath(), ...) —
  ReplicatorItem has no GetPath.
  FIX: Pass the camera ITEM: rep.create.render_product(cam, (w,h)).
- FAILURE 3: rep.orchestrator.step() raised OrchestratorError
  ("only in a standalone workflow... use step_async").
  FIX: Inside Kit always `await rep.orchestrator.step_async()`
  (bridge sends support top-level await).

---

# Part: adv (merged from `sdg-adv`)

# sdg-adv — Failure Catalog (live-verified, 6.0.0)

## R6: detach_all crashes on stale writers bound to removed products
- First Kitti probe died in `rep.WriterRegistry.detach_all()`:
  "Accessed invalid null prim" from N2/S2-era writers still
  attached to products of deleted lidar prims. Worse, the
  MID-TEARDOWN crash wedged the next capture (writer silently
  idle, zero files); the run after recovered.
- RECOVERY: guard every `detach_all()` in try/except; a skipped
  detach is survivable, a crashed one poisons the next run.
- PREVENTION: detach writers explicitly (`bw.detach()`) at each
  capture's end; never rely on detach_all across drills.

## R7: bbox annotators freeze the labeled INSTANCE set
- After removing A1/K cubes, new abox cubes (same frozen class!)
  returned ZERO rows: idToLabels {} — new instances never join,
  removed instances never return. Sharper than pack-R5 (which
  spoke of the semantic SET): it is the instance set that
  freezes at first capture.
- RECOVERY: sim restart + label-before-first-capture. A2/A3/VA
  share one frozen set on purpose (abox).
- Note: semantic_segmentation stays live (pack-R5, reused).

## R8: KittiWriter uint16 outputs silently missing
- `instance/` and `depth/` never land (not even dirs); rgb,
  label_02, semantic, semantic_rgb all fine. Common factor:
  uint16 PNG backend writes (instance renumbered uint16, depth
  uint16) are silently dropped. No log errors.
- RECOVERY: gate rgb/labels/semantic only; take instance/depth
  pixels via direct annotator reads (S1 pattern) when needed.

## R9: KittiWriter label/case gotchas
- Default labels embed a dict REPR WITH A SPACE:
  `"{'class': 'kboxa'}"` — naive `.split()` parsing shifts every
  field by one. Use `omit_semantic_type=True` for plain tokens.
- Class names are case-FOLDED ('kboxA' -> 'kboxa'); mapping_dict
  keys must be lowercase or nothing matches (all-zero sem map).
- Semantic ids are 0-based class indices with background folded
  into 0 (bg+kboxa=0, kboxb=1): first class is inseparable from
  bg in the sem map. Use instance/semrgb for separation.

## R10: writer attach counts warmup steps
- KittiWriter attached BEFORE the warmup step wrote frame 0
  during warmup (51 files for a 50-frame sweep). RECOVERY:
  warm up first (120 app updates + 1 step), attach after.

## Ruled OUT during A-drills (do not chase)
- KittiWriter RGB is NOT black in Kit (mean 63.7): pack-R3
  (BasicWriter RGB zeros) does not apply to KittiWriter.
- `rep.set_global_seed` was suspected of detaching annotators;
  dropping it changed nothing (real cause was R7 + warmup).
  np `default_rng(seed)` alone gives deterministic layouts.
- Missing PIL/cv2/mpl in system AND pixi pythons: pixel stats
  run under `C:/isaacsim/python.bat` (pngstats.py helper).
- First-frame empty reads on a fresh sim: renderer warmup
  (120 app updates), then boxes every step.
