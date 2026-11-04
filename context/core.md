# Action Reasoner — Verified Operator Context

Live-probed on Isaac Sim 6.0.0-rc.59 via the action bridge (92 probes,
`evidence.jsonl`). Every claim cites its probe (`ctx_*`). Paste this file
to operate the executor; `actions.json` carries per-action schemas,
verified examples, and observed failures.

Companion files: `actions.json` (57 actions), `evidence.jsonl` (92 rows),
`probe_plan.md` (method).

## 1. Batch protocol

- One action per line: `action.key param=value ...`. No spaces inside
  values; vec3 as `1,2,3`; quat as `x,y,z,w` (w last).
- `#` comments allowed, but comment AND blank lines COUNT in error line
  numbers (`ctx_60a`: the first action after a comment errors as "line 2").
- A batch STOPS at the first failure (`ok:false`); later lines never run.
  For independent probes use separate files (bridge runs `*.txt` in
  `inbox/` alphabetically, sequentially, ~1.5 s poll).
- Every result carries a snapshot; its FIRST line is sim state
  (`sim: playing t=...` / `sim: paused ...`) — but see the async rule.

## 2. Sim states (the state machine)

Four states; snapshot prints stopped as "paused" (only `timeline.log`
distinguishes them).

| action class | never-played (fresh stage) | playing | paused | stopped |
|---|---|---|---|---|
| create dynamic (cuboid/sphere/cyl/cone/capsule) | ok | ok | ok | ok |
| create fixed/visual | ok | ok | ok | ok |
| mass/pose/joint/articulation/clone | ok | REFUSE | ok | ok |
| delete/material/sensors/gravity | ok | ok | ok | ok* |
| velocity/step | BUG | BUG | BUG | BUG |

(`*` delete/dt while stopped not directly probed; handlers have no
state check except dt, which needs non-playing. `ctx_01/01b/03/04/06/08/08b`.)

- never-played (fresh stage, t=0, physics never ran) is the golden build
  state: everything allowed, nothing moves. `ctx_01/01b` all-ok.
- paused-only actions refuse while playing with exactly:
  `pause the sim first (timeline is playing)`. `ctx_04a/b/c`, `ctx_10a`.
- `sim.pause`/`sim.stop` are ASYNC (~110-135 ms to land; batch-ok does NOT
  mean landed). After either: wait for its result, sleep 5 s, then send
  state-dependent lines. NEVER put paused-only lines after `sim.pause` in
  the SAME batch (proven: PAUSE event fired 113 ms after batch-ok and the
  next batch in the same poll still saw playing, `ctx_12/13`).
- `sim.play` is SYNC (event fires before batch-ok): play-then-X in one
  batch is safe (`ctx_07b/c`, `ctx_42`).
- Result snapshots are taken immediately post-batch: a control action's
  effect may NOT be visible in its OWN snapshot. Verify state from the
  NEXT read (`ctx_07c` snapshot still said playing after stop-ok).
- `scene.open` resets the timeline to paused t=0 and CLEARS the name
  registry (prims persist; `ctx_50d`).
- `sim.reset` ENDS PLAYING (t=0) and re-initializes the backend (see 3).
  Verified 5x (`ctx_27/33/43/47/62`).
- Redundant controls fail loudly: play-when-playing `already playing`
  (`ctx_09`), pause-when-paused `not playing` (`ctx_60i`),
  stop-unless-playing `not playing` (`ctx_07/13`).

## 3. THE WEDGE (backend poisoning) — the most important rule

- Deleting a RIGID (dynamic) prim, or stripping rigid via
  `physics.remove.rigid_body`, POISONS the physics backend: every later
  dynamic cuboid/sphere create fails with
  `Failed to get rigid body velocities from backend` — in EVERY state
  including playing.
- Proven: rigid-delete then create fails (`ctx_28` -> `ctx_29`);
  `remove.rigid_body` isolated single-variable (`ctx_43` heal-ok,
  `ctx_44` pause, `ctx_45` remove-rigid-ok, `ctx_46` create FAILS).
  Deleting STATIC/VISUAL prims is SAFE (5x, no wedge).
- Recovery: `sim.reset` (verified 5x). stop+play does NOT reliably heal
  (`ctx_24/25` still wedged).
- SAFE WORKFLOW: never delete rigid prims mid-build. If you must, run
  `sim.reset` immediately after (it ends playing; re-pause if needed),
  then a one-line probe create to confirm the heal.
- Deleted-rigid names ARE reusable after reset (`ctx_61/62`: `healchk3`
  deleted, reset, recreated ok). The wedge is global-transient, not
  per-name poisoning.
- Failed creates leave STALE half-prims (prim exists, unregistered):
  they occupy name+slot but do NOT wedge (`ctx_37` all-ok with a stale
  prim present). Either leave them (use fresh names/slots) or delete
  them (rigid ones re-wedge: reset after).

## 4. BROKEN — do not use (executor bugs, exact errors)

- `physics.set.velocity` (ALL states):
  `'PhysxRigidBodyAPI' object has no attribute 'CreateVelocityAttr'`
  (`ctx_01`, `ctx_03`). Skill guidance: velocities must be set via
  RigidPrim AFTER play; no working action exists yet.
- `sim.step` (ALL states):
  `'NoneType' object has no attribute '_step' (needs a live physics
  context...)` (`ctx_10b/12b/14`). No stepping; use play/pause.
- `orient=` on `create.objects.cuboid`/`sphere`, and `set.pose orient=`
  on them: fails (root cause: Dynamic* pre-creates double-precision
  orient ops; handler Sets float). The message VARIES: either
  `Type mismatch for ...xformOp:orient... expected 'GfQuatd'` (`ctx_35`,
  `ctx_40b`) or the backend-velocities error (`ctx_38b/c`) — same cause.
  Orient on cylinder/cone/capsule WORKS (`ctx_38e/f/g` + Nov-1 wheels).
- `robot.set.velocity_limit`: on a JOINT target
  `no articulation root above target` (joints live in `/World/Joints`,
  never below a root, `ctx_41`); on the ROOT body
  `PhysX build lacks maxJointVelocity` (`ctx_41b`). Unusable here.
- Working extras: `scale=` on cuboid+cylinder (`ctx_38a/d`), `mass=` and
  `color=` on create (`ctx_34/35/38a`).

## 5. Naming, registry, references

- Pass explicit `name=` for anything later referenced (joints, drives,
  mass, pose). Auto-names: `cube_01...`/`sphere_01...` per shape class.
- Joint auto-name is `{from}_to_{to}`; drive/torque targets use it
  (`body_to_wheel_fl`).
- Registry clears on `scene.open`; references still resolve by
  `/World/<name>` guess. Duplicate names fail:
  `prim already exists: /World/X` (`ctx_60d`).
- Joint frames sit at the to-body center, world-aligned (code-read).

## 6. Per-group verified notes

- create 16/16 incl. plane (`ctx_01b/34`): dynamic cuboid/sphere go
  through core-API Dynamic* (backend-sensitive, see 3); cylinder/cone/
  capsule + ALL fixed/visual go through pure-USD `_create_shape`
  (no backend queries in code).
- physics 9/10 (`ctx_01/06/08/08b/40/40b`): scene/mass/pose/rigid+-
  /collider+-/rigid-opts/static-collider all ok paused. Details: mass
  rule `value > 0` (`ctx_60h`); rigid_body approximation ignored for
  non-mesh (`mesh-only` note); collider add-then-remove and
  remove-then-add both ok; static_collider works on bare visuals.
- joint 5/5 + robot 4/6 (`ctx_41/41b/c`): fixed/revolute+axis/
  prismatic+axis/spherical/distance-minimal all ok; rigid-to-static
  joints allowed (`not rigid` note, works); articulation root = path;
  drive (k/d/fmax/vel) ok; torque ok (maxForce + hint to pair with
  target_velocity); torque_limit ok; velocity_limit BROKEN (see 4);
  clone ok: `cloned 2: kx_1_clone1, kx_1_clone2 (joints inside clones
  keep original targets)` — clones do NOT rewire.
- material 2/2 (`ctx_22/31/36`): add echoes density/frictions/
  restitution; bind accepts registry-name prims.
- sensor 6/6 (`ctx_48a-f`): lidar/radar/ultrasonic + 2 raycast + beam,
  all ok playing. Short-name paths land under `/World`; absolute
  `/World/` paths also accepted. Creation only: no data-readback
  action exists.
- scene 4/4 (`ctx_50a-d`): create prim ok; delete ok but
  `refusing to delete /World itself` (`ctx_60f`) and
  `unknown target 'X'` (`ctx_60e`); save ok (197 KB file verified on
  disk); open ok but ASYNC (marker-vanish proof: marker created after
  save was gone post-open; sleep 10 s before checking).
- sim 6/7 (see 2): play/pause/stop/reset/gravity/dt ok; step BROKEN.
  `set.dt physics=0.008 rendering=0.0166` verified (`ctx_12a`).
- import/export 5/5, all paused (`ctx_51*`): URDF ok (sidecar `.usda`
  written next to source; prim `/World/<robot>`); MJCF ok (prim named
  from the SOURCE FILENAME, not the model attr); USD ref ok via
  `name=` + optional `pos=` (NOT `prim_path` — unknown-param error);
  heightmap ok from BMP via PIL (2035 instances, scale=2);
  URDF export ok (first articulation root found; 352-byte file
  verified on disk).

## 7. Verified recipes

- Rover, never-played single batch (Nov-1, all-ok): plane, chassis
  cuboid, 2 sphere wheels, 2 revolute `axis=Y`, articulation, 2
  drives (`stiffness=0 damping=500 max_force=100` + `target_velocity`),
  `sim.play`.
- Build-while-playing: creates (playing) -> `sim.pause` + sleep 5 s ->
  `set.pose` restores (parts fell during creates) -> joints ->
  articulation -> drives -> `sim.play`. (WALL-E pattern.)
- Save/open proof pattern: save -> marker create -> open -> sleep 10 s
  -> check (marker gone).
- Heal pattern: `[sim.reset, probe-create]` — ends playing AND proves
  the backend healthy in one batch.
- Drive tuning: `target_velocity` sets speed; raise `max_force` if the
  bot crawls under load (Nov-1 tuning history).

## 8. Failure table (message -> cause -> fix)

- `Failed to get rigid body velocities from backend` -> wedged backend
  (rigid delete / remove.rigid earlier) OR orient-on-cuboid/sphere ->
  `sim.reset` + heal-probe; drop orient on cuboid/sphere.
- `pause the sim first (timeline is playing)` -> paused-only action
  while playing -> pause + sleep 5 s, then run.
- `already playing` / `not playing` -> redundant control -> read state
  from the last snapshot first.
- `prim already exists: /World/X` -> dup name (or stale half-prim) ->
  fresh name (deleting a rigid stale re-wedges: reset after).
- `unknown target 'X'` -> typo / cleared registry -> use full path.
- `refusing to delete /World itself` -> by design.
- `line N: ...` -> validation; N counts comments/blank lines.
- `unknown action 'K'` / `no handler for 'K' yet` -> not in catalog /
  catalogued but unimplemented (only 57 handled of 3279).
- `unknown param 'P' for 'K'` -> wrong param name (hit: `prim_path`
  on usd-ref; use `name=`).
- `missing required param 'P'` / `joint_type must be one of ...` /
  `param 'value' must be > 0` / `bad token 'X' (want key=value)` ->
  fix the line; exact messages in `ctx_60*`.
- `no articulation root on stage (build or import a robot first)` ->
  export with no robot present.
- `file not found: X` / `not a USD file: X` -> bad import path.
- `Type mismatch ... xformOp:orient ... GfQuatd` -> see 4 (orient).
- `PhysX build lacks maxJointVelocity` /
  `'PhysxRigidBodyAPI' object has no attribute 'CreateVelocityAttr'` /
  `'NoneType' object has no attribute '_step'` -> see 4 (broken).

## 9. Honest untested list

- sphere+mass/scale; cone/capsule+scale/mass (expected ok: same helper
  as probed cuboid/cylinder).
- `set.pose orient=` on `_create_shape` prims (expected ok: fresh ops).
- cylinder/cone/capsule creates DURING a wedge (expected ok: no backend
  queries in code; never probed live).
- delete/dt while stopped; gravity never-played (expected per handlers).
- clone-wedge? prismatic/spherical/distance-wedge? pose-exception-wedge?
  (suspects only; `sim.reset` after any of them to be safe).
- URDF/MJCF options, heightmap PNG (BMP proven), export with multiple
  roots (first match wins).
- Sensor DATA readback (creation only; no read action exists).
- The long-play wedge trigger (63-min session failed; reset heals
  regardless of cause).
