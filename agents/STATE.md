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
- CAPTURE 2026-11-04: stage cleared for vision capture AFTER saving DWA scene to C:/isaacsim/stages/dwa_final.usd. World now = GroundPlane + 4 walls + PhysicsScene + materials, sim paused, gravity -9.81. vis16-20 captured ok. Backend needed one scene.open rebind (see memory).

- [tool-pass 18/18] Every pack has TOOLS.md: 223 tools / 299 live-verified limits / 293 unknowns. New files only, no pack edits.

- [mastery 18/18] Every pack has TOOLS_REF.md (deep ref) + TOOLS.md pointer. ~11.7k lines total. Cube/Sphere/Cylinder/Cone/Plane configurables in modeling T11 appendix.

- [datatype 18/18] 1384/1385 signatures typed (units+defaults+script cites). Only gap: physics png_stats (imported-unused, out-of-pack). Zero bare (...) in FUNCTIONS entries.

- [fix1] routing 50->63 entries (12 packs + sensors lane), both copies identical, 0 drill misses, 138 tests green. pyapi desc gained 'steps' vocab (regression fix).
- [fix2-offline] sys.exit on 57 verifiers (libfix in-sim skipped); s3 exits 1 on FAIL. s3_run/s3_out + drill03v1 evidence refresh BLOCKED on sim.
- [fix3-offline] +22 DRILL_TASKS (ST1/MO1/PH1/AR1/SE1), handled_undrilled 37->0, finetune 84->150 traces, coverage rebuilt. Live plan-execution check BLOCKED on sim.

- [live-evidence] drill03v1 DRILL03-PASS (deterministic legs + pause/settle freeze + truth-shaped prelude); S3-PASS 9/9 (clean stage + 120-step warmup). Game stage restored 16/16, car pose exact. Backup: C:/tmp/live_game_backup.usd.
- [live-traces] velocity handler FIXED (tensors-after-play, was CreateVelocityAttr AttributeError), verified 5/5 live. Rewrote PH1/AR1/MO1 traces self-sufficient; live 26/28 (velocity_limit lacks maxJointVelocity in this PhysX build - honest handler FAIL). Suite 159 green, handled_undrilled=0.
- [flag] ANOTHER session is editing concurrently (dispatcher.py, guided regex, trace_schema, thinker.py 18:58, dwa.py). My gates green as of 19:10; shared thinker.py - coordinate.
- [DWA-carryover] lead session owns live sim from 20:47: backup capture stage, open dwa_final.usd, instrumented DWA drive (proof+stall), lidar reparent test, velocity_limit fix. Capture stage restored after.
- [sim-crash 21:25 IST] Kit died (carb crashreporter gpu.foundation frames, 5.5h uptime). No bridge activity since 20:57. Lead restarting sim for carryover work.
- [sim-crash2 21:40 IST] rep.orchestrator.step_async() with RTX lidar sensor crashed Kit (carb frames). Writer/orchestrator GMO path ABANDONED (2 crashes); N2 ROS-Helper path is the stable alternative. Restarting.
- [DWA-carryover 21:5x] PROOF REFRESHED (nav/demo_proof.txt, 42 legs, GOAL at (-1.85,2.09) d=0.47, min_clear 0.84): fixes in nav/dwa.py - _pivot fallback (cruise_seed excluded v=0), TRUE wall bounds (old sat 0.7m inside real walls), wheel v-sign RECALIBRATED (+joints=nose-fwd; old map drove backward), mission_step waypoint latch + precision-0.7 final leg, tensor continuous drive (no pause shocks). Row0-yaw law: yaw=atan2(m[0][1],m[0][0]). 10/10 dwa tests.
- [stall] DIAGNOSED: 2-wheel pitch instability -> nose plants (tilt 11deg, front edge z=0) -> drag stall. Forward-only (fwd pitches nose-down, reverse levels it: tilt 11->2deg live). Recovery = reverse-unstick. Caster wheel = physical fix (proposed, not built).
- [velocity_limit] FIXED: software clamp in handlers (limit rad/s recorded per root, joint_drive targets clamped deg/s). 2 offline tests + live verified (120 -> 28.6 deg/s at 0.5 rad/s limit). 13/13 reflex.
- [lidar] root mount OK (prim+schemas+graph+/scan_ride advertised) but 0 frames: GMO writer path NEVER fires in Kit; orchestrator.step_async CRASHED Kit (2nd crash today, writer path ABANDONED). Suspect zombie render product (recreated lidar reused Replicator path); fresh ride2 mount testing now. N2 ROS pattern replicated.
- [sim-crash3 22:00 IST] rtx.sensors.lidar.core.plugin.dll crashed during sensor render init (RIDE2 graph). Riding-lidar CARRYOVER BLOCKED: RTX sensor rendering crashes this box (3x); mount+graph recipe proven, frames never render. Writer/orchestrator/GMO paths all implicated. Needs driver/shader/GPU investigation. DWA stays on synth_scan. Restarting to restore capture stage.
- [sim-window] Lead session DONE with live sim: capture stage restored from C:/tmp/capture_stage_backup.usd. Sim released.
