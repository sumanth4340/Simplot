# Behavior & Animation — Failure Catalog (live-verified)

## R3: mid-play joint commands must use the tensor API (radians)
- FAILURE (M3 R4, re-confirmed): USD drive-target sets during play
  do NOT propagate; they need stop/play re-parse per waypoint.
- RECOVERY: Articulation.set_dof_position_targets(np rad) applies
  mid-play, single session (B3: q=0.4991/-0.4982/-0.0009 exact).
  Echo targets with get_dof_position_targets; both radians.

## R2: rotation units differ by layer (op deg, DOF rad, GetAngle deg)
- FAILURE: Gated world-matrix angle against pi/4 (assumed radians);
  Gf.Rotation.GetAngle returned 45.0/90.0 (DEGREES).
- MAP: xformOp:rotate* author degrees; DriveAPI angular targets
  degrees; Articulation.get_dof_positions radians; Gf.GetAngle
  degrees. Convert at every boundary; never assume.

## R1: XformCache has no GetLocalToWorld in this USD
- FAILURE: cache.GetLocalToWorld(prim) raised AttributeError.
- CAUSE: Guessed C++ name; this build exposes
  GetLocalToWorldTransform (+ GetParentToWorldTransform,
  ComputeRelativeTransform).
- RECOVERY: Probe dir() live (Skill 6 R3 rule); use
  UsdGeom.XformCache(tc).GetLocalToWorldTransform(prim).
