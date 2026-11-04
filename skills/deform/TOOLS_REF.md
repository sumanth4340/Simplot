# Deform TOOLS_REF — exhaustive tool reference (2026-11-04)

15 tools · 61 functions/accessors · 33 knobs · 21 limits · 19 unknowns
(14 per-tool U-tags + 5 cross-tool unverified).
DATATYPE pass (2026-11-04): 61/61 signatures typed · 33/33 knobs typed ·
16 still-unknown ([theoretical] type slots, upstream-default unknowns excluded:
T1.1 upstream params, T1.7 return, T1.9 element detail, T3.5 return, T4.1
other params, T5.1 return, T7.1/T7.2 extra params, T8.2/T8.3/T8.5/T8.6/T8.7
Set returns, T9.4 RemovePrim return, T11.1 full sig, T13.1 invocation).
Sources: SKILL.md, TOOLS.md, failures.md (all full); scripts d1_build.py,
d1_drive.py, d1_probe.py, d1_diag.py, verify_d1.py (all full, 5/5 scripts);
evidence/d1_nodes.json (full, context). No discovery.md exists in this pack.
Claim tags: [verified] = live-observed in pack evidence/scripts;
[probable] = strongly implied by pack text/code but not directly executed;
[theoretical] = inferred/general knowledge, NOT pack-proven.

---

## T1. DeformablePrim (isaacsim.core.experimental.prims)

DOES: authors a volume-deformable body on an Xform prim (cooks sim +
collision meshes at construction) and exposes nodal tensor reads
(positions, velocities, stresses, tet connectivity) [verified].

### Functions (9 callables + 2 attributes) — 11/11 typed

1. `DeformablePrim(path, deformable_type="volume")` [verified as observed]
   - SIG: `DeformablePrim(path: str, deformable_type: str = "volume" [probable-default]) -> DeformablePrim` [verified-params]
   - Call sites: d1_build.py:34, d1_drive.py:16, d1_probe.py:36, d1_diag.py:17 — all pass `path` positional + `deformable_type` keyword. Units: n/a (Sdf path string / enum-like string).
   - Params observed: `path: str` positional ("/World/D1Soft");
     `deformable_type: str` keyword, always `"volume"` in pack.
   - Defaults: `"volume"` is the value passed, not a proven upstream
     default [probable that it is also the upstream default; theoretical].
   - Returns: DeformablePrim handle. SIDE EFFECT: cooks deformable meshes
     via PhysX cooking interface (`cook_auto_deformable_body`, F1) [verified].
   - Unobserved params: full upstream signature unread (no in-pack
     introspection beyond dir() filter for nodal/elem/pos/stress names)
     [theoretical].
2. `apply_physics_materials(material)` [verified]
   - SIG: `apply_physics_materials(material: VolumeDeformableMaterial) -> None [probable-return]` [verified-params]
   - Call sites: d1_build.py:38, d1_probe.py:40 (required positional, no default). Units: n/a.
   - Params: `material` = VolumeDeformableMaterial instance (d1_build,
     d1_probe). Returns: None observed (return unused) [verified].
3. `get_nodal_positions()` [verified]
   - SIG: `get_nodal_positions() -> tuple[Tensor, Tensor, Tensor]` = (sim, collision, rest); each `(nBodies: int, nNodes: int, 3)` float tensor, unit m [probable-unit], warp/CUDA-backed with `.numpy()` [verified-shape/call]
   - Call sites: d1_drive.py:20 (`[0]`, `.numpy()`, `[0]`), d1_probe.py:55 (generic loop), d1_diag.py:33 (`len(p)` == 3).
   - Params: none. Returns: 3-TUPLE `(sim, collision, rest)`, each
     `(N_bodies, N_nodes_per_body, 3)` warp/CUDA-backed tensor with
     `.numpy()` (d1_drive `sim_pos()` unpacks `[0]`, `.numpy()`, `[0]`) [verified].
4. `get_nodal_velocities()` [verified]
   - SIG: `get_nodal_velocities() -> Tensor`, single (not tuple), `(nBodies: int, nNodes: int, 3)` float, unit m/s [probable-unit], with `.numpy()` [verified-shape/call]
   - Call sites: d1_drive.py:25 (`.numpy()`, `[0]`), d1_probe.py:55 (loop; name not in its probe list — positions/elements/stresses only, so velocities grounded in d1_drive only).
   - Params: none. Returns: SINGLE array (not tuple),
     `(N_bodies, N_nodes, 3)` with `.numpy()` (d1_drive `sim_vel()`) [verified].
5. `get_nodal_stresses()` [verified]
   - SIG: `get_nodal_stresses() -> Tensor`, single, observed `(1, 2544, 3, 3)` float (per-tet 3x3), unit Pa [probable-unit], with `.numpy()` [verified-shape/call]
   - Call sites: d1_drive.py:53 (`.numpy()`, shape/mean/max), d1_probe.py:48 (probe-list name).
   - Params: none. Returns: SINGLE array, observed shape `[1, 2544, 3, 3]`
     (per-tet 3x3 stress), `.numpy()`-able (d1_drive; evidence) [verified].
6. `get_element_indices()` [verified]
   - SIG: `get_element_indices() -> tuple` (len 3, sim/collision/rest [probable-slots]); `[0]` = sim-mesh tets, observed `(1, 2544, 4)` int [probable-dtype], `.numpy()` OPTIONAL (guard with hasattr) [verified-shape/call]
   - Call sites: d1_drive.py:59-60 (`[0]`, hasattr-numpy guard), d1_probe.py:48 (probe-list name).
   - Params: none. Returns: 3-TUPLE; `[0]` is sim-mesh tets, observed
     shape `[1, 2544, 4]`; element may lack `.numpy()` (d1_drive guards
     with hasattr) [verified].
7. `get_world_poses()` [probable-exists]
   - SIG: `get_world_poses() -> Unknown [theoretical]` — existence probed, return NEVER observed (no recorded output) [theoretical].
   - Call sites: d1_probe.py:49 (probe-list name), d1_probe.py:55 (`fn()` generic call) — but NO result recorded in evidence/.
   - Probed in d1_probe.py via getattr loop, but NO result recorded in
     evidence/ (probe crashed at F1 Newton cook before reads, or output
     unrecorded) [verified that it was probed; theoretical return shape].
8. `is_physics_tensor_entity_valid()` [verified]
   - SIG: `is_physics_tensor_entity_valid() -> bool` [verified]
   - Call sites: d1_diag.py:22 (printed as `tensor-entity-valid:`). Units: n/a.
   - Params: none. Returns: bool — tensor-entity binding state (d1_diag).
     NOTE: can read valid while backend reads still fail (F3: views valid,
     reads raised for 120+ steps) [verified].
9. `view.get_simulation_nodal_positions()` on
   `d._physics_deformable_body_view` [verified]
   - SIG: `view.get_simulation_nodal_positions() -> Tensor [probable-type] with .shape [verified-access]; element dtype/units [theoretical]`; raises Exception(`Failed to get ... from backend`) when backend unbound [verified]
   - Call sites: d1_diag.py:28-29 (only `.shape` read via `tuple(r.shape)`).
   - Low-level view read used only in d1_diag; raises `Failed to get ...
     from backend` when backend unbound (F3) [verified].
10. Attribute `.valid` [verified] — prim validity bool (d1_diag prints
    `prim-valid:`) [verified].
    - TYPE: `.valid: bool` [verified] (d1_diag.py:18). Units: n/a. No default (read-only state).
11. Attribute `._physics_deformable_body_view` [verified] — underlying
    deformable-body view or None; private (leading underscore) [verified].
    - TYPE: `._physics_deformable_body_view: DeformableBodyView [probable-name] | None` [verified-None-check] (d1_diag.py:23 `is None`, d1_diag.py:28 method call on it). Units: n/a.

### Knobs (2) — 2/2 typed

- K1 `path`: TYPE `str` (Sdf prim path), unit n/a, default none (required positional) [verified] (d1_build.py:34). Which Xform hosts the body. Effect: must match the Xform
  created by stage_utils + cooking Mesh child; mismatch = invalid/cooks
  wrong prim [probable].
- K2 `deformable_type`: TYPE `str` (enum-like {"volume" [verified], "surface" (unexercised)}), unit n/a, default `"volume"` [probable] (always passed; upstream unproven). `"volume"` drill-proven [verified]; `"surface"`
  never exercised — behavior unknown (TOOLS.md UNKNOWN) [theoretical].

### EKB rules

- IF authoring a DeformablePrim THEN assert PhysX is the active engine
  first BECAUSE cooking goes through the PhysX cooking interface whose
  stage handle is NULL under Newton → native fatal, no traceback (F1)
  [verified].
- IF any getter returns a tuple THEN unpack `[0]` (sim mesh) then `[0]`
  (first body) BECAUSE positions/elements return (sim, collision, rest)
  while velocities/stresses return single arrays; `.numpy()` on a tuple
  raises AttributeError (F4) [verified].
- IF first tensor read fails after play() THEN retry across warmup steps
  (12×10 pattern) BECAUSE backend buffers populate only after real
  post-play physics steps (F3/F4) [verified].
- IF the scene changed (new PhysicsScene, re-author) THEN rebuild the
  DeformablePrim AFTER the change BECAUSE the tensor backend binds at
  authoring time against the scene/device state (F3, SKILL.md recipe)
  [verified].
- IF diagnosing empty reads THEN check the full chain (prim valid →
  tensor-entity valid → view not None → sim-view valid → view read →
  getter read) BECAUSE F3 proved upper layers can be valid while the
  backend is unbound (d1_diag) [verified].

### LIMITS (with cites)

- L1. Cooking FATALS natively (connection reset, no traceback) when PhysX
  is not the active engine (failures.md F1) [verified].
- L2. Tensor backend NEVER binds without explicit `/World/PhysicsScene`;
  reads raise "Failed to get ... from backend" even with valid views
  (failures.md F3) [verified].
- L3. Position/element getters return tuples, not arrays; `.numpy()` on
  the tuple raises AttributeError (failures.md F4) [verified].
- L4. Backend buffers need real post-play physics steps; first read after
  5 steps raises (failures.md F4) [verified].
- L5. Must rebuild the deformable AFTER any scene change (SKILL.md
  authoring recipe; failures.md F3) [verified].

### UNKNOWN (theoretical)

- U1. `deformable_type="surface"` behavior — drill uses volume only
  [theoretical].
- U2. `get_world_poses()` return shape/values on a deformable — probed,
  no result recorded [theoretical].

---

## T2. VolumeDeformableMaterial (isaacsim.core.experimental.materials)

DOES: defines stiffness/friction response of the volume body [verified].

### Functions (1) — 1/1 typed

1. `VolumeDeformableMaterial(path, youngs_moduli=[...],
   poissons_ratios=[...], dynamic_frictions=[...],
   static_frictions=[...])` [verified as observed]
   - SIG: `VolumeDeformableMaterial(path: str, youngs_moduli: list[float], poissons_ratios: list[float], dynamic_frictions: list[float], static_frictions: list[float]) -> VolumeDeformableMaterial` [verified-params; upstream defaults [theoretical]]
   - Call sites: d1_build.py:35-37 (path positional + 4 keyword lists), d1_probe.py:37-39 (same shape). Units: path n/a; youngs_moduli Pa [verified-use]; poissons/dyn/stat dimensionless [probable-unit].
   - Params observed: `path: str` ("/World/D1Mat"); four single-element
     float lists. Drill values: E=[1e5] (d1_build), E=[1e4] (d1_probe);
     poisson=[0.3]; dyn/stat friction=[0.5] [verified].
   - Defaults: none observed — every call passes all four lists
     [theoretical whether upstream has defaults].
   - Returns: material handle passed to `apply_physics_materials` [verified].
   - Multi-element lists (per-body values?) never tried [theoretical].

### Knobs (5) — 5/5 typed

- K1 `path`: TYPE `str` (Sdf prim path), unit n/a, default none (required positional) [verified] (d1_build.py:35). Material prim path [verified].
- K2 `youngs_moduli`: TYPE `list[float]`, unit Pa, default none observed — drill passes [1e5] (d1_build.py:36) / [1e4] (d1_probe.py:38) [verified]. Stiffness E. Effect-of-change: 1 m cone at E=1e4 Pa
  is jelly (self-weight ≈ E, sinks 1/3 under ground, zmin −0.33); E=1e6 Pa
  effectively rigid (zero squash, h 1.000→0.999); E=1e5 sweet spot (rest
  zmin −0.040, height −1.4%, spread +1.2%, live stress) (F5) [verified].
- K3 `poissons_ratios`: TYPE `list[float]`, unit dimensionless [probable], default none observed — drill [0.3] [verified] (d1_build.py:36). Only 0.3 drill-proven; sensitivity unknown
  [theoretical].
- K4 `dynamic_frictions`: TYPE `list[float]`, unit dimensionless [probable], default none observed — drill [0.5] [verified] (d1_build.py:37). Only 0.5 drill-proven [theoretical].
- K5 `static_frictions`: TYPE `list[float]`, unit dimensionless [probable], default none observed — drill [0.5] [verified] (d1_build.py:37). Only 0.5 drill-proven [theoretical].

### EKB rules

- IF sizing E THEN scale it to body size (≈ self-weight stress regime)
  BECAUSE a 1 m cone's self-weight ≈ 10 kPa puts E=1e4 in the 100%-strain
  regime and E=1e6 in the rigid regime (F5) [verified].
- IF gating deformation THEN gate squash AND rest-on-ground together
  BECAUSE either alone admits jelly-sink or rigid-fall (F5) [verified].

### LIMITS

- L6. Young's modulus must scale with body size: 1e4 = jelly-sink, 1e6 =
  rigid, 1e5 = sweet spot for the 1 m cone (failures.md F5) [verified].

### UNKNOWN (theoretical)

- U3. Poisson-ratio / friction sensitivity — only 0.3/0.5 proven [theoretical].
- U4. Behavior for bodies much smaller/larger than 1 m [theoretical].

---

## T3. SimulationManager (isaacsim.core.simulation_manager)

DOES: selects device/engine and reports backend state [verified].

### Functions (5 callables + 1 attribute) — 6/6 typed

1. `SimulationManager.set_device("cuda")` [verified]
   - SIG: `SimulationManager.set_device(device: str) -> None [probable-return]` (class/static-style) [verified-params]
   - Call sites: d1_build.py:13 (`set_device("cuda")`, first line before stage setup). Units: n/a. Default: none observed [theoretical].
   - Class/static-style call, first line before stage setup (d1_build).
     `"cpu"` never tried [theoretical]. Returns: unused/None observed [verified].
2. `SimulationManager.get_active_physics_engine()` [verified]
   - SIG: `SimulationManager.get_active_physics_engine() -> str` ("physx" | "newton") [verified]
   - Call sites: d1_build.py:14, d1_drive.py:15, d1_drive.py:65, d1_probe.py:19, d1_probe.py:22, d1_diag.py:16 (all printed as `ACTIVE:`). Units: n/a.
   - Params: none. Returns: `"physx"` / `"newton"` string (printed as
     `ACTIVE:` in all four in-sim scripts) [verified].
3. `SimulationManager.get_available_physics_engines()` [verified]
   - SIG: `SimulationManager.get_available_physics_engines() -> list[tuple[str, bool]]` (name, active) [verified]
   - Call sites: d1_probe.py:16 (printed as `ENGINES`). Units: n/a.
   - Params: none. Returns: list of (name, active) tuples, observed
     `[('physx', False), ('newton', True)]` after enable (F2) [verified].
4. `SimulationManager.switch_physics_engine("newton")` [verified]
   - SIG: `SimulationManager.switch_physics_engine(engine: str) -> None [probable-return]` [verified-params]
   - Call sites: d1_probe.py:20 (`switch_physics_engine("newton")`, required positional). Units: n/a.
   - Params: engine-name string. Observed only toward newton on empty
     stage in d1_probe [verified]. Return unused [verified].
5. `SimulationManager.get_backend()` [probable]
   - SIG: `SimulationManager.get_backend() -> Unknown [theoretical]` — called, return NEVER recorded [theoretical].
   - Call sites: d1_probe.py:23 (`print("BACKEND", ...)`); no recorded output in evidence/.
   - Params: none. Called in d1_probe (`print("BACKEND", ...)`); no
     recorded output in evidence/ [verified-called; theoretical values].
6. Attribute `SimulationManager._physics_sim_view__warp` [verified]
   - TYPE: `SimulationManager._physics_sim_view__warp: WarpSimView [probable-name] | None`, with `.is_valid: bool` read as ATTRIBUTE (no call parens) [verified-access] (d1_diag.py:24-26). Private (leading underscore). Units: n/a.
   - Warp sim-view or None; d1_diag checks `is None` and `.is_valid`
     [verified]. Private (leading underscore) [verified].

### Knobs (2) — 2/2 typed

- K1 device string: TYPE `str` (enum-like {"cuda" [verified], "cpu" (untried)}), unit n/a, default unknown [theoretical] (only call passes "cuda", d1_build.py:13). `"cuda"` required before authoring (F3 recovery)
  [verified]; `"cpu"` unknown [theoretical].
- K2 engine-name string for switch: TYPE `str` (enum-like {"newton" [verified], "physx" (unobserved in-session)}), unit n/a, default none (required positional) [verified] (d1_probe.py:20). `"newton"` observed [verified];
  switching back to `"physx"` in-session unobserved [theoretical].

### EKB rules

- IF calling set_device THEN do it BEFORE stage setup/deformable authoring
  BECAUSE the tensor backend binds against device state at authoring time;
  late set_device leaves reads failing (F3) [verified].
- IF enabling/switching engines THEN re-query `get_active_physics_engine()`
  before stepping BECAUSE flags/enables select only among loaded engines
  and may silently leave PhysX active (F2) [verified].
- IF a stage is loaded THEN NEVER switch_physics_engine BECAUSE it hits
  the same NULL-stage native fatal as F1 cooking (F1 recovery) [verified].

### LIMITS

- L7. NEVER `switch_physics_engine` with a loaded stage — same NULL-stage
  native fatal as F1 (failures.md F1) [verified].
- L8. After any enable/switch, re-query active engine before stepping;
  never assume (failures.md F2) [verified].
- L9. `set_device("cuda")` must precede stage setup/deformable authoring
  or the tensor backend never binds (failures.md F3) [verified].

### UNKNOWN (theoretical)

- U5. `set_device("cpu")` for deformables — drill is CUDA-only [theoretical].
- U6. `get_backend()` return values beyond the probe print — no recorded
  output [theoretical].

---

## T4. app_utils (isaacsim.core.experimental.utils.app)

DOES: drives extensions, timeline, and stepped physics [verified].

### Functions (4) — 4/4 typed

1. `play(commit=True)` / `play()` [verified]
   - SIG: `play(commit: bool = ? [theoretical-default]) -> None [probable-return]`; other params unobserved [theoretical] [verified-params]
   - Call sites: d1_drive.py:38 (`commit=True`), d1_diag.py:19 (`commit=True`), d1_probe.py:46 (bare `play()`). Units: n/a.
   - `commit=True` in d1_build-flow/d1_drive/d1_diag; bare `play()` in
     d1_probe. Both step physics; commit was NOT the F3 fix (ruled-out)
     [verified]. Other params/defaults unobserved [theoretical].
2. `update_app_async(steps=N)` [verified]
   - SIG: `update_app_async(steps: int) -> Awaitable[Any] [probable-shape]` — MUST be awaited in async context; resolved value unused at all sites [verified-call]
   - Call sites: d1_drive.py:41 (`steps=10`), d1_drive.py:50 (`steps=300`), d1_probe.py:14/21/47 (`steps=10`), d1_diag.py:20 (`steps=30`) — all `await`ed. Units: steps = physics-step count. Default: none observed (always passed) [theoretical].
   - Awaited stepping; observed N = 10 (warmup/probe/enable-settle),
     30 (diag), 300 (settle). Returns: awaitable; return value unused
     [verified]. Must be awaited in async context (all call sites await)
     [verified].
3. `stop()` [verified] — stops timeline after reads (d1_drive, d1_probe,
   d1_diag). Params: none [verified].
   - SIG: `stop() -> None [probable-return]` [verified] (d1_drive.py:64, d1_probe.py:63, d1_diag.py:37). Units: n/a.
4. `enable_extension("isaacsim.physics.newton")` [verified]
   - SIG: `enable_extension(ext_id: str) -> None [probable-return]` [verified-params]
   - Call sites: d1_probe.py:13 (required positional). Units: n/a.
   - In-session enable on empty stage; verified to flip ACTIVE to newton
     with ENGINES list showing newton True (F2) [verified].

### Knobs (3) — 3/3 typed

- K1 `commit` flag on play(): TYPE `bool`, unit n/a, default unknown [theoretical] (True passed d1_drive.py:38; omitted d1_probe.py:46). True vs omitted — no behavioral difference
  observed for deformable stepping (ruled-out) [verified]; other effects
  unknown [theoretical].
- K2 `steps=N`: TYPE `int`, unit physics steps (count), default none observed — drill uses 10/30/300 [verified] (d1_drive.py:41,50; d1_diag.py:20). 10 = warmup quantum (12×10 retry loop), 300 = settle run
  [verified]. Exact minimum warmup count unproven — drill uses
  retry-until-success [theoretical].
- K3 extension-name string: TYPE `str` (extension id), unit n/a, default none (required positional) [verified] (d1_probe.py:13). Only `isaacsim.physics.newton` observed [verified].

### EKB rules

- IF warming up for first tensor read THEN use read retries (12×10 steps),
  not a fixed small guess BECAUSE backend buffers need real post-play
  steps and first-read-after-5-steps raises (F3/F4) [verified].
- IF enabling newton in-session THEN do it on an EMPTY stage and settle
  10 steps before querying BECAUSE d1_probe's verified flip used that
  sequence (F2) [verified].

### LIMITS

- L10. `play()` vs `play(commit=True)` both step physics; commit was NOT
  the F3 fix (failures.md ruled-out) [verified].
- L11. Fixed small step guesses are unreliable for first reads — warm up
  with read retries, 12×10 steps pattern (failures.md F3/F4) [verified].

### UNKNOWN (theoretical)

- U7. Exact minimum warmup step count — retry-until-success, no proven
  minimum [theoretical].

---

## T5. stage_utils (isaacsim.core.experimental.utils.stage)

DOES: defines the Xform prim that hosts the deformable [verified].

### Functions (1) — 1/1 typed

1. `stage_utils.define_prim("/World/D1Soft", "Xform")` [verified]
   - SIG: `define_prim(path: str, type_name: str [probable-names]) -> Usd.Prim [theoretical-return]` (return unused at all sites) [verified-params]
   - Call sites: d1_build.py:31, d1_probe.py:33 (both positional). Units: n/a. No defaults observed.
   - Params observed: path string + type-name string, both positional
     (d1_build, d1_probe). Returns: unused [verified]. Other type names /
     extra params unobserved [theoretical].

### Knobs (2) — 2/2 typed

- K1 prim path: TYPE `str` (Sdf prim path), unit n/a, default none (required positional) [verified] (d1_build.py:31). "/World/D1Soft" must match DeformablePrim path + Mesh
  parent path [verified].
- K2 prim type name: TYPE `str` (USD type name), unit n/a, default none (required positional) [verified] (d1_build.py:31). Only "Xform" observed [verified]; other hosts unknown
  [theoretical].

### EKB rules

- IF hosting a volume deformable THEN define an Xform at the body path
  first BECAUSE DeformablePrim wraps that Xform and the cooking Mesh hangs
  under it (d1_build order) [verified].

### LIMITS

- L12. None pack-attested (no failures.md entry) [verified-absence].

### UNKNOWN (theoretical)

- U8. Whether other prim types can host a volume DeformablePrim [theoretical].

---

## T6. prim_utils (isaacsim.core.experimental.utils.prim)

DOES: prim helpers — imported in d1_probe.py but NEVER called there [verified].

### Functions (0) — 0/0 typed (nothing to type)

- None observed [verified]. Import site only: d1_probe.py:5 (`import ... prim as prim_utils`), zero call sites [verified].

### Knobs (0) — 0/0 typed

- None [verified-absence].

### EKB rules

- IF tempted to rely on prim_utils for deformables THEN note zero drill
  coverage BECAUSE the import is dead in the only script that has it
  (d1_probe) [verified].

### LIMITS

- L13. None pack-attested (no failures.md entry) [verified-absence].

### UNKNOWN (theoretical)

- U9. Entire module surface — not drill-exercised [theoretical].

---

## T7. GroundPlane + Mesh (isaacsim.core.experimental.objects)

DOES: ground collider and cooking-mesh geometry for the deformable [verified].

### Functions (2) — 2/2 typed

1. `GroundPlane("/World/D1Ground")` [verified]
   - SIG: `GroundPlane(path: str, ... [theoretical-extra]) -> GroundPlane [probable-return]` (return unused at all sites) [verified-params]
   - Call sites: d1_build.py:30, d1_probe.py:32 (path positional). Units: n/a. No defaults observed.
   - Params observed: path string positional (d1_build, d1_probe).
     Returns: unused [verified]. Extra params unobserved [theoretical].
2. `Mesh("/World/D1Soft/mesh", primitives="Cone",
   positions=[0.0, 0.0, 1.5])` [verified]
   - SIG: `Mesh(path: str, primitives: str = ? [theoretical-default], positions: list[float] = ? [theoretical-default], ... [theoretical-extra]) -> Mesh [probable-return]` (return unused) [verified-params]
   - Call sites: d1_build.py:32-33, d1_probe.py:34-35 (path positional; primitives/positions keyword). Units: path/primitives n/a; positions m [probable-unit].
   - Params observed: path positional; `primitives="Cone"` keyword;
     `positions=[x,y,z]` keyword (drop start). Returns: unused [verified].
     Full signature (other primitives, rotations, scales) unobserved
     [theoretical].

### Knobs (4) — 4/4 typed

- K1 ground path: TYPE `str` (Sdf prim path), unit n/a, default none (required positional) [verified] (d1_build.py:30). Ground path [verified].
- K2 mesh path: TYPE `str` (Sdf prim path), unit n/a, default none (required positional) [verified] (d1_build.py:32). Must be a child of the deformable Xform
  ("/World/D1Soft/mesh"); cooking consumes it [probable].
- K3 `primitives`: TYPE `str` (enum-like; only "Cone" observed), unit n/a, default unknown [theoretical] (always passed, d1_build.py:32). Only "Cone" observed [verified]; others unknown
  [theoretical].
- K4 `positions`: TYPE `list[float]` ([x,y,z]), unit m [probable], default unknown [theoretical] (always passed, d1_build.py:33). Only [0,0,1.5] drop height observed [verified]; the 1 m
  cone at 1.5 m anchors the F5 stiffness scale and all 10 verify gates
  (drop > 0.5 m, tet shape [1,2544,4]) [verified].

### EKB rules

- IF changing the cooking mesh THEN re-derive stiffness AND gate thresholds
  BECAUSE E-sweet-spot, tet counts, and drop/squash gates are all
  cone-at-1.5 m-specific (F5; verify_d1.py) [verified].

### LIMITS

- L14. None directly; cone geometry anchors the F5 stiffness scale
  (failures.md F5) [verified].

### UNKNOWN (theoretical)

- U10. Non-cone primitives as deformable cooking meshes [theoretical].
- U11. Drop heights other than 1.5 m [theoretical].

---

## T8. UsdPhysics.Scene + PhysxSceneAPI + Gf (pxr)

DOES: explicit PhysicsScene with gravity, 60 Hz, TGS solver [verified].

### Functions (8) — 8/8 typed

1. `UsdPhysics.Scene.Define(st, "/World/PhysicsScene")` [verified]
   - SIG: `UsdPhysics.Scene.Define(stage: Usd.Stage, path: str [probable-names]) -> UsdPhysics.Scene [probable-type]` [verified-call]
   - Call sites: d1_build.py:20 (both positional; `st` from d1_build.py:15). Units: n/a. No defaults observed.
   - Params: stage handle + path. Returns scene object with
     GetPrim()/Create*Attr (d1_build) [verified].
2. `CreateGravityDirectionAttr()` + `.Set(Gf.Vec3f(0,0,-1))` [verified].
   - SIG: `scene.CreateGravityDirectionAttr() -> Usd.Attribute [probable-type]; attr.Set(value: Gf.Vec3f) -> bool [theoretical-return]` (Set return unused) [verified-call]
   - Call sites: d1_build.py:21. Units: unitless direction vector (normalized (0,0,−1)).
3. `CreateGravityMagnitudeAttr()` + `.Set(9.81)` [verified].
   - SIG: `scene.CreateGravityMagnitudeAttr() -> Usd.Attribute [probable-type]; attr.Set(value: float) -> bool [theoretical-return]` (Set return unused) [verified-call]
   - Call sites: d1_build.py:22 (float literal 9.81). Units: m/s² [probable-unit].
4. `PhysxSchema.PhysxSceneAPI.Apply(prim)` [verified] — applies PhysX
   schema to the scene prim [verified].
   - SIG: `PhysxSchema.PhysxSceneAPI.Apply(prim: Usd.Prim) -> PhysxSceneAPI [probable-type]` [verified-call]
   - Call sites: d1_build.py:23 (`Apply(ps.GetPrim())`, required positional; result `px` used for Create*Attr). Units: n/a.
5. `CreateTimeStepsPerSecondAttr()` + `.Set(60)` [verified].
   - SIG: `px.CreateTimeStepsPerSecondAttr() -> Usd.Attribute [probable-type]; attr.Set(value: int | float [probable]) -> bool [theoretical-return]` (Set return unused) [verified-call]
   - Call sites: d1_build.py:24 (int literal 60). Units: Hz [verified-semantics].
6. `CreateSolverTypeAttr()` + `.Set("TGS")` [verified].
   - SIG: `px.CreateSolverTypeAttr() -> Usd.Attribute [probable-type]; attr.Set(value: str) -> bool [theoretical-return]` (Set return unused) [verified-call]
   - Call sites: d1_build.py:25 (str literal "TGS"). Units: n/a (enum-like token).
7. `CreateEnableStabilizationAttr()` + `.Set(True)` [verified].
   - SIG: `px.CreateEnableStabilizationAttr() -> Usd.Attribute [probable-type]; attr.Set(value: bool) -> bool [theoretical-return]` (Set return unused) [verified-call]
   - Call sites: d1_build.py:26 (bool literal True). Units: n/a.
8. `Gf.Vec3f(0, 0, -1)` [verified] — gravity direction vector [verified].
   - SIG: `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` [verified-call]
   - Call sites: d1_build.py:21 (three positional int/float literals). Units: unitless direction.

### Knobs (5) — 5/5 typed

- K1 gravity direction: TYPE `Gf.Vec3f`, unit unitless direction, drill default (0,0,−1) [verified] (d1_build.py:21); upstream default [theoretical]. Only (0,0,−1) observed [verified].
- K2 gravity magnitude: TYPE `float`, unit m/s² [probable], drill default 9.81 [verified] (d1_build.py:22); upstream default [theoretical]. Only 9.81 observed [verified].
- K3 time steps per second: TYPE `int | float` [probable] (int literal passed), unit Hz, drill default 60 [verified] (d1_build.py:24); upstream default [theoretical]. Only 60 observed [verified].
- K4 solver type: TYPE `str` (token), unit n/a, drill default "TGS" [verified] (d1_build.py:25); upstream default [theoretical]. Only "TGS" observed [verified].
- K5 stabilization: TYPE `bool`, unit n/a, drill default True [verified] (d1_build.py:26); upstream default [theoretical]. Only True observed [verified].
- Effect-of-change for K1–K5 on deformables: untested — any non-drill
  value is unproven [theoretical].

### EKB rules

- IF the stage is bare THEN define an explicit UsdPhysics.Scene +
  PhysxSceneAPI BEFORE authoring the deformable BECAUSE rigid bodies
  tolerate a missing scene but the deformable tensor backend never binds
  without one (F3) [verified].
- IF re-running a build THEN guard scene creation with a prim-validity
  check (SCENE-CREATED vs SCENE-EXISTS) BECAUSE d1_build is idempotent on
  the scene but rebuilds ground/body/material unconditionally [verified].

### LIMITS

- L15. Rigid bodies tolerate a missing scene; the deformable tensor
  backend NEVER binds without one (failures.md F3) [verified].

### UNKNOWN (theoretical)

- U12. Non-TGS solvers or rates other than 60 Hz for deformables [theoretical].

---

## T9. omni.usd

DOES: stage access for prim validity checks and cleanup [verified].

### Functions (5) — 5/5 typed

1. `omni.usd.get_context()` [verified] — returns USD context [verified].
   - SIG: `omni.usd.get_context() -> UsdContext [probable-type]` (supports `.get_stage()`) [verified-call]
   - Call sites: d1_build.py:15, d1_probe.py:25, d1_diag.py:9. Units: n/a.
2. `.get_stage()` on the context [verified] — returns stage handle `st`
   (d1_build, d1_probe, d1_diag) [verified].
   - SIG: `context.get_stage() -> Usd.Stage [probable-type]` (supports GetPrimAtPath/RemovePrim) [verified-call]
   - Call sites: d1_build.py:15, d1_probe.py:25, d1_diag.py:9. Units: n/a.
3. `st.GetPrimAtPath(path)` [verified] — returns prim; `.IsValid()` gates
   cleanup/scene-create/diag [verified].
   - SIG: `stage.GetPrimAtPath(path: str) -> Usd.Prim [probable-type]; prim.IsValid() -> bool` [verified-call]
   - Call sites: d1_build.py:17/19/39, d1_probe.py:26/28/30, d1_diag.py:13 (path positional; `.IsValid()` bool-gates cleanup/scene-create/diag). Units: n/a.
4. `st.RemovePrim(path)` [verified] — deletes ground/body/material prims
   for idempotent rebuild (d1_build, d1_probe) [verified].
   - SIG: `stage.RemovePrim(path: str) -> bool [theoretical-return]` (return unused at all sites) [verified-params]
   - Call sites: d1_build.py:18, d1_probe.py:27/29/31 (path positional). Units: n/a.
5. `prim.GetTypeName()` [verified] — diag print only (d1_diag) [verified].
   - SIG: `prim.GetTypeName() -> str [probable]` (string-formatted with %s) [verified-call]
   - Call sites: d1_diag.py:15 (`pr.GetTypeName() if pr.IsValid() else "-"`, %s-formatted). Units: n/a.

### Knobs (0) — 0/0 typed

- Paths acted on, not tool knobs — covered under owning tools [verified].

### EKB rules

- IF rebuilding THEN RemovePrim ground/body/material when valid but keep
  the PhysicsScene BECAUSE d1_build's idempotent order preserves the
  scene while re-cooking the body (F3 rebuild rule) [verified].

### LIMITS

- L16. None pack-attested (no failures.md entry) [verified-absence].

### UNKNOWN

- None — thin usage, fully observed [verified].

---

## T10. omni.timeline

DOES: confirms the timeline is actually playing during diagnosis [verified].

### Functions (2) — 2/2 typed

1. `omni.timeline.get_timeline_interface()` [verified] — returns timeline
   interface (d1_diag) [verified].
   - SIG: `omni.timeline.get_timeline_interface() -> ITimeline [probable-type]` (supports `.is_playing()`) [verified-call]
   - Call sites: d1_diag.py:21. Units: n/a.
2. `.is_playing()` [verified] — returns bool; F3 evidence showed playing
   yet reads failing, proving play-state is necessary but not sufficient
   [verified].
   - SIG: `timeline.is_playing() -> bool` [verified] (d1_diag.py:21, printed as `playing:`). Units: n/a.

### Knobs (0) — 0/0 typed

- None [verified].

### EKB rules

- IF reads fail THEN check is_playing() as one chain link, but do NOT stop
  there BECAUSE F3 had playing=True with 120+ steps of backend failures
  (missing scene) [verified].

### LIMITS

- L17. None pack-attested (no failures.md entry) [verified-absence].

### UNKNOWN

- None — single observed call [verified].

---

## T11. PhysX cooking interface (implicit via DeformablePrim)

DOES: `cook_auto_deformable_body(path)` cooks sim/collision meshes at
authoring time (deformable_prim.py:164, per F1) [probable — pack cites the
file:line but the file itself is not in the pack].

### Functions (1) — 1/1 typed (all [theoretical]: zero direct call sites)

1. `get_physx_cooking_interface().cook_auto_deformable_body(path)`
   [probable] — never called directly; invoked inside
   `DeformablePrim.__init__` → `_check_or_apply_deformable_schema`
   (py-spy trace, F1) [verified-trace].
   - SIG: `get_physx_cooking_interface() -> IPhysxCooking [theoretical]; .cook_auto_deformable_body(path: str [probable]) -> bool | None [theoretical]` — ZERO direct call sites in pack (invoked inside DeformablePrim.__init__ per F1 py-spy trace). Units: n/a. Defaults unknown [theoretical].

### Knobs (0) — 0/0 typed

- None directly accessible from the drill [verified].

### EKB rules

- IF a DeformablePrim constructor hard-crashes Kit with no traceback THEN
  suspect the cooking stage handle (check active engine) BECAUSE the F1
  fatal was a NULL-stage member lookup inside cooking, proven by py-spy
  [verified].

### LIMITS

- L18. Stage handle is NULL under Newton-active sims → native fatal on
  member lookup (failures.md F1) [verified].

### UNKNOWN (theoretical)

- U13. Direct calls to the cooking interface — never drill-exercised
  [theoretical].

---

## T12. Kit boot CLI flags

DOES: selects/enables physics engines at launch [verified].

### Functions (2 flags) — 2/2 typed

1. `--/exts/isaacsim.core.simulation_manager/default_engine=newton`
   [verified] — selects among LOADED engines only [verified].
   - SIG: `--/exts/isaacsim.core.simulation_manager/default_engine=<engine: str>` ("physx" | "newton"); upstream default `"physx"` [probable] (flag alone still reports ACTIVE: physx, F2). Value type grounded in F2 evidence (failures.md), not a script call site [verified-evidence].
2. `--enable isaacsim.physics.newton` [verified] — loads the Newton
   extension (ships disabled) [verified].
   - SIG: `--enable <ext_id: str>` (repeatable [probable]); no default (flag absent = extension not force-loaded). Value type grounded in F2 evidence [verified-evidence].

### Knobs (0 beyond the two flags) — 0/0 typed (flags ARE the knobs; both typed above)

- Flag combination is the knob: TYPE pair of `str` values, unit n/a, default = both absent (ships-State: newton disabled, physx active) [probable] (F2). Default_engine alone vs + enable
  [verified].

### EKB rules

- IF booting for Newton THEN pass BOTH the default_engine flag AND
  `--enable isaacsim.physics.newton` BECAUSE the flag alone still reports
  `ACTIVE: physx` (F2) [verified].
- IF booted with engine flags THEN still re-query the active engine
  before stepping BECAUSE flags express intent, the query reports fact
  (F2 prevention) [verified].

### LIMITS

- L19. The `default_engine=newton` flag alone does NOT activate Newton
  (`isaacsim.physics.newton` ships disabled); must also `--enable` it
  (failures.md F2) [verified].

### UNKNOWN

- None — flag interaction fully drill-proven [verified].

---

## T13. py-spy

DOES: native crash-trace sampling; proved the F1 NULL-stage fatal location
[verified].

### Functions (1 procedure) — 1/1 typed (all [theoretical]: invocation unrecorded)

1. Crash-trace read: MainThread inside
   `_check_or_apply_deformable_schema` ← `DeformablePrim.__init__`
   (failures.md F1) [verified].
   - SIG: `py-spy <subcommand: str> --pid <pid: int> ... [theoretical]` → stack-sample text (MainThread frames) [theoretical]. Invocation/command-line NOT recorded in pack (U14); zero call sites. Params/return all [theoretical].

### Knobs (0) — 0/0 typed

- Invocation/command-line used — not recorded in the pack [verified-absence].

### EKB rules

- IF Kit hard-crashes with no traceback THEN sample with py-spy BECAUSE it
  located the F1 fatal inside cooking schema application when Python
  gave nothing [verified].

### LIMITS

- None pack-attested against it (diagnostic tool) [verified-absence].

### UNKNOWN (theoretical)

- U14. Invocation/command-line used — not recorded in the pack [theoretical].

---

## T14. numpy

DOES: array conversion and snapshot statistics for nodal reads [verified].

### Functions (6) — 6/6 typed (item 3 = .min + .max)

1. `_np.asarray(x.numpy(), dtype=float)` [verified] — warp→numpy bridge in
   d1_drive sim_pos/sim_vel/stress/elems [verified].
   - SIG: `numpy.asarray(a: array_like, dtype: type = float [verified-passed]) -> ndarray` (units inherit input: m, m/s, Pa, index) [verified]
   - Call sites: d1_drive.py:21, d1_drive.py:26, d1_drive.py:53, d1_drive.py:60 (dtype=float passed at :21/:26/:53, omitted at :60 — upstream default [probable] dtype-inference).
2. `.mean(axis=0)` [verified] — centroid in snap() [verified].
   - SIG: `ndarray.mean(axis: int = 0 [verified-passed]) -> ndarray` ((3,) centroid, unit m) [verified]
   - Call sites: d1_drive.py:32 (`p.mean(axis=0)`).
3. `.min()` / `.max()` [verified] — zmin/zmax in snap(), stress stats
   [verified].
   - SIG: `ndarray.min() -> float; ndarray.max() -> float` (scalar; units: m for zmin/zmax, m/s for vmax, Pa for stress) [verified]
   - Call sites: d1_drive.py:33 (zmin/zmax), d1_drive.py:35 (vmax), d1_drive.py:54-55 (stress mean/max; mean shares item-2 shape with axis=None [probable]).
4. `.std()` [verified] — x/y spread (bulge metric) in snap() [verified].
   - SIG: `ndarray.std() -> float` (scalar, unit m) [verified]
   - Call sites: d1_drive.py:34 (`p[:, :2].std()`).
5. `_np.abs(v).max()` [verified] — vmax (falling/at-rest metric) [verified].
   - SIG: `numpy.abs(x: ndarray) -> ndarray; .max() -> float` (unit m/s) [verified]
   - Call sites: d1_drive.py:35 (`_np.abs(v).max()`).

### Knobs (0) — 0/0 typed

- None — standard usage [verified]. (Inline args typed above: dtype=float, axis=0.)

### EKB rules

- IF converting a tensor read THEN wrap with `asarray(..., dtype=float)`
  and guard `.numpy()` with hasattr BECAUSE element indices may arrive
  without `.numpy()` (d1_drive elems block) [verified].

### LIMITS

- None pack-attested (no failures.md entry) [verified-absence].

### UNKNOWN

- None — standard usage, fully observed [verified].

---

## T15. verify_d1.py local gate harness (json/sys)

DOES: gates recorded evidence with 10 checks (engine, topology, drop,
rest, squash, bulge, falling, at-rest, stress, tets); exit 0/1 [verified].

### Functions (1 + 10 gates) — 11/11 typed

1. `gate(name, ok, detail="")` — appends (name, bool, detail); prints
   PASS/FAIL per gate + `D1-PASS n/10`; `sys.exit(0 if not fails else 1)`
   [verified].
   - SIG: `gate(name: str, ok: bool, detail: str = "") -> None` — EXACT signature from source (verify_d1.py:10-11); `gates.append((name, bool(ok), detail))` [verified]
   - Call sites: verify_d1.py:19-36 (10 calls); `sys.exit(0 if not fails else 1)` at verify_d1.py:43 (exit `int`). Units: n/a.
2. Gates over `evidence/d1_nodes.json` via `json.load` [verified]:
   G1 engine-physx · G2 topology-stable · G3 drop · G4 rest-on-ground ·
   G5 squash-height · G6 bulge-spread · G7 was-falling · G8 at-rest ·
   G9 stress-live · G10 tets [verified].
   - SIG: `json.load(fp: TextIO) -> dict` (verify_d1.py:14 `json.load(open(EV))`); each gate Gi = `gate(name: str, comparison: bool, detail: str)` [verified]
   - Gate expressions (verify_d1.py:19-36): G1 `d["engine"] == "physx"`; G2 `e0["n"] == e1["n"] and e0["n"] >= 100`; G3 `e0["c"][2] - e1["c"][2] > 0.5`; G4 `e1["zmin"] > -0.12`; G5 `h1 < h0` (h = zmax−zmin); G6 `e1["spread"] > e0["spread"]`; G7 `e0["vmax"] > 1.0`; G8 `e1["vmax"] < 0.5`; G9 `d["stress"].get("max", 0) > 0`; G10 shape-check (see K10) [verified].

### Knobs (10 thresholds) — 10/10 typed

- K1 engine: TYPE `str`, unit n/a, threshold (default) `== "physx"` [verified] (verify_d1.py:19). Engine == "physx" [verified].
- K2 n: TYPE `int` (node count), unit count, thresholds `e0n == e1n` and `>= 100` (observed 678) [verified] (verify_d1.py:20-21). N early == n settled, n ≥ 100 (observed 678) [verified].
- K3 drop: TYPE `float` (centroid-z delta), unit m, threshold `> 0.5` (observed ≈0.82) [verified] (verify_d1.py:22-23). Drop: zc early − zc settled > 0.5 (observed ≈0.82) [verified].
- K4 rest: TYPE `float` (settled zmin), unit m, threshold `> −0.12` (observed −0.040) [verified] (verify_d1.py:24). Rest: settled zmin > −0.12 (observed −0.040) [verified].
- K5 squash: TYPE `float` (height h=zmax−zmin), unit m, threshold `h1 < h0` (observed 1.000→0.986) [verified] (verify_d1.py:16-17,25). Squash: h1 < h0 (observed 1.000→0.986) [verified].
- K6 bulge: TYPE `float` (x/y std spread), unit m, threshold `spread1 > spread0` (observed +1.2%) [verified] (verify_d1.py:26-27). Bulge: spread1 > spread0 (observed +1.2%) [verified].
- K7 was-falling: TYPE `float` (early vmax), unit m/s, threshold `> 1.0` (observed 1.96) [verified] (verify_d1.py:28). Was-falling: early vmax > 1.0 (observed 1.96) [verified].
- K8 at-rest: TYPE `float` (settled vmax), unit m/s, threshold `< 0.5` (observed 0.054) [verified] (verify_d1.py:29). At-rest: settled vmax < 0.5 (observed 0.054) [verified].
- K9 stress-live: TYPE `float` (stress max), unit Pa [probable], threshold `max > 0` (observed max ≈24.6k, mean ≈−490) [verified] (verify_d1.py:30-31). Stress-live: stress max > 0 (observed max ≈24.6k, mean ≈−490)
  [verified].
- K10 tets: TYPE `list[int]` (elem shape), unit count/shape, threshold `shape[1:] == [2544,4]` OR generic-tet (3 dims, last==4, mid>0) [verified] (verify_d1.py:32-36). Elems shape [1:]==[2544,4] OR (3 dims, last==4, mid>0) —
  exact [1,2544,4] is cone-specific; fallback is generic-tet [verified].

### EKB rules

- IF gating landing THEN never gate x/y BECAUSE landing tip-over varies
  run to run (0.02 m vs 0.5 m drift); z/shape/stress/velocity gates are
  stable (F5) [verified].
- IF gating deformation THEN gate squash AND rest-on-ground together
  BECAUSE either alone admits jelly-sink or rigid-fall (F5) [verified].

### LIMITS

- L20. Never gate x/y (tip-over variance); z/shape/stress/velocity stable
  (failures.md F5) [verified].
- L21. Squash + rest-on-ground must be gated together (failures.md F5)
  [verified].

### UNKNOWN

- None — 10/10 gates drill-proven, 3/3 bit-identical runs (SKILL.md)
  [verified].

---

## Cross-tool UNVERIFIED (pack-level, theoretical)

- Newton deformable runs (pre-cooked USD on Newton-from-boot sim with
  render-observation verification) — future work, unbuilt (SKILL.md;
  failures.md F1 prevention) [theoretical].
- Fabric Scene Delegate effect on reads — ruled OUT for sim-mesh reads
  (viz only), never directly tested (failures.md ruled-out) [theoretical].
- Warp CUDA-graph compile message — classified one-time JIT noise, not an
  error (failures.md ruled-out) [theoretical].
- Upstream example
  `$ISAAC_SIM_DIR/standalone_examples/api/isaacsim.core.experimental.api/deformable_stress_visualization.py`
  — cited in SKILL.md References, not in pack, not read [theoretical].
- Exact tet-count generality — [1,2544,4] gate is cone-specific
  (verify_d1.py + evidence) [theoretical].
