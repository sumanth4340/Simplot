# Agent team state (persistent — the team never forgets)

The platform cannot idle agents between turns; this file is their
standing memory instead. Every tasking resumes from here: zero ramp-up,
full context, all 18 effectively always alive.

| Agent | State | Standing findings |
|---|---|---|
| articulation | standby | W1: wheel revolute attach verified; executor sets wheel-center frames; `{from}_to_{to}` names unique; joints need paused sim |
| rosnav | standby | Drive = articulation + drives `stiffness=0 damping=2 max_force=2`; N1 rolling-collider rule (analytic spheres ✓); +vel about Y rolls +X |
| sensors | standby | `arena_lidar` static at /World (executor can't parent to moving root — open gap); tick_rate=10; scans are writer-only, never in snapshots |
| physics | standby | Drive units are DEG/S (live-confirmed: -60 → 0.29 m/s); 2-wheel pitch rock watch; cones are true fixed colliders |
| sense/stage/modeling/manipulation/rendering/viewport/omnigraph/behavior/appsession/pyapi/deform/gpunuc/sdg/xval | standby | never tasked this run |

## Live world state (updated every leg)

- Arena spread 2026-11-04: cones cone_a(-2,0) cone_b(1,2.2) cone_c(1,-2.2), all ≥3.7 m apart; goal = green visual cuboid at (-2.2,2.4); walls unchanged.
- Car: think_cube + wheel_l/r, articulation rooted, AT GOAL (-2.11,1.95) dist 0.46 < 0.5 — REACHED 2026-11-04 (legs think_64–85, sim paused, drives zeroed).
- DWA planner: action-reasoner/nav/dwa.py, 7/7 tests green (added escape-reverses test). Fixes that won: _escape back-up recovery, traj[1:] clearance, cruise_seed, live radius 1.2, waypoint (-0.5,1.1) + latch, precision-0.7 inside 1.5 m of goal, pivot-to-face for >50° turns. Demo proof in nav/demo_proof.txt (refresh: now stale, predates escape fix).
- OPEN: intermittent drive stall (5/20+ legs: targets ack'd, ~0 motion, self-recovers; forward-only so far, reverse always moves). Cause unknown — needs code-server DOF reads (server currently down).
- Lidar: arena watch only. Avoidance loop = DWA legs via bridge until a riding scan exists.

- [tool-pass 18/18] Every pack has TOOLS.md: 223 tools / 299 live-verified limits / 293 unknowns. New files only, no pack edits.

- [mastery 18/18] Every pack has TOOLS_REF.md (deep ref) + TOOLS.md pointer. ~11.7k lines total. Cube/Sphere/Cylinder/Cone/Plane configurables in modeling T11 appendix.

- [datatype 18/18] 1384/1385 signatures typed (units+defaults+script cites). Only gap: physics png_stats (imported-unused, out-of-pack). Zero bare (...) in FUNCTIONS entries.

- [fix1] routing 50->63 entries (12 packs + sensors lane), both copies identical, 0 drill misses, 138 tests green. pyapi desc gained 'steps' vocab (regression fix).
- [fix2-offline] sys.exit on 57 verifiers (libfix in-sim skipped); s3 exits 1 on FAIL. s3_run/s3_out + drill03v1 evidence refresh BLOCKED on sim.
- [fix3-offline] +22 DRILL_TASKS (ST1/MO1/PH1/AR1/SE1), handled_undrilled 37->0, finetune 84->150 traces, coverage rebuilt. Live plan-execution check BLOCKED on sim.

- [live-evidence] drill03v1 DRILL03-PASS (deterministic legs + pause/settle freeze + truth-shaped prelude); S3-PASS 9/9 (clean stage + 120-step warmup). Game stage restored 16/16, car pose exact. Backup: C:/tmp/live_game_backup.usd.
- [live-traces] velocity handler FIXED (tensors-after-play, was CreateVelocityAttr AttributeError), verified 5/5 live. Rewrote PH1/AR1/MO1 traces self-sufficient; live 26/28 (velocity_limit lacks maxJointVelocity in this PhysX build - honest handler FAIL). Suite 159 green, handled_undrilled=0.
- [flag] ANOTHER session is editing concurrently (dispatcher.py, guided regex, trace_schema, thinker.py 18:58, dwa.py). My gates green as of 19:10; shared thinker.py - coordinate.
