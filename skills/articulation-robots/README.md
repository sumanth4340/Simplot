# Skill 4 ARTICULATION & ROBOTS — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, PhysX engine, Windows.

## Verified facts (do not guess these)
- Root pattern (mirrors URDF importer): ArticulationRootAPI on the
  DYNAMIC base link + FixedJoint anchoring base to the (non-rigid)
  robot root. Root-on-Xform + static base yields 0 DOFs (failures R1).
- DOF API: `Articulation(<root-link-path>)`, `dof_names`,
  `get_dof_positions()` after play(). Tensors need play; USD parses
  need the root API.
- Units: angular drive targets in DEGREES (position and velocity);
  DOF readback in RADIANS. 90deg->pi/2, 45deg->pi/4, both exact.
- q0 reads slip under active drives (physics F5): assert travel +
  arrival, not q0~=0.
- Robot schema: `prim.ApplyAPI("IsaacRobotAPI")`, type attr from
  `Attributes.ROBOT_TYPE.value`, `PopulateRobotSchemaFromArticulation`
  + `ValidateRobotSchemaRelationships` live in the `.utils` submodule
  (not the package root). Populate applies Link/Joint APIs itself.
- Drive overs author cleanly on referenced joints (V4 proved arrival).

## Dataset (evidence/, replayable)
- A1 root: single root on base, ndof=1, rest q~1e-8.
- A2 chain: 3 links, Hinge1/Hinge2 named, connected, rest ~1e-8.
- A3 drive: PD 90deg, q 0.44->1.5705 (pi/2 exact).
- A4 schema: Manipulator, 3 links + 3 joints, 0 invalid.
- V4 exam: imported arm (schema Default, root present) driven to pi/4.

## Tools (scripts/, in-sim via isaacsim_send.py unless noted)
- aN_build/aN_run, a4_schema, v4_build/v4_run: authorship + execution.
- verify_aN/verify_v4: local evaluators, exit 0 on pass.

## Eval
Suite: A1 A2 A3 A4 V4 (5/5 green at graduation).

## Failure catalog
See failures.md (R1).
