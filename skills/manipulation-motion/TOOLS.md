# Manipulation-Motion Tool Knowledge (2026-11-04)

> Full mastery reference: [TOOLS_REF.md](TOOLS_REF.md) — 15 tools, 82 functions, 40 knobs, 27 limits, 19 unknowns (every claim tagged verified/probable/theoretical).

Pack: `action-reasoner/skills/manipulation-motion/` (Graduated Skill 5: arm
manipulation — grasp frames, DLS differential IK, joint-space motion,
FixedJoint grasp, object-pose-validated pick-and-place).

## Tools

### pxr UsdGeom (in-sim stage authoring)
- DOES: Defines geometry prims (cubes, planes, Xforms) and transform ops.
- FUNCTIONS USED:
  - `UsdGeom.Cube.Define(stage, path)` + `GetSizeAttr().Set(size)` (links, block, shelves, target)
  - `UsdGeom.Plane.Define` + width/length attrs (grounds)
  - `UsdGeom.Xform.Define` (bot root, GraspSite)
  - `UsdGeom.Xformable(...).AddTranslateOp/Set`, `AddScaleOp`, `AddOrientOp`, `GetOrderedXformOps` (pose authoring + USD-stamp release)
- LIMITS-live-verified:
  - Never scale articulation links: scale ops distort joint anchors + child frames (R1; fix: size via `GetSizeAttr`). (Scale IS used on static shelf cubes — non-articulated only.)
- UNKNOWN: Non-cube/plane geom types; orient ops on links during motion.

### pxr UsdPhysics (in-sim physics authoring)
- DOES: Authors physics scene, bodies, joints, limits, drives, grasp joints.
- FUNCTIONS USED:
  - `UsdPhysics.Scene.Define` + gravity direction/magnitude attrs
  - `RigidBodyAPI.Apply`, `CollisionAPI.Apply`, `MassAPI.Apply().GetMassAttr().Set`
  - `ArticulationRootAPI.Apply` (root link)
  - `RevoluteJoint.Define` + Body0/Body1 rels, LocalPos/Rot attrs, axis token `UsdPhysics.Tokens.y`, `CreateLower/UpperLimitAttr` (+/-170)
  - `DriveAPI.Apply(joint, "angular")` + type/stiffness/damping/maxForce/targetPosition attrs (force drives, gains 100000/10000)
  - `FixedJoint.Define` + body rels + local frames (root fixing, M4 grasp attach, computed frames m4a_run.py)
  - Raw attr path `drive:angular:physics:targetPosition` via `GetAttribute(...).Set(deg)` — THE verified command path (re-play)
- LIMITS-live-verified:
  - Goal markers must be visual-only: a CollisionAPI target cube parked the arm ON the marker at q1=+0.29 (R7).
  - Out-of-range `dof_indices` writes CRASH Kit natively with no error (R6 probe 8); print buffer shapes first.
  - `HasAPI()`/attr reads on invalid prims throw instead of returning False — gate every touch with `IsValid` (R11).
- UNKNOWN: Prismatic/other joint types; non-y hinge axes in manipulation drills; drive types other than "force".

### pxr PhysxSchema (in-sim articulation tuning)
- DOES: Tunes PhysX articulation solver/sleep behavior on the root.
- FUNCTIONS USED:
  - `PhysxArticulationAPI.Apply` + `CreateSleepThresholdAttr().Set(0.0)`, solver position iterations 32, velocity 1, `CreateEnabledSelfCollisionsAttr().Set(False)`
- LIMITS-live-verified:
  - Flush-stacked pitch links self-collide and lock (~9 deg) — clearance by construction instead (0.2 cubes/0.2 gaps clear +/-63 deg, R5).
- UNKNOWN: Other solver iteration counts; Newton-backend equivalents.

### pxr Gf (math types)
- DOES: Vector/quaternion values for USD attrs and frame math.
- FUNCTIONS USED:
  - `Gf.Vec3f/Vec3d`, `Gf.Quatf`, `GetInverse().Transform`, quat multiply (`qw.GetInverse() * bq` for grasp frames)
- LIMITS-live-verified: none (pure math; verified via bit-identical V5 re-run).
- UNKNOWN: none material.

### omni.usd (in-sim stage access)
- DOES: Gets the live stage; prim lookup for attr writes and removal.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`, `stage.GetPrimAtPath`, `stage.RemovePrim`
- LIMITS-live-verified:
  - Builds must remove ALL prior drill prims (`/World/{M1,M2,M3,M4,Y}*` + PhysicsScene) or co-located live bots collide (R8); removal lists must also name every experimental prefix ever built (R12: stray M4V2 rig silently corrupted V5).
  - Cross-check snapshots must be READ-ONLY: delete-before-build + crash gutted the live stage (R11).
- UNKNOWN: none material.

### omni.timeline (in-sim timeline control)
- DOES: Resets playhead between run-script legs.
- FUNCTIONS USED:
  - `omni.timeline.get_timeline_interface()`, `tl.set_current_time(0.0)`, `tl.pause()`
- LIMITS-live-verified:
  - Every run script resets the timeline before play; rebuild-while-paused leaves stale tensors (R3).
- UNKNOWN: Scrub/step APIs beyond play/pause/reset.

### isaacsim.core.experimental.utils.app (app_utils, in-sim transport)
- DOES: Timeline play/stop + async stepping — the core of re-play commanding.
- FUNCTIONS USED:
  - `app_utils.play()`, `app_utils.stop()`, `await app_utils.update_app_async(steps=N)`
- LIMITS-live-verified:
  - Rapid stop/play races kill re-parse: 10 settle steps after EVERY stop; settle+measure per leg (R9).
  - Sub-0.01 target deltas parse as no-change — never blind micro-step loops (R9).
  - `stop()` reverts joint-carried bodies to USD-authored pose — USD-stamp live pose before release (R10).
- UNKNOWN: Step-size/dt control; behavior under Newton backend.

### isaacsim.core.experimental.prims.Articulation (in-sim tensor reads)
- DOES: Live articulation state reads (q, Jacobian). READS ONLY.
- FUNCTIONS USED:
  - `Articulation(root_path)` (fresh handle after every re-play), `get_dof_positions()`, `get_jacobian_matrices()`
  - Jacobian slicing: `Jn[0, 2, 0:3, 6:8]` linear / `Jn[0, 2, 3:6, 6:8]` angular for Link2 of 2-DOF arm; site Jacobian via skew-symmetric `Js = Jl - S @ Ja`, planar x/z rows
- LIMITS-live-verified:
  - Tensor WRITES (`set_dof_position_targets`, indexed AND full-row) half-respond then freeze; efforts ignored; qd bit-zero (R4). Command ONLY via USD drive targets + stop/play re-parse.
  - `get_dof_positions()` asserts tensor-entity-invalid after rebuild-while-paused (R3): stop + settle, then play, then construct handle.
- UNKNOWN: `set_dof_position_targets` under Newton; velocity/effort tensor reads in this pack (qd only via finite-difference speed check in m4b).

### isaacsim.core.experimental.prims.RigidPrim (in-sim body reads)
- DOES: Live world-pose reads for links and the grasped block.
- FUNCTIONS USED:
  - `RigidPrim(path)`, `get_world_poses()` (link pose for site computation, block pose for gates)
- LIMITS-live-verified: none (read path; site = link pose + quat-rotated offset verified by gates).
- UNKNOWN: Velocity reads via API (pack uses finite-difference instead).

### isaacsim.core.experimental.utils.xform (xform_utils, USD pose reads)
- DOES: USD-level world pose reads at stop (seeds, not live state).
- FUNCTIONS USED:
  - `xform_utils.get_world_pose(path)` (m1/m2 site reads; `_seed_ik` shoulder read in m4a)
- LIMITS-live-verified:
  - USD reads are stop-time only; ALL live reads go via tensors (m4a docstring; physics-master tensor-read rule).
- UNKNOWN: none material.

### IsaacSiteAPI (grasp frame marker)
- DOES: Marks the grasp site Xform on Link2.
- FUNCTIONS USED:
  - `prim.ApplyAPI("IsaacSiteAPI")` on `Link2/GraspSite` at +0.2 z offset (site itself tracked via tensor math, not API reads)
- LIMITS-live-verified: none.
- UNKNOWN: Whether any Isaac API consumes the site marker (pack only needs it as authored frame).

### warp (in-sim array interop)
- DOES: GPU array type returned by tensor APIs; must convert before numpy use.
- FUNCTIONS USED:
  - `warp as wp`, `isinstance(a, wp.array)` → `a.numpy()` (`_vec`/`_w` helpers)
- LIMITS-live-verified:
  - `np.asarray(wp_array)` and `arr[0]` raise RuntimeError once tensors are live (R2).
- UNKNOWN: none material.

### numpy (in-sim IK math)
- DOES: DLS inverse kinematics, frame math, error norms.
- FUNCTIONS USED:
  - `np.linalg.inv(Jp @ Jp.T + LAM^2 I) @ ep` (2x2 planar DLS, LAM=0.1), `np.clip` (MAXDQ 0.1-0.12), `np.linalg.norm`, `np.cross` (quat rotate, skew matrix)
- LIMITS-live-verified:
  - Analytic seed (sub-mm) + trim-only-if-needed; larger steps beat micro-steps (R9).
  - Mirror rule: mirrored pick/place branch is (q1,q2)->(-q1,-q2), bit-exact (README).
- UNKNOWN: 6-DOF/full-pose IK (pack is planar x/z only); obstacle-aware binding.

### isaacsim_send.py bridge (host → sim transport)
- DOES: Sends each mN/v5 script into the live sim; evidence JSONs are its result envelopes.
- FUNCTIONS USED:
  - Per README: all build/run scripts execute in-sim via the bridge; `evidence/*.json` capture status/output.
- LIMITS-live-verified: none in this pack's failures.md.
- UNKNOWN: Bridge CLI flags/retry semantics (owned by another pack).

### verify_mN / verify_v5 (local evaluators)
- DOES: Locally parse evidence JSON REPORT lines and gate pass/fail; exit 0 on pass.
- FUNCTIONS USED:
  - stdlib `json` (utf-8-sig/utf-16/utf-8 fallback loads), `re` (REPORT regex), `sys.exit`
  - Gates: M2 err<2cm; M3 arr<0.01/maxdev<0.05; M4 grasp g0b<0.02, lift zmax>1.0, place pxy<0.05/pz<0.03/spd<0.05, attached+released; V5 14/14 gates
- LIMITS-live-verified: none (pure local checks).
- UNKNOWN: none material.

## Unverified

- Tensor WRITES (`set_dof_position_targets`, efforts): proven UNRELIABLE on PhysX here (R4) — no verified write path via tensors exists; Newton-backend behavior unknown.
- 6-DOF / orientation-including IK: pack is planar 2-DOF x/z only; full-pose DLS not drill-proven.
- Obstacle-aware motion / world binding (motion-generation source): cited in discovery.md, never drilled.
- Velocity/effort live reads via tensor API: pack uses finite-difference speed; direct reads not drill-proven.
- Drive types other than force, axes other than y-hinge, joint types other than revolute/fixed: not drilled.
- Grasping anything other than FixedJoint attach on a cube: suction/friction grasps not drilled.
- Bridge CLI details of isaacsim_send.py: used but not documented in this pack.
- x5_live.py + verify_x5.py cross-val snapshot: cited in README but live in another pack (not in scripts/).

## Sources-read

- `action-reasoner/skills/manipulation-motion/README.md` (FULL — no SKILL.md exists)
- `action-reasoner/skills/manipulation-motion/failures.md` (FULL, R1-R12)
- `action-reasoner/skills/manipulation-motion/discovery.md` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m2_build.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m2_run.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m4_build.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m4a_run.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m4b_run.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/m3_run.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/v5_build.py` (FULL)
- `action-reasoner/skills/manipulation-motion/scripts/verify_m4.py` (FULL)
- SKIMMED (name + imports only): m1_build.py, m1_run.py, m3_build.py, v5a_run.py, v5b_run.py, verify_m1.py, verify_m2.py, verify_m3.py, verify_v5.py
- `action-reasoner/skills/manipulation-motion/evidence/` (directory listing only, 11 JSON files)
