# GPUNUC TOOLS_REF (full tool mastery, 2026-11-04)

Detail reference for pack `gpunuc`. Companion to `TOOLS.md` (summary).
Sources: SKILL.md, failures.md, scripts/g1_probe.py, scripts/g1_drive.py,
scripts/g2_probe.py, scripts/verify_g1.py, scripts/verify_g2.py,
evidence/g1_devices.json, evidence/g2_assets.json — all read FULL.
No discovery.md exists in this pack (checked 2026-11-04).
Environment: Isaac Sim 6.0.0 / Kit 110, 1x RTX 3050 Laptop 4 GB.
Counts (datatype pass 2026-11-04): signatures typed 23/23
callables across 8 sections (+1 import binding typed) · knobs
typed 25/25 (each: type + unit + default) · still-unknown
(untyped) 0; type details beyond drill calls carry [probable]
(x48 added, incl. [probable-stdlib]) / [theoretical] (x14 added).

Claim tags: [verified] = live evidence in this pack; [probable] =
strongly implied by code/stdlib semantics but not drill-proven;
[theoretical] = general knowledge, NOT proven here.

---

## 1. torch.cuda (PyTorch CUDA device query)

### DOES
Reports CUDA availability, device count, and device name on the sim
host. First half of the torch/warp agreement cross-check [verified].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `torch.cuda.is_available() -> bool` — params: none (zero-arg
  calls [verified: g1_probe.py L11/L13/L15]). Return `bool`
  (unitless; True iff a CUDA-capable GPU + driver is visible to the
  torch build) [verified: returned true, evidence `torch_cuda`].
- `torch.cuda.device_count() -> int` — params: none (zero-arg call
  [verified: g1_probe.py L12]). Return `int` (unit: devices;
  number of visible CUDA devices; observed 1). Gated: called only
  when is_available() is True, else the probe records `0: int`
  [verified: g1_probe.py L12-13; returned 1].
- `torch.cuda.get_device_name(device: int) -> str` — param `device:
  int` (unit: device ordinal, unitless; no default exercised —
  drill always passes `0` explicitly [verified: g1_probe.py L14];
  torch's own default [theoretical — never relied on here]).
  `torch.device` / `str` specifiers also accepted by torch
  [theoretical — never passed here]. Return `str` (unitless GPU
  name; observed "NVIDIA GeForce RTX 3050 Laptop GPU"). Gated on
  is_available(), else the probe records None (the None is the
  probe's fallback, NOT the function's return) [verified:
  g1_probe.py L14-15].

### Knobs + effect-of-change (each: type + unit + default)
- Knob `device` arg to get_device_name: type `int` [verified:
  g1_probe.py L14 passes `0`]; unit: device ordinal (unitless);
  default: none exercised — always passed explicitly (torch-side
  default [theoretical]). `0` -> names the only GPU [verified].
  Index >= device_count raises (CUDA error / invalid device
  ordinal) [theoretical — never tried here].
- Knob `CUDA_VISIBLE_DEVICES` env: type `str` of comma-separated
  ordinals/UUIDs [theoretical]; unit: device list (unitless);
  default: unset [probable — never set or read in this pack; torch
  enumerated the box's only GPU]. Restricts which GPUs torch sees;
  count and indices shift accordingly [theoretical — not set or
  tested in this pack].
- Knob guard pattern `if is_available() else <fallback>`: fallback
  for device_count is `0: int` (unit: devices) [verified:
  g1_probe.py L12-13]; fallback for get_device_name is `None:
  NoneType` (unitless) [verified: g1_probe.py L14-15]. Prevents
  exceptions on CPU-only hosts; without it device_count/get_name
  raise or return garbage [probable — guard is in g1_probe.py; the
  CPU-only branch never executed].

### EKB rules (IF/THEN/BECAUSE)
- IF torch.cuda.is_available() is False THEN treat the box as
  CPU-only and skip all cuda selection BECAUSE every downstream
  cuda call assumes a visible device [probable].
- IF device_count != 1 THEN the single-GPU drill contract is void;
  do NOT apply G1 pass criteria BECAUSE all gates assume exactly one
  GPU (failures.md scope bound) [verified].
- IF torch and warp device lists disagree THEN stop and investigate;
  do not trust either alone BECAUSE agreement is the drill's honesty
  signal (failures.md G1) [verified].
- IF wrapping probe calls THEN catch broad `Exception` and record
  `repr(e)[:150]` BECAUSE the probe must survive any single-tool
  failure and still dump JSON (g1_probe.py pattern) [verified].

### LIMITS (with cites)
- Single-GPU box only: reports exactly 1 device here; multi-GPU
  distribution unrunnable (failures.md scope bound; evidence
  `torch_ndev: 1`) [verified].
- `torch_name0` is informational only; no gate depends on the name
  string (verify_g1.py has no name gate) [verified].
- Probe failure mode is silent-record (`torch_err` key), not raise —
  a missing/broken torch still yields a JSON file missing the torch
  keys, which then fails gates at verify time [verified: g1_probe.py
  L9-17].

### UNKNOWN (theoretical)
- Behavior on multi-GPU boxes (counts > 1, name indexing beyond 0)
  [theoretical].
- Which torch build ships with Kit 110 and whether is_available can
  be False while warp still sees cuda [theoretical].
- Effect of `CUDA_VISIBLE_DEVICES` on the torch/warp agreement check
  [theoretical].

---

## 2. warp / wp (NVIDIA Warp device enumeration)

### DOES
Enumerates compute devices via `wp.get_devices()` as the
source-of-truth cross-check against torch [verified].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `import warp as wp` — NOT a callable: module binding. `wp:
  module` (the warp package) [verified: g1_probe.py L19]; unit:
  n/a; default: n/a. Import inside try/except; failure records
  `warp_err: str` (150-char `repr(e)`, unitless) [verified:
  g1_probe.py L18-22].
- `wp.get_devices() -> list[wp.Device]` — params: none (zero-arg
  call [verified: g1_probe.py L20]). Return `list[wp.Device]`
  (element class name `Device` [probable — objects observed only
  via `str(d)`]; unit: device list, unitless; length 2 here).
  Each device rendered via `str(d: wp.Device [probable]) -> str`
  (unitless label) to `["cpu", "cuda:0"]` [verified:
  g1_probe.py L20; evidence `warp_devices`].

### Knobs + effect-of-change (each: type + unit + default)
- Knob (none): get_devices() takes no arguments, so no settable
  knob exists — type n/a, unit n/a, default n/a [verified:
  g1_probe.py L20 zero-arg call].
- Knob `str(d)` rendering: input `d: wp.Device` [probable]
  (unit: device handle); output `str` (unitless label `cpu` /
  `cuda:N`; no default — pure function of `d`). The gate tests
  `"cuda:0" in warp_devices: list[str]` on these strings
  [verified: verify_g1.py L17-18]. A different warp version could
  change string form and break the gate [theoretical].
- Knob warp runtime init (first wp call triggers kernel-module
  load): no settable attr (type n/a, unit n/a); default state is
  uninitialized-then-init-on-first-call [probable]. Failure would
  land in `warp_err: str` (150-char repr, unitless) [probable —
  except-branch at g1_probe.py L21-22 exists but never fired].

### EKB rules (IF/THEN/BECAUSE)
- IF `"cuda:0" not in warp_devices` THEN fail gate `warp-cuda0`
  BECAUSE warp must independently confirm the GPU torch reports
  [verified: verify_g1.py].
- IF warp import fails THEN record `warp_err` and continue the probe
  BECAUSE one dead tool must not kill enumeration of the others
  [verified: g1_probe.py pattern].
- IF comparing devices across tools THEN compare on the stringified
  lists, not object identity BECAUSE torch ints and warp Device
  objects share no type (probe stringifies warp side) [verified].

### LIMITS (with cites)
- Must agree with torch: exactly `[cpu, cuda:0]`
  (failures.md G1; evidence/g1_devices.json) [verified].
- Only membership of `cuda:0` is gated, not exact list equality —
  an extra device entry would still pass `warp-cuda0` (verify_g1.py
  L17 uses `in`, not `==`) [verified].
- No warp version pinned or recorded anywhere in the pack [verified].

### UNKNOWN (theoretical)
- Warp device list on multi-GPU or CPU-only hosts [theoretical].
- Whether warp can see a GPU torch cannot (or vice versa) under
  mismatched driver/CUDA versions [theoretical].
- String form stability of `str(Device)` across warp versions
  [theoretical].

---

## 3. isaacsim.core.simulation_manager.SimulationManager (device selection)

### DOES
Reports and selects the sim compute device; reports tensor backend
and active physics engine. All calls in this pack are static/class
calls, no instance constructed [verified: g1_probe.py, g1_drive.py].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `SimulationManager.get_device() -> Any` — params:
  none (static/class call, zero args [verified: g1_probe.py L24;
  g1_drive.py L8/L10/L22 executed; L17 is the unfired
  phantom-stuck branch]). Return `Any`: runtime class unprobed
  [theoretical]; observed only via `str() -> str`
  (unitless enum-like label: `"cpu"` on fresh sim, `"cuda:0"`
  after set_device("cuda")) [verified: evidence `sim_device: cpu`,
  `init_device: cpu`, `cuda_device: cuda:0`].
- `SimulationManager.set_device(spec: str) -> None` — param `spec:
  str` (unitless device selector; no default exercised — always
  passed explicitly [verified: g1_drive.py L9/L16]; whether the
  API defines a default [theoretical]). Tested `"cuda"` (selects
  cuda:0 [verified: g1_drive.py L9-10]) and `"cuda:1"` (raises
  [verified: g1_drive.py L16]). Return `None` (unitless)
  [probable — return value never inspected; effect read back via
  get_device() [verified: g1_drive.py L10/L22]].
- `SimulationManager.get_backend() -> Any` — params:
  none (zero-arg call [verified: g1_probe.py L28; g1_drive.py
  L12]). Return `Any`: runtime class unprobed [theoretical];
  observed only via `str() -> str` (unitless
  tensor-frontend label `"numpy"`). Stays `numpy` even on cuda:0
  — NOT an error [verified: failures.md G1; evidence `backend` +
  `cuda_backend` both `numpy`].
- `SimulationManager.get_active_physics_engine() -> str` —
  params: none (zero-arg call [verified: g1_probe.py L31]).
  Return `str` (unitless engine name; recorded to JSON uncoerced
  and gated `== "physx"` [verified: g1_probe.py L31; evidence;
  gate `engine-physx`]).

### Knobs + effect-of-change (each: type + unit + default)
- Knob `spec="cuda"`: type `str` (unitless selector); default:
  none exercised — required arg, always passed explicitly
  [verified: g1_drive.py L9] (API-side default, if any,
  [theoretical]). -> device becomes `cuda:0` (default/only GPU
  selected) [verified: g1_drive.py L9-10].
- Knob `spec="cuda:1"` (phantom): type `str` (unitless);
  default: none exercised — required arg [verified:
  g1_drive.py L16]. -> raises `ValueError('Invalid device
  specification (cuda:1): Invalid device identifier: cuda:1')`
  (exception type `ValueError` [verified: evidence `cuda1_err`
  text]); device stays `cuda:0`, sim healthy [verified: evidence
  `cuda1_rejected: true`, `final_device: cuda:0`]. Records
  `cuda1_rejected: bool` (unitless; True = rejected) and
  `cuda1_err: str` (200-char repr, unitless) [verified:
  g1_drive.py L20-21].
- Knob `spec` variants `"cpu"`, `"cuda:0"` explicit, torch.device
  objects: type `str | torch.device` [theoretical]; unitless;
  default n/a. Never tried here; effect unknown [theoretical].
- Knob call order (get before set = init, after set = cuda, after
  phantom = final): type: sequencing of 3 `str` reads
  (`init_device / cuda_device / final_device: str`, unitless
  labels; no defaults — each assigned by its read) [verified:
  g1_drive.py L8-22]. The three-read pattern is what proves
  select + reject + healthy-after.

### EKB rules (IF/THEN/BECAUSE)
- IF get_device() on a fresh sim returns cpu THEN that is the
  expected default, not a failure BECAUSE the drill pins
  cpu/numpy as the fresh-sim default (failures.md G1) [verified].
- IF backend still reads numpy after cuda selection THEN do NOT
  flag it BECAUSE it is the tensor frontend label, not the device
  (failures.md G1) [verified].
- IF negative-testing a phantom id THEN wrap set_device in
  try/except, record rejection + err, and ALWAYS re-read
  get_device() after BECAUSE the healthy-after proof requires the
  post-exception read (g1_drive.py L11-22) [verified].
- IF set_device("cuda:1") does NOT raise THEN record
  `cuda1_set` + `cuda1_rejected: False` and fail the gate BECAUSE a
  phantom id that sticks means dishonest reporting (g1_drive.py
  L16-18; verify_g1.py gate `cuda1-rejected`) [verified].
- IF get_backend() raises THEN record `cuda_backend_err` (first
  120 chars) and continue BECAUSE backend read is auxiliary to the
  device proof (g1_drive.py L11-14) [verified].

### LIMITS (with cites)
- Fresh sim defaults to cpu/numpy (failures.md G1; evidence
  `sim_device`, `backend`) [verified].
- Backend label stays numpy on cuda:0 (failures.md G1; evidence
  `cuda_backend: numpy`) [verified].
- Phantom `cuda:1` raises clean ValueError; sim stays healthy on
  cuda:0 (failures.md G1; evidence `cuda1_err`, `final_device`)
  [verified].
- Active engine observed `physx` only; renderer observed `rtx` only
  (evidence; gates `engine-physx`, `renderer-rtx`) [verified].
- `cuda1_err` truncated to 200 chars, `cuda_backend_err` to 120 —
  long tracebacks are cut (g1_drive.py) [verified].

### UNKNOWN (theoretical)
- set_device with `"cpu"`, `"cuda:0"`, `"cuda: 0"`, index ints, or
  torch.device objects [theoretical].
- get_backend under non-numpy frontends (torch/cupy/warp tensors)
  [theoretical].
- Whether set_device re-creates the sim/physics context or migrates
  live state; cost of a device switch mid-scene [theoretical].
- Behavior when called with no sim open, or twice with the same spec
  [theoretical].

---

## 4. carb.settings (Kit settings read)

### DOES
Reads renderer settings keys. Provides context (`/renderer/active`)
and documents one ANTI-signal (`/renderer/activeGpuIndex` reads None
— never gate on it) [verified].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `carb.settings.get_settings() -> carb.settings.ISettings` —
  params: none (zero-arg call [verified: g1_probe.py L32]).
  Return `ISettings` handle (class name `ISettings` [probable —
  handle observed only via its `.get` method]; unit: settings
  handle).
- `settings.get(key: str) -> Any` — param `key: str` (unitless
  `/`-path; no default exercised — required, drill passes
  `"/renderer/active"` and `"/renderer/activeGpuIndex"`
  [verified: g1_probe.py L33-34]). Any further params (e.g. a
  fallback default) [theoretical — never passed]. Return `Any`
  (unitless; observed `str "rtx"` for `/renderer/active` and
  `None: NoneType` for `/renderer/activeGpuIndex` [verified:
  evidence `renderer`, `gpu_found: null`]).

### Knobs + effect-of-change (each: type + unit + default)
- Knob key string: type `str` (unitless `/`-path); default: none
  exercised — required arg [verified: g1_probe.py L33-34].
  `/renderer/active` yields `renderer: str` (`"rtx"`, unitless)
  [verified]; `/renderer/activeGpuIndex` yields `gpu_found: None`
  (NoneType, unitless) on this box [verified]. Other keys
  untested [theoretical].
- Knob `settings.set()` (absent — read-only usage): would-be type
  `(key: str, value: Any) -> None` [theoretical]; unit n/a;
  default n/a. No `set()` calls anywhere in the pack; writing
  settings is out of scope [verified: no set call in
  g1_probe.py].

### EKB rules (IF/THEN/BECAUSE)
- IF you need the GPU the sim uses THEN use torch/warp enumeration,
  NEVER `/renderer/activeGpuIndex` BECAUSE it reads None here and is
  explicitly not a usable signal (failures.md G1) [verified].
- IF gating the renderer THEN assert `renderer == "rtx"` BECAUSE
  that is the observed + gated value (verify_g1.py gate
  `renderer-rtx`) [verified].
- IF `gpu_found` is None THEN record it and move on; do NOT fail
  BECAUSE it is explicitly not gated (failures.md G1: "Not gated.")
  [verified].

### LIMITS (with cites)
- `/renderer/activeGpuIndex` reads None — not usable, never gate
  (failures.md G1; evidence `gpu_found: null`) [verified].
- `/renderer/active` observed `rtx` only (evidence; gate
  `renderer-rtx`) [verified].
- Only two keys ever read; the rest of the settings tree is
  untouched by this pack [verified: g1_probe.py L32-34].

### UNKNOWN (theoretical)
- Whether activeGpuIndex ever yields a valid index on other configs
  (multi-GPU, non-RTX, headless) [theoretical].
- Full key space under `/renderer/*` and which keys are safe to gate
  [theoretical].
- Whether settings reads can raise for missing keys vs returning
  None (`.get` returned None here without error) [probable-None;
  still theoretical].

---

## 5. isaacsim.storage.native (public asset-root API)

### DOES
Returns the configured asset root and joins relative asset paths
without hardcoded endpoints. The ONLY sanctioned path to asset URLs
in this pack [verified: failures.md G2; g2_probe.py].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `get_assets_root_path() -> str` — params: none passed in drill
  (zero-arg call [verified: g2_probe.py L14]; any further params
  the API may accept [theoretical — unused here]). Return `str`
  (unit: URL string; observed tail
  `...amazonaws.com/Assets/Isaac/6.0`, classified `remote`,
  fetched in 0.0 ms [verified: g2_probe.py L14-15; evidence
  `root_ms`, `root_kind`, `root_tail`]).
- `path_join(root: str, rel: str) -> str` — param `root: str`
  (unit: URL string; no default — required; the root from
  get_assets_root_path, proven `str` by `.startswith` use
  [verified: g2_probe.py L16/L26]); param `rel: str` (unit:
  relative asset path, unitless; no default — required; 3 literal
  rels tried [verified: g2_probe.py L21-24]). Return `str` (unit:
  full asset URL for the resolver) [probable — never recorded;
  fed directly to Resolve(path: str)]. Called 3x (ti_radar,
  lidar_2d, missing) [verified: g2_probe.py L26].

### Knobs + effect-of-change (each: type + unit + default)
- Knob `rel` path: type `str` (unit: relative asset path,
  unitless); default: none — required arg [verified:
  g2_probe.py L21-24]. Known rels resolve True in ~1 ms; bogus
  rel `Isaac/Sensors/NOPE/No_Such_Sensor.usd` resolves False in
  ~889 ms [verified: evidence `ti_radar`, `lidar_2d`, `missing`].
- Knobs `ISAACSIM_ASSET_ROOT` / `ISAACSIM_ASSET_REGION_PROFILE`
  env: type `str | None` (unitless URL / profile name); default:
  None (absent) — both None in this drill = default hosted
  profile [verified: g2_probe.py L11-12; evidence]. Setting them
  would change the root; effect untested here [theoretical].
- Knob `root_kind` classifier in-probe: type `str` enum
  (`"remote" | "local" | "other"`, unitless); default: n/a
  (computed, not settable). startswith omniverse:///http ->
  remote; drive-letter/leading-slash -> local; else other
  [verified: g2_probe.py L16-18]. A `file://` or `nfs://` root
  would classify `other` [probable — code-read, untested].
- Knob `root_tail = root[-60:]`: type `str | None` (unit: chars
  of URL tail; None iff root falsy); default: n/a (derived).
  Evidence keeps only the last 60 chars; the full endpoint is
  intentionally NOT stored [verified: g2_probe.py L19].

### EKB rules (IF/THEN/BECAUSE)
- IF building any asset URL THEN always `get_assets_root_path()` +
  `path_join`, NEVER hardcode the endpoint BECAUSE roots move across
  profiles/regions/releases (failures.md G2; SKILL.md G2) [verified].
- IF either env override is set THEN the default-profile gate fails;
  re-baseline before comparing against G2 evidence BECAUSE G2 pins
  the default hosted profile only (verify_g2.py gate
  `default-profile`) [verified].
- IF root_ms >= 5000 THEN fail gate `root-fast` BECAUSE root
  resolution must be fast/cached (verify_g2.py L20; observed 0.0 ms)
  [verified].
- IF root_kind != remote THEN fail gate `root-remote` in this drill
  BECAUSE the pinned profile is S3-backed remote (verify_g2.py L18)
  [verified].

### LIMITS (with cites)
- Default hosted profile only: remote S3-backed root, no env
  overrides (failures.md G2; evidence `env_root/env_profile: null`,
  `root_kind: remote`) [verified].
- Root resolution 0.0 ms cached; known assets ~1 ms / 0.0 ms
  (failures.md G2; evidence) [verified].
- Only 3 rel paths ever joined (2 known + 1 bogus); no other asset
  families exercised [verified: g2_probe.py L21-24].
- `get_assets_root_path()` called with zero args only; any params it
  may accept are unused [verified].

### UNKNOWN (theoretical)
- Regional profiles, local packs, availability manifests (SKILL.md
  Limitations; upstream `isaac-sim-assets` workflows) [theoretical].
- Cold-cache / first-fetch latency for root and assets [theoretical].
- Behavior when offline or when the root host is unreachable (raise
  vs slow-None vs stale cache) [theoretical].
- Signature details beyond drill usage (optional args, sync/async)
  [theoretical].

---

## 6. pxr.Ar (USD asset resolver)

### DOES
Resolves joined asset URLs to confirm they exist. The existence
oracle for G2: True = asset there, False = clean miss [verified].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `Ar.GetResolver() -> ArResolver` — params: none (zero-arg call
  [verified: g2_probe.py L20]). Return resolver singleton (class
  name `ArResolver` [probable — object observed only via its
  `.Resolve` method]; unit: resolver handle).
- `resolver.Resolve(path: str) -> str` — param `path: str` (unit:
  URL string; no default — required; takes the path_join URL
  [verified: g2_probe.py L26-28]). Return `str` (unit: resolved
  path string; empty/falsy = clean miss) [probable — only
  truthiness observed via `bool(r: str [probable]) -> bool`:
  known assets True, bogus False [verified: g2_probe.py L28-29;
  evidence]].

### Knobs + effect-of-change (each: type + unit + default)
- Knob input URL: type `str` (unit: URL string); default: none —
  required arg [verified: g2_probe.py L26-28]. Selects the
  outcome: TI radar USD -> `resolved: bool = True` / 1.0 ms;
  Example_Rotary_2D USDA -> True / 0.0 ms; bogus NOPE path ->
  False / 888.6 ms [verified: evidence]. `ms: float` (unit:
  milliseconds, 1 decimal via `round(number: float, ndigits: int |
  None = None [probable-stdlib]) -> float` — drill passes `1`
  explicitly [verified: g2_probe.py L29/L32]).
- Knob miss-vs-hit latency: type `float` (`ms`, unit:
  milliseconds); default: n/a (measured, not settable). A miss
  costs ~3 orders of magnitude more wall time (~889 ms vs ~1 ms)
  but still returns — no hang, no raise [verified: failures.md
  G2; evidence `missing.ms: 888.6`].
- Knob per-asset try/except record `{resolved: False, err, ms}`:
  `resolved: bool` (unitless; False on raise), `err: str`
  (150-char `repr(e: BaseException) -> str`, unitless), `ms:
  float` (milliseconds) [verified-pattern: g2_probe.py L30-32].
  A resolver exception is a recorded miss, not a probe crash.
  Never fired in this drill (bogus path returned False, no
  exception) [verified].

### EKB rules (IF/THEN/BECAUSE)
- IF Resolve returns falsy THEN treat as clean miss (resolved False
  + latency), NOT an error BECAUSE the bogus path proves False is
  the designed miss signal (failures.md G2) [verified].
- IF Resolve raises THEN record err (150 chars) + ms and continue
  BECAUSE one asset's failure must not kill the remaining resolves
  (g2_probe.py L30-32) [verified-pattern; unfired here].
- IF miss latency is ~1 s THEN that is normal (observed 888.6 ms);
  only a hang (no return) would be a fault BECAUSE the gate asserts
  False-ness, not speed, on the missing asset (verify_g2.py gate
  `missing-clean`) [verified].
- IF R1/N2 config-reference loads fail downstream THEN re-run this
  resolver check first BECAUSE G2 pins the resolution layer beneath
  those loads (failures.md G2) [verified].

### LIMITS (with cites)
- Known assets resolve True in ~1 ms; bogus returns False in 889 ms
  — clean miss, no hang (failures.md G2; evidence) [verified].
- Gate `missing-clean` asserts `resolved is False` only — no upper
  latency bound on the miss path (verify_g2.py L25-26) [verified].
- Only 3 URLs ever resolved, all `.../Isaac/Sensors/...` USD/USDA;
  no textures/materials/caches tested [verified].
- Resolver instance shared across all 3 resolves (one GetResolver
  call); per-call resolver construction untested [verified].

### UNKNOWN (theoretical)
- Resolver behavior on malformed URLs, network outage, auth failure,
  or non-USD files [theoretical].
- Whether Resolve caches (2nd resolve of same URL faster?) —
  hit latencies 1.0/0.0 ms hint at caching but no repeat-resolve
  test exists [theoretical].
- Resolve timeout / hang threshold, if any [theoretical].
- Anchored vs relative path handling (all drill inputs are absolute
  joined URLs) [theoretical].

---

## 7. os.environ (env override check)

### DOES
Checks for asset-root env overrides. The default-profile gate input:
both keys must be absent [verified].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `os.environ.get(key: str, default: str | None = None) -> str |
  None` — param `key: str` (unitless env name; no default —
  required; drill passes `"ISAACSIM_ASSET_ROOT"` [verified:
  g2_probe.py L11]); param `default: str | None = None`
  (unitless; never passed explicitly — 1-arg `.get` form, None
  observed for the absent key [verified: g2_probe.py L11]).
  Return `str | None` (unitless value, or None when absent;
  observed None [verified: evidence `env_root: null`]; the `str`
  half [probable — no set value ever observed]).
- Same `os.environ.get(key: str, default: str | None = None) ->
  str | None` for key `"ISAACSIM_ASSET_REGION_PROFILE"`: `key:
  str` required [verified: g2_probe.py L12], `default: str |
  None = None` unpassed (unitless), return `str | None`
  (unitless; observed None [verified: evidence `env_profile:
  null`]; `str` half [probable]).

### Knobs + effect-of-change (each: type + unit + default)
- Knob `.get` default: type `str | None`, value `None` (unitless;
  1-arg `.get(key: str)` form returns None when absent [verified:
  g2_probe.py L11-12]). Setting either var (to any `str`) would
  flip gate `default-profile` to FAIL [probable — gate logic `is
  None and is None`, verify_g2.py L15-17; never fired].
- Knob downstream effect of a set override on
  get_assets_root_path output: type of effect [theoretical]
  (would-be `str` root of unknown form); unit: URL string;
  default: the default-hosted root (override absent [verified]).
  Untested in this pack [theoretical].

### EKB rules (IF/THEN/BECAUSE)
- IF either override is set THEN do not compare results against G2
  evidence BECAUSE G2 pins the default hosted profile only
  (failures.md G2) [verified].
- IF diagnosing a `root-remote` failure THEN check these two vars
  first BECAUSE a local override is the likeliest cause of a
  non-remote root [probable].
- IF recording env THEN use `.get` (None when absent), never
  `os.environ[...]` BECAUSE subscript raises KeyError and would
  crash the probe (g2_probe.py uses .get) [verified-pattern].

### LIMITS (with cites)
- Both must be None for this drill (failures.md G2; verify_g2.py
  default-profile gate) [verified].
- Only these two keys checked; any other ISAACSIM_*/USD_* env
  influence is invisible to G2 [verified: g2_probe.py L11-12].

### UNKNOWN (theoretical)
- Effect of setting either override (which wins, URL form, does the
  resolver follow it) [theoretical].
- Whether overrides are read once at import/first-call or live on
  every get_assets_root_path call [theoretical].

---

## 8. Local evidence verifiers (stdlib-only gates: json / sys / time)

### DOES
Gate recorded evidence JSON offline without a live sim: G1 7 gates,
G2 6 gates. Pure local logic — no Isaac/Kit imports [verified:
verify_g1.py, verify_g2.py].

### Functions + full signatures (each: param type + unit + default; return type + unit)
- `open(file: str, mode: str = "r", buffering: int = -1
  [probable-stdlib], encoding: str | None = None [probable-stdlib],
  errors: str | None = None [probable-stdlib], newline: str | None
  = None [probable-stdlib], closefd: bool = True [probable-stdlib],
  opener: Callable[..., int] | None = None [probable-stdlib]) ->
  TextIO` + `json.load(fp: TextIO, cls: type | None = None
  [probable-stdlib], object_hook: Callable | None = None
  [probable-stdlib], parse_float: Callable | None = None
  [probable-stdlib], parse_int: Callable | None = None
  [probable-stdlib], parse_constant: Callable | None = None
  [probable-stdlib], object_pairs_hook: Callable | None = None
  [probable-stdlib]) -> dict[str, Any]` — `open` param `file:
  str` (unitless path; required; `os.PathLike` also accepted
  [probable-stdlib — never passed]; EV = repo-relative
  `action-reasoner/skills/gpunuc/evidence/g1_devices.json` /
  `.../g2_assets.json`, run from repo root [verified:
  verify_g1.py L5/L14; verify_g2.py L5/L14]); `mode: str = "r"`
  (unitless; stdlib default, never passed explicitly here —
  verifiers read-only [probable-stdlib]); all other `open`/`load`
  params [probable-stdlib — never passed]. `json.load` return
  `dict[str, Any]` (unitless evidence map [verified: subscripted
  at verify_g1.py L15-27; verify_g2.py L15-26]).
- `json.dump(obj: dict[str, Any], fp: TextIO, skipkeys: bool =
  False [probable-stdlib], ensure_ascii: bool = True
  [probable-stdlib], check_circular: bool = True [probable-stdlib],
  allow_nan: bool = True [probable-stdlib], cls: type | None = None
  [probable-stdlib], indent: int | None = None
  [probable-stdlib], separators:
  tuple[str, str] | None = None [probable-stdlib], default:
  Callable | None = None [probable-stdlib], sort_keys: bool = False
  [probable-stdlib]) -> None` — probe-side write: `obj:
  dict[str, Any]` (unitless; required; the `out`/`d` map
  [verified: g1_probe.py L35-36; g1_drive.py L23-24; g2_probe.py
  L33-34]); `fp: TextIO` (unit: file handle; required;
  `open(EV, "w")` with `file: str` absolute evidence path +
  `mode: str = "w"` passed explicitly [verified: same lines]);
  `indent: int | None` (unit: spaces; stdlib default None
  [probable-stdlib]; drill passes `1` explicitly [verified]); all
  other kwargs [probable-stdlib — never passed].
  Return `None` (unitless).
- `gate(name: str, ok: Any, detail: str = "") -> None` — param
  `name: str` (unitless gate id; required); param `ok: Any`
  (unitless truthiness input, coerced via `bool(ok: Any) -> bool`;
  required); param `detail: str = ""` (unitless display string;
  default `""` [verified: def line]). Appends `(name: str,
  bool(ok): bool, detail: str)` tuple to module-level `gates:
  list[tuple[str, bool, str]]`. Local helper defined identically
  in both verifiers [verified: verify_g1.py L10-11 + calls L15-27;
  verify_g2.py L10-11 + calls L15-26]. Return `None` (unitless).
- `sys.exit(code: int | str | None = None [probable-stdlib]) ->
  NoReturn` — param `code: int | str | None` (unitless exit
  status; stdlib default None [probable-stdlib]; drill passes
  `0: int` iff all gates pass else `1: int` explicitly [verified:
  verify_g1.py L34; verify_g2.py L34]; the `str | None` halves
  [probable-stdlib — never passed here]). Raises SystemExit; no
  return (NoReturn).
- `print(*values: Any, sep: str = " ", end: str = "\n", file:
  TextIO | None = None [probable-stdlib], flush: bool = False
  [probable-stdlib]) -> None` — `values: Any` (unitless; drill
  passes one pre-formatted `str` per call, e.g. `"PASS <name>
  <detail>"`, `"G1-PASS 7/7"` [verified: verify_g1.py L30-33;
  verify_g2.py L30-33]); `sep: str = " "` / `end: str = "\n"`
  (unitless stdlib defaults, never overridden [probable-stdlib]);
  `file`/`flush` [probable-stdlib — never passed]. Return `None`
  (unitless).
- `time.time() -> float` — params: none (zero-arg calls
  [verified: g2_probe.py L13/L15/L25/L29/L32]). Return `float`
  (unit: seconds since the epoch [probable-stdlib]; numeric type
  proven by subtraction/multiply in-probe [verified]). Latency
  pattern `round((time.time()-t0)*1000, 1): float` (unit:
  milliseconds, 1 decimal) around root fetch and each resolve
  [verified: g2_probe.py L13-15, L25-29].

### Knobs + effect-of-change (each: type + unit + default)
- Knobs G1 gates (7, all must pass; each `ok: Any` truthiness,
  unitless; no defaults — each `ok` expression required):
  single-gpu (`torch_cuda: bool and torch_ndev: int == 1`),
  warp-cuda0 (`"cuda:0" in warp_devices: list[str]`),
  cuda-select (`cuda_device: str == "cuda:0"`), cuda1-rejected
  (`cuda1_rejected: bool is True`), healthy-after
  (`final_device: str == "cuda:0"`), engine-physx
  (`active_engine: str == "physx"`), renderer-rtx (`renderer: str
  == "rtx"`) [verified: verify_g1.py L15-27].
- Knobs G2 gates (6, all must pass; each `ok: Any`, unitless; no
  defaults): default-profile (`env_root: str | None is None and
  env_profile: str | None is None`), root-remote (`root_kind: str
  == "remote"`), root-fast (`root_ms: float < 5000`), ti-resolves
  (`ti_radar.resolved: bool`), lidar-resolves
  (`lidar_2d.resolved: bool`), missing-clean (`missing.resolved:
  bool is False`) [verified: verify_g2.py L15-26].
- Knob threshold `root_ms: float < 5000` (unit: milliseconds; no
  default — literal bound): observed 0.0 ms; a 5 s+ root fetch
  fails [verified: verify_g2.py L20]. No latency bound on
  resolves (hits or miss) [verified].
- Knob detail strings: type `str` (unitless; e.g. `ndev=...`,
  tail slice, `%.0fms`); default `""` when unpassed (gate def
  default [verified: verify_g1.py L10; verify_g2.py L10]).
  Display-only; pass/fail depends solely on the `ok` expression
  [verified: verify_g1.py L10-11; verify_g2.py L10-11].

### EKB rules (IF/THEN/BECAUSE)
- IF any gate FAILs THEN exit 1 with `G1-FAIL n/7` / `G2-FAIL n/6`
  BECAUSE one red gate voids the drill claim (both verifiers L29-34)
  [verified].
- IF re-running probes THEN run g1_probe BEFORE g1_drive BECAUSE
  drive loads + extends probe's JSON (`json.load(open(EV))` at
  g1_drive.py L7; drive without probe crashes on missing file)
  [verified].
- IF running verifiers THEN run from the repo root BECAUSE EV paths
  are repo-relative (`action-reasoner/skills/...`, verify_*.py L5)
  [verified].
- IF comparing latencies THEN note hits are ~ms and the miss ~889
  ms BECAUSE that asymmetry is the verified clean-miss signature,
  not noise (evidence g2_assets.json) [verified].

### LIMITS (with cites)
- G1 7/7 green, G2 6/6 green on Isaac Sim 6.0.0/Kit 110 + RTX 3050
  (SKILL.md metadata) [verified].
- Verifiers read evidence only; they cannot detect a stale JSON
  (no timestamp/hash freshness check) — re-run probes before
  trusting a PASS [verified: no freshness logic in either file].
- `warp-cuda0` uses membership (`in`), not exact equality — extra
  devices pass [verified: verify_g1.py L17].
- `missing-clean` has no latency bound — a 60 s False still passes
  [verified: verify_g2.py L25-26].
- Evidence truncation: torch_err/warp_err 150 chars, cuda1_err 200,
  cuda_backend_err 120, resolver err 150, root_tail 60 — long values
  are cut [verified: probe sources].

### UNKNOWN
- None; pure local gating logic [verified — TOOLS.md agrees].

---

## Unverified / cross-tool unknowns

- Multi-GPU device reporting/selection/distribution (single-GPU box
  bound) [theoretical].
- Regional asset profiles, local asset packs, availability manifests
  (deferred to `isaac-sim-assets`) [theoretical].
- Cold-cache asset fetch latency; offline/network-failure resolver
  behavior [theoretical].
- SimulationManager.set_device variants beyond `"cuda"` / `"cuda:1"`
  [theoretical].
- Non-PhysX engines, non-RTX renderers, non-numpy backends through
  this probe path [theoretical].
- Whether `/renderer/activeGpuIndex` is ever valid elsewhere
  [theoretical].
- torch-vs-warp disagreement modes (one sees a GPU the other hides)
  [theoretical].
- g1_probe/g1_drive/g2_probe run INSIDE Isaac Sim (Kit python) only;
  none are runnable from a plain local python (carb/isaacsim/pxr
  imports) — verifiers alone are local-runnable [verified: imports
  at probe tops].
