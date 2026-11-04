# Omnigraph TOOLS_REF — exhaustive tool reference (2026-11-04)

Pack: Skill 9 OMNIGRAPH (graduated), Isaac Sim 6.0.0 / Kit 110, windowed GUI,
Windows. In-sim scripts run inside Isaac Sim via the bridge; verifiers run locally.

Claim tags: [verified] = seen in a fully-read script, evidence JSON, or
failures.md/discovery.md/README.md text. [probable] = seen only in a skimmed
probe (logic read, saved output absent) or strongly implied by pack text.
[theoretical] = hypothesis, untested, or absent-from-pack.

No SKILL.md exists in this pack; README.md is the skill doc [verified].

DATATYPE pass (2026-11-04): every Functions bullet carries exact param
types, return type, units, and defaults, grounded in script call sites
(`script.py:line`). Types with no call site or no saved output are marked
[probable] or [theoretical]. Every knob carries attr type + unit +
default. Entry counts unchanged (74 signatures, 40 knobs); typed totals
appended under Coverage counts [verified].

## T1. omni.graph.core (`og`) — graph authoring + runtime API

DOES: Authors OmniGraph graphs atomically via `Controller.edit` and controls
graph instances at runtime (disable/enable, link surgery, introspection) [verified].

### Functions (params typed, return typed, units, defaults)

- `og.Controller.edit(graph_path: str, edit: dict) -> None` [verified]
  - Params: `graph_path: str` (Sdf prim path, e.g. `"/World/O1Graph"`;
    unit n/a; no default — always passed, o1_build.py:30);
    `edit: dict` mapping `Keys` constants to lists of tuples (unit n/a;
    no default). Returns `None` (nothing captured in any script)
    [verified]. Used in o1/o2/o3/o4/v9 builds (o1_build.py:30,
    o2_build.py:28, o3_build.py:54, o4_build.py:58, v9_build.py:60),
    o4_run/v9_run revive (o4_run.py:32-33, v9_run.py:37-38),
    probe_disconn (probe_disconn.py:9), probe_fresh (probe_fresh.py:8),
    probe_math (probe_math.py:15), probe_og8 (probe_og8.py:15) [verified].
- `og.Controller.Keys` — key constants (dict keys; unit n/a) [verified]
  - `CREATE_NODES: list[tuple[str, str]]` — `(node_name: str,
    type_str: str)` (o1_build.py:31-34) [verified]
  - `CONNECT: list[tuple[str, str]]` — `(src_attr: str, dst_attr: str)`
    (o1_build.py:35-37) [verified]
  - `SET_VALUES: list[tuple[str, Any]] | list[tuple[str, Any, og.Type]]` —
    `(attr: str, value: Any)` or `(attr: str, value: Any,
    resolve: og.Type)`; drilled value types: `str` (primPath/name),
    `bool` (usePath), `float` (Mul/Add b, typed 3-tuple only),
    `tuple[float, float, float]` (translate 3-tuple, o1_build.py:42)
    (o1_build.py:38-43, o3_build.py:65-70, v9_build.py:73-79) [verified]
  - `DISCONNECT: list[tuple[str, str]]` — `(src_attr: str, dst_attr: str)`
    (o4_run.py:32, probe_disconn.py:9) [verified]
  - Full key list probed by `dir(og.Controller.Keys)` in probe_og4
    (probe_og4.py:14), but its saved output is absent from evidence/
    [probable].
- `og.Type(base: og.BaseDataType) -> og.Type` [verified]
  - Param `base: og.BaseDataType` (enum member; only `DOUBLE` drilled;
    no default — always passed, o3_build.py:66, v9_build.py:59).
    Returns an `og.Type` resolve-type object used as the 3rd element of a
    SET_VALUES tuple for token-template inputs [verified]. Aliased as `DT`
    in v9_build.py:59 [verified]. Unit n/a.
- `og.BaseDataType.DOUBLE` — enum member of type `og.BaseDataType` (unit
  n/a; no params) naming the double resolve type [verified].
- `og.get_graph_by_path(graph_path: str) -> og.Graph` [verified]
  - Param `graph_path: str` (full prim path, e.g. `"/World/O4Graph"`;
    o4_run.py:36, v9_run.py:41, probe_gobj.py:2). Returns a live graph
    handle used for `set_disabled`/`is_disabled` [verified]. Unit n/a;
    no default.
- `Graph.set_disabled(disabled: bool) -> None` [verified]
  - Param `disabled: bool` (unit n/a; no default — always passed
    `True`/`False`, o4_run.py:37/41, v9_run.py:42/46). `True` freezes all
    writes; `False` resumes with catch-up (R7) [verified]. Returns `None`.
- `Graph.is_disabled() -> bool` [verified]
  - No params. Returns current disabled state; asserted as `dis=True` /
    `en=False` in O4/V9 report lines (o4_run.py:38/42/46, v9_run.py:43/47)
    [verified].
- `og.ObjectLookup.attribute(full_attr_path: str) -> og.Attribute` [verified]
  - Param `full_attr_path: str` (unit attr path; no default) — must be a
    FULL path, e.g. `"/World/O4Graph/Write.inputs:value"`
    (o4_build.py:78-79, v9_build.py:83-84, probe_disconn.py:12,
    probe_rtype.py:2, probe_rtype2.py:5) [verified].
- `Attribute.get_upstream_connections() -> list[Any]` [verified call]
  - No params. Returns upstream connection list (element type unsaved —
    element type [theoretical]); `len(up) == 1` is the `linked=True`
    build gate (o4_build.py:78-81, v9_build.py:83-85,
    probe_disconn.py:13) [verified].
- `og.get_node_by_path(node_path: str) -> og.Node` [probable]
  - Param `node_path: str` (full node path, e.g.
    `"/World/O4GraphB/Write"`, probe_gobj.py:7); no default; unit n/a.
    Cited in discovery.md; return handle used only for `dir()` there; no
    saved output in-pack [probable].
- `Node.get_attribute(name: str) -> og.Attribute [probable]; Attribute.get() -> Any [probable]` [probable]
  - Param `name: str` (attr name); no default. Probe-documented per
    discovery.md; no pack script with saved output demonstrates a return
    value, so the `.get()` value type is attr-dependent `Any` [probable].
- `og.Controller.get(attr_path: str) -> Any` [probable]
  - Param `attr_path: str` (full `/World/O3Graph/...` path, no default;
    probe_write.py:10, probe_vals.py:9). Returns the LIVE attr value;
    type follows the target attr (`float` for doubles, tuple for
    vectors); outputs not saved in evidence/ [probable].
- `og.GraphRegistry.get_node_type_version(type_str: str) -> Any` [probable call; theoretical return]
  - Param `type_str: str` (node type string; no default; probe_og4.py:2-10
    over 12 candidates). Return assigned to `v` and stringified; version
    object shape unknown (outputs not saved) [theoretical]. Unit n/a.
- `og.NodeType(type_str: str) -> og.NodeType` [probable]
  - Param `type_str: str` (no default; probe_og7.py:2-8 over 8
    candidates). Constructor outputs not saved [probable]. Unit n/a.
- `og.Controller.create_graph(*args: Any, **kwargs: Any) -> Any`,
  `og.Controller.create_node(*args: Any, **kwargs: Any) -> Any`,
  `og.Controller.connect(*args: Any, **kwargs: Any) -> Any`
  [probable existence; theoretical signature]
  - Referenced by `inspect.signature` calls in probe_og2.py:3-5, so the
    names resolve at import time in-sim; exact params, defaults, units,
    and return types unknown (no saved output), and no drill calls them
    [theoretical].
- `Attribute.get_resolved_type() -> Any` [probable call; theoretical return]
  - No params. Called in probe_rtype2.py:6 over 7 `/World/O3Graph/...`
    specs and stringified; resolved-type object shape unknown (outputs
    not saved) [theoretical].
- `og.GraphEvaluationMode`, `og.ExecutionAttributeState`,
  `og.NodeController`, `og.GraphRegistry` module surface [probable]
  - Module/class objects (object types `module`/`type` [probable];
    unit n/a); enumerated via `dir()` in probe_gobj.py:4-6 /
    probe_og3.py:3; member names, signatures, and semantics unknown (no
    saved output) [theoretical].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Graph path: `str` (Sdf prim path; unit n/a; no default — caller-chosen).
  Fresh path (`/World/O4GraphB`) writes immediately (`t1=5.0` first try);
  RemovePrim+recreate at the same path leaves a stale dead instance
  (`t1=0.000`) [verified].
- Edit shape: `dict[Keys, list[tuple]]` key-set per `Controller.edit` call
  (unit n/a; drilled default = one atomic call with CREATE_NODES +
  CONNECT + SET_VALUES). One edit (create+connect+values) has fewer
  ordering hazards; splitting does NOT fix R2 (both fail) [verified].
- Attr refs: `str` (bare `Node.attr` or full `/World/G/Node.attr`; unit
  attr path; no default). Bare names resolve ONLY via the per-call
  creation map; a later edit with bare names raises "At least one end of
  the connection must be an attribute" [verified].
- SET_VALUES tuple shape: 2-tuple `(str, Any)` (implicit resolve; drilled
  default for str/bool/tuple values, o1_build.py:38-43) vs 3-tuple
  `(str, float, og.Type)` (explicit resolve; required for bare floats on
  token-template inputs, o3_build.py:66, v9_build.py:74-75). Bare floats
  without the type raise "Failed to set value"; tuples/strings resolve
  implicitly and need no type [verified].
- Revive-touch: `bool`-equivalent (DISCONNECT+re-CONNECT of one VALUE link
  performed or not; unit n/a; default absent). Present revives recreated
  paths (proven 3/3, `t3=25.000`, o4_run.py:32-33, v9_run.py:37-38);
  absent leaves them dead despite `linked=True` [verified].
- `set_disabled(disabled: bool)` flag (unit n/a; graph default = enabled,
  i.e. `False` — O1/O2/O3 run with no call). `True` freezes writes
  exactly (`frozen=0.0000`); `False` resumes at live world time
  (catch-up) [verified].
- Exec-wire CONNECT (`tick -> execIn`): `bool` (connection present; unit
  n/a; drilled default present). Present vs cut: no effect on
  WritePrimAttribute firing either way (data-flow firing, R5) [verified].
- `og.Type` resolve-type choice: `og.Type` built from an
  `og.BaseDataType` member (unit n/a; no default — required 3rd tuple
  element). `DOUBLE` works for float template inputs; every other resolve
  type is undrilled [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF authoring a graph THEN use ONE atomic `Controller.edit`
  (CREATE_NODES + CONNECT + SET_VALUES) BECAUSE split edits add ordering
  hazards with no benefit (R2 fails both ways) [verified].
- IF a later edit touches the graph THEN use full `/World/G/Node.attr`
  paths BECAUSE bare names resolve only via the per-call creation map
  (R4) [verified].
- IF setting a bare-float value on a token-template input THEN pass a
  typed 3-tuple `(attr, v, og.Type(DOUBLE))` BECAUSE bare floats raise
  "Failed to set value" (R3) [verified].
- IF the graph path was recreated (RemovePrim + rebuild) THEN
  DISCONNECT+re-CONNECT one value link at run start BECAUSE the stale
  runtime instance shadows the new prim until re-touched (R6, 3/3)
  [verified].
- IF gating graph liveness THEN require live-first `t1 > 0`, never
  `linked=True` alone BECAUSE a dead graph still reports its upstream
  link present (R6) [verified].
- IF disabling a graph THEN call `Graph.set_disabled(True)` and assert
  `is_disabled()` BECAUSE exec-cut does not stop data-flow writes (R5)
  and live value-cut is a runtime no-op (R7) [verified].
- IF predicting post-resume values THEN expect catch-up to LIVE world
  time (missed + new windows), not continuation from the freeze point
  BECAUSE the world clock runs while the graph is disabled (R7:
  `resumed=20.000` O4, `resumed=10.000` V9) [verified].
- IF starting any drill THEN sweep `/World` for rival same-target graphs
  and assert exactly one writer per target BECAUSE duplicates contaminate
  silently with no warning (R8: a leftover made a DISABLED graph look
  live across two runs) [verified].
- IF building a graph THEN author while STOPPED BECAUSE
  RemovePrim+recreate during play leaves connections dead and `stop()`
  does not clear the stale instance (R6; o4_build.py comment) [verified].

### LIMITS (live-verified, with cites)

- L1: Bare names resolve only in-call; later edits MUST use full paths
  (failures.md R4) [verified].
- L2: Bare floats on template inputs raise; typed 3-tuples required
  (failures.md R3) [verified].
- L3: Authoring evaluates PROMPTLY (usdWriteBack): reset targets after
  build; gate authoring-effect vs tick-effect separately (failures.md R1;
  evidence/o1_run.json `z0a=1.5000`) [verified].
- L4: Recreated paths stay dead until revive-touch; never trust
  `linked=True` alone, gate live-first `t1>0` (failures.md R6;
  evidence/o4_run.json `t3=25.000` post-revive) [verified].
- L5: Live DISCONNECT does not recompile; only `Graph.set_disabled`
  truly disables (failures.md R7; evidence/o4_run.json `frozen=0.0000`
  exact) [verified].
- L6: World clock runs while disabled; resume catches up to live time
  (failures.md R7; evidence/o4_run.json `resumed=20.000`,
  evidence/v9_run.json `resumed=10.000`) [verified].
- L7: One writer per target; duplicates contaminate silently, no warning
  (failures.md R8; R8 sweep in v9_build.py) [verified].
- L8: Author graphs while STOPPED; RemovePrim+recreate during play
  leaves dead connections and `stop()` does not clear the stale instance
  (o4_build.py comment; failures.md R6) [verified].

### UNKNOWN (theoretical)

- U1: Node-level `set_disabled` exists but is untested (failures.md R7)
  [theoretical].
- U2: Rival-writer per-tick mix order is unspecified ("last writer wins
  per tick in an unspecified mix", discovery.md) [theoretical].
- U3: Exact signatures of `create_graph` / `create_node` / `connect`
  (probe_og2.py output not saved) [theoretical].
- U4: Graph/Node method surface beyond `set_disabled`/`is_disabled` /
  `get_attribute` (probe_gobj.py output not saved) [theoretical].
- U5: `GraphEvaluationMode` / `ExecutionAttributeState` /
  `NodeController` / `GraphRegistry` members and semantics
  (probe_gobj.py / probe_og3.py outputs not saved) [theoretical].

## T2. OmniGraph node type set (4 drilled types + probed candidates)

DOES: Tick source, math, and prim-attribute writing inside graphs [verified].

### Functions (type identifiers used in CREATE_NODES; attrs typed)

- `omni.graph.action.OnPlaybackTick` [verified]
  - `outputs:tick: execution` (trigger; unit n/a; fires per played tick;
    o1_build.py:36, o2_build.py:34, o3_build.py:61, o4_build.py:65,
    v9_build.py:68, probe_fresh.py:15) [verified].
  - `outputs:time: double` (playback time in SECONDS; o2_build.py:35 feeds
    it into the `og:stamp` double; o2_run.py:18-21 reports seconds-scale
    stamps) [verified].
- `omni.graph.nodes.Multiply` [verified]
  - `inputs:a: double` (unitless; no default — always connected to
    `outputs:time`, o3_build.py:62, o4_build.py:66, v9_build.py:69,
    probe_fresh.py:16) [verified].
  - `inputs:b: double` (unitless scale; no default — always SET via typed
    3-tuple, o3_build.py:66, o4_build.py:70, v9_build.py:74,
    probe_fresh.py:20) [verified].
  - `outputs:product: double` (`a*b`; o3_build.py:63, o4_build.py:67,
    v9_build.py:70) [verified].
- `omni.graph.nodes.Add` [verified]
  - `inputs:a: double`, `inputs:b: double` (chain units — degrees in V9;
    no defaults: `a` connected from `Mul.outputs:product`, `b` SET via
    typed 3-tuple, v9_build.py:70/75), `outputs:sum: double` (`a+b`;
    v9_build.py:71) [verified]. (Probed attr list adds `node:type*`,
    discovery.md.)
- `omni.graph.nodes.WritePrimAttribute` [verified]
  - `inputs:execIn: execution` (trigger; unit n/a; optional — R5,
    o1_build.py:36) [verified].
  - `inputs:value: template` (resolves to the target attr type at setup;
    `token` pre-resolve per o2_build.py:44 `valuetype=token`; accepts a
    connected double, o2_build.py:35, or a SET tuple, o1_build.py:42; no
    default) [verified].
  - `inputs:primPath: string` (destination prim path, e.g.
    `/World/O2Cube`; no default; o1_build.py:39, o2_build.py:38,
    o3_build.py:67, o4_build.py:71, v9_build.py:76, probe_fresh.py:21)
    [verified].
  - `inputs:name: string` (destination attr name, e.g.
    `drive:angular:physics:targetPosition`; no default; o1_build.py:40,
    o3_build.py:68, v9_build.py:77) [verified].
  - `inputs:usePath: bool` (unit n/a; always SET `True` in drills,
    o1_build.py:41, v9_build.py:78; `False` undrilled) [verified].
  - `state:correctlySetup: bool [probable]` (setup flag; attr name read in
    probe_write.py:5; value type unsaved) [verified name; probable type].
  - `inputs:usdWriteBack: bool [theoretical]` (attr name seen in
    probe_write.py:6; never set or read for effect; type unsaved)
    [verified name; theoretical type].
- Candidate math/vector/const set (existence probed, NOT drilled):
  `Subtract`, `Divide`, `ComposeVector3`, `ConstructVector3`,
  `MakeVector3`, `ConstantDouble` (probe_math.py:5-19 MADE/GHOST/FAIL
  matrix; outputs not saved). Attr names, types, units, defaults all
  [theoretical] [probable].
- Candidate action/registry set (existence probed, NOT drilled):
  `OnTick`, `OnStageEvent`, `Print` (action + nodes), `ConstantInt`,
  `ReadPrimAttribute`, `core.Constant`, `Time` (nodes + action)
  (probe_og4.py:2-13 / probe_og7.py:2-11 / probe_og8.py:5-19; outputs not
  saved). Attr names, types, units, defaults all [theoretical] [probable].
- `Vec` tuple node (`Vec.inputs:x/y/z` in, `Vec.outputs:tuple` out)
  [probable]. Referenced by probe_rtype.py:2 / probe_rtype2.py:2-3 /
  probe_types.py:4 / probe_vals.py:5-7 against an O3Graph iteration; its
  type string (which Compose/Construct/Make spelling, if any), attr
  types, units, and defaults are not recorded in-pack (all [theoretical])
  [probable].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- `Mul.inputs:b: double` (unitless scale; no default — must author; O3/O4
  use 10.0 = 10 deg/s ramp, `dt=10.000` in evidence/o3_run.json,
  o3_build.py:66, o4_build.py:70, probe_fresh.py:20; V9 uses 5.0 = 5
  deg/s pre-offset, v9_build.py:74). Larger b = steeper target ramp
  [verified].
- `Add.inputs:b: double` (chain units = degrees in V9; no default — must
  author; V9 uses 1.0 = constant +1.0 deg, v9_build.py:75) [verified].
- `Write.inputs:primPath: string` (prim path; unit path; no default —
  must author). Selects the destination prim (`/World/O2Cube`,
  `/World/O3Bot/Hinge1`, ...); must match the intended target exactly or
  writes land elsewhere / nowhere [verified].
- `Write.inputs:name: string` (attr name; unit n/a; no default — must
  author). Selects the destination attribute (`xformOp:translate`,
  `og:stamp`, `drive:angular:physics:targetPosition`); single-double
  destinations work, tuple destinations do not configure (R2) [verified].
- `Write.inputs:usePath: bool` (unit n/a; always `True` drilled, e.g.
  o1_build.py:41, v9_build.py:78). `False` undrilled — effect and true
  default unknown [verified drilled value]; true default [theoretical].
- `Write.inputs:value` source: template (resolves to target type; unit =
  target unit — degrees for joint targets, stage length for translate;
  no default). SET-tuple works (O1, o1_build.py:42); connected-DOUBLE
  works (O2/O3/V9, o2_build.py:35); connected-TUPLE computes correctly
  upstream yet the Write never configures (`correctlySetup` false, no
  motion, no log error) (R2 OPEN) [verified].
- `tick -> execIn` wire: `bool` (connection present; unit n/a; drilled
  default present). Present vs cut: no effect on Write firing either way;
  the exec wire is optional (R5) [verified].
- Chain length: `int` (node count; unit nodes; no default). 2-node
  (O1/O2), 3-node (O3/O4), 4-node (V9 exam max) chains drilled; 5+ node
  chains undrilled [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF choosing a Write destination THEN drive a single-double attribute
  (joint target, custom double) BECAUSE connected-tuple writes silently
  never configure (R2 OPEN) [verified].
- IF a Write never configures THEN inspect `state:correctlySetup` on the
  Write prim BECAUSE it stays false for the R2 failure with NO log error
  (probe_write.py reads it) [verified].
- IF a Write must fire per-tick THEN feed it changing upstream DATA, not
  just the exec wire BECAUSE WritePrimAttribute fires on data flow and
  the exec wire is optional (R5) [verified].
- IF the chain needs scale/offset THEN insert Multiply/Add doubles
  (`Mul.inputs:b`, `Add.inputs:b` as typed 3-tuples) BECAUSE the
  all-double chain is the O2/O3/V9-proven pattern [verified].

### LIMITS (live-verified, with cites)

- L1: `WritePrimAttribute` fires on upstream DATA flow; cutting
  tick->execIn does NOT freeze writes (failures.md R5) [verified].
- L2: Connected-TUPLE writes silently never configure (`correctlySetup`
  false, no motion, NO log error); SET-tuple (O1) and connected-DOUBLE
  (O2) work — drive single-double destinations (failures.md R2 OPEN)
  [verified].
- L3: Atomic-vs-split edit order does NOT fix R2 (both fail)
  (failures.md R2) [verified].

### UNKNOWN (theoretical)

- U1: R2 root cause is hypothesis only (setup runs before template
  outputs resolve, never re-runs) (failures.md R2 OPEN) [theoretical].
- U2: Exec-only firing (tick changing while data static) never isolated
  from data-flow firing [theoretical].
- U3: Any node type beyond the drilled 4 (all probe_math/probe_og4/
  probe_og7/probe_og8 candidates lack saved outputs) [theoretical].
- U4: `usePath=False` behavior (never drilled) [theoretical].
- U5: Non-string `primPath` forms (never drilled) [theoretical].
- U6: Chains beyond 4 nodes (V9 exam max) [theoretical].
- U7: Which type string the `Vec` tuple node used (probe-only refs)
  [theoretical].
- U8: `inputs:usdWriteBack` semantics (attr name seen in
  probe_write.py; never set or read for effect) [theoretical].

## T3. omni.usd — stage access + prim management

DOES: Opens the stage, inspects/removes prims, reads back written
attributes in run scripts [verified].

### Functions (params typed, return typed, units, defaults)

- `omni.usd.get_context() -> UsdContext; UsdContext.get_stage() -> pxr.Usd.Stage` [verified]
  - No args, no defaults, unit n/a. Every in-sim script opens the stage
    this way (o1_build.py:11, o1_run.py:10, o2_build.py:11, o2_run.py:9,
    o3_build.py:11, o3_run.py:12, o4_build.py:15, o4_run.py:14,
    v9_build.py:12, v9_run.py:14, all probes) [verified].
- `stage.GetPrimAtPath(path: str) -> pxr.Usd.Prim` [verified]
  - Param `path: str` (prim path; unit path; no default; o1_build.py:21,
    o1_run.py:14, o2_run.py:13, v9_build.py:51, ...). Returns the prim or
    an invalid prim; callers check `.IsValid()` before use (all build
    scripts) [verified].
- `stage.DefinePrim(path: str, typeName: str) -> pxr.Usd.Prim` [verified]
  - Params `path: str` (prim path) and `typeName: str` (USD type name;
    only `"Xform"` drilled); both always passed, no defaults exercised
    (o3_build.py:23, o4_build.py:27, v9_build.py:18) [verified]. Unit n/a.
  - Used only as `DefinePrim("/World/OxBot", "Xform")` (o3/o4/v9 builds)
    [verified].
- `stage.RemovePrim(path: str | Sdf.Path) -> bool` [verified call; probable return]
  - Param `path: str` prim path (o1_build.py:23, all build sweeps) or
    `Sdf.Path` (from `prim.GetPath()`, probe_killdup.py:7); no default.
    Returns `bool` success [probable] (never captured in-pack).
    Deletes prims; used for anonymous rebuild sweeps (all builds),
    R6-recreate, and `probe_killdup.py` rival kills [verified].
- `prim.GetAttribute(name: str) -> pxr.Usd.Attribute` [verified]
  - Param `name: str` (attr name; unit n/a; no default). Used for target
    readback (`og:stamp`, o2_run.py:13-14;
    `drive:...:targetPosition`, o3_run.py:17-18; `inputs:primPath`,
    v9_build.py:54; `inputs:value`, o2_build.py:44;
    `state:correctlySetup`, probe_write.py:5) [verified].
- `attr.Get() -> Any (attr-typed)` [verified]
  - No params. Returns the authored/live value in the attr's own type:
    `float` for doubles (o2_run.py:13-14, o3_run.py:16-18 wrapped in a
    `float` cast; o4_run.py:22-24, v9_run.py:22-24, probe_fresh.py:28-29),
    `str` for primPath (v9_build.py:55 `==` string compare), `bool` for
    flags [probable]. Unit follows the attr [verified].
- `attr.GetTypeName() -> Sdf.ValueTypeName` [verified call; probable class]
  - No params. Returns the type-name object, e.g. `token` for the template
    value attr (o2_build.py:43-44 `valuetype=token` in
    evidence/o2_build.json); pack only ever stringifies it (`str` applied /
    `%s` formatting: probe_math2.py:10, probe_og9.py:8, probe_types.py:9), so the
    exact class is [probable]. Used in probe_math2 / probe_og9 /
    probe_types attr dumps [verified].
- `obj.IsValid() -> bool` [verified]
  - No params. Validity gate on prims and attributes before every
    read/remove (all builds e.g. o1_build.py:22, probe_math2.py:6,
    probe_og9.py:6, v9_build.py:55 R8 sweep) [verified].
- `prim.GetChildren() -> Iterable[pxr.Usd.Prim]` [verified]
  - No params. Iterated for node lists (`sorted(nodes)` in every BUILD-OK
    line, e.g. o1_build.py:46) and the V9 R8 rival sweep over `/World`
    children (v9_build.py:51); wrapped in `list` in probe_og3.py:8
    [verified].
- `prim.GetName() -> str` [verified]
  - No params. Node-name collection and `Graph*` / `O4Graph*` name
    matching (builds e.g. o1_build.py:46, v9 R8 sweep v9_build.py:52,
    probe_killdup.py:5-6) [verified].
- `prim.GetTypeName() -> str` [verified]
  - No params. `Graph`-type check (`== "Graph"`, v9_build.py:52); node
    attr dumps (probe_og3.py:6/11) [verified].
- `prim.GetPath() -> Sdf.Path` [verified call; probable class]
  - No params. Passed to `RemovePrim` in probe_killdup.py:7 [verified];
    exact path-object class [probable].
- `prim.CreateAttribute(name: str, typeName: Sdf.ValueTypeName) -> pxr.Usd.Attribute` [verified]
  - Params `name: str`, `typeName: Sdf.ValueTypeName` (both always passed;
    further optional USD params never passed — defaults [theoretical]).
    Used once: `CreateAttribute("og:stamp", Sdf.ValueTypeNames.Double)`
    (o2_build.py:25) [verified]. Unit n/a.

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Removal sweep path list: `tuple[str, ...]` (unit prim paths; no default
  — per-build literal, e.g. o1_build.py:12-20, o3_build.py:12-20;
  `Sdf.Path` elements also accepted per probe_killdup.py:7). Each build
  removes its own + prior-drill prims (incl. `V8*`/`OGProbe*`/`M4*`
  leftovers and `/World/PhysicsScene`) for anonymous rebuild; omitting a
  stale rival re-triggers R8 contamination [verified].
- `DefinePrim` typeName: `str` (USD type name; unit n/a; no default
  exercised — always passed). Only `"Xform"` drilled (bot roots,
  o3_build.py:23, o4_build.py:27, v9_build.py:18); other type names
  undrilled [verified].
- `CreateAttribute` (name, type): `name: str`,
  `type: Sdf.ValueTypeName` (unit n/a; no defaults exercised). Only
  `("og:stamp", Double)` drilled (o2_build.py:25); the attr then serves
  as a Write target and readback source [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF rebuilding a scene THEN RemovePrim every same-path prim first
  (anonymous rebuild) BECAUSE stale prims/rivals shadow or contaminate
  the new drill (R6/R8) [verified].
- IF reading any prim or attribute THEN check `.IsValid()` first BECAUSE
  missing paths return invalid objects (pack-wide defensive pattern)
  [verified].
- IF hunting rival writers THEN iterate `/World` children filtering
  `GetTypeName() == "Graph"` and compare each node's
  `inputs:primPath` BECAUSE duplicates are silent — the sweep is the
  only detector (v9_build.py R8 sweep) [verified].

### LIMITS (live-verified, with cites)

- L1: `RemovePrim` + recreate at the same graph path leaves a stale
  runtime instance shadowing the new prim (failures.md R6) [verified].
- L2: `stop()` does not clear the stale instance (failures.md R6)
  [verified].

### UNKNOWN (theoretical)

- U1: Whether any stage-level operation other than link re-touch (e.g.
  reload, new layer) clears a stale graph instance [theoretical].

## T4. pxr USD authoring (UsdGeom / UsdPhysics / Gf / Sdf)

DOES: Builds drill scenes: cubes, translate ops, 1R arms (rigid bodies,
joints, limits, position drives), custom attrs [verified].

### Functions (params typed, return typed, units, defaults)

- `UsdGeom.Cube.Define(stage: pxr.Usd.Stage, path: str) -> UsdGeom.Cube` [verified]
  - Both params always passed (o1_build.py:25, o2_build.py:22,
    o3_build.py:24/33, o4_build.py:28/37, v9_build.py:20/29); no defaults
    exercised; unit n/a. Defines drill cubes (`/World/O1Cube`, `/O2Cube`,
    `/OxBot/Base|Link`, `/V9Bot/Base|Link`) [verified].
- `cube.GetSizeAttr() -> pxr.Usd.Attribute; attr.Set(size: float) -> bool` [verified call; probable return]
  - `size: float` (edge length; unit stage length, meters [probable]; no
    default — always passed). Sizes: 1.0 (O1/O2 cubes, o1_build.py:26,
    o2_build.py:23), 0.15 (Base), 0.2 (Link) (o3_build.py:25/34,
    o4_build.py:29/38, v9_build.py:21/30) [verified]. `Set` return never
    captured in-pack (success bool [probable]).
- `UsdGeom.Xformable(prim: pxr.Usd.Prim) -> UsdGeom.Xformable` [verified]
  - Param `prim: Usd.Prim` (always passed; no default; unit n/a).
    Wrapper for translate-op authoring (all builds, e.g. o1_build.py:27,
    v9_build.py:19/22) [verified].
- `xformable.AddTranslateOp() -> UsdGeom.XformOp; op.Set(value: Gf.Vec3d) -> bool` [verified call; probable return]
  - `AddTranslateOp` called with no args (op name/precision defaults never
    exercised — [theoretical]); `value: Gf.Vec3d` (translation; unit stage
    length, meters [probable]; no default). Places cubes/arms; O1 baseline
    `(0, 0, 0.5)` (o1_build.py:27, o2_build.py:24), arm links
    `(0,0,0.2/0.4)` (o3_build.py:26/35), V9Bot offset `(3.0, 0, 0)`
    (v9_build.py:19) [verified]. `Set` return never captured (success
    bool [probable]).
- `xformable.GetOrderedXformOps() -> list[UsdGeom.XformOp]` [verified call; probable element]
  - No params. o1_run.py:15/24 translate readback/reset loop: finds the
    `TypeTranslate` op [verified].
  - `op.GetOpType() -> UsdGeom.XformOp.Type` [verified call; probable class]
    (compared to `UsdGeom.XformOp.TypeTranslate`, o1_run.py:16/25).
  - `op.Get() -> Gf.Vec3d` [verified call; probable class] (translate
    value, unit meters [probable]; indexed `[2]` and converted with `float`,
    o1_run.py:17).
  - `op.Set(value: Gf.Vec3d) -> bool` [verified call; probable return]
    (reset with `op.Set(Gf.Vec3d(0, 0, v))`, o1_run.py:26; return never
    captured).
- `UsdPhysics.Scene.Define(stage: pxr.Usd.Stage, path: str) -> UsdPhysics.Scene` [verified]
  - Both always passed; path always `"/World/PhysicsScene"`; no defaults
    exercised (o3_build.py:22, o4_build.py:26) [verified]. Physics scene
    for the O3/O4 arm drills (V9 reuses the surviving scene — no
    Scene.Define in v9_build.py) [verified]. Unit n/a.
- `UsdPhysics.RigidBodyAPI.Apply(prim: pxr.Usd.Prim) -> UsdPhysics.RigidBodyAPI` [verified call; probable return]
  - Param always passed; no default; unit n/a. Applied to Base and Link
    (o3_build.py:27/36, o4_build.py:31/40, v9_build.py:23/32); return
    never captured (schema object [probable]) [verified].
- `UsdPhysics.MassAPI.Apply(prim: pxr.Usd.Prim) -> UsdPhysics.MassAPI; .GetMassAttr() -> pxr.Usd.Attribute; .Set(mass: float) -> bool` [verified call; probable returns]
  - `mass: float` (unit kg [probable]; no default — always passed): 2.0
    (Base), 0.5 (Link) (o3_build.py:28/37, o4_build.py:32/41,
    v9_build.py:24/33) [verified]. Returns never captured.
- `UsdPhysics.ArticulationRootAPI.Apply(prim: pxr.Usd.Prim) -> UsdPhysics.ArticulationRootAPI` [verified call; probable return]
  - Param always passed (Base prim); no default; unit n/a. Applied to
    Base, making it the articulation root read by the `Articulation` reader (T6)
    (o3_build.py:29, o4_build.py:33, v9_build.py:25); return never
    captured (schema object [probable]) [verified].
- `UsdPhysics.FixedJoint.Define(stage: pxr.Usd.Stage, path: str) -> UsdPhysics.FixedJoint` +
  `CreateBody0Rel() -> pxr.Usd.Relationship` / `CreateBody1Rel() -> pxr.Usd.Relationship` +
  `.SetTargets(targets: list[str]) -> bool` [verified call; probable returns]
  - No-arg `CreateBody*Rel`; `targets: list[str]` (body prim paths; unit
    paths; no default) — roots Base to the bot Xform (o3_build.py:30-32,
    o4_build.py:34-36, v9_build.py:26-28) [verified]. Returns never
    captured (schema/relationship objects [probable]).
- `UsdPhysics.RevoluteJoint.Define(stage: pxr.Usd.Stage, path: str) -> UsdPhysics.RevoluteJoint` +
  `CreateAxisAttr(axis: str) -> pxr.Usd.Attribute` +
  `CreateLocalPos0Attr(pos: Gf.Vec3f) -> pxr.Usd.Attribute` +
  `CreateLocalPos1Attr(pos: Gf.Vec3f) -> pxr.Usd.Attribute` [verified call; probable returns]
  - `axis: str` (unit n/a; no default exercised; drilled `"Y"`,
    o3_build.py:41); `pos: Gf.Vec3f` (unit stage length, meters
    [probable]; no defaults exercised; drilled `(0,0,0.075)` /
    `(0,0,-0.1)`, o3_build.py:42-43, o4_build.py:46-47, v9_build.py:38-39)
    [verified]. The Hinge1 1R joint all motion drills drive
    (o3_build.py:38-43) [verified]. Returns never captured.
- `UsdPhysics.LimitAPI.Apply(prim: pxr.Usd.Prim, name: str) -> UsdPhysics.LimitAPI` +
  `CreateLowAttr(low: float) -> pxr.Usd.Attribute` /
  `CreateHighAttr(high: float) -> pxr.Usd.Attribute` [verified call; probable returns]
  - `name: str` drilled `"rotY"`; `low`/`high: float` in DEGREES (unit
    deg; drilled -170.0 / +170.0, o3_build.py:44-46, o4_build.py:48-50,
    v9_build.py:40-42); no defaults exercised [verified]. Returns never
    captured (schema/attribute objects [probable]).
- `UsdPhysics.DriveAPI.Apply(prim: pxr.Usd.Prim, name: str) -> UsdPhysics.DriveAPI` +
  `CreateTypeAttr(type: str) -> pxr.Usd.Attribute` +
  `CreateTargetPositionAttr() -> pxr.Usd.Attribute` + `.Set(pos: float) -> bool` +
  `CreateStiffnessAttr(k: float) -> pxr.Usd.Attribute` +
  `CreateDampingAttr(c: float) -> pxr.Usd.Attribute` [verified call; probable returns]
  - `name: str` drilled `"angular"`; `type: str` drilled `"position"`;
    `pos: float` in DEGREES (unit deg; initial `0.0`, o3_build.py:49);
    `k: float` drilled 100.0 (unit [theoretical]); `c: float` drilled 10.0
    (unit [theoretical]); no defaults exercised (o3_build.py:47-51,
    o4_build.py:51-55, v9_build.py:43-47) [verified]. The position drive
    whose `drive:angular:physics:targetPosition` is the graph Write target
    [verified]. Returns never captured (except the target attr, for `.Set`).
- `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` / `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` [verified]
  - All three `float` components always passed (ints never passed); no
    defaults exercised; unit follows use (meters for translates/local-pos).
    Double vs float vectors for translate ops (o1_build.py:27) vs joint
    local positions (o3_build.py:42-43) [verified].
- `Sdf.ValueTypeNames.Double` — type token of type `Sdf.ValueTypeName`
  (unit n/a; no params; exact class [probable]) for the `og:stamp` custom
  attribute (o2_build.py:25) [verified].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Cube size: `float` (UsdGeom `size`; unit stage length, meters [probable];
  no default — always `Set`: 1.0 / 0.15 / 0.2, o1_build.py:26,
  o3_build.py:25/34). Visual/collision scale only; no graph semantics
  depend on it [verified].
- Translate placement: `Gf.Vec3d` (unit meters [probable]; no default —
  always authored: `(0,0,0.5)` cubes, `(0,0,0.2/0.4)` arm links, `(3,0,0)`
  V9Bot, v9_build.py:19). V9 offset proves scene-independence of the
  graph pattern [verified].
- Mass: `float` (MassAPI `mass`; unit kg [probable]; no default — always
  `Set`: 2.0 Base / 0.5 Link, o3_build.py:28/37). Physics follow dynamics
  only [verified].
- Joint axis: `str` (RevoluteJoint `axis`; unit n/a; no default exercised
  — always `"Y"`, o3_build.py:41). Only Y drilled [verified].
- Joint local positions: `Gf.Vec3f` (`localPos0/1`; unit meters [probable];
  no defaults exercised: 0.075 / -0.1 z, o3_build.py:42-43). Arm geometry
  only [verified].
- Joint limits: `float` (`low`/`high`; unit DEGREES; no defaults exercised:
  -170 / +170, o3_build.py:45-46). Bounds of legal rotation; ramps that
  exceed them would saturate (ramps here stay small) [probable].
- Drive type: `str` (`type`; unit n/a; no default exercised — always
  `"position"`, o3_build.py:48). Only position drilled [verified].
- Drive stiffness / damping: `float` / `float` (unit [theoretical] for both;
  no defaults exercised: 100.0 / 10.0, o3_build.py:50-51, fixed across
  O3/O4/V9). Follow responsiveness [verified].
- Drive targetPosition: `float` (unit DEGREES; initial `0.0` via `.Set(0.0)`,
  o3_build.py:49). THE graph-written knob: time x scale (+ offset) lands
  here each tick; joint follows in radians [verified].
- Custom attr type: `Sdf.ValueTypeName` (unit n/a; no default — always
  passed). Only `Double` for `og:stamp` drilled (o2_build.py:25)
  [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF building a graph-driven joint THEN copy the O3 1R pattern
  (Xform root, FixedJoint, Base + ArticulationRoot, RevoluteJoint Y,
  rotY limits, angular position drive) BECAUSE it is the O3/O4/V9-proven
  rig [verified].
- IF setting drive targets from a graph THEN write DEGREES BECAUSE
  `targetPosition` is degrees while `get_dof_positions` reads RADIANS
  (discovery.md session notes) [verified].
- IF placing a drill scene THEN offset it from prior drills (V9Bot at
  x=+3) BECAUSE a fresh pose proves the pattern is scene-independent
  [verified].

### LIMITS (live-verified, with cites)

- L1: Joint drive `targetPosition` is written in DEGREES while
  `get_dof_positions` reads RADIANS (discovery.md session notes;
  verify_v9.py converts `t3 * pi / 180`) [verified].

### UNKNOWN (theoretical)

- U1: Non-position drive types under graph control (never drilled)
  [theoretical].
- U2: Multi-DOF arms under graph control (only 1R drilled)
  [theoretical].

## T5. isaacsim app transport (`app_utils`)

DOES: Timeline control and stepped execution around graph runs [verified].

### Functions (params typed, return typed, units, defaults)

- `app_utils.stop() -> None` [verified]
  - No params. Stops the timeline; called before builds (o4_build.py:13
    R6 note, probe_fresh.py:5) and at run starts (o3_run.py:22,
    o4_run.py:27, v9_run.py:34) [verified].
- `app_utils.play(commit: bool) -> None` [verified call; theoretical default]
  - Param `commit: bool` (unit n/a; always passed as `commit=True` —
    o1_run.py:32, o2_run.py:17, o3_run.py:24, o4_run.py:29, v9_run.py:36,
    probe_fresh.py:26, probe_vals.py:3; the default is never exercised,
    so its value is [theoretical]). Starts/resumes the timeline so ticks
    execute. `commit=False` never drilled [verified].
- `await app_utils.update_app_async(steps: int) -> None` [verified]
  - Param `steps: int` (unit app steps [probable] — steps-to-seconds
    uncalibrated; always passed, so default [theoretical]). Async; MUST
    be awaited. Steps drilled: 5 (probe_fresh.py:6 settle), 10 (settle
    after stop: o3_run.py:23, o4_run.py:28, v9_run.py:35, probe_vals.py:4),
    30 (live windows: o2_run.py:18, o3_run.py:34, o4_run.py:34, v9_run.py:39,
    probe_fresh.py:27), 60 (freeze/resume windows: o1_run.py:33,
    o2_run.py:20, o3_run.py:36, o4_run.py:39/43, v9_run.py:44/48) [verified].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- `steps: int` (unit app steps [probable]; no default exercised — always
  passed: 5 / 10 / 30 / 60). 10 = settle after stop/play; 30 =
  live-measurement window (`t1=5.0` O4, `t1=3.5` V9); 60 =
  freeze/resume windows (`frozen`, `resumed` deltas). Larger N = longer
  sim window, but steps-to-seconds is uncalibrated [verified].
- `commit: bool` (unit n/a; always `True` drilled, e.g. o1_run.py:32;
  default [theoretical]). Only value drilled; starts play so ticks fire
  [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF a build ran during play THEN stop + settle (10 steps) + play before
  trusted reads BECAUSE stop/play re-parses physics (o3_run.py Skill 5
  R3 note) [verified].
- IF authoring a graph THEN `stop()` first BECAUSE builds during play
  leave connections dead (o4_build.py R6 note) [verified].
- IF measuring freeze/resume THEN use asymmetric windows (30 live, 60
  off, 60 on) BECAUSE the O4/V9 gates (`frozen=0`, `resumed=20/10`)
  assume that exact shape [verified].

### LIMITS (live-verified, with cites)

- L1: Stop/play re-parses physics; builds that ran during play need a
  stop/play cycle before trusted reads (o3_run.py Skill 5 R3 note)
  [verified].
- L2: Author graphs while STOPPED (o4_build.py R6 note) [verified].

### UNKNOWN (theoretical)

- U1: `update_app_async` steps-to-sim-seconds mapping is uncalibrated;
  timing gates (`t1=5.0/3.5`) are framerate-dependent, not a clock
  [theoretical].

## T6. Articulation joint readout (`isaacsim.core.experimental.prims`)

DOES: Reads live joint positions to prove tick-driven motion [verified].

### Functions (params typed, return typed, units, defaults)

- `Articulation(root_path: str) -> Articulation` [verified]
  - Param `root_path: str` (unit prim path; no default — always passed)
    is the articulation ROOT prim (`/World/O3Bot/Base`,
    `/World/V9Bot/Base` — the prim with ArticulationRootAPI), NOT the
    joint path (o3_run.py:28, v9_run.py:28) [verified]. Further
    constructor params (if any) never passed — [theoretical].
- `art.get_dof_positions() -> wp.array | np.ndarray` [verified]
  - No params. Returns DOF positions in RADIANS (unit rad); callers
    defensively branch on `isinstance(q, wp.array)` before `.numpy()`
    (o3_run.py:29-31, v9_run.py:29-31), so both return types are live
    possibilities [verified].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Root path: `str` (unit prim path; no default — must pass the
  ArticulationRoot prim, o3_run.py:28, v9_run.py:28). Must be the
  ArticulationRoot prim; a non-root path has unspecified behavior
  (never tried) [verified].
- Read timing: `int` steps (unit app steps [probable]; drilled after 30 /
  +60 steps, o3_run.py:34-37, v9_run.py:39-49; no default). q1 (early) vs
  q2/q3 (late) prove following: O3 `dq=0.1624`, V9 `q3-q1>0.05`
  (evidence/o3_run.json, evidence/v9_run.json) [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF reading joint state THEN construct `Articulation` on the ROOT prim
  (Base), never the joint BECAUSE the drilled pattern roots there
  (o3_run.py, v9_run.py) [verified].
- IF converting the readout THEN branch on `isinstance(q, wp.array)`
  BECAUSE the return type is version-unstable (`wp.array` vs other)
  [verified].
- IF asserting follow-through THEN require same-direction delta
  (`dq > 0.05` rad) and V9-style absolute tracking
  (`|q3 - t3*pi/180| < 0.15`) BECAUSE target-following is the O3/V9 gate
  [verified].

### LIMITS (live-verified, with cites)

- L1: Returns RADIANS; joint targets are DEGREES (discovery.md;
  evidence/o3_run.json `t1=5.000` deg vs `q1=0.0804` rad) [verified].
- L2: O3 gate is target delta ~10 deg with q following (`dq > 0.05`
  rad, same direction); V9 `q1=0.0516 q3=0.2261` (README dataset;
  evidence/v9_run.json) [verified].

### UNKNOWN (theoretical)

- U1: Return-type stability (`wp.array` vs other) across versions —
  callers defensively branch [theoretical].

## T7. numpy + warp readout conversion

DOES: Converts DOF readouts to plain floats for report lines [verified].

### Functions (params typed, return typed, units, defaults)

- `isinstance(q: Any, wp.array: type) -> bool` [verified] — return-type
  branch (o3_run.py:31, v9_run.py:31). `q` is the `get_dof_positions()`
  result (unit rad); `wp.array` is the warp array class [verified].
- `q.numpy() -> np.ndarray` [verified call; probable class] — warp-to-numpy
  hop, no params, taken only in the `wp.array` branch (o3_run.py:31,
  v9_run.py:31). Exact return class [probable] (immediately normalized by
  `np.asarray`). Unit rad preserved.
- `np.asarray(a: array_like) -> np.ndarray` [verified] — normalizes either
  branch to ndarray (o3_run.py:30-31, v9_run.py:30-31). Param `a` is
  `wp.array | np.ndarray` (no default); unit rad preserved [verified].
- `ndarray.flatten() -> np.ndarray; [index: int] -> np.float64` [verified call; probable scalar]
  — selects the FIRST (only) DOF of the 1R arm (`flatten()[0]`,
  o3_run.py:31, v9_run.py:31). Index `0: int` (unit index) [verified];
  exact scalar class [probable].
- `float(x: Any) -> float` [verified] — plain float (unit rad) for `%.4f`
  report formatting (o3_run.py:30, v9_run.py:30) [verified].
- Full chain (one expression):
  `float(np.asarray(q.numpy() if isinstance(q, wp.array) else q).flatten()[0])`
  `(q: wp.array | np.ndarray) -> float` (unit rad) [verified]
  (o3_run.py:30-31, v9_run.py:30-31).

### Knobs (every knob + attr type + unit + default + effect-of-change)

- DOF index: `int` (`[0]`; unit index; drilled 0). Only index 0 drilled
  (1R arms, o3_run.py:31, v9_run.py:31); multi-DOF indexing undrilled
  [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF formatting a DOF readout THEN use the full chain (branch, asarray,
  flatten, [0], float) BECAUSE it tolerates both return types and yields
  a plain float for report lines [verified].

### LIMITS (live-verified, with cites)

- L1: numpy space-padded floats need tolerant regex in verifiers
  (discovery.md session notes) [verified].

### UNKNOWN

- None beyond the regex note [verified].

## T8. Local verify evaluators (`verify_*.py`)

DOES: Offline pass/fail grading of build/run report lines; grading is by
STDOUT text (`O1-PASS`), NOT by exit code — the scripts never call
`sys.exit`, so the process exits 0 even on FAIL [verified].

### Functions (params typed, return typed, units, defaults)

- `open(path: str, mode: str = "r" [theoretical]) -> TextIO; json.load(fp: TextIO) -> dict[str, Any]; ["output"] -> str` [verified]
  - `json.load(open("action-reasoner/skills/omnigraph/evidence/<name>.json"))["output"]`
    loads the bridge-envelope `output` string; `<name>` is `o1_build`,
    `o1_run`, etc. (all five verifiers, e.g. verify_o1.py:4-5,
    verify_v9.py:4-5) [verified]. `open` mode never passed (default
    [theoretical]); envelope keys `output: str`, `status: str`,
    `result: None`. Units n/a.
- `re.search(pattern: str, string: str) -> Match | None` via helper
  `f(pat: str, s: str, i: int = 1) -> float` [verified] — `f` params
  `pat: str` (regex), `s: str` (report text), `i: int = 1` (group index;
  default 1 [verified] in `def f(pat, s, i=1)`, verify_o1.py:7; never
  overridden). Returns `float(m.group(i))` on match, `float("nan")` on
  MISS (so a missing field fails numeric gates via nan comparisons)
  (verify_o1.py:7-9, same shape in all five verifiers) [verified].
- `checks: dict[str, bool]` + `all(checks.values()) -> bool` [verified] —
  gate table (`checks = {}`, e.g. verify_o1.py:11); `ok` decides the
  final line (`ok = all(checks.values())`, verify_o1.py:18) [verified].
- `print(*objects: str) -> None` per gate + final
  `print("O1-" + ("PASS" if ok else "FAIL"))` [verified] — per-gate
  (`print(("PASS " if v else "FAIL ") + k)`, verify_o1.py:20) and suite
  verdict lines (O1 5 gates, O2 4, O3 4, O4 8, V9 10;
  verify_o1.py:21 ... verify_v9.py:31) [verified]. `print` sep/end never
  overridden (defaults [theoretical]).
- `math` (verify_v9 only): `t3: float` (degrees) `* math.pi: float / 180.0`
  `-> float` (radians) degrees-to-radians conversion for the q-tracks gate
  (verify_v9.py:22-24) [verified].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Substring gates: `str` tokens (`graph=True`, node names, `linked=True`,
  `rivals=[]`, `dis=True`, `en=False`; unit n/a; exact-match, no
  tolerance). A renamed node or extra rival flips the gate [verified].
- Float-tolerance gates: `float` thresholds (unit = gated field's unit —
  deg for t/dt/resumed, rad for dq/q, stage-length for z, seconds for s;
  drilled per-gate, no shared default): O1 `1e-6` (z exact,
  verify_o1.py:14-16); O4/V9 frozen `1e-9` (freeze must be EXACT,
  verify_o4.py:16, verify_v9.py:20); O3 `dt~10 +/-1.5`, `dq>0.05`
  (verify_o3.py:14-15); O4 `resumed~20 +/-1.5` (verify_o4.py:17); V9
  `t1~3.5 +/-1.0`, catch-up `~10 +/-1.5`,
  `|q3 - t3*pi/180| < 0.15`, `q3-q1 > 0.05` (verify_v9.py:19-24).
  Tightening rejects framerate drift; loosening hides real stalls
  [verified].
- Missing-field semantics: `f()` returns `float("nan")` (unit n/a; no
  default to tune — hardcoded, verify_o1.py:9), and every numeric
  comparison with nan is False — a missing report field FAILs its gate
  instead of crashing the verifier [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF grading a drill THEN match the verifier's gate SHAPE (report field
  names, substring tokens, tolerances) BECAUSE grading is exact-text
  matching on the `output` string [verified].
- IF a gate uses `f()` THEN ensure the report line always prints the
  field BECAUSE a missing field yields nan and FAILs silently (no
  exception) [verified].
- IF asserting a freeze THEN require `frozen == 0` within `1e-9`
  BECAUSE the O4/V9 freeze is bit-exact (`frozen=0.0000`), and anything
  looser could hide rival-writer contamination (R8) [verified].

### LIMITS (live-verified, with cites)

- L1: Regexes must tolerate numpy space-padded floats (discovery.md)
  [verified].
- L2: Suite is O1 O2 O3 O4 V9 (5/5 green) + X9 co-val 11/11 claim
  (README) [verified].
- L3: Grading signal is stdout text, not exit code: no verifier calls
  `sys.exit`, so a FAIL still exits 0 — callers must grep the verdict
  line (all five verify_*.py fully read) [verified].

### UNKNOWN (theoretical)

- U1: `verify_x9.py` is referenced (README) but absent from this pack's
  scripts/ — its gates are unverifiable here [theoretical].

## T9. isaacsim_send.py bridge (in-sim delivery)

DOES: Ships `oN_build` / `oN_run` / `v9_build` / `v9_run` / `probe_*`
into the running sim and returns stdout/stderr report lines, persisted
as evidence/*.json envelopes [verified].

### Functions (params typed, return typed, units, defaults)

- Bridge invocation: external CLI `isaacsim_send.py` (argv: script path
  `str` + flags [theoretical] — no CLI string appears in-pack) per README
  ("in-sim via isaacsim_send.py") [verified]. No direct calls inside pack
  scripts; the pack assumes an external sender [verified]. Params, units,
  and defaults all [theoretical].
- Evidence envelope: `dict[str, Any]` with `status: str` (`"ok"`),
  `output: str` (report line), `result: None` (`null`) [verified] — all
  10 evidence/*.json files share this exact shape (`status`, `output`,
  `result`) [verified]. Units n/a; no defaults.

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Which script is sent: `str` (script path; unit n/a; no default). Build
  scripts author stage+graph; run scripts measure; probes interrogate;
  verifiers run LOCALLY (never sent) [verified].
- Send order: ordered `list[str]` (unit sequence; fixed drilled order =
  build BEFORE run). Runs assume the build's stage exists; re-sending
  build anonymously rebuilds (RemovePrim sweeps) [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF running a drill THEN send build first, then run, then grade locally
  BECAUSE runs read build-authored stage state and verifiers read
  run-produced evidence files [verified].
- IF the sim crashes THEN relaunch windowed + bridge-poll and re-send
  BECAUSE scripts rebuild the stage anonymously and evidence on disk is
  never lost (discovery.md session notes) [verified].

### LIMITS (live-verified, with cites)

- L1: Sim crashed 4x during this arc (render/lidar/bridge-reset);
  recovery is relaunch windowed + bridge poll; scripts rebuild the
  stage anonymously and evidence on disk is never lost (discovery.md
  session notes) [verified].

### UNKNOWN (theoretical)

- U1: Bridge CLI flags/timeout behavior are not documented in-pack
  [theoretical].

## T10. inspect stdlib (docstring probe)

DOES: Reads live `Controller.edit` docstrings to pin calling conventions
(Skill 6 R3 rule) [verified].

### Functions (params typed, return typed, units, defaults)

- `inspect.signature(obj: Callable) -> inspect.Signature` [verified] —
  param `obj` is the target callable (no default; unit n/a); applied to
  `og.Controller.create_graph`, `create_node`, `connect` in
  probe_og2.py:3-5 (stringified via `str`) [verified].
- `og.Controller.edit.__doc__: str` + slicing `[start: int, stop: int] -> str` [verified]
  — the docstring `str` printed in windows `[:1500]` (probe_og5.py:2),
  `[1500:4500]` (probe_og6.py:2), `[4500:8500]` (probe_og10.py:2)
  [verified]. Slice bounds `int` (unit chars); the `str` wrap guards
  a `None` docstring [verified].

### Knobs (every knob + attr type + unit + default + effect-of-change)

- Docstring slice window: `tuple[int, int]` (`(start, stop)` char offsets;
  unit chars; no default — three fixed windows cover `[0:8500)` of the
  edit docstring across three probes, probe_og5.py:2 / probe_og6.py:2 /
  probe_og10.py:2). Content beyond 8500 chars is never printed [verified].

### EKB rules (IF / THEN / BECAUSE)

- IF pinning a calling convention THEN probe the live docstring in-sim
  (`inspect` + `__doc__` slices) BECAUSE installed signatures are the
  ground truth (discovery.md Skill 6 R3 rule) [verified].

### LIMITS (live-verified, with cites)

- L1: Docstring probing is pack procedure alongside node introspection
  (discovery.md) [verified].

### UNKNOWN (theoretical)

- U1: Node `.ogn/.cpp` + Kit-log probing is prescribed by discovery.md
  but no pack script reads `.ogn/.cpp` files or the Kit log (no such
  imports) — that half is unverified in-pack [theoretical].

## Coverage counts

- Tools: 10 (T1-T10, all of TOOLS.md) [verified].
- Function entries: 74 (T1:19, T2:7, T3:13, T4:15, T5:3, T6:2, T7:6,
  T8:5, T9:2, T10:2) [verified].
- Knobs: 40 (T1:8, T2:8, T3:3, T4:10, T5:2, T6:2, T7:1, T8:3, T9:2,
  T10:1) [verified].
- EKB rules: 32 (T1:9, T2:4, T3:3, T4:3, T5:3, T6:3, T7:1, T8:3, T9:2,
  T10:1) [verified].
- LIMITS: 24 (T1:8, T2:3, T3:2, T4:1, T5:2, T6:2, T7:1, T8:3, T9:1,
  T10:1) [verified].
- UNKNOWN: 21 (T1:5, T2:8, T3:1, T4:2, T5:1, T6:1, T7:0, T8:1, T9:1,
  T10:1) [verified].
- Signatures typed: 74/74 (DATATYPE pass 2026-11-04) — every entry
  carries param types, return type, units, and defaults; zero ellipsis
  signatures or bare params remain [verified].
- Knobs typed: 40/40 (DATATYPE pass 2026-11-04) — every knob carries
  attr type, unit, and default [verified].
- Still-unknown: 38 signature bullets + 10 knob bullets carry
  [probable]/[theoretical] type details (44 [probable] + 24 [theoretical]
  markers) for lack of a pack call site or saved output [verified].

## Sources-read

Fully read (24): TOOLS.md, README.md (no SKILL.md in pack), failures.md,
discovery.md, o1_build.py, o1_run.py, o2_build.py, o2_run.py, o3_build.py,
o3_run.py, o4_build.py, o4_run.py, v9_build.py, v9_run.py, verify_o1.py,
verify_o2.py, verify_o3.py, verify_o4.py, verify_v9.py, probe_og2.py,
probe_disconn.py, probe_enable.py, probe_fresh.py, probe_write.py, plus
all 10 evidence/*.json envelopes.
Skimmed (17 probes): probe_gobj, probe_killdup, probe_math, probe_math2,
probe_og, probe_og10, probe_og3, probe_og4, probe_og5, probe_og6,
probe_og7, probe_og8, probe_og9, probe_rtype, probe_rtype2, probe_types,
probe_vals (full text scanned once for API surface; outputs unsaved).
