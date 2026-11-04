# Omnigraph Tool Knowledge (2026-11-04)

> Full reference: TOOLS_REF.md — 10 tools, 74 functions, 40 knobs, 32 EKB rules, 24 limits, 21 unknowns.

Pack scope: Skill 9 OMNIGRAPH (graduated), Isaac Sim 6.0.0 / Kit 110,
windowed GUI, Windows. All in-sim scripts run inside Isaac Sim via the
bridge; verifiers run locally.

## Tools

### 1. omni.graph.core (`og`) — graph authoring + runtime API
- DOES: Authors OmniGraph graphs atomically and controls graph
  instances at runtime (disable/enable, link surgery, introspection).
- FUNCTIONS USED:
  - `og.Controller.edit(path, {keys.CREATE_NODES / CONNECT / SET_VALUES / DISCONNECT})`
  - `og.Controller.Keys` key constants
  - `og.Type(og.BaseDataType.DOUBLE)` typed resolve for template inputs
  - `og.get_graph_by_path(path)` + `Graph.set_disabled(True/False)` + `Graph.is_disabled()`
  - `og.ObjectLookup.attribute(path).get_upstream_connections()` (link check)
  - `og.get_node_by_path(P).get_attribute(name).get()` (per discovery.md, probe-documented)
- LIMITS-live-verified:
  - One atomic edit: bare `Node.attr` names resolve only via the
    per-call creation map; later edits MUST use full paths
    `/World/G/Node.attr` (failures.md R4).
  - Bare floats on template inputs raise "Failed to set value";
    use typed 3-tuples `(attr, v, og.Type(DOUBLE))` (failures.md R3).
  - Authoring evaluates PROMPTLY (usdWriteBack): reset targets after
    build, gate authoring-effect vs tick-effect separately
    (failures.md R1).
  - Recreated graph paths stay dead until a disconnect+reconnect
    revive-touch of one value link at run start (3/3 proven); never
    trust `linked=True` alone, gate live-first `t1>0` (failures.md R6;
    evidence/o4_run.json `t3=25.000` post-revive).
  - Live DISCONNECT does not recompile the running instance; only
    `Graph.set_disabled` truly disables (failures.md R7;
    evidence/o4_run.json `frozen=0.0000` exact).
  - World clock runs while disabled; resume catches up to live time
    (missed + new windows: evidence/o4_run.json `resumed=20.000`,
    evidence/v9_run.json `resumed=10.000`) (failures.md R7).
  - One writer per target: duplicate same-target graphs contaminate
    silently with no warning; sweep rivals pre-drill, probes use
    unique targets (failures.md R8; R8 sweep in v9_build.py).
  - Author graphs while STOPPED; RemovePrim+recreate during play
    leaves connections dead, and `stop()` does not clear the stale
    instance (o4_build.py comment; failures.md R6).
- UNKNOWN:
  - Node-level `set_disabled` exists but is untested (failures.md R7).
  - Rival-writer per-tick mix order is unspecified ("last writer wins
    per tick in an unspecified mix", discovery.md).

### 2. OmniGraph node type set (4 drilled types)
- DOES: Tick source, math, and prim-attribute writing inside graphs.
- FUNCTIONS USED (type identifiers in CREATE_NODES):
  - `omni.graph.action.OnPlaybackTick` (`outputs:tick` exec, `outputs:time` double seconds)
  - `omni.graph.nodes.Multiply` (`inputs:a/b`, `outputs:product`)
  - `omni.graph.nodes.Add` (`inputs:a/b`, `outputs:sum`)
  - `omni.graph.nodes.WritePrimAttribute` (`inputs:execIn/value/primPath/name/usePath`)
- LIMITS-live-verified:
  - `WritePrimAttribute` fires on upstream DATA flow; the exec wire
    is optional — cutting tick->execIn does NOT freeze writes
    (failures.md R5).
  - Connected-TUPLE writes silently never configure (`correctlySetup`
    stays false, cube never moves, NO log error); SET-tuple values
    work (O1) and connected-DOUBLE chains work (O2) — drive
    single-double destinations (failures.md R2 OPEN).
  - Atomic-vs-split edit order does NOT fix R2 (both fail)
    (failures.md R2).
- UNKNOWN:
  - R2 root cause is hypothesis only (setup runs before template
    outputs resolve, never re-runs) (failures.md R2 OPEN).
  - Exec-only firing (tick changing while data static) never isolated
    from data-flow firing.
  - Any node type beyond these 4; chains beyond 4 nodes (V9 exam max).
  - `usePath=False` and non-string `primPath` forms not drilled.

### 3. omni.usd — stage access + prim management
- DOES: Opens the stage, inspects/removes prims, reads back
  written attributes in run scripts.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`
  - `stage.GetPrimAtPath / DefinePrim / RemovePrim`
  - `prim.GetAttribute(name).Get()` (target readback)
  - `prim.GetChildren() / GetName() / GetTypeName()` (R8 sweep, node lists)
- LIMITS-live-verified:
  - `RemovePrim` + recreate at the same graph path leaves a stale
    runtime instance shadowing the new prim (failures.md R6).
  - `stop()` does not clear the stale instance (failures.md R6).
- UNKNOWN:
  - Whether any stage-level operation other than link re-touch
    (e.g. reload, new layer) clears a stale graph instance.

### 4. pxr USD authoring (UsdGeom / UsdPhysics / Gf / Sdf)
- DOES: Builds drill scenes: cubes, translate ops, 1R arms
  (rigid bodies, joints, limits, position drives), custom attrs.
- FUNCTIONS USED:
  - `UsdGeom.Cube.Define`, `GetSizeAttr().Set`, `UsdGeom.Xformable(...).AddTranslateOp().Set`
  - `UsdPhysics.Scene.Define`, `RigidBodyAPI/MassAPI/ArticulationRootAPI.Apply`
  - `FixedJoint/RevoluteJoint.Define`, `CreateBody0/1Rel`, `CreateAxisAttr`,
    `CreateLocalPos0/1Attr`, `LimitAPI` low/high, `DriveAPI` type/target/stiffness/damping
  - `Gf.Vec3d/Vec3f`, `Sdf.ValueTypeNames.Double`, `CreateAttribute("og:stamp", ...)`
- LIMITS-live-verified:
  - Joint drive `targetPosition` is written in DEGREES while
    `get_dof_positions` reads RADIANS (discovery.md session notes).
- UNKNOWN:
  - Non-position drive types and multi-DOF arms under graph control.

### 5. isaacsim app transport (`app_utils`)
- DOES: Timeline control and stepped execution around graph runs.
- FUNCTIONS USED:
  - `app_utils.stop()`, `app_utils.play(commit=True)`
  - `await app_utils.update_app_async(steps=N)` (N=10 settle, 30/60 windows)
- LIMITS-live-verified:
  - Stop/play re-parses physics; builds that ran during play need a
    stop/play cycle before trusted reads (o3_run.py Skill 5 R3 note).
  - Author graphs while STOPPED (o4_build.py R6 note).
- UNKNOWN:
  - `update_app_async` steps-to-sim-seconds mapping is uncalibrated;
    timing gates (`t1=5.0/3.5`) are framerate-dependent, not a clock.

### 6. Articulation joint readout (`isaacsim.core.experimental.prims`)
- DOES: Reads live joint positions to prove tick-driven motion.
- FUNCTIONS USED:
  - `Articulation("/World/.../Base")`, `art.get_dof_positions()`
- LIMITS-live-verified:
  - Returns RADIANS; joint targets are DEGREES (discovery.md).
  - O3 gate: target delta ~10 deg with q following (delta > 0.05 rad,
    same direction); V9 `q1=0.0516 q3=0.2261` (README dataset;
    evidence/v9_run.json).
- UNKNOWN:
  - Return-type stability (`wp.array` vs other) across versions —
    callers defensively branch on `isinstance(q, wp.array)`.

### 7. numpy + warp readout conversion
- DOES: Converts DOF readouts to plain floats for report lines.
- FUNCTIONS USED:
  - `np.asarray(q.numpy() if isinstance(q, wp.array) else q).flatten()[0]`, `float(...)`
- LIMITS-live-verified:
  - numpy space-padded floats need tolerant regex in verifiers
    (discovery.md session notes).
- UNKNOWN: none beyond the regex note.

### 8. Local verify evaluators (`verify_*.py`)
- DOES: Offline pass/fail grading of build/run report lines; exit 0 on pass.
- FUNCTIONS USED:
  - `json` + `re` report parsing (`verify_o1/o2/o3/o4/v9`); `math` in `verify_v9`
- LIMITS-live-verified:
  - Regexes must tolerate numpy space-padded floats (discovery.md).
  - Suite: O1 O2 O3 O4 V9 (5/5 green) + X9 co-val 11/11 (README).
- UNKNOWN:
  - `verify_x9.py` is referenced (README) but absent from this
    pack's scripts/ — its gates are unverifiable here.

### 9. isaacsim_send.py bridge (in-sim delivery)
- DOES: Ships `oN_build/oN_run/v9_build/v9_run/probe_*` into the
  running sim and returns stdout/stderr report lines to evidence/.
- FUNCTIONS USED: invoked per README ("in-sim via isaacsim_send.py");
  no direct calls inside pack scripts.
- LIMITS-live-verified:
  - Sim crashed 4x during this arc (render/lidar/bridge-reset);
    recovery is relaunch windowed + bridge poll; scripts rebuild the
    stage anonymously and evidence on disk is never lost
    (discovery.md session notes).
- UNKNOWN:
  - Bridge CLI flags/timeout behavior are not documented in-pack.

### 10. inspect stdlib (docstring probe)
- DOES: Reads live `Controller.edit` docstrings to pin calling
  conventions (Skill 6 R3 rule).
- FUNCTIONS USED: `inspect` (in `probe_og2.py`, per imports).
- LIMITS-live-verified:
  - Docstring probing is pack procedure alongside node
    introspection (discovery.md).
- UNKNOWN:
  - Node `.ogn/.cpp` + Kit-log probing is prescribed by
    discovery.md but no pack script reads `.ogn/.cpp` files or the
    Kit log (no such imports) — that half is unverified in-pack.

## Unverified

- `x9_live.py` + `verify_x9.py`: referenced by README §Tools but
  absent from scripts/ (X9 11/11 claim not re-checkable from this pack).
- Node-level `set_disabled` (failures.md R7: exists, untested).
- R2 root cause (failures.md OPEN hypothesis only).
- Rival-writer per-tick ordering (discovery.md: unspecified mix).
- `.ogn/.cpp` + Kit-log signature probing (discovery.md prescribes;
  no pack script implements it).
- Bridge CLI surface (flags, timeouts) — used but not specified in-pack.
- Framerate dependence of step-count timing gates.
- Graph features beyond the drilled set: 5+ node chains, non-Add/Mul
  math nodes, `usePath=False`, non-position drives, multi-DOF targets.

## Sources-read

Fully read (13):
- action-reasoner/skills/omnigraph/README.md (no SKILL.md in pack)
- action-reasoner/skills/omnigraph/failures.md
- action-reasoner/skills/omnigraph/discovery.md
- action-reasoner/skills/omnigraph/scripts/o1_build.py
- action-reasoner/skills/omnigraph/scripts/o2_build.py
- action-reasoner/skills/omnigraph/scripts/o3_build.py
- action-reasoner/skills/omnigraph/scripts/o4_build.py
- action-reasoner/skills/omnigraph/scripts/o3_run.py
- action-reasoner/skills/omnigraph/scripts/o4_run.py
- action-reasoner/skills/omnigraph/scripts/v9_build.py
- action-reasoner/skills/omnigraph/scripts/v9_run.py
- action-reasoner/skills/omnigraph/evidence/o4_run.json
- action-reasoner/skills/omnigraph/evidence/v9_run.json

Skimmed by name + imports only (29 scripts): o1_run, o2_run,
probe_disconn, probe_enable, probe_fresh, probe_gobj, probe_killdup,
probe_math, probe_math2, probe_og, probe_og2, probe_og3, probe_og4,
probe_og5, probe_og6, probe_og7, probe_og8, probe_og9, probe_og10,
probe_rtype, probe_rtype2, probe_types, probe_vals, probe_write,
verify_o1, verify_o2, verify_o3, verify_o4, verify_v9.
