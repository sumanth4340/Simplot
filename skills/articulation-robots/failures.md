# Articulation & Robots — Failure Catalog (live-verified)

## R1: root API on plain Xform + static base yields 0 DOFs
- FAILURE: A1 v1 put ArticulationRootAPI on /World/A1Bot (Xform) with a
  static base link; PhysX query returned ndof=0 (root found, no DOFs).
- CAUSE: The articulation root must be a DYNAMIC rigid body (the base
  link), anchored by a FixedJoint to the (non-rigid) robot root, exactly
  as the URDF importer emits (see m2 physics.usda: root API + RigidBody
  on base, root_joint fixed base->robot-root).
- RECOVERY: Base dynamic + root API on base + fixed joint; ndof=1, rest
  q~1e-8. Verified green.
- PREVENTION: Mirror the importer pattern for hand-authored robots.

## W1 (2026-11-04): wheel-on-cube revolute attach via executor — verified live
- PROCEDURE: Two `create.objects.sphere` wheels + `joint.create.joint`
  revolute each, `axis=Y` for X-rolling wheels on +/-Y cube faces.
- VERIFIED: Executor sets wheel-center frames itself (LocalPos0 = wheel
  offset in cube frame, LocalPos1 = origin, inverse-orient rots), so no
  snap on play; auto-names `{from}_to_{to}` are unique per wheel.
- CONSTRAINTS: Sim must be paused (`_need_paused`); both sides dynamic
  rigid (DynamicSphere is); wheels need a small lateral gap from the
  cube face (0.05 used: inner edge 0.55 vs face 0.5).
- NOTE: No articulation root needed for attach-only; add root on the
  dynamic cube (per R1) before drives or DOF readback.
