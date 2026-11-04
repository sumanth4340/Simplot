# Manipulation & Motion — Failure Catalog (live-verified)

## R12: stray physics-LIVE leftover rigs silently corrupt exams
- FAILURE: V5 re-run diverged (v5b err_p 0.77, conv=False, block 7cm
  short) after passing bit-exact before. PAPP seed err 0.82 vs 0.0011
  for the same q.
- CAUSE: A half-built experimental rig (/World/M4V2Bot: RigidBody +
  Collision + ArticulationRoot, crashed mid-build) survived because no
  removal list named it. Its floating link fell onto / collided with
  the exam arm every play segment; at zero pose it interpenetrated
  Link1 by 0.1 m over the full footprint.
- RECOVERY: Sense + modeling agents (read-only audit) found the extra
  rig; added /World/M4V2Bot + /World/M4V2Block to v5_build's removal
  list; re-ran V5 -> bit-identical PASS (determinism restored).
- PREVENTION: Removal lists must name EVERY experimental prefix ever
  built (not just the drill's own). Before an exam, audit the stage
  (sense inventory + modeling diff); any physics-live extra is fatal.
  Reusable probes: workspace-sense/.../probes/dup_inventory.py,
  modeling-assets/.../probes/audit_m4*.py.

## R11: clean-slate + mid-build crash guts the live stage
- FAILURE: x5_all.py removed all V5 prims, then crashed on a wrong
  DriveAPI call (CreateTargetAttr) before rebuilding; stage left
  empty; follow-up snapshots threw "Accessed invalid null prim".
- CAUSE: Delete-before-build ordering + an untested build path. Also:
  HasAPI()/attr reads on invalid prims throw instead of returning
  False (so naive snapshot scripts crash instead of reporting FAIL).
- RECOVERY: Re-ran v5_build + V5 chain to restore; hardened x5_live
  (valid[] gate before every HasAPI/attr/tensor read; clean FAIL
  report with sentinel values when prims are missing).
- PREVENTION: Cross-check snapshots are READ-ONLY (never clean-slate
  in a snapshot script); guard every prim touch with IsValid; test
  build paths before pointing a deleter at the live scene.

## R10: stop() reverts joint-carried bodies to USD-authored pose
- FAILURE: M4b carried the block to place (zmax 1.80) but after
  release the block read at PICK (bit-identical to authored).
- CAUSE: stop() drops the FixedJoint-driven motion of externally
  jointed bodies, restoring their USD-authored pose.
- RECOVERY: Before stop/release, stamp the live tensor pose into
  the block's USD translate/orient ops; then remove joint + play.
- PREVENTION: Always USD-stamp live pose before releasing a grasp.

## R9: rapid stop/play races kill re-parse; micro-steps deadlock
- FAILURE: M4 trims froze after 1 cycle (dq constant, q frozen);
  probe-20 re-plays died after C1; DLS micro-steps never landed.
- CAUSE: play() before stop() commits skips re-parse; sub-0.01
  target deltas (lagged micro-steps) parse as no-change.
- RECOVERY: 10 settle steps after EVERY stop; settle+measure per
  leg; analytic seed (sub-mm) + trim-only-if-needed; larger steps.
- PREVENTION: Settle-measure legs; never blind micro-step loops.

## R8: drill builds must remove ALL prior drill prims (clean slate)
- FAILURE: M3's run started at q0=0.295 (shoved) and dof0 never
  tracked: M2Bot persisted live at the same origin, colliding.
- CAUSE: Builds removed only their own paths; co-located robots
  overlap physically. Older bots usually ghost (scene rebuilds), but
  the most recent stays live and fatal.
- RECOVERY: Every build removes /World/{M1,M2,M3,M4,Y}*
  (bots+grounds+targets) + the PhysicsScene first.
- PREVENTION: Clean-slate removal list in every build script.

## R7: goal markers must be visual-only (no CollisionAPI)
- FAILURE: Every M2 variant stalled with the site ~14cm short; three
  static probes froze at exactly q1=+0.29.
- CAUSE: The 0.1m target cube carried CollisionAPI. Link2's +X face
  meets the cube face at exactly q1=+0.29 -> the arm parked ON the
  marker. Marker looked innocent; it was a wall.
- RECOVERY: Target prims get NO physics APIs. Collidable objects are
  task objects only (M4 grasp block). M2 converged 7 iters after this.
- PREVENTION: Separate goal markers (visual-only) from task objects
  (collision+mass) by construction; suspect any freeze angle that
  repeats across runs (probe the link-face/marker geometry).

## R6: out-of-range dof_indices CRASHES Kit (native, no error)
- FAILURE: Probe 8 wrote dof_indices=[6,7] on a 2-DOF arm; the app
  died (port closed, process gone), no traceback.
- CAUSE: Native OOB write into the physics view buffer.
- RECOVERY: Relaunch sim; split shape-reads from writes; never guess
  index ranges.
- PREVENTION: Print buffer shapes first; write only in-range indices.

## R5: flush-stacked pitch links self-collide and lock (~9 deg)
- FAILURE: v1/v2 arm (0.6/0.4 cubes flush) froze mid-motion; both
  command paths looked dead; tensor/US contradicted each other.
- CAUSE: Pitching corner digs into parent link -> PhysX contact lock.
  (Z-hinge skills never saw this: spin-in-place is contact-free.)
- RECOVERY: v3 arm: 0.3-cube links with 0.15 gaps (clears +/-45 deg).
- PREVENTION: Clearance by construction; A3-vs-M2 axis cross-check.

## R1: scale ops on links distort joint anchors + child frames
- FAILURE: M1 v1 used unit cubes with scale (0.3,0.3,0.6); PhysX
  snapped links to scaled-frame anchors; tip site read z=1.52 not 2.0.
- CAUSE: Joint local-pos and child Xform offsets are interpreted in
  the link's SCALED frame.
- RECOVERY: Uniform-size cubes, no scale ops (A2 pattern); site exact.
- PREVENTION: Never scale articulation links; size via GetSizeAttr.

## R2: pose readback returns warp arrays during sim
- FAILURE: `np.asarray(wp_array)` and `arr[0]` raise RuntimeError
  (item indexing unsupported) once physics tensors are live.
- RECOVERY: `isinstance(a, wp.array)` -> `a.numpy()` -> numpy.
- PREVENTION: Always convert via the _vec helper in run scripts.

## R4: tensor runtime position writes proved unreliable; RE-PLAY works
- FAILURE: Tensor set_dof_position_targets (indexed AND full-row)
  gave half-response, then total freeze (dof0 ignored +0.1/iter for
  30 iters); efforts also ignored; qd bit-zero (articulation asleep).
- CAUSE: Unresolved mechanism (sleep + view/write decoupling both
  implicated); indexed writes additionally showed ~half response.
- RECOVERY: RE-PLAY commanding: set USD drive targets (degrees) ->
  stop()/play() re-parses (probe 19: exact arrival) -> step -> fresh
  Articulation handle. M2 converges in 7 iters on this path.
- PREVENTION: Command joints ONLY via re-play; tensors for READS
  (q, qd, Jacobian, poses) only. Gains 100000/10000 (probe 13 exact).

## R3: rebuild-while-paused leaves stale physics tensors
- FAILURE: `get_dof_positions()` asserted tensor entity invalid after
  a rebuild sent while the timeline was paused.
- RECOVERY: `app_utils.stop()` + settle, then play, then construct
  the Articulation handle.
- PREVENTION: Every run script resets the timeline before play.
