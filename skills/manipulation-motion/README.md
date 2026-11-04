# Skill 5 MANIPULATION & MOTION — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0 / Kit 110, PhysX engine, Windows.
Co-validated with Skills 1-4 + workspace-sense (X5 gauntlet, 10/10).

## Verified facts (do not guess these)
- Command path: tensors for READS only (q, Jacobian, poses); joints
  are COMMANDED via USD drive targets (degrees) + stop/play re-parse
  (R4). Tensor writes half-respond then freeze.
- Grasp frame: IsaacSiteAPI site at Link2 + (0,0,0.2); DLS IK on the
  site Jacobian (planar x/z rows), seeds analytic, trim-if-needed.
- Grasp attach: FixedJoint with computed frames; zero-snap frames;
  USD-stamp the live block pose BEFORE stop/release (R10).
- Limits +/-170deg + wrap against windup; settle-measure every leg
  (10 steps after every stop; R9).
- Mirror rule: mirrored pick/place branch is (q1,q2)->(-q1,-q2),
  verified bit-exact by the V5 exam.
- Physics is deterministic run-to-run on a clean stage (V5 re-ran
  bit-identical twice); any divergence means stage contamination —
  audit for stray physics-live rigs (R12).
- Cross-check snapshots must be READ-ONLY and IsValid-gated; never
  clean-slate inside a snapshot script (R11).

## Dataset (evidence/, replayable)
- M1 grasp frame: site=[0,0,2.0], target dist 0.4301, ndof 2.
- M2 diff IK: err 0.3418->0.0143, 7 iters, conv.
- M3 joint traverse: arr 0.0003, maxdev 0.0151.
- M4 pick-place: gates 0.0006/0.0011/0.0014/0.0072, zmax 1.8028,
  err_p 0.0091, pxy 0.0024, released+settled.
- V5 exam (mirror B->A): 14/14 gates, bit-identical re-run PASS.
- X5 cross-val: V5-final scene under all five lenses, 10/10.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- mN_build/mN_run, v5_build/v5a_run/v5b_run: authorship + execution.
- verify_mN/verify_v5: local evaluators, exit 0 on pass.
- cross-val x5_live.py + verify_x5.py: co-validation snapshot.

## Eval
Suite: M1 M2 M3 M4 V5 (5/5 green) + X5 co-val (10/10) at graduation.

## Failure catalog
See failures.md (R1-R12).
