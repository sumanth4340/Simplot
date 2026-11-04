# sdg — Discovery Notes (live-verified)

---

# Part: base (merged from `sdg`)

# SDG — Discovery Notes (live-verified, 6.0.0)

## Interactive-Kit Replicator contract
- Cameras: rep.create.camera() then pose ONLY via the
  `with cam: rep.modify.pose(position=, look_at=)` context.
  Direct `rep.modify.pose(cam, ...)` raises TypeError (R1).
- Render products take the camera ITEM:
  rep.create.render_product(cam, (w, h)). No GetPath on items.
- Stepping: `await rep.orchestrator.step_async()` (+
  `await ...wait_until_complete_async()` before reading files).
  Sync step()/wait raise OrchestratorError in Kit.
- set_capture_on_play(False) for manual step control; attach
  annotators/writers before stepping; detach after (plus
  detach_all() at capture start — R4 stale writers).

## Data shapes (this build)
- rgb: bare uint8 array (H,W,4). bbox_2d_tight/loose: dict
  data=[(semId,x0,y0,x1,y1,?)] + info{bboxIds,idToLabels,
  primPaths}. semantic_segmentation: dict data=(H,W) uint32
  + info{idToLabels: 0 BACKGROUND, 1 UNLABELLED, 2+ labels}.
- add_labels(prim, labels=[...]) keyword-only; dedups on
  re-run; get_labels returns {taxonomy: [...]}.

## Writer realities (Kit-interactive vs headless)
- BasicWriter bbox path is CORRECT in Kit (matches direct
  reads exactly); RGB path writes zeros (R3 OPEN) — writers
  are validated for headless/standalone flows.
- Proven Kit pattern: BasicWriter(structured) + direct
  annotator reads saved in-script (pixels). Never block in
  Writer.write() (R4 killed all writers + backend batch).
- Flat output layout (R2); frame counters are per-instance
  (self._frame_id=0 in __init__).
- bbox semantic set freezes at first capture (R5); semseg
  stays live. Consequence: self-contained exam scenes.

## Drill design rules
- Predict exact box/pixel facts where possible (S2: area
  7225, npix2 5847); gate modalities independently (rgb
  mean, box area, class pixels) so one bad channel fails
  loudly instead of contaminating the verdict.
- Scripted variation (S4: poses; V12: cameras) beats RNG for
  determinism; note rep.set_global_seed for randomized runs.
- Class-name regexes must allow digits ([\w+]+, not [a-z+]).

## Session notes
- 1 bridge hiccup (WinError 121, transient, port stayed up);
  1 deliberate sim restart (V12 fresh state for R5). No crash
  losses: all evidence on disk.

---

# Part: adv (merged from `sdg-adv`)

# sdg-adv — Discovery Notes (live-verified, 6.0.0)

## KittiWriter contract (Kit-interactive)
- `initialize(output_dir, use_kitti_dir_names=True,
  omit_semantic_type=True, mapping_dict={lowercase: RGBA})`.
  Layout: `Camera/image_02/*.png`, `label_02/*.txt`,
  `semantic/*.png`, `semantic_rgb/*.png`. No `instance/` or
  `depth/` (R8: uint16 silently dropped).
- Label rows: `class 0.00 occ 0.00 x0 y0 x1 y1 + 7x 0.00`
  (alpha/dims/location/rot/score unsupported, always 0).
  Boxes <25px tall are discarded by the writer.
- `mapping_dict` keys MUST be lowercase (R9); unmapped
  classes render as unlabelled (zeroed sem).
- Attach AFTER warmup (R10); detach explicitly at end (R6).

## Determinism + scale
- Seeded `np.default_rng` poses + scripted USD translates give
  bit-identical layouts across runs (A2: leg0==leg1 exact).
- 50-frame KITTI sweep: 23s cold (2.2 fps incl. material
  warmup), ~4s warm (13.7 fps). Re-sweep exam: 12/12.
- bbox annotator data is a 1-D STRUCTURED array (fields
  semId,x0,y0,x1,y1): index rows (`r[0..4]`), never `[:, i]`.

## Session notes
- 2 sim restarts (R5/R7 freeze resets). No crashes. All
  evidence on disk under `evidence/` (a1_out, a2_layouts,
  a3_out, va_out).
