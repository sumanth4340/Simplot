# Skill 9 OMNIGRAPH — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, windowed GUI, Windows.
Co-validated with graduated skills (X9 gauntlet, 11/11).

## Verified facts (do not guess these)
- Author graphs with one atomic Controller.edit: CREATE_NODES +
  CONNECT + SET_VALUES (bare names resolve only in-call, R4).
- Template inputs need typed 3-tuples: (attr, v, og.Type(DOUBLE))
  for bare floats (R3); tuples/strings resolve implicitly.
- Authoring evaluates PROMPTLY: reset targets after build, gate
  authoring-effect vs tick-effect separately (R1).
- WritePrimAttribute fires on DATA flow; exec wire optional (R5).
  Connected DOUBLE chains work; connected TUPLE writes never
  configure (R2 OPEN) — drive single-double destinations.
- Recreated graph paths stay dead until re-touched: revive with a
  disconnect+reconnect of one value link at run start (R6), and
  always gate live-first (t1>0), never linked=True alone.
- Only Graph.set_disabled(True/False) truly disables (R7);
  is_disabled() asserts state. World clock runs while disabled:
  resume catches up to live time.
- One writer per target: sweep rivals before drills (R8); probes
  MUST use unique targets.

## Dataset (evidence/, replayable)
- O1 graph+tick: 5/5, reset-separation (z0a authoring vs z1 tick).
- O2 dynamic values: 4/4, s1=75.01 s2=76.01.
- O3 tick-driven motion: 4/4, dt=10.0, dq>0.05, q follows.
- O4 enable/disable: 8/8, t1=5 t2=5 frozen=0.0000 exact,
  t3=25 catch-up=20 (10 missed + 10 new), dis/en states.
- V9 exam (new scene, 4-node Mul+Add chain): 10/10, t1=3.5
  t2=3.5 t3=13.5, q1=0.0516 q3=0.2261 rad, no rivals.
- X9 cross-val: 11/11 across stage/model/sense/physics/graph/R8.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- oN_build / oN_run (N=1..4), v9_build / v9_run: authorship +
  execution; probe_*.py: live API/signature probes.
- verify_oN / verify_v9: local evaluators, exit 0 on pass.
- cross-val x9_live.py + verify_x9.py: co-validation snapshot.

## Eval
Suite: O1 O2 O3 O4 V9 (5/5 green) + X9 co-val (11/11).

## Failure catalog
See failures.md (R1-R8, R2 open).
