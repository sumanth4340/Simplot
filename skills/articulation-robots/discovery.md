# Skill 4 ARTICULATION & ROBOTS — Discovery

## Scope
Owns articulated robots: articulation roots, multi-link chains, DOF
state readback, joint drives on chains, robot schema overlay, grippers.
Builds on physics (joints/drives), stage (prims), modeling (imports).

## Competence goals (must pass unaided after training)
1. Author a valid articulation: exactly one ArticulationRootAPI, one
   connected joint hierarchy.
2. Read live DOF positions/velocities via the Articulation API.
3. Drive chain joints to targets and verify arrival.
4. Apply + validate the Isaac robot schema overlay.
5. Assemble multi-arm (FixedJoint, single root) per the correct pattern.

## Drill plan (each: run + local verify + evidence)
- A1 root: 1-DOF arm + root API; DOF readback ~0 at rest.
- A2 chain: 3-link arm; all DOFs readable; structure connected.
- A3 drive: PD to target; joints arrive within tolerance.
- A4 schema: robot/link/joint APIs + populated relations verified.
- V4 exam: imported URDF arm articulated, driven, schema-valid.

## Sources (to be verified live, not trusted)
- usd-articulation: root rules, fixed-joint assembly, schema overlay.
- Articulation API: isaacsim.core.experimental.prims (read source first).
