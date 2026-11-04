# Action Reasoner

Glimmer thinks in logic actions, not English. A plain-English task becomes
validated action lines (`create.objects.cuboid size=1 pos=0,0,2`), executed
live in Isaac Sim by the Reasoner extension. Multi-agent work flows through a
dispatch grammar (`DEPLOY`/`STEP`/`PARALLEL`/`COWORK`) and a supervisor; all
fine-tune data is text-only traces, with stage awareness from the sense
watchdog's `event.*` lines instead of screenshots.

## How it works

- **Action catalog** (`actions_compact.json`): 195 keys, 169 runnable, 26
  no-handler (flagged, never emitted: `rl.*`, `ros2.*`, `sensor.add.*`,
  `create.asset.conveyor`).
- **Thinker** (plain English → actions): `reflex` fast path for primitives
  (no LLM call) → `glimmer` endpoint (streams action lines via SSE) →
  `mock` fallback. Output rules: action lines only, color triples, scalar
  size, no interpenetration, `sim.play` last.
- **Executor**: every line validated against the catalog, run top to
  bottom, stop at first failure. GUI buttons: Run / Think / Think & Run /
  Reason loop / Dispatch.
- **File bridge** (preferred channel): validate offline → write
  `action-reasoner-bridge/inbox/<stem>.txt` (`#` task header first line) →
  poll `outbox/<stem>.result.json` by fresh mtime (never pre-delete).
  One transport op per leg; verify hold-state from the *next* result.
- **Sense watchdog**: always-on stage diff → `event.*` lines
  (`event.stage.prim_added/removed`, `event.joint.*`, `event.pose.moved`,
  `event.timeline.*`). Delta-only: quiet = no change.
- **Multi-agent**: 18 skill agents (see `AGENTS.md`), spawned on demand;
  `xval` is the QA gate after multi-pack builds. Dispatch plans validate
  via `dispatcher.validate_block`.

## Repo layout

| Path | What |
|---|---|
| `ext/isaacsim.action.reasoner.executor/` | Extension source of truth (thinker, protocol, handlers, dispatcher, supervisor, watcher, window, bridge, diagnose, optimize) |
| `skills/` | 18 canonical skill packs (procedures + drills + evidence) |
| `nav/` | DWA planner + math preflight + proof-replay driver |
| `finetune/` | SFT traces (`traces_{mock,drills,dispatch,live}.jsonl`, 470 total) |
| `build_*.py` | Trace builders (mock, drills, dispatch, live, vision) |
| `modal/` | Trainer + adapter grader (Modal) |
| `eval/` | 12-task scored suite (8 action + 4 dispatch) |
| `tests/` | Offline suite (`tests/run_all.py`, 21 files, 250+ tests) |

Live sim loads a **copy** at `C:/isaacsim/extsUser/isaacsim.action.reasoner.executor`,
not this checkout — after changing `ext/`, copy over, clear `__pycache__`,
reload remotely, re-enable the bridge on the new window. Details in `HANDOFF.md`.

## Quickstart

```powershell
# 1. Full offline suite (no Isaac Sim, no GPU)
python action-reasoner/tests/run_all.py

# 2. Install the extension (once): copy ext/ into C:\isaacsim\extsUser\,
#    enable "Action Reasoner" in Window > Extensions (see EXECUTOR_README.md)

# 3. Drive the sim via the file bridge:
#    validate lines offline, write inbox/<stem>.txt, poll outbox/<stem>.result.json
```

Minimal action batch:

```
create.objects.plane size=20
create.objects.cuboid size=1 pos=0,0,2 color=0.2,0.4,0.9
sim.play
```

## Skills and agents

18 packs, one agent each (roster in `AGENTS.md`, team memory in
`agents/STATE.md`): `sense`, `stage`, `modeling`, `articulation`,
`manipulation`, `rendering`, `viewport`, `omnigraph`, `behavior`,
`appsession`, `physics`, `pyapi`, `deform`, `gpunuc`, `rosnav`, `sensors`,
`sdg`, `xval`. Standing orders: read the pack first, live read-only
evidence before theory, report action lines not prose, catalog keys only,
no silent skill writes (propose first, write after confirmation).

## Training loop

1. **Grow data**: valid inbox batches auto-convert via
   `build_live_traces.py` (`# task` header + all-ok lines required).
2. **Freeze**: re-run all builders + coverage + full suite; commit + push.
3. **Launch** (explicit go only): `modal run action-reasoner/modal/train_glimmer.py`.
4. **Grade**: `modal run action-reasoner/modal/grade_adapter.py` vs the mock
   floor (action 1.000, skill 12/12).
5. **Serve** (TODO): vLLM endpoint + `GLIMMER_ENDPOINT` config — only then
   does Glimmer drive the GUI.

Current data: 470 traces (19 mock + 282 drills + 36 dispatch + 133 live),
all assistant blocks machine-validated against the catalog. Full schema and
curation notes in `FINETUNE_README.md`.

## Proven live

- **DWA rover drive**: car drove (-0.79,-0.89) → goal (-2.2,2.4), finished
  0.46 m out (`nav/demo_proof.txt`, 41 drive commands). Lessons baked in:
  plan-from-cruise (pause-per-leg defeats the dynamic window), footprint =
  wheel span, escape back-up recovery, waypoint latch, pivot-to-face.
- **Safety net** (`nav/preflight.py`, `executor/diagnose.py`,
  `executor/optimize.py`, `nav/drive_mission.py`): math preflight gate,
  failure black box, emission gate, proof-replay driver with zero/pause/stop.

## Hard rules (earned the hard way)

- NEVER delete `/World/PhysicsScene` mid-session (orphans backend views).
- NEVER spawn touching/overlapping bodies (poisons backend views).
- Net-zero stage for test batches: delete everything you make.
- `status.json` can lie stale; timeline + outbox are truth.
- One transport op per leg; forward slashes only in action values.
- Refuse inbox work when a second session's foreign files are present.

## Docs index

- `EXECUTOR_README.md` — install, buttons, Thinker, actions, safety net.
- `FINETUNE_README.md` — trace format, builders, curation, training.
- `HANDOFF.md` — new-AI operator checklist (bridge, sync, training).
- `AGENTS.md` — agent roster + standing orders.
- `VALIDATION_REPORT.md` — validation record.

## Status / roadmap

- Open: vLLM serve endpoint, optimizer hook at supervisor/executor boundary,
  closed-loop pose feedback in the replay driver, window live verification
  in Kit, eval metric beyond eyeballing.
- Known: `sim.step` broken live (use play+settle); intermittent forward-leg
  stall needs DOF-level diagnosis; one pre-existing test red when the live
  thinker config flips the backend to glimmer.
