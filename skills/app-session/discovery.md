# App & Session — Discovery Notes (live-verified, 6.0.0)

## Operating the session from outside
- Pattern: local driver builds SEND=[python, isaacsim_send.py,
  --raw, --timeout, N], shells --file <library> --arg k=v...,
  parses the JSON envelope's output (+traceback on error),
  appends "$ send <args>" transcripts to evidence txt.
- simulation_control.py actions: status (state + dt + sim
  time + steps + backend + device + scenes), play, pause,
  stop, step (+num_steps, auto-plays first). Sync update_app
  inside is fine for these short calls.
- open_stage.py actions: new (+template), open/save (+usd_path
  absolute, forward slashes), info (URL, up-axis, units, prim
  count, loading). save_as_stage returns bool; "Saved as:".
- stage_info.py: tree default (excludes /Render), list +
  filter_type for type queries, prim_path for "Path:" detail.
- Always end drivers STOPPED (clean handoff to next drill).

## State facts (this build)
- Physics DT 1/60; 60 update steps ~= 1.0 sim-second.
- 659 extensions loaded; python_server enabled (else no
  bridge at all — A3 doubles as a bridge self-check).
- Empty-stage template has a small prim count; any authored
  prim makes wipe-vs-loaded counts strictly ordered.
- Viewport shots work immediately after reopen+step (no extra
  warm-up needed beyond the step itself here).

## Drill design rules
- Local drivers (not in-sim scripts) for multi-send session
  flows: each send is one action, transcript is the evidence.
- Gate transitions (cycle ORDER), not just end states; gate
  the LAST sim-time line in transcripts (status repeats it).
- UTF-8 for all transcript IO (R2); absolute forward-slash
  USD paths in --arg values.

## Session notes
- Zero crashes, zero bridge hiccups this skill. Sim carried
  over from the V12 fresh restart; stage now = V13 reopen.
