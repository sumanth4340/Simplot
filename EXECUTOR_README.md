# Action Reasoner Executor (v0) — install & run

In-sim prompt GUI + validated action executor for Isaac Sim 6.

## Install (once)

1. Copy the extension into Isaac Sim's user folder:
   `action-reasoner/ext/isaacsim.action.reasoner.executor` → `C:\isaacsim\extsUser\isaacsim.action.reasoner.executor`
2. Start Isaac Sim (`C:\isaacsim\isaac-sim.bat`).
3. Open `Window > Extensions`, search `Action Reasoner`, enable it.
   The `Action Reasoner` window opens automatically; reopen anytime via `Window > Action Reasoner`.

## Use

Type one action per line, `#` starts a comment. Example:

```
create.objects.plane size=20
create.objects.cuboid size=1 pos=0,0,2 color=0.2,0.4,0.9
create.objects.sphere radius=0.4 pos=1.5,0,2
sim.play
```

- `Think` turns the plain-English task box into action lines (see Thinker below); `Think & Run` plans and runs.
- `Reason` runs the in-GUI Reasoner loop: observe → plan → run actions → verify, until DONE or the step budget (see Reasoner below); `Stop` ends it after the current step.
- `Run` validates every line against the catalog, then executes top to bottom, stopping at the first failure.
- `Snapshot` prints stage telemetry: sim state, prims with rigid (R) / collider (C) / articulation (A) flags, rigid-body positions, name registry — and captures a viewport screenshot (see Observer).
- `Shots` opens the screenshot folder in Explorer.
- `Actions` lists the 15 runnable v0 actions with signatures.
- `Clear` empties the log.

More examples:

```
physics.set.mass target=cube_01 value=5
physics.set.pose target=cube_01 pos=1,0,1
physics.set.velocity target=cube_01 linear=0,2,0
sim.pause
sim.step n=10
sim.stop
```

Targets are the auto names (`cube_01`, `sphere_01`) unless you pass `name=` on create,
or absolute prim paths like `/World/my_thing`.

Mini rover (chassis + 2 wheels + joints + articulation + drive + lidar):

```
create.objects.plane size=20
create.objects.cuboid name=chassis size=1.2 pos=0,0,0.65
create.objects.sphere name=wheel_l radius=0.3 pos=0,0.95,0.3
create.objects.sphere name=wheel_r radius=0.3 pos=0,-0.95,0.3
joint.create.joint joint_type=revolute from_prim=chassis to_prim=wheel_l axis=Y
joint.create.joint joint_type=revolute from_prim=chassis to_prim=wheel_r axis=Y
robot.add.articulation path=chassis
robot.set.joint_drive target=chassis_to_wheel_l stiffness=0 damping=500 max_force=100
material.add.rigid_body_material path=/World/Looks/rubber staticFriction=0.9 dynamicFriction=0.7
material.bind.material prim_path=wheel_l material_path=/World/Looks/rubber
sensor.create.rtx_lidar path=lidar_top tick_rate=10
sim.play
```

## What v2 runs (56 actions)

create (plane, cuboid, sphere, cylinder, cone, capsule + fixed/visual variants) ·
physics (rigid body ±, collider ±, physics scene, mass, pose, velocity, rigid opts, static collider) ·
joint (fixed/revolute/prismatic/spherical/distance) ·
robot (articulation root, joint drive, torque, torque/velocity limits, clone) ·
material (physics material, bind) ·
sensor (rtx lidar/radar/ultrasonic, raycast range + lidar, light beam) ·
import/export (urdf, mjcf, usd reference, heightmap, urdf export) ·
scene (create/delete prim, save, open) ·
sim (play, pause, stop, step, reset, gravity, dt). Everything else in the
195-action catalog validates but reports "no handler yet" until its handler lands.

Scene cleanup and tuning:

```
scene.delete.prim target=wheel_l
sim.set.gravity value=0,0,-9.81
sim.set.dt physics=0.008 rendering=0.0166
scene.save path=C:/robots/rover.usd
```

Real-robot import (paused sim; extension auto-enabled on first use):

```
import.robot.urdf path=C:/robots/arm.urdf fix_base=true merge_fixed_joints=true
robot.set.torque_limit target=arm_joint_1 value=50
export.asset.urdf path=C:/robots/arm_out.urdf
```

## Thinker (plain-English tasks)

Type a task like "make a moon rover with two wheels" in the Thinker box:

- `Think` plans it into action lines (shown in the action prompt, not run yet).
- `Think & Run` plans and immediately runs the plan.
- The status line shows the backend: `reflex`, `glimmer` (Modal
  endpoint), or `mock`.

How it plans: primitive commands ("create a cube", "play", "delete
cube_01") are answered in milliseconds by the `reflex` dispatcher — a
built-in grammar with no LLM call, so there is no English in or out,
only action lines. Anything compositional falls through to Think:
every Think first captures a fresh viewport screenshot, then
the task + screenshot + live stage snapshot + relevant skill docs are sent
to the Glimmer endpoint (multimodal: text + image in), which must reply
with action-only lines; the reply is cleaned (fences/prose stripped)
before it lands in the prompt box. The log shows `vision: sent N
screenshot(s)` when images go out (max 3, 8 MB each).

The Glimmer reply streams (SSE): each complete action line lands in the
prompt box the moment it finishes — `Think` streams the transcript only,
while `Think & Run` validates and runs every line live, stopping at the
first failure (same contract as the `Run` button, per line). A worker
thread reads the stream so the GUI and viewport keep pumping; the lines
trigger on the main thread. If the stream breaks mid-reply, the lines
already triggered stand and the log says how many were kept — the
planner never re-emits a fallback over a partial run.
`mock` is a built-in task parser used when no endpoint is configured or
reachable, so the whole flow works with no GPU. It splits the task into
clauses (on and/then/commas) and parses each into a shape spec: count
(number words or digits, max 6), color (red/green/blue/yellow/orange/
purple/pink/cyan/white/black/gray/brown), size (tiny/small/medium/big/
large/huge/giant), tower stacking, and heavy/weight (targets the named
body, e.g. `name=heavy_cube`). Instances are laid out overlap-free in a
row, or one vertical stack per tower clause — e.g. "red cube and blue
sphere", "stack three tiny boxes", "build a huge green cylinder". The
mock is text-only (it notes attached images) and skips the ground plane
when the snapshot already has one. Tasks it cannot parse get the demo
scene (plane + cuboid + sphere), and it says so in the log.

Configure the endpoint (no restart needed, re-read on every Think):

1. Copy `data/thinker_config.example.json` to `data/thinker_config.json`
   (in the installed copy under `extsUser`) and fill in your Modal URL
   (from `modal deploy`) and the same `GLIMMER_API_KEY`.
2. Or set env vars before starting Isaac Sim: `GLIMMER_ENDPOINT`,
   `GLIMMER_API_KEY`, `GLIMMER_MODEL` (default `glimmer-30b`).
   Env vars override the config file per-field.

## Reasoner (in-GUI agent loop)

`Reason` runs the whole task inside the GUI — no outside driver needed.
Each step captures a fresh screenshot, plans with the task + snapshot +
screenshot + skills, and runs the resulting action lines; the next step
re-observes and either repairs failures or finishes when the planner
replies with the single line `DONE` (max 6 steps, `Stop` ends early).
Every step's plan lands in the action prompt box, so you always see
exactly which actions ran.

- With the Glimmer endpoint configured, the loop verifies and self-repairs:
  failures come back with the error text so the next plan fixes them.
- With no endpoint (`mock`), Reasoner does one single pass — the mock
  planner is deterministic and cannot observe or repair, so looping it
  would only duplicate prims. It says so in the log.
- A primitive task answered by `reflex` is likewise one single pass —
  the whole task was one command, so there is nothing to verify further.
- If the endpoint drops mid-run, the loop fails loudly instead of
  silently degrading to mock.

Everything the Reasoner runs is validated catalog actions
(`create.objects.*`, `joint.*`, `robot.*`, ...) through the same
executor as the `Run` button. There is no code-execution path in the
extension: the Reasoner emits action lines, never Python.

## Bridge (outside driver: tests and external tools)

The Bridge lets a program outside Isaac Sim drive the executor — used
for offline checks and external tooling. Batches are action lines only
(the exact format of the prompt box); like every other path, they run
through catalog validation and the action executor.

1. In the Action Reasoner window press `Bridge: Start` (polls every 1.5 s).
2. The driver writes one `*.txt` batch per command into
   `~/action-reasoner-bridge/inbox/` (same format as the prompt box).
3. Each batch runs exactly like `Run` (validate, top to bottom, stop at
   first failure). The inbox file moves to `done/`, and `outbox/` gets:
   - `<name>.result.json` — per-line ok/msg, log lines, stage snapshot
   - `<name>.png` — viewport screenshot after the run (path patched into
     the JSON as `shot` once the async capture lands)
4. `status.json` shows liveness (`bridge` on/off, `pending`, `last_cmd`,
   `last_ok`). Press `Bridge: Stop` (or disable the extension) to end it.

Bridge runs are also appended to the traces log (`bridge_run` events),
so they become fine-tune data like GUI runs.

## Observer (screenshot verification)

Every `Snapshot` also captures the active viewport (no UI chrome) to
`~/action-reasoner-captures/snapshot_<timestamp>.png` via Isaac Sim's
replicator rgb annotator, and logs the path once it lands. The capture
runs async so the GUI never freezes; the Thinker includes the latest
screenshot path in its context.

Notes:

- First capture auto-enables the `isaacsim.test.utils` extension (takes a
  few extra frames once, then instant).
- Think screenshots are saved with the `think_` prefix; manual Snapshot
  shots use `snapshot_`.

## Offline tests (no Isaac Sim needed)

```
python action-reasoner/tests/test_protocol.py
python action-reasoner/tests/test_thinker.py
python action-reasoner/tests/test_observer.py
python action-reasoner/tests/test_traces.py
python action-reasoner/tests/test_bridge.py
python action-reasoner/tests/test_reasoner.py
```

Covers parsing, type coercion, defaults, catalog pre-rules (clamps, value > 0),
unknown-action suggestions, handler/catalog consistency, plus Thinker prompt
building, skill routing, action extraction, vision blocks (encode, cap,
unreadable-skip), mock plans (all validated against the catalog), endpoint
failover to mock, observer availability/paths, and fine-tune data
curation/schema.

Every Think and Run also appends to `~/action-reasoner-traces/traces.jsonl`
for future training data — see `FINETUNE_README.md`.

## Notes

- Physics edits, joints, and articulation roots require a paused timeline; the executor refuses while playing.
- `pos=` is `x,y,z` (no spaces). `orient=` is a quaternion `x,y,z,w`, `scale=` is `x,y,z` — honored by every shape creator (not the ground plane), so models spawn fully posed.
- Cylinder wheels: lay the barrel onto its side with `orient=0.7071,0,0,0.7071` (axle along Y), then joint with `axis=Y`, e.g. `create.objects.cylinder name=wheel_l radius=0.3 height=0.25 pos=0,0.95,0.3 orient=0.7071,0,0,0.7071`.
- Joint frames sit at the to-body center and are world-aligned: oriented bodies joint correctly, and `axis=` (X, Y, or Z) always means a world axis.
- `material.bind.material` accepts `strength=strong|weak` and `material_purpose=` (default all-purpose).
- After editing extension code, re-copy the folder to `extsUser` and press `Refresh` in Extensions (or restart Isaac Sim).
