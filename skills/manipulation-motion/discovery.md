# Skill 5 MANIPULATION & MOTION — Discovery

## Scope
Owns arm manipulation: grasp frames, differential IK, joint-space
motion, assisted grasping, and object-pose-validated pick-and-place.
Builds on physics (drives), articulation (roots/chains), stage (prims).

## Competence goals (must pass unaided after training)
1. Author/find a grasp frame (IsaacSiteAPI) before any IK.
2. Drive an arm's end-effector to a target via differential IK.
3. Transport via joint-space interpolation (hybrid with IK).
4. Grasp (FixedJoint at contact), lift, place, release.
5. Validate OBJECT pose at grasp/lift/place gates, not tool pose.

## Drill plan (each: run + local verify + evidence)
- M1 frame: 2-DOF pitch arm + grasp site; site/target offset measured.
- M2 reach: DLS position IK converges site to target (<2cm).
- M3 transport: joint-space traverse between configs, arrival exact.
- M4 grasp: FixedJoint grasp + lift + place, 3 gates on object.
- V5 exam: fresh-stage full pick-and-place, object-pose evidence.

## Sources (to be verified live, not trusted)
- manipulation-ik: DLS pattern, virtual-base slicing, grasp gates.
- motion-generation: phase machine, world binding (obstacle-aware later).
- Articulation API: get_jacobian_matrices, set_dof_position_targets.
