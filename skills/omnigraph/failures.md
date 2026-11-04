# OmniGraph — Failure Catalog (live-verified)

## R8: duplicate graphs on one target contaminate silently
- FAILURE: A leftover probe graph (O4GraphB) targeting the same hinge
  made a DISABLED graph look live (t2-t1=10 with dis=True) across
  two runs before the duplicate was found.
- CAUSE: Two graphs writing one attribute; no warning issued.
- RECOVERY: Kill all same-target graphs; probes MUST use unique
  targets. Sim crash conveniently wiped the duplicate; clean re-run
  confirmed R7 (frozen=0.0000 exact).
- PREVENTION: Pre-drill sweep: list /World for Graph* prims and
  assert exactly one writer per target.

## R7: only set_disabled truly disables (surgery does not)
- FAILURE: Exec-link cut (run#1): writes continued (data-flow
  firing). Value-link cut on live graph (run#4): no-op at runtime.
  An early "freeze" (run#2, t2==t1==0) was VACUOUS — the graph was
  dead (R6), so nothing could write; it proved nothing.
- CAUSE: WritePrimAttribute fires on upstream data flow, not exec;
  live DISCONNECT does not recompile the running instance.
- RECOVERY: First-class API: og.get_graph_by_path(P).set_disabled(
  True/False) + is_disabled() state assert. Node-level set_disabled
  exists too (untested).
- SEMANTICS: World clock runs while disabled; on resume the graph
  catches up to live time (resumed=20: 10 missed + 10 new).

## R6: recreated graph paths stay dead until re-touched
- FAILURE: RemovePrim + recreate at /World/O4Graph: upstream link
  present (linked=True) but zero writes (t1=0.000) until a
  disconnect+reconnect of the VALUE link revived it (t3=25).
- CONTRAST: Fresh path /World/O4GraphB wrote immediately (t1=5.0).
- CAUSE: Stale runtime instance shadows the recreated prim; stop()
  does not clear it; only a re-touch recompiles.
- RECOVERY: Revive-touch at run start (disconnect+reconnect one
  value link, proven 3/3) OR build at a fresh indexed path.
- PREVENTION: Prefer stable paths + revive-touch (keeps verifiers
  simple); never trust linked=True alone — gate t1>0 live-first.

## R5: WritePrimAttribute fires on data flow, exec is optional
- FAILURE: Cutting OnPB.outputs:tick -> Write.inputs:execIn did
  NOT freeze writes (t2=t1+10, full motion during "disabled"
  window).
- CAUSE: Node fires whenever upstream DATA changes; the exec wire
  is not required for evaluation.
- RECOVERY: See R7 — use set_disabled, not surgery.

## R4: later edits can't resolve bare node names
- FAILURE: Second edit's CONNECT with ("OnPB.outputs:tick", ...)
  raised "At least one end of the connection must be an attribute".
- CAUSE: Bare names resolve via the per-call creation map only.
- RECOVERY: Full paths in later edits ("/World/G/Node.attr")...
  but see R2: prefer ONE atomic edit anyway.

## R3: SET_VALUES bare floats reject on template inputs
- FAILURE: ("Mul.inputs:b", 0.01) raised "Failed to set value".
- CAUSE: Token-template inputs need explicit resolve types.
- RECOVERY: Typed 3-tuple: (attr, value, og.Type(DOUBLE)).
  (Tuples/strings resolve implicitly; bare floats don't.)

## R2: connected-tuple WritePrimAttribute silently never configures (OPEN)
- FAILURE: Vec.outputs:tuple(double3) -> Write.inputs:value targeting
  xformOp:translate: chain computes (live product/tuple correct) but
  the cube never moves; correctlySetup stays false; NO log error.
- CONTRAST: SET-tuple value works (O1); connected-DOUBLE works (O2).
- HYPOTHESIS: setup() runs before template outputs resolve and never
  re-runs; concrete sources (time) resolve at authoring, computed
  tuples don't. Atomic-vs-split edit order ruled out (both fail).
- WORKAROUND: Drive single-double destinations (joint targets, O3).

## R1: Controller.edit evaluates promptly (authoring writes land pre-play)
- FAILURE: O1's WritePrimAttribute value (z=1.5) was already on the
  cube BEFORE play; "pre-play untouched" gate failed (z0=1.5).
- CAUSE: Graph authoring triggers prompt evaluation; usdWriteBack
  persists the value immediately.
- RECOVERY: Reset-then-play separation: record z0a (authoring
  effect), reset to baseline, play, record z1 (tick effect).
- PREVENTION: Always reset target state after graph authoring and
  gate authoring-effect vs tick-effect separately.
