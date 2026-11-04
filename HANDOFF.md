# Handoff: operate the Action Reasoner as a new AI

Read this file, `AGENTS.md` (agent roster), and `agents/STATE.md` (team
state) first. Then run the checklist at the bottom. Everything below is
live-verified on this machine (Windows, Isaac Sim at `C:/isaacsim`).

## What this is

Glimmer thinks in logic actions, not English. A task becomes action
lines (`create.objects.cuboid size=1 pos=0,0,2`), validated against
`actions_compact.json`, executed live in Isaac Sim by the Reasoner
extension. Multi-agent work flows through the dispatcher grammar
(`DEPLOY`/`STEP`/`PARALLEL`/`COWORK`) and `supervisor.py`. All
fine-tune data is text-only traces; stage awareness comes from the
sense watchdog's `event.*` lines, not screenshots.

## Layout

- `ext/isaacsim.action.reasoner.executor/` — the Isaac Sim extension
  source of truth (thinker, protocol, handlers, dispatcher,
  supervisor, watcher, window, bridge).
- `skills/` — 18 canonical skill packs (procedures + drills + evidence).
- `finetune/` — SFT traces (`traces_{mock,drills,dispatch,live}.jsonl`).
- `build_*.py` — trace builders; `modal/` — trainer + grader;
  `eval/` — 12-task scored suite; `tests/` — offline suite (215+).
- `.agents/skills/` (repo root) — registered skill shortcuts.

## Operating Isaac Sim (three channels)

1. **File bridge (preferred for actions):** validate lines offline,
   write `action-reasoner-bridge/inbox/<stem>.txt` (first `#` line is
   the task), poll `outbox/<stem>.result.json` (match by fresh mtime —
   NEVER pre-delete it). Bridge polls every 1.5s when on.
2. **Remote python** (`isaacsim_send.py` → `127.0.0.1:8226`): for
   diagnosis, revival, and extension reload only — never for actions.
3. **GUI:** prompt box + Run/Think/Dispatch/Reason buttons. Same code
   path as the bridge (`_run_batch_text`).

## Extension sync rule (critical)

The sim loads a COPY at
`c:/isaacsim/extsuser/isaacsim.action.reasoner.executor`, not this
checkout. After changing `ext/` or `data/`: copy files over, clear its
`__pycache__`, reload the extension remotely, then re-enable the
bridge on the NEW window (find by `_run_dispatch_text`, silence stale
instances so only one loop polls). Never edit the copy directly.

## Skills and agents

- 18 agents = 18 roster names (`dispatcher.ROSTER`), each mapped to a
  skill pack (`dispatcher.AGENT_PACKS`). One model serves all roles;
  specialization comes from per-call skill docs.
- Skill routing: `skills_routing.json` + `thinker.select_skills`.
- Watcher (`watcher.py`) is sense's always-on half: USD diffs into
  `event.*` lines, quiet unless something changed.
- Standing workflow: build new skills on graduated ones; co-validate
  against all prior skills; on any error, freeze and gather live
  read-only evidence before theorizing.
- No silent skill writes: PROPOSE first, write only after confirmation.

## Training loop

1. Grow data: valid inbox batches auto-convert via
   `build_live_traces.py` (needs `# task` header + all-ok lines).
2. Freeze: re-run all builders + coverage + full suite; commit + push.
3. Launch: `modal run action-reasoner/modal/train_glimmer.py`
   (pins are in the file; never train without an explicit go).
4. Grade: `modal run action-reasoner/modal/grade_adapter.py`, compare
   against the mock floor (action 1.000, skill 12/12).
5. Serve (still TODO): vLLM endpoint + `GLIMMER_ENDPOINT` config —
   only then does Glimmer drive the GUI.

## Hard rules (earned the hard way)

- NEVER delete `/World/PhysicsScene` (orphans the physics backend).
- NEVER spawn touching/overlapping bodies (poisons backend views).
- Net-zero stage for test batches: delete everything you make.
- The bridge `status.json` can lie stale; timeline + outbox are truth.
- A second session shares this sim: refuse inbox work when foreign
  files are present; never touch in-flight captures.
- Check `git status` before any commit; push only as `sumanth4340`.

## New-session checklist

1. `python action-reasoner/tests/test_*.py` — full suite green?
2. Probe the sim (remote): extension enabled? window has the dispatch
   branch? bridge loop on exactly one instance?
3. Diff checkout `ext/` vs the live copy; sync + reload if stale.
4. Send one trivial inbox batch; confirm outbox result + trace event.
5. Read `agents/STATE.md` and announce your focus before starting work.
