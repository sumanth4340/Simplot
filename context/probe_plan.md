# Context probe plan (live execution → evidence → context pack)

Goal: every handled action probed live at least once; every claim in
`core.md` backed by a row in `evidence.jsonl`.

## Rules of probing
- Fresh names per probe (`sm_play_cub`, never reused after delete).
- State set explicitly before state-dependent batches; state read back
  from the result snapshot (never assumed).
- `sim.pause` is ASYNC (~113 ms to land): after a pause batch, wait for
  its result + sleep 5 s before any paused-only batch.
- Expected-fail probes go solo (one line per batch) to capture the exact
  message; expected-ok probes are grouped.
- Position slots per group (x = 4, 6, 8, ...) so probe bodies never collide.

## Phase 1 — sim-state matrix (foundation)
States: PLAYING, PAUSED-after-play, STOPPED-after-play.
(never-played verified once, after a fresh Isaac restart, in Phase 5.)
- sm_play_probes: cuboid + fixed + visual + velocity + gravity (all expect ok)
- sm_play_refuse_mass / _pose / _joint (solo, expect "pause first" refusals)
- sm_pause_probes: fixed, visual, mass, pose, joint, delete (expect ok),
  cuboid create LAST (expect backend FAIL — the paused-creates bug)
- sm_stop_probes: same shape as pause batch
- timing: play/pause/stop latency measured via timeline.log event stamps

## Phase 2 — group probes
- create ×16 (playing): all shapes + fixed/visual variants, one batch;
  extras batch: orient + scale + color + mass params.
- physics ×10 (paused): rigid±, collider±, scene, mass, pose, velocity,
  rigid opts, static collider on dedicated fixtures.
- joint ×5 types + robot ×6 (paused): chained bodies, articulation,
  drives, torque, limits, clone.
- material ×2, sensor ×6 (playing): add/bind; all six sensor creators.
- scene: create prim, delete prim; save to temp (verify file lands);
  open it back (LAST — replaces the stage).
- import/export: URDF (write a minimal 2-link arm fixture), MJCF
  (minimal fixture), USD ref (reference the saved stage), heightmap
  (generated PNG fixture), URDF export of the probe robot.

## Phase 3 — failure modes (solo batches, exact messages)
unknown action, bad token, missing required param, dup create, delete
unknown target, delete /World (refusal), pause-when-paused,
play-when-playing, stop-when-stopped, joint bad type, mass value=0,
name reuse after delete (stale-handle check), create while paused,
joint while playing.

## Phase 4 — write the pack
- `core.md`: paste-ready context (state machine, global rules, recipes).
- `actions.json`: filled from evidence (this file's skeleton + results).
- `evidence.jsonl`: every probe batch + result (append-only).
- `failures.md`: failure → cause → fix table.

## Phase 5 — prove it
User restarts Isaac (fresh stage = never-played state). From `core.md`
alone, build + physics + simulate a robot in minutes. WALL-E finishes here.
