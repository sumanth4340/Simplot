# Fine-tuning data for the Action Reasoner

## What's here

| File | Content |
|---|---|
| `finetune/actions_finetune.json` | 169 trainable compact actions (26 dead excluded, see below) |
| `finetune/traces_mock.jsonl` | 19 task -> action traces in chat format |
| `finetune/traces_drills.jsonl` | 270 drill-derived traces (90 validated tasks x 3 snapshots) |
| `finetune/traces_dispatch.jsonl` | 36 dispatcher traces (12 deploy plans x 3 snapshots) |
| `finetune/traces_live.jsonl` | 116 converted live traces (all-ok GUI + bridge runs) |
| `~/action-reasoner-traces/traces.jsonl` | Live traces, appended by the GUI (think + run events) |

Regenerate offline data anytime (no Isaac Sim, no GPU):

```
python action-reasoner/build_traces.py [--out DIR]
python action-reasoner/build_drill_traces.py [--out DIR]
python action-reasoner/build_dispatch_traces.py [--out DIR]
python action-reasoner/build_live_traces.py [--out DIR]
```

## Trace format

One JSON object per line, OpenAI chat style — the same messages the
Thinker sends at inference, so fine-tuning aligns with deployment:

```json
{"messages": [
  {"role": "system", "content": "<output rules + runnable actions + skills>"},
  {"role": "user", "content": "TASK: ...\n\nLIVE STAGE SNAPSHOT: ..."},
  {"role": "assistant", "content": "create.objects.plane size=20\n..."}
 ],
 "meta": {"task": "...", "backend": "mock", "skills": [...],
          "validated": true, "images": 0, "snapshot": "canned-empty",
          "actions": ["create.objects.plane", "..."]}}
```

Every assistant block is machine-validated against the catalog before it
is written (the generator refuses to emit invalid traces).

This `messages` shape loads directly into common chat fine-tuning stacks
(TRL `SFTTrainer`, Axolotl, torchtune chat templates). All traces are
text-only (`images: 0`); stage awareness comes from the sense
watchdog's `event.*` lines, not screenshots.

## Curation: the 26 excluded actions

Excluded because their catalog resolution is `import-failed` (stale Kit
API paths) and the validator rejects them — training on outputs the
executor can never run would teach failure:

- rl (14): env/reward/termination/observation/action/command/curia/event,
  agent, train/play, actuator
- ros2 (8): bridge, publishers/subscribers/topics, clock, tf, urdf, sim
- sensor (3): add camera/contact/imu (stale paths; rtx lidar uses the
  native `Lidar` handler instead)
- create (1): asset conveyor

They stay in `actions_compact.json` for reference. Revisit when native
handlers land for these groups.

## Live traces (reasoning data)

Mock traces teach FORMAT (action-only lines over runnable actions), not
reasoning. Reasoning data accumulates while you work: every `Think`,
every `Run`, and every Reasoner step appends to
`~/action-reasoner-traces/traces.jsonl`:

- `think`: task, backend (mock/glimmer), skills, screenshot paths,
  snapshot, planned actions, notes (Reasoner steps add `reason_step`)
- `run`: executed lines + per-line ok/FAIL results (Reasoner steps add
  `reason_step`)
- `reason_done`: Reasoner task, final status (done/failed/stopped),
  reason, step count

Once the Modal endpoint is live, filter the log for
`backend == "glimmer"` + all run lines `ok` to mine more text traces
(stage deltas arrive as watchdog `event.*` lines).

Text SFT consumes the converted set: `build_live_traces.py` mines
all-ok GUI + bridge runs into `finetune/traces_live.jsonl`
(protocol- and schema-validated, mock-fallback intent mismatches
dropped, snapshots truncated to trainable size).

## Skill context caveat

The `skills` in each trace come from best-effort keyword retrieval, which
can attach a weakly related skill. The model learns to use skills as
hints, not orders — an improvement to the router (e.g. stricter
thresholds) upgrades both inference and future traces at once.
