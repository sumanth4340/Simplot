# Manipulation-Motion TOOLS_REF (exhaustive, 2026-11-04)

Datatype pass (2026-11-04): 82/82 signatures typed, 40/40
knobs typed, 0 bare params, 3 still-unknown ([theoretical]:
set_dof_position_targets signature, bridge CLI, Physx sleep
unit). Types grounded to script:line call sites; unobserved
names/defaults marked [probable]/[theoretical].

Pack: `action-reasoner/skills/manipulation-motion/`. Companion to
[TOOLS.md](TOOLS.md). Every claim tagged
[verified]=live-drilled in this pack, [probable]=strong in-pack
evidence but not isolated, [theoretical]=untested inference.
No SKILL.md exists; the pack doc is README.md [verified].

Sources FULLY read: README.md, failures.md (R1-R12), discovery.md,
TOOLS.md, all 17 scripts (m1_build, m1_run, m2_build, m2_run,
m3_build, m3_run, m4_build, m4a_run, m4b_run, v5_build, v5a_run,
v5b_run, verify_m1, verify_m2, verify_m3, verify_m4, verify_v5);
evidence/ directory listing (11 JSONs) [verified].

Conventions: signatures below are the AS-USED observed form
[verified]; full upstream overloads/defaults are [theoretical]
unless a script observes them. Degrees vs radians: USD drive
targets are DEGREES, tensor reads are RADIANS [verified].

## 1. pxr UsdGeom (in-sim stage authoring)

- DOES: Defines all geometry prims (cubes, planes, Xforms) and all
  transform ops (translate/scale/orient) for bots, grounds, shelves,
  targets, block, GraspSite [verified].
- FUNCTIONS (typed; `stage` = live Usd.Stage from
  omni.usd.get_context().get_stage(), no default [verified]):
  - `UsdGeom.Cube.Define(stage: Usd.Stage, path: str)`
    `-> UsdGeom.Cube` [verified; type names probable].
    Calls: m1_build.py:27,71; m2_build.py:33,81;
    m3_build.py:32,80; m4_build.py:36,89,99;
    v5_build.py:37,90,100. path: Sdf.Path-compatible
    str, no default. Upstream overloads [theoretical].
  - `cube.GetSizeAttr() -> UsdAttribute;`
    `.Set(size: float) -> None` [verified]. size: uniform
    edge length, METERS, no default (required). Observed
    1.0/0.6/0.4/0.3?/0.2/0.15/0.12/0.1
    (m1_build.py:28,72; m4_build.py:90,100).
  - `UsdGeom.Plane.Define(stage: Usd.Stage, path: str)`
    `-> UsdGeom.Plane` [verified; type names probable].
    Calls: m1_build.py:19; m2_build.py:25; m3_build.py:24;
    m4_build.py:28; v5_build.py:29. path: str, no default.
  - `plane.CreateWidthAttr() -> UsdAttribute;`
    `.Set(w: float) -> None`, same for `CreateLengthAttr`
    `.Set(l: float)` [verified]. w/l: METERS, no default;
    observed 20.0/20.0 (m1_build.py:20-21;
    m2_build.py:26-27; m3_build.py:25-26; m4_build.py:29-30;
    v5_build.py:30-31). Upstream Create*Attr(default,
    sparsely) args [theoretical].
  - `UsdGeom.Xform.Define(stage: Usd.Stage, path: str)`
    `-> UsdGeom.Xform` [verified; type names probable].
    Bot roots + GraspSite (m1_build.py:23,68;
    m4_build.py:32,83).
  - `UsdGeom.Xformable(prim: Usd.Prim)`
    `-> UsdGeom.Xformable [probable]` [verified]. prim:
    raw prim from GetPrim()/GetPrimAtPath(), no default
    (m1_build.py:29; m4b_run.py:148).
  - `x.AddTranslateOp() -> UsdGeom.XformOp;`
    `.Set(v: Gf.Vec3d) -> None` [verified]. v: METERS
    (x,y,z) float64, no default (m1_build.py:30;
    m4_build.py:38,92,101-102). Suffix/precision args
    [theoretical].
  - `xp.AddScaleOp() -> UsdGeom.XformOp;`
    `.Set(v: Gf.Vec3f) -> None` [verified]. v:
    dimensionless float32 scale factors, no default;
    ONLY observed value (0.2,0.2,0.3) on static shelves
    (m4_build.py:93; v5_build.py:94).
  - `xp.AddOrientOp() -> UsdGeom.XformOp;`
    `.Set(q: Gf.Quatf) -> None` [verified]. q: (w,x,y,z)
    float32 unitless normalized quat, no default; stamp
    path only when no orient op exists (m4b_run.py:164-165;
    v5b_run.py:164-165).
  - `xp.GetOrderedXformOps()`
    `-> list[UsdGeom.XformOp] [probable]` [verified]. No
    params; iterate ops to find translate/orient for
    stamping (m4b_run.py:150; v5b_run.py:150).
  - `op.GetOpType() -> UsdGeom.XformOp.Type [probable]`
    [verified]. No params; compared against
    `UsdGeom.XformOp.TypeTranslate` / `.TypeOrient` enum
    members [probable] (m4b_run.py:151,155).
  - `op.Set(value: Gf.Vec3d | Gf.Quatf) -> None [probable
    overload]` [verified]. Vec3d METERS on translate ops
    (m4b_run.py:152-153), Quatf (w,x,y,z) on orient ops
    (m4b_run.py:156-157). No default.
- KNOBS (typed):
  - `size` (link cubes: float METERS edge, required): 0.2
    w/ 0.2 gaps clears +/-63 deg (M2v4); 0.6/0.4 flush
    LOCKS at ~9 deg pitch (R5). Bigger link + flush
    stack -> MORE self-collision, not more reach
    [verified].
  - `size` (root/base: float METERS edge, required): 1.0
    (M1-M3) vs 0.15 floating (M4/V5); smaller root +
    fixed joint at z=0.825 gives +/-170 deg shoulder
    clearance [verified].
  - Plane width/length (float METERS each, required):
    20.0; floor extent; smaller risks falling off the
    world edge [probable].
  - Shelf scale (Gf.Vec3f dimensionless, required):
    observed (0.2,0.2,0.3) on unit cube = 0.2x0.2x0.3
    pedestal, top at z=0.3; taller shelves (M4v1 1.64)
    BLOCK both IK branches (m4_build docstring)
    [verified].
  - GraspSite offset (Gf.Vec3d METERS translate,
    required): +0.2 z (M1/M4/V5), +0.1 z (M2/M3); must
    match SITE_OFF (np.ndarray float64 METERS shape (3,))
    in the paired run script or IK tracks a phantom
    point [verified].
- EKB RULES:
  - IF prim is an articulation link THEN size ONLY via
    GetSizeAttr, never AddScaleOp, BECAUSE joint local-pos
    and child offsets resolve in the SCALED frame (R1:
    tip read z=1.52 not 2.0) [verified].
  - IF prim is static (shelf) THEN scale ops are allowed,
    BECAUSE no joint anchors live under it (m4_build) [verified].
  - IF stamping a release pose THEN reuse existing ops when
    found and Add*Op only when missing, BECAUSE duplicate
    translate ops compose and double-offset (m4b found_t/
    found_o logic) [probable].
- LIMITS:
  - Scale on links distorts anchors + child frames (R1) —
    failures.md R1, m1_build v1 history [verified].
  - Only Cube/Plane/Xform drilled; spheres/capsules/meshes
    unproven here — discovery.md scope is cubes [verified].
- UNKNOWN:
  - Orient ops on links during motion: effect on joint
    frames untested [theoretical].
  - Non-uniform GetSizeAttr (cubes are uniform by schema)
    [theoretical].

## 2. pxr UsdPhysics (in-sim physics authoring)

- DOES: Authors the physics scene, rigid bodies, collisions,
  masses, articulation roots, revolute hinges + force drives,
  joint limits, root-fixing and grasp FixedJoints; raw
  `drive:angular:physics:targetPosition` attr is THE verified
  command path [verified].
- FUNCTIONS (typed):
  - `UsdPhysics.Scene.Define(stage: Usd.Stage, path: str)`
    `-> UsdPhysics.Scene [probable]` [verified]. Calls:
    m1_build.py:16; m2_build.py:22; m3_build.py:21;
    m4_build.py:25; v5_build.py:26. path: always
    "/World/PhysicsScene" here, no default.
  - `scene.CreateGravityDirectionAttr() -> UsdAttribute;`
    `.Set(d: Gf.Vec3f) -> None` [verified]. d:
    dimensionless unit vector float32, no default;
    observed (0,0,-1) (m1_build.py:17; m2_build.py:23;
    m3_build.py:22; m4_build.py:26; v5_build.py:27).
  - `scene.CreateGravityMagnitudeAttr() -> UsdAttribute;`
    `.Set(g: float) -> None` [verified]. g: M/S^2, no
    default; observed 9.81 (m1_build.py:18;
    m2_build.py:24; m3_build.py:23; m4_build.py:27;
    v5_build.py:28).
  - `UsdPhysics.RigidBodyAPI.Apply(prim: Usd.Prim)`
    `-> UsdPhysics.RigidBodyAPI [probable]` [verified].
    prim: link/root/block prim, no default; links,
    roots, grasp block (m1_build.py:31; m4_build.py:39,
    103).
  - `UsdPhysics.CollisionAPI.Apply(prim: Usd.Prim)`
    `-> UsdPhysics.CollisionAPI [probable]` [verified].
    Links, grounds, pedestals, task block; NEVER goal
    markers (R7) (m1_build.py:22,32,75; m4_build.py:94).
  - `UsdPhysics.MassAPI.Apply(prim: Usd.Prim)`
    `-> UsdPhysics.MassAPI [probable]; .GetMassAttr()`
    `-> UsdAttribute; .Set(m: float) -> None` [verified].
    m: KILOGRAMS, no default; observed 2.0 root, 1.0
    Link1, 0.5 Link2, 0.3/0.5 block (m1_build.py:33;
    m4_build.py:41,105).
  - `UsdPhysics.ArticulationRootAPI.Apply(prim: Usd.Prim)`
    `-> ArticulationRootAPI [probable]` [verified].
    Exactly one per arm, on the root link (Base/Root)
    (m1_build.py:35; m2_build.py:40; m4_build.py:43).
  - `UsdPhysics.RevoluteJoint.Define(stage: Usd.Stage,`
    `path: str) -> UsdPhysics.RevoluteJoint [probable]`
    [verified] (m1_build.py:40; m2_build.py:50;
    m3_build.py:49; m4_build.py:53; v5_build.py:54).
  - `joint.GetBody0Rel() -> UsdRelationship [probable];`
    `.AddTarget(path: str) -> None`, same for
    `GetBody1Rel` [verified]. Hinge topology parent ->
    child link paths, no default (m1_build.py:41-42;
    m4_build.py:54-55).
  - `joint.GetLocalPos0Attr() -> UsdAttribute;`
    `.Set(p: Gf.Vec3f) -> None`, same for `GetLocalPos1`
    [verified]. p: METERS in that body's frame, no
    default; e.g. (0,0,0.5)/(0,0,-0.3)
    (m1_build.py:43,45; m4_build.py:56,58).
  - `joint.GetLocalRot0Attr() -> UsdAttribute;`
    `.Set(q: Gf.Quatf) -> None`, same for `GetLocalRot1`
    [verified]. q: (w,x,y,z) unitless, no default;
    always identity `Gf.Quatf(1.0)` = (w=1, xyz 0
    [probable]) here; hinges rely on axis token, not
    rotated frames (m1_build.py:44,46; m4_build.py:57,59).
  - `joint.GetAxisAttr() -> UsdAttribute;`
    `.Set(a: Tf.Token [probable]) -> None` [verified]. a:
    axis token, no default; ONLY `UsdPhysics.Tokens.y`
    (pitch) drilled (m1_build.py:47; m4_build.py:60).
  - `joint.CreateLowerLimitAttr() -> UsdAttribute;`
    `.Set(lo: float) -> None`, same for
    `CreateUpperLimitAttr(hi: float)` [verified]. lo/hi:
    DEGREES, no default; -170.0/+170.0, M4/V5 only
    (M1-M3 have NO limits) (m4_build.py:61-62;
    v5_build.py:62-63).
  - `UsdPhysics.DriveAPI.Apply(prim: Usd.Prim, mode: str)`
    `-> UsdPhysics.DriveAPI [probable]` [verified].
    prim: joint prim via j.GetPrim(); mode: drive-mode
    token as str, no default; ONLY "angular" drilled
    (m1_build.py:48; m4_build.py:63).
  - `drive.CreateTypeAttr() -> UsdAttribute;`
    `.Set(t: str) -> None` [verified]. t: drive-type
    token as str, no default; ONLY "force" drilled
    (m1_build.py:49; m4_build.py:64).
  - `drive.CreateStiffnessAttr() -> UsdAttribute;`
    `.Set(k: float) -> None` [verified]. k: stiffness,
    N*M/RAD [probable unit], no default; 400.0 (M1) vs
    100000.0 (M2-M4/V5) (m1_build.py:50; m2_build.py:60;
    m4_build.py:65).
  - `drive.CreateDampingAttr() -> UsdAttribute;`
    `.Set(c: float) -> None` [verified]. c: damping,
    N*M*S/RAD [probable unit], no default; 40.0 (M1) vs
    10000.0 (M2-M4/V5) (m1_build.py:51; m4_build.py:66).
  - `drive.CreateMaxForceAttr() -> UsdAttribute;`
    `.Set(f: float) -> None` [verified]. f: NEWTONS
    [probable unit], no default; 1000000.0 all drills
    (m1_build.py:52; m4_build.py:67).
  - `drive.CreateTargetPositionAttr() -> UsdAttribute;`
    `.Set(t: float) -> None` [verified]. t: DEGREES, no
    default; 0.0 initial at build (m1_build.py:53;
    m4_build.py:68).
  - `stage.GetPrimAtPath(jp: str) -> Usd.Prim;`
    `.GetAttribute(name: str) -> UsdAttribute;`
    `.Set(deg: float) -> None` [verified]. jp: joint
    path; name: always "drive:angular:physics:
    targetPosition"; deg: DEGREES = radians*180/pi, no
    default. THE live command write (m2_run.py:48-49,78;
    m3_run.py:41-43; m4a_run.py:84-86; m4b_run.py:73-75).
  - `UsdPhysics.FixedJoint.Define(stage: Usd.Stage,`
    `path: str) -> UsdPhysics.FixedJoint [probable]`
    [verified]. RootFixed (bot root -> static Xform) and
    /World/M4GraspJoint (Link2 -> block)
    (m1_build.py:57; m4_build.py:72; m4a_run.py:204;
    v5a_run.py:204).
  - FixedJoint `GetBody0Rel()/GetBody1Rel()` targets (str
    prim paths, no default) + `GetLocalPos0/1Attr().Set`
    (Gf.Vec3f METERS, no default) +
    `GetLocalRot0/1Attr().Set` (Gf.Quatf (w,x,y,z), no
    default) [verified]. Grasp frames COMPUTED:
    localPos0=(0,0,0.2) identity rot; localPos1 =
    block-frame offset via inverse-quat transform;
    localRot1 = qw^-1 * bq, zero-snap attach
    (m4a_run.py:205-218).
- KNOBS (typed):
  - stiffness k (float, N*M/RAD [probable], required)
    400.0 (M1) vs 100000.0 (M2+); damping c (float,
    N*M*S/RAD [probable], required) 40.0 vs 10000.0:
    low gains hold rest (M1 q<0.10) but re-play exact
    arrival proven at 100000/10000 (probe 13, R4);
    raising gains -> tighter tracking, lowering ->
    sag/overshoot [verified].
  - maxForce f (float, NEWTONS [probable], required):
    1000000.0, effectively uncapped for 0.3-2kg bodies;
    lowering could stall the lift [probable].
  - limits lo/hi (float DEGREES each, required when
    present): +/-170.0 (M4/V5) vs absent (M1-M3).
    Limits bound windup but the pack ALSO wraps q to
    [-pi,pi] before every write; limits alone do not
    stop windup across legs [verified].
  - targetPosition (float DEGREES attr; tensors read
    RADIANS): every write multiplies by 180/pi;
    forgetting the factor under-drives by 57x [verified].
  - Grasp attach gates (float METERS code constants):
    g0<0.05 attach (m4a_run.py:199) then g0b<0.02
    post-play verify (m4a_run.py:222,229): attaching
    with a larger gap snaps the block to the site
    [probable].
- EKB RULES:
  - IF commanding a joint THEN write USD targetPosition +
    stop/play re-parse, never tensor writes, BECAUSE
    tensor writes half-respond then freeze (R4) while
    re-parse arrives exactly (probe 19) [verified].
  - IF a prim is a goal marker THEN give it NO physics APIs,
    BECAUSE a collidable marker is a wall (R7: arm parked
    ON the target at q1=+0.29) [verified].
  - IF grasping THEN compute FixedJoint frames from live
    tensor poses (not authored constants), BECAUSE any
    frame error becomes snap displacement at attach (m4a
    section C) [verified].
  - IF writing dof-indexed tensor data THEN print buffer
    shapes first and write only in-range indices, BECAUSE
    OOB dof_indices CRASH Kit natively with no error (R6
    probe 8) [verified].
  - IF touching any prim for read/api-check THEN gate with
    `prim and prim.IsValid()` first, BECAUSE HasAPI/attr
    reads on invalid prims THROW instead of False (R11)
    [verified].
- LIMITS:
  - Goal markers must be visual-only (R7) — failures.md R7
    [verified].
  - OOB dof_indices crash Kit with no traceback (R6) —
    failures.md R6 [verified].
  - HasAPI/attr reads on invalid prims throw (R11) —
    failures.md R11 [verified].
  - Only y-axis revolute + fixed joints drilled; only
    "force" drives; only "angular" mode — TOOLS.md Unknown
    [verified].
- UNKNOWN:
  - Prismatic/distance/spherical joint types [theoretical].
  - Non-y hinge axes in manipulation (z-hinge known only
    from other skills) [theoretical].
  - Drive types "acceleration"/"velocity" [theoretical].
  - Gravities other than 9.81 -z [theoretical].

## 3. pxr PhysxSchema (in-sim articulation tuning)

- DOES: Tunes the PhysX articulation solver + sleep behavior on
  the root link; applied ONLY on root=True links (M2-M4/V5,
  never M1) [verified].
- FUNCTIONS (typed):
  - `PhysxSchema.PhysxArticulationAPI.Apply(prim: Usd.Prim)`
    `-> PhysxArticulationAPI [probable]` [verified]. prim:
    root-link prim ONLY (M2-M4/V5, never M1), no default
    (m2_build.py:41; m3_build.py:40; m4_build.py:44;
    v5_build.py:45).
  - `api.CreateSleepThresholdAttr() -> UsdAttribute;`
    `.Set(t: float) -> None` [verified]. t: sleep
    threshold, unit [theoretical: still-unknown], no
    default; observed 0.0 = never sleep
    (m2_build.py:42; m4_build.py:45).
  - `api.CreateSolverPositionIterationCountAttr()`
    `-> UsdAttribute; .Set(n: int) -> None` [verified].
    n: COUNT of solver iterations, no default; observed
    32 (m2_build.py:43; m4_build.py:46).
  - `api.CreateSolverVelocityIterationCountAttr()`
    `-> UsdAttribute; .Set(n: int) -> None` [verified].
    n: COUNT, no default; observed 1 (m2_build.py:44;
    m4_build.py:47).
  - `api.CreateEnabledSelfCollisionsAttr()`
    `-> UsdAttribute; .Set(b: bool) -> None` [verified].
    b: flag, no default; observed False = OFF
    (m2_build.py:45; m4_build.py:48).
- KNOBS (typed):
  - sleepThreshold (float, unit [theoretical:
    still-unknown], required): 0.0, articulation never
    sleeps; nonzero risks the R4-style freeze where qd
    reads bit-zero and commands are ignored [probable].
  - position iters (int COUNT, required) 32 / velocity
    iters (int COUNT, required) 1: the proven pair;
    lowering position iters likely softens drive
    tracking under load; raising costs step time
    [probable].
  - selfCollisions (bool flag, required): False REQUIRED
    for pitch arms even with clearance gaps; True would
    reintroduce R5-style contact locks [probable].
- EKB RULES:
  - IF building a pitch articulation THEN set sleep 0.0 +
    self-collisions False + iters 32/1, BECAUSE this is the
    exact combo under which re-play exact arrival was
    proven (probe 13/19, R4) [verified].
  - IF links still lock mid-motion THEN fix clearance by
    construction (gap the links), not by solver knobs,
    BECAUSE flush links lock by contact geometry (~9 deg,
    R5) which no iteration count removes [verified].
- LIMITS:
  - Flush-stacked pitch links self-collide and lock even
    with solver tuning (R5) — failures.md R5 [verified].
  - No Newton-backend equivalents drilled — TOOLS.md
    [verified].
- UNKNOWN:
  - Other iteration counts; sleep>0 behavior; GPU vs CPU
    solver differences [theoretical].

## 4. pxr Gf (math types)

- DOES: Value types for every USD attr write and every frame
  computation (offsets, grasp frames, stamp poses) [verified].
- FUNCTIONS (typed):
  - `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f`
    [verified]. float32 triple; unit by use: METERS
    (joint local-pos m1_build.py:43; grasp frames
    m4a_run.py:207,216-217) or dimensionless (shelf
    scale m4_build.py:93; gravity dir m1_build.py:17).
    No defaults (all 3 always passed; `Gf.Vec3f(*a0)`
    unpacks a 3-tuple, m1_build.py:43).
  - `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d`
    [verified]. float64 triple, METERS; translate ops +
    stamp positions (m1_build.py:30; m4_build.py:38;
    m4b_run.py:152-153,160-162). No defaults.
  - `Gf.Quatf(w: float, x: float, y: float, z: float)`
    `-> Gf.Quatf` [verified]. float32 unitless quat in
    (w,x,y,z) order; single-arg `Gf.Quatf(1.0)` =
    identity (w=1, xyz default 0 [probable])
    (m1_build.py:44; m4a_run.py:202-203,208,210-211;
    m4b_run.py:156-157,164-165).
  - `quat.GetInverse() -> Gf.Quatf` [verified]. No
    params; block-frame offset + relative rotation
    (m4a_run.py:213,218; v5a_run.py:213,218).
  - `quat.Transform(vec: Gf.Vec3f) -> Gf.Vec3f [probable]`
    [verified]. Rotates offset into block frame (dl1
    computation, m4a_run.py:213-215). Other-arg
    overloads [theoretical: unused here].
  - `qw.GetInverse() * bq -> Gf.Quatf` [verified]. `*`:
    (Gf.Quatf, Gf.Quatf) -> Gf.Quatf quat multiply =
    relative rotation for FixedJoint localRot1
    (m4a_run.py:218).
- KNOBS (typed):
  - Vec3f (float32) vs Vec3d (float64): f for physics
    attrs, d for xform ops; mixing them up is a type
    error at Set [probable].
  - Quat normalization (float lens from np.linalg.norm,
    unitless; normalized comps float): m4a divides by
    norm explicitly (m4a_run.py:201-203,209-211);
    unnormalized quats would skew the grasp frame
    [probable].
- EKB RULES:
  - IF converting a tensor quat to USD THEN normalize
    explicitly first, BECAUSE the pack never trusts raw
    tensor magnitude (m4a qlen/blen) [verified].
  - IF computing a grasp offset THEN express it in the
    BODY1 (block) frame via inverse-quat transform,
    BECAUSE FixedJoint localPos1 lives in body1's frame
    (m4a dl1) [verified].
- LIMITS:
  - None live-verified; pure math, bit-identical V5 re-run
    (README) [verified].
- UNKNOWN:
  - None material [verified].

## 5. omni.usd (in-sim stage access)

- DOES: Gets the live stage; prim lookup for attr writes,
  grasp-joint authoring, and clean-slate removal [verified].
- FUNCTIONS (typed):
  - `omni.usd.get_context() -> UsdContext [probable];`
    `.get_stage() -> Usd.Stage [probable]` [verified].
    No params (m1_build.py:10; m1_run.py:9; m2_run.py:47;
    m4a_run.py:79,173).
  - `stage.GetPrimAtPath(path: str) -> Usd.Prim [probable]`
    [verified]. path: Sdf.Path-compatible str, no
    default. Falsy/invalid prim when missing
    (m1_build.py:13; m2_run.py:48; m4b_run.py:147,166).
  - `stage.RemovePrim(path: str) -> bool [probable:
    return never used]` [verified]. path: prim path
    str, no default. Clean-slate removal + grasp joint
    release (m1_build.py:15; m4b_run.py:168).
  - `schema.GetPrim() -> Usd.Prim [probable]` [verified].
    No params; the raw prim for API application, on
    Cube/Plane/Xform/joint wrappers (m1_build.py:29,31).
  - `prim.IsValid() -> bool` [verified]. No params; gate
    before EVERY touch (R11) (m1_build.py:14;
    m4b_run.py:167).
  - `prim.HasAPI(name: str) -> bool` [verified]. name:
    API schema name str, no default; observed
    "IsaacSiteAPI" (m1_run.py:11).
  - `prim.ApplyAPI(name: str) -> bool [probable: return
    never used]` [verified]. Site marking (see tool 11)
    (m1_build.py:70; m2_build.py:80; m4_build.py:85).
- KNOBS (typed):
  - Removal-list contents (tuple[str, ...] of prim-path
    strs, code constant, required): must name EVERY
    prefix ever built (/World/{M1..M4,M4V2,Y}* +
    PhysicsScene); missing one leaves a physics-live
    ghost (R12: M4V2 rig corrupted V5 by 0.77 err)
    [verified] (m2_build.py:13-18; v5_build.py:15-22).
- EKB RULES:
  - IF building a drill THEN remove ALL prior drill prims
    + PhysicsScene FIRST, BECAUSE co-located live bots
    collide (R8: M2Bot shoved M3 to q0=0.295) [verified].
  - IF auditing before an exam THEN inventory the stage for
    stray physics-live rigs, BECAUSE one leftover rig
    silently corrupts results (R12) [verified].
  - IF writing a cross-check snapshot THEN make it READ-ONLY
    (never clean-slate inside), BECAUSE delete-before-build
    + crash guts the live stage (R11) [verified].
- LIMITS:
  - Removal lists must name every experimental prefix ever
    built (R12) — failures.md R12, v5_build M4V2 entries
    [verified].
  - Snapshots must be read-only + IsValid-gated (R11) —
    failures.md R11 [verified].
- UNKNOWN:
  - None material (stage access fully drilled) [verified].

## 6. omni.timeline (in-sim timeline control)

- DOES: Resets the playhead and pauses at script end; every run
  script resets before play (R3 prevention) [verified].
- FUNCTIONS (typed):
  - `omni.timeline.get_timeline_interface()`
    `-> TimelineInterface [probable]` [verified]. No
    params (m1_run.py:33; m2_run.py:50; m3_run.py:28;
    m4a_run.py:174).
  - `tl.set_current_time(t: float)`
    `-> None [probable: return never used]` [verified].
    t: SECONDS (timeline time), no default; observed
    0.0 only, called after stop before play in every
    run script (m2_run.py:52; m3_run.py:30;
    m4a_run.py:176; m4b_run.py:116).
  - `tl.pause() -> None [probable: return never used]`
    [verified]. No params; freeze at end for REPORT
    reads (m1_run.py:33; m2_run.py:89; m4b_run.py:182).
- KNOBS (typed):
  - Reset time (float SECONDS, required arg): always 0.0;
    no other value drilled; nonzero reset untested
    [verified].
- EKB RULES:
  - IF starting a run script THEN stop + set_current_time(0.0)
    + settle steps + play, BECAUSE rebuild-while-paused
    leaves stale tensors that assert on read (R3) [verified].
  - IF ending a run script THEN pause, BECAUSE downstream
    legs (m4b after m4a) and verifiers assume a frozen
    final state [probable].
- LIMITS:
  - Rebuild-while-paused leaves stale tensors (R3) —
    failures.md R3 [verified].
- UNKNOWN:
  - Scrub/step APIs beyond play/pause/reset; play() via
    timeline vs app_utils equivalence [theoretical].

## 7. isaacsim.core.experimental.utils.app / app_utils

- DOES: Timeline play/stop + async stepping; the transport core
  of re-play commanding (stop -> set USD targets -> play ->
  step -> fresh handle) [verified].
- FUNCTIONS (typed):
  - `app_utils.play() -> None [probable: return never
    used]` [verified]. No params; sync; starts/resumes
    physics (m1_run.py:14; m2_run.py:54,79; m3_run.py:32).
  - `app_utils.stop() -> None [probable: return never
    used]` [verified]. No params; sync; stops physics
    AND reverts joint-carried bodies to USD pose (R10)
    (m1_run.py:12; m2_run.py:51,76; m4a_run.py:81).
  - `await app_utils.update_app_async(steps: int)`
    `-> None [probable: return never used]` [verified].
    steps: COUNT of physics steps (int), keyword, no
    observed default (always passed); observed
    {5,10,20,30,60} (m1_run.py:13; m2_run.py:53,55,80;
    m3_run.py:45; m4a_run.py:82,88,140,142). Coroutine:
    must be awaited.
- KNOBS (typed):
  - Settle steps (int COUNT, required kwarg): 10 (m4/v5
    _replay m4a_run.py:82, _settle_measure m4a_run.py:140)
    or 5 (m1/m2/m3 openers m1_run.py:13); fewer risks
    the R9 race where play() skips re-parse [verified].
  - Leg steps STEPS (int COUNT, code constant): 30
    (m2/m4/v5) / 20 (m3, m3_run.py:18): motion settle
    per re-play; 60 for final settle_measure; shorter
    legs under-settle and read transient error [verified].
  - Sub-0.01 target deltas (float RADIANS joint-space):
    parse as no-change: micro-steps are DEADLOCK, not
    slow convergence (R9) [verified].
- EKB RULES:
  - IF stop()ing THEN await 10 settle steps before the next
    play, BECAUSE rapid stop/play races kill re-parse (R9:
    M4 trims froze after 1 cycle) [verified].
  - IF commanding THEN settle+measure per leg (stop/settle/
    play/step/fresh-handle), BECAUSE only a fresh handle
    after re-parse reads valid state (R3+R9) [verified].
  - IF releasing a grasp THEN USD-stamp the live block pose
    BEFORE stop(), BECAUSE stop() reverts joint-carried
    bodies to USD-authored pose (R10: block teleported back
    to PICK) [verified].
  - IF steps stall (dq constant, q frozen) THEN suspect
    micro-deltas or missing settle, never larger LAM,
    BECAUSE the stall signature is transport, not math (R9)
    [verified].
- LIMITS:
  - stop() reverts joint-carried bodies to USD pose (R10) —
    failures.md R10 [verified].
  - Rapid stop/play races kill re-parse (R9) — failures.md
    R9 [verified].
  - Sub-0.01 deltas parse as no-change (R9) — failures.md
    R9 [verified].
- UNKNOWN:
  - Step-size/dt control; behavior under Newton backend;
    play-while-playing / stop-while-stopped idempotence
    [theoretical].

## 8. isaacsim.core.experimental.prims.Articulation

- DOES: Live articulation state READS (q, Jacobian). READS ONLY
  — every write path through it proved unreliable (R4) [verified].
- FUNCTIONS (typed):
  - `Articulation(root_path: str) -> Articulation`
    [verified; class name probable]. root_path:
    articulation-root prim path str, no default;
    observed "/World/MxBot/Base|Root". Fresh handle
    required after EVERY re-play (m1_run.py:16;
    m2_run.py:56,81; m3_run.py:34,46; m4a_run.py:111,
    143,180).
  - `robot.get_dof_positions()`
    `-> wp.array | np.ndarray, shape (1,ndof), dtype`
    `float [probable]` [verified]. No params. RADIANS;
    shape verified via [0]/flatten use; read via _q/_w
    converters (isinstance->.numpy()->flatten,
    m2_run.py:35-38; m4a_run.py:39-40; m1_run.py:18).
  - `robot.get_jacobian_matrices()`
    `-> wp.array | np.ndarray, shape (1,nlinks,6,6+ndof)`
    [verified]. No params. Indexed Jn[0,2,0:3,6:8]
    linear / Jn[0,2,3:6,6:8] angular for Link2 of the
    2-DOF arm (m2_run.py:41-44,66-67; m4a_run.py:100-101).
    Units: linear rows (M/S)/RAD [probable], angular
    rows RAD/RAD=unitless [probable].
  - `robot.set_dof_position_targets(targets: ndarray |`
    `wp.array [theoretical], dof_indices: list[int] |`
    `None [theoretical]) -> None [theoretical]` —
    KNOWN-BAD [theoretical: still-unknown, NEVER called
    in any pack script, no call site]. Indexed AND
    full-row writes half-respond then freeze; efforts
    ignored; NEVER call (R4) [verified behavior].
- KNOBS (typed):
  - Jacobian slice indices (int index + slice, code
    constants, required): [0,2,...,6:8]: 0=env, 2=Link2,
    6:8=the 2 arm DOFs after the 6 virtual-base DOFs;
    wrong slice = wrong-body or virtual-base columns
    [verified] (m2_run.py:67; m4a_run.py:101).
  - Handle freshness (construction-ordering constraint,
    not a value: no type/unit/default): a handle built
    before stop/play re-parse reads STALE or asserts
    tensor-entity-invalid (R3); always rebuild after
    play [verified] (m2_run.py:81; m4a_run.py:111).
- EKB RULES:
  - IF reading live state THEN use a post-play fresh
    Articulation handle, BECAUSE pre-re-parse handles are
    stale/invalid (R3) [verified].
  - IF commanding THEN never use set_dof_position_targets,
    BECAUSE both indexed and full-row writes freeze (R4:
    dof0 ignored +0.1/iter for 30 iters) [verified].
  - IF slicing the Jacobian THEN verify link index 2 ==
    Link2 and dof cols 6:8 for THIS 2-DOF arm, BECAUSE the
    layout encodes (env, link, 6 twists, 6 virtual + ndof)
    (m2_run _jac) [verified].
- LIMITS:
  - Tensor WRITES unreliable on PhysX (R4) — failures.md R4
    [verified].
  - get_dof_positions asserts after rebuild-while-paused
    (R3) — failures.md R3 [verified].
  - qd reads bit-zero (asleep); velocity via tensor unread
    here — m4b uses finite-difference instead [verified].
- UNKNOWN:
  - set_dof_position_targets under Newton; velocity/effort
    tensor reads; multi-env batch rows [theoretical].

## 9. isaacsim.core.experimental.prims.RigidPrim

- DOES: Live world-pose reads for links (site computation) and
  the grasp block (gates) [verified].
- FUNCTIONS (typed):
  - `RigidPrim(path: str) -> RigidPrim [probable class
    name]` [verified]. path: prim path str, no default;
    constructed fresh per read group (_link_pose/_block);
    observed LINK/BLOCK consts (m4a_run.py:57,68;
    m4b_run.py:51,62,141).
  - `rp.get_world_poses()`
    `-> tuple[wp.array | ndarray, wp.array | ndarray]`
    [verified]. No params. (positions METERS shape
    (N,3), quaternions (w,x,y,z) unitless shape (N,4)
    per _quat_rot); consumed as _w(p)[0], _w(q)[0]
    (m4a_run.py:58-59,69-70,192-195; m4b_run.py:141-144).
    dtype float [probable].
- KNOBS (typed):
  - Read batching (call pattern, not a value: no
    type/unit/default): m4a calls _link_pose() twice per
    IK iter (m4a_run.py:94-95, lp then lq separately) —
    wasteful but harmless; single-call unpack (m4b _ik
    m4b_run.py:83) halves tensor traffic [probable].
- EKB RULES:
  - IF tracking the site THEN compute site = link_pos +
    quat_rot(link_quat, SITE_OFF) from RigidPrim reads,
    BECAUSE the USD site Xform does not move live during
    play (tensors are truth; m4a docstring) [verified].
  - IF gating grasp/lift/place THEN gate on BLOCK pose, not
    tool pose, BECAUSE tool arrival does not imply object
    arrival (discovery.md goal 5) [verified].
- LIMITS:
  - None live-verified on the read path (gates all green)
    [verified].
- UNKNOWN:
  - Velocity reads via API (pack uses finite-difference
    speed: |b2-b1|/0.5 over 30 steps) [theoretical].

## 10. isaacsim.core.experimental.utils.xform / xform_utils

- DOES: USD-level world pose reads at STOP (seeds and static
  checks, never live state) [verified].
- FUNCTIONS (typed):
  - `xform_utils.get_world_pose(path: str)`
    `-> tuple[pos, quat]` [verified]. path: prim path
    str, no default. pos: array-like float shape (3,)
    METERS; quat: array-like float shape (4,) (w,x,y,z)
    [probable order: matches _quat_rot/RigidPrim
    convention]; container wp.array|ndarray [probable:
    routed through _vec/_w converters]. Used for
    SITE/TARGET (m1_run.py:28-29; m2_run.py:30-32 _pos)
    and ROOT shoulder seed (m4a _seed_ik via _pos_usd
    m4a_run.py:73-75,127).
- KNOBS (typed):
  - None: pure read; no parameters beyond path: str, no
    return beyond (pos, quat) [verified].
- EKB RULES:
  - IF sim is stopped THEN USD reads are valid seeds
    (shoulder pos for analytic IK), BECAUSE USD matches
    physics at rest (m4a _seed_ik) [verified].
  - IF sim is playing THEN never trust USD pose for live
    bodies; use RigidPrim tensors, BECAUSE USD only
    updates at stop (physics-master tensor-read rule,
    m4a docstring) [verified].
- LIMITS:
  - USD reads are stop-time only (m4a docstring) [verified].
- UNKNOWN:
  - None material (stop-time read role fully drilled) [verified].

## 11. IsaacSiteAPI (grasp frame marker)

- DOES: Marks the GraspSite Xform as a grasp frame; the pack
  tracks the site via TENSOR MATH, never via API reads —
  the marker is declarative only [verified].
- FUNCTIONS (typed):
  - `site_prim.ApplyAPI(name: str)`
    `-> bool [probable: return never used]` at build
    (m1_build.py:70; m4_build.py:85; v5_build.py:86);
    `site_prim.HasAPI(name: str) -> bool` check in
    m1_run (m1_run.py:11; site_api=True gate in
    verify_m1) [verified]. name: "IsaacSiteAPI" literal
    str, no default.
- KNOBS (typed):
  - Site offset under Link2 (Gf.Vec3d METERS translate,
    required): (0,0,0.2) M1/M4/V5 (m1_build.py:69;
    m4_build.py:84), (0,0,0.1) M2/M3 (m2_build.py:79);
    run-script SITE_OFF (np.ndarray float64 METERS
    shape (3,)) must match exactly [verified].
- EKB RULES:
  - IF authoring a grasp frame THEN ApplyAPI BEFORE any IK,
    BECAUSE competence goal 1 requires the frame to exist
    first (discovery.md) [verified].
  - IF reading the site live THEN use link tensor pose +
    offset math, not the API, BECAUSE no API read path is
    drilled (m4a _site) [verified].
- LIMITS:
  - None observed (marker never fails) [verified].
- UNKNOWN:
  - Whether any Isaac API consumes the marker (pack only
    needs it as authored frame) [theoretical].

## 12. warp (in-sim array interop)

- DOES: GPU array type returned by tensor APIs; MUST convert
  before numpy use [verified].
- FUNCTIONS (typed):
  - `import warp as wp` [verified]. Module binding (no
    signature): wp = warp module (m1_run.py:19;
    m2_run.py:10; m3_run.py:9; m4a_run.py:12).
  - `isinstance(a: object, wp.array) -> bool` [verified].
    a: Any tensor-read result; the live-tensor check in
    _vec/_w/_q/_jac (m1_run.py:23; m2_run.py:25,37,43;
    m4a_run.py:34).
  - `a.numpy() -> np.ndarray` [verified]. No params; a:
    wp.array. The ONLY safe conversion once tensors are
    live (m1_run.py:18,24; m2_run.py:26,37,43).
- KNOBS (typed):
  - None: no warp config touched; no warp-constructed
    values (arrays arrive from tensor APIs only)
    [verified].
- EKB RULES:
  - IF consuming any tensor read THEN route through
    isinstance->.numpy() first, BECAUSE np.asarray(wp_array)
    and arr[0] raise RuntimeError once live (R2) [verified].
- LIMITS:
  - np.asarray/item-indexing on live warp arrays raises
    (R2) — failures.md R2 [verified].
- UNKNOWN:
  - None material (convert-then-compute fully drilled) [verified].

## 13. numpy (in-sim IK math)

- DOES: All DLS IK, frame math, error norms, seeds, clamps,
  traverse interpolation [verified].
- FUNCTIONS (typed; all dtypes float64 via
  dtype=float converters [verified]; angles RADIANS,
  positions METERS):
  - `np.linalg.inv(A: ndarray shape (2,2))`
    `-> ndarray shape (2,2)` [verified]. A =
    `Jp @ Jp.T + LAM**2 * eye(2)`: 2x2 planar DLS solve;
    Jp = site Jacobian x/z rows, shape (2,2),
    (M/S)/RAD mixed rows [probable units]
    (m2_run.py:73; m4a_run.py:107; m4b_run.py:96).
  - `dq = Jp.T @ inv2x2 @ ep -> ndarray shape (2,)`
    [verified]. Full DLS update (m2/m4a/m4b/v5a/v5b
    identical); ep: METERS shape (2,); dq: RADIANS
    shape (2,) (m2_run.py:73; m4a_run.py:107).
  - `np.clip(dq: ndarray shape (2,), -step: float,`
    `step: float) -> ndarray shape (2,)` [verified].
    Step clamp (RADIANS); step = 0.05 if err<0.05 else
    MAXDQ (0.1 m2 m2_run.py:21,74; 0.12 m4/v5
    m4a_run.py:91,108-109) [verified].
  - `np.linalg.norm(v: ndarray) -> float` [verified].
    All error/gate norms: err (METERS m2_run.py:58,63),
    g0/g0b (METERS m4a_run.py:196,222), pxy/pz (METERS
    m4b_run.py:180-181), spd (M/S m4b_run.py:178), quat
    lens (unitless m4a_run.py:201,209).
  - `np.cross(u: tuple[int,int,int] | ndarray shape (3,),`
    `v: ndarray shape (3,)) -> ndarray shape (3,)` twice
    [verified]. Quat-vector rotation in _quat_rot
    (Rodrigues form): u=(x,y,z) unitless, v=offset
    METERS (m4a_run.py:51-52; m4b_run.py:45-46).
  - `np.asarray(a: wp.array | array-like, dtype=float)`
    `-> ndarray float64` / `np.array(obj: list |`
    `ndarray-expr, dtype=float64 [probable default])`
    `-> ndarray` [verified]. Tensor flattening
    (+.flatten() -> (N,)), waypoints, wrap math
    (m2_run.py:27,38,44; m4a_run.py:36,80; m3_run.py:38).
  - `np.eye(N: int) -> ndarray shape (N,N) float64`
    [verified]. N: int COUNT, no default (always passed);
    observed N=2 always: DLS damping matrix (m2_run.py:73;
    m4a_run.py:107).
  - `np.round(q: ndarray, decimals: int)`
    `-> ndarray; .tolist() -> list[float]` [verified].
    decimals: int COUNT, no observed default (always
    passed); observed 4. TRACE/REPORT formatting
    (m2_run.py:84-85; m4a_run.py:114-115,227).
- KNOBS (typed):
  - LAM (float, unitless damping, default 0.1 code
    constant m2_run.py:21; m4a_run.py:30): DLS damping;
    larger -> slower but stabler near singularities;
    pack never retunes [verified].
  - MAXDQ (float RADIANS, default 0.1 m2 / 0.12 m4/v5):
    per-iter joint step cap; near-field step 0.05
    RADIANS when err<0.05 METERS (m4/v5 adaptive
    m4a_run.py:108-109); LARGER steps beat micro-steps
    (R9: sub-0.01 deltas parse as no-change) [verified].
  - TOL (float METERS, default 0.02 m2_run.py:21;
    m4a_run.py:30): convergence gate for every leg;
    analytic seed lands sub-mm so trim often skips (m4a
    _leg) [verified].
  - Analytic seed branch (int SIGN +1/-1, required
    _seed_ik arg m4a_run.py:126,182-183,186):
    elbow-up/down via _seed_ik; picks IK branch; wrong
    branch reaches around the long way or hits limits
    [verified].
  - q wrap `(q+pi)%2pi-pi` (float RADIANS elementwise,
    before every _replay m4a_run.py:80, m4b_run.py:69):
    prevents windup across legs; M2/M3 lack it (short
    runs, no wraparound observed) [verified].
  - Mirror rule (q1,q2)->(-q1,-q2) (float RADIANS pair):
    mirrored pick/place branch, bit-exact (README, V5
    exam rule: v5a q_grasp[0]<0, v5b q_end[0]>0)
    [verified].
- EKB RULES:
  - IF seeding IK THEN use the analytic 2-link seed first
    and trim-only-if-needed, BECAUSE the seed lands
    sub-mm and blind DLS-from-home wastes legs (R9,
    m4a _leg) [verified].
  - IF err<0.05 THEN clamp steps to 0.05, BECAUSE full
    MAXDQ overshoots the gate (m4/v5 adaptive step)
    [probable].
  - IF choosing a branch THEN mirror by negating BOTH
    joints, BECAUSE the planar arm is x-symmetric (README
    mirror rule, V5 bit-exact) [verified].
- LIMITS:
  - Planar x/z 2-DOF only; 6-DOF/full-pose IK not drilled
    (TOOLS.md Unverified) [verified].
  - No obstacle-aware binding (motion-generation source
    cited, never drilled; discovery.md) [verified].
- UNKNOWN:
  - 6-DOF DLS tuning; orientation-error weighting;
    singularity escape beyond damping [theoretical].

## 14. isaacsim_send.py bridge (host -> sim transport)

- DOES: Sends each mN/v5 build+run script into the live sim;
  evidence/*.json files are its result envelopes
  (status/output/evalue) [verified].
- FUNCTIONS (typed):
  - Bridge invocation per README ("in-sim via
    isaacsim_send.py"): exact CLI signature (argv types /
    flags / defaults) [theoretical: still-unknown, NO
    call site in this pack]. Envelope fields (observed
    dict, verified via verifier reads): `status: str`
    ("ok", verify_m1.py:22; verify_m4.py:24),
    `output: str` (stdout incl. REPORT lines,
    verify_m1.py:28), `evalue: Any | None [probable]`
    (error payload, verify_m1.py:23-24). Envelope JSON
    paths: str (EVDIR + "<name>.json",
    verify_m1.py:6,21).
- KNOBS (typed):
  - None documented in-pack (no bridge flags / retries /
    timeouts observed here) [verified].
- EKB RULES:
  - IF a run reports status != "ok" THEN the verifier fails
    fast naming status+evalue, BECAUSE no REPORT line can
    be trusted from a crashed send (verify_m1..m4)
    [verified].
  - IF chaining legs (m4a->m4b) THEN rely on the paused
    end-state persisting in-sim between sends, BECAUSE m4b
    starts from m4a's paused attached state (m4b
    docstring) [verified].
- LIMITS:
  - None in this pack's failures.md (TOOLS.md) [verified].
- UNKNOWN:
  - Bridge CLI flags / retry / timeout semantics (owned by
    another pack) [theoretical].

## 15. verify_mN / verify_v5 (local evaluators)

- DOES: Locally parse evidence JSON REPORT lines and gate
  pass/fail; exit 0 on pass (m1-m4); v5 prints PASS/FAIL
  per check (no sys.exit code!) [verified].
- FUNCTIONS (typed):
  - `_load(path: str) -> dict` (verify_m1..m4)
    [verified]. path: evidence JSON path str, no
    default; tries encodings tuple[str, ...] =
    ("utf-8-sig", "utf-16", "utf-8")
    (verify_m1.py:9-16; identical verify_m2.py:9-16,
    verify_m3.py:9-16, verify_m4.py:9-16); falls back
    to plain utf-8 open. Returns parsed envelope dict.
  - `main() -> int` + `sys.exit(main())`
    (verify_m1..m4) [verified]. No params; 0 pass / 1
    fail (verify_m1.py:19,53-56; verify_m4.py:19,74-77).
  - `re.search(pattern: str, output: str)`
    `-> re.Match | None` [verified]. Per-drill REPORT
    regex (str pattern, no default); output: envelope
    "output" str; missing REPORT (None) = FAIL naming
    output head (verify_m1.py:26-31; verify_m4.py:28-33,
    46-51).
  - verify_v5 `f(pat: str, s: str, i: int = 1) -> float`
    (no-match -> float("nan"), verify_v5.py:14-16) /
    `b(pat: str, s: str) -> bool | None [probable:
    `m and ...` yields None on miss]
    (verify_v5.py:18-20)` + 14 checks dict[str, bool]
    (GATE1..GATE6+GATE3b/5b/5c + 5 EXAM rules,
    verify_v5.py:22-37); reads evidence JSONs with bare
    json.load(open(path: str)) (utf-8 default, no _load
    fallback) (verify_v5.py:11-12) [verified].
- KNOBS (gates; typed: thresholds float unless noted,
  comparisons in code):
  - M1: api bool True (verify_m1.py:39), ndof int == 2
    COUNT (verify_m1.py:41), dist float METERS
    0.30<dist<0.60 (verify_m1.py:43), |q| float RADIANS
    <0.10 each (verify_m1.py:45) [verified].
  - M2: conv bool True, err1 float METERS <0.02
    (verify_m2.py:37), err0 float METERS >=0.30
    non-triviality (verify_m2.py:39) [verified].
  - M3: conv bool True, arr float RADIANS-norm <0.01,
    maxdev float RADIANS-norm <0.05
    (verify_m3.py:38-41) [verified].
  - M4a: err_pd/err_a/err_t/err_g float METERS <0.02
    (verify_m4.py:38-41), g0b float METERS <0.02
    (verify_m4.py:42), attached bool (verify_m4.py:44)
    [verified].
  - M4b: zmax float METERS >1.0, err_p float METERS
    <0.02, pxy float METERS <0.05, pz float METERS <0.03,
    spd float M/S <0.05 [probable unit: finite-difference
    |b2-b1|/0.5 over 30 steps, m4b_run.py:175-178],
    released bool (verify_m4.py:56-67) [verified].
  - V5: 14 checks (bool) incl. tighter touch float
    METERS <0.01, zmax>1.5, pxy<0.02, spd<0.2, pz<=0.001
    + mirror EXAM rules (block0.x<0, block1.x>0,
    q_grasp[0]<0, q_end[0]>0, conv) (verify_v5.py:22-37)
    [verified].
  - verify_v5 has NO exit code (prints only) while m1-m4
    exit 0/1 (int): CI must grep V5-PASS, not trust $?
    [verified].
- EKB RULES:
  - IF verifying THEN check status=="ok" before regex,
    BECAUSE a crashed send has no REPORT (verify_m1..m4)
    [verified].
  - IF adding a drill THEN mirror the REPORT/regex/exit-0
    contract, BECAUSE the suite's greenness depends on
    uniform machine-readable lines (README Eval 5/5)
    [probable].
- LIMITS:
  - None live-verified (pure local checks) [verified].
  - verify_v5 encoding fragility: bare json.load vs
    _load fallback elsewhere (observed code difference)
    [verified].
- UNKNOWN:
  - None material [verified].

## Cross-tool contracts (verified)

- RE-PLAY LOOP: Articulation read -> numpy DLS -> USD
  targetPosition write (deg) -> app_utils stop/settle/play/
  step -> fresh Articulation (R4+R9+R3; m2_run, m4a _replay).
- GRASP CONTRACT: RigidPrim site+block poses -> g0 gate ->
  FixedJoint computed frames -> play -> g0b gate (m4a C).
- RELEASE CONTRACT: RigidPrim live pose -> UsdGeom USD-stamp ->
  RemovePrim grasp joint -> play/settle -> OBJECT-pose
  gates (R10; m4b E).
- ENVELOPE CONTRACT: bridge status/output -> verifier regex ->
  exit 0 / V5-PASS (README Eval).
- DETERMINISM: clean stage + same script = bit-identical
  re-run; any divergence means contamination (R12; README).

