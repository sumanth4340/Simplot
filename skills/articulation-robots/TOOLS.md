# Articulation-Robots Tool Knowledge (2026-11-04)

> Exhaustive reference: TOOLS_REF.md — 11 tools, 81 functions, 30 knobs, 30 EKB rules, 30 limits, 22 unknowns (all 14 scripts read in full).

## Tools

### pxr.UsdPhysics — physics/USD joint + articulation authoring
- DOES: Authors scenes, rigid bodies, joints, drives, and articulation roots in USD.
- FUNCTIONS USED:
  - `UsdPhysics.Scene.Define` + `CreateGravityDirectionAttr` / `CreateGravityMagnitudeAttr`
  - `UsdPhysics.RigidBodyAPI.Apply`, `UsdPhysics.CollisionAPI.Apply`, `UsdPhysics.MassAPI.Apply` + `GetMassAttr().Set`
  - `UsdPhysics.ArticulationRootAPI.Apply`
  - `UsdPhysics.FixedJoint.Define`, `UsdPhysics.RevoluteJoint.Define`
  - Joint `GetBody0Rel` / `GetBody1Rel` + `AddTarget`, `GetLocalPos0Attr` / `GetLocalRot0Attr` / `GetLocalPos1Attr` / `GetLocalRot1Attr` + `Set`, `GetAxisAttr().Set(UsdPhysics.Tokens.z)`
  - `UsdPhysics.DriveAPI.Apply(prim, "angular")` + `CreateTypeAttr` ("force"), `CreateStiffnessAttr`, `CreateDampingAttr`, `CreateMaxForceAttr`, `CreateTargetPositionAttr`
- LIMITS-live-verified:
  - ArticulationRootAPI must sit on the DYNAMIC base link, anchored by a FixedJoint to the (non-rigid) robot root; root-on-Xform + static base yields ndof=0 (failures.md R1).
  - Angular drive `TargetPosition` is in DEGREES while DOF readback is in RADIANS (90deg->pi/2 exact, 45deg->pi/4 exact; README verified facts; evidence/a3_run.json, evidence/v4_run.json).
  - No articulation root needed for attach-only joints; add root before drives or DOF readback (failures.md W1).
- UNKNOWN:
  - Non-force drive types, linear drives, and joints other than revolute/fixed (prismatic, spherical, D6) — never drilled.

### pxr.UsdGeom — geometry + xform authoring
- DOES: Authors link geometry, robot-root Xforms, ground planes, and translate ops.
- FUNCTIONS USED:
  - `UsdGeom.Xform.Define`, `UsdGeom.Cube.Define` + `GetSizeAttr().Set`
  - `UsdGeom.Plane.Define` + `CreateWidthAttr` / `CreateLengthAttr`
  - `UsdGeom.Xformable(prim).AddTranslateOp().Set`
- LIMITS-live-verified: (none cited — plain geometry authoring, no pack failure entries)
- UNKNOWN:
  - Mesh/capsule/sphere link geometry inside articulations — drills use cubes only.

### pxr.Gf — math value types
- DOES: Provides vector/quaternion values for physics and xform attributes.
- FUNCTIONS USED:
  - `Gf.Vec3f`, `Gf.Vec3d`, `Gf.Quatf(1.0)` (identity joint frames)
- LIMITS-live-verified: (none cited)
- UNKNOWN: (none — trivial value types)

### omni.usd — stage access + prim management
- DOES: Opens the live stage and creates/removes/looks-up prims.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`
  - `stage.GetPrimAtPath`, `stage.DefinePrim`, `stage.RemovePrim`, `prim.IsValid()`
  - `prim.GetReferences().AddReference` (V4 references the M2 URDF .usda package)
  - `prim.ApplyAPI`, `prim.HasAPI`, `prim.CreateAttribute`, `prim.GetAttribute().Get()`, `prim.GetRelationship(...).GetTargets()`
- LIMITS-live-verified:
  - Referenced (imported) joints accept authored DriveAPI overs cleanly and arrive at target (README verified facts; evidence/v4_run.json).
- UNKNOWN:
  - Payload-based (vs reference-based) composition of robot packages — never drilled.

### omni.timeline — sim clock + pause control
- DOES: Reads sim time and pauses the timeline after a run leg.
- FUNCTIONS USED:
  - `omni.timeline.get_timeline_interface()`, `get_current_time()`, `pause()`
- LIMITS-live-verified: (none cited)
- UNKNOWN:
  - `play()` via the timeline interface itself — drills play via app_utils instead.

### isaacsim.core.experimental.prims.Articulation — live DOF state
- DOES: Reads live articulation DOF positions after play.
- FUNCTIONS USED:
  - `Articulation(root_link_path)`, `get_dof_positions().numpy()`, `dof_names` (README documents; a1/a2 run scripts construct it on the root link)
- LIMITS-live-verified:
  - Tensors need play; USD parses need the root API (README verified facts).
  - q0 reads slip under active drives — assert travel + arrival, not q0~=0 (README verified facts, physics F5).
  - Rest q reads ~1e-8 on undriven vertical-axis chains (evidence/a1_run.json, evidence/a2_run.json).
- UNKNOWN:
  - `get_dof_velocities` and any velocity readback — discovery goal names it but no drill evidence captures it.
  - DOF writes / effort interfaces through this class — never drilled.

### isaacsim.core.experimental.utils.app — play + stepping
- DOES: Starts play and advances the app a fixed step count inside async in-sim scripts.
- FUNCTIONS USED:
  - `app_utils.play()`, `await app_utils.update_app_async(steps=120)`
- LIMITS-live-verified: (none cited beyond the 120-step settle legs used in A3/V4 evidence)
- UNKNOWN:
  - Other step counts / stop behavior — drills always use 120 steps then `timeline.pause()`.

### usd.schema.isaac.robot_schema — robot schema overlay + validation
- DOES: Applies the Isaac robot/link/joint/site schema overlay and validates populated relations.
- FUNCTIONS USED:
  - `Classes.ROBOT_API.value`, `Classes.SITE_API.value` via `prim.ApplyAPI`
  - `Attributes.ROBOT_TYPE.value` (name/type tuple) for the type attribute; set to "Manipulator", read back on imported arm as "Default"
  - `Relations.ROBOT_LINKS` / `Relations.ROBOT_JOINTS` relationship targets
  - `usd.schema.isaac.robot_schema.utils.PopulateRobotSchemaFromArticulation(stage, robot, base_link)`
  - `usd.schema.isaac.robot_schema.utils.ValidateRobotSchemaRelationships(robot)`
- LIMITS-live-verified:
  - `PopulateRobotSchemaFromArticulation` + `ValidateRobotSchemaRelationships` live in the `.utils` submodule, NOT the package root; Populate applies Link/Joint APIs itself (README verified facts; verify_a4 asserts links Base/Link1/Link2 + joints Hinge1/Hinge2, 0 invalid).
- UNKNOWN:
  - Robot types other than Manipulator/Default; SiteAPI use beyond apply; schema behavior on multi-arm (multi-root-anchored) assemblies — never drilled.

### isaacsim_send.py bridge — in-sim execution transport
- DOES: Ships the aN_build/aN_run/a4_schema/v4 scripts into the live Isaac Sim process and returns JSON evidence.
- FUNCTIONS USED:
  - (transport only; pack README notes all authorship/execution scripts run in-sim via this bridge)
- LIMITS-live-verified: (none cited in this pack)
- UNKNOWN:
  - Bridge CLI flags/error envelope — owned by another pack, not documented here.

### Local verify harness (stdlib json/re/sys/math) — evidence evaluators
- DOES: Parses evidence/*.json report lines locally and exits 0 on pass.
- FUNCTIONS USED:
  - `json.load` with multi-encoding fallback (`utf-8-sig`, `utf-16`, `utf-8`)
  - `re.search` on `A4-REPORT`/`A3-REPORT`-style lines; `math` pi comparisons; `sys.exit(main())`
- LIMITS-live-verified: (none cited — pure local parsing)
- UNKNOWN: (none — fully visible in-script)

### Executor joint actions (create.objects.sphere / joint.create.joint) — attach-only wheels
- DOES: Attaches wheels to a dynamic cube via revolute joints without hand USD.
- FUNCTIONS USED:
  - `create.objects.sphere` wheels + `joint.create.joint` revolute each, `axis=Y` for X-rolling wheels on +/-Y cube faces
- LIMITS-live-verified:
  - Sim must be paused (`_need_paused`); both sides must be dynamic rigid; wheels need a small lateral gap from the cube face (0.05 used); executor sets wheel-center frames itself so no snap on play; auto-names `{from}_to_{to}` unique per wheel (failures.md W1).
- UNKNOWN:
  - Driving those executor-created wheel joints (root + drives on top) — attach verified, drive not.

## Unverified

- DOF velocity readback (`get_dof_velocities`) — discovery goal, zero drill evidence.
- Multi-arm assembly via FixedJoint under a single root — discovery goal 5, never drilled.
- Grippers — in discovery scope, never drilled.
- Prismatic / spherical / D6 joints and linear drives — never drilled.
- Drive types other than "force" — never drilled.
- Executor-created wheel joints driven under an articulation root — attach-only verified (W1), drive step open.
- Payload-based robot composition — only references drilled.
- `omni.timeline` play path — drills play via app_utils only.

## Sources-read

- action-reasoner/skills/articulation-robots/README.md (full)
- action-reasoner/skills/articulation-robots/failures.md (full)
- action-reasoner/skills/articulation-robots/discovery.md (full)
- action-reasoner/skills/articulation-robots/scripts/a1_build.py (full)
- action-reasoner/skills/articulation-robots/scripts/a2_build.py (full)
- action-reasoner/skills/articulation-robots/scripts/a3_build.py (full)
- action-reasoner/skills/articulation-robots/scripts/a4_schema.py (full)
- action-reasoner/skills/articulation-robots/scripts/v4_build.py (full)
- action-reasoner/skills/articulation-robots/scripts/v4_run.py (full)
- action-reasoner/skills/articulation-robots/scripts/a3_run.py (full)
- action-reasoner/skills/articulation-robots/scripts/verify_a4.py (full)
- Skimmed by name + imports only: scripts/a1_run.py, scripts/a2_run.py, scripts/verify_a1.py, scripts/verify_a2.py, scripts/verify_a3.py, scripts/verify_v4.py
