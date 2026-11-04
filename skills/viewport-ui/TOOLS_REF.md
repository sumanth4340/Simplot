# Viewport-UI TOOLS_REF (FULL-TOOL-MASTERY, 2026-11-04)

DATATYPE pass (2026-11-04): signatures typed 65/65, knobs typed 41/41, still-unknown 0. (Counts: 13 scripts re-verified — 8 pack-local + 5 library — plus 13 evidence JSONs; no other file touched.)

Claim tags: [verified] = drilled live in this pack's evidence/scripts, [probable] = read in library/source but not drilled here, [theoretical] = inferred, not observed.
Library sources: `Downloads/IsaacSim-release-6.3/.../skills/isaac-sim-remote/scripts/*.py` (6.3; pack drilled against Isaac Sim 6.0.0/Kit 110 — drift possible).
Pack doc note: SKILL.md is absent in this pack; README.md is the pack doc. TOOLS.md "Sources-read" line claiming SKILL.md is stale.

## 1. isaacsim_send.py (bridge CLI, local)

DOES: [verified] Sends inline code / stdin / `--file` scripts from OUTSIDE into the running sim's python_server over loopback TCP `127.0.0.1:8226` and returns a JSON envelope `{status, output, result, ...}`. This pack consumes only the reply JSON (`status == "ok"` + output markers); every `evidence/*.json` is one such reply.

Functions + full signatures ([probable] from source; usage [verified]):
- `send_and_receive(host: str, port: int, source: str, timeout: float = 60.0) -> dict[str, Any]` — one TCP request/response: `asyncio.open_connection`, `write(source)`, `write_eof`, reads full reply, `json.loads`. Returns envelope dict (keys `status, output, result, ...`). Units: host = IP/hostname string (loopback); port = TCP port number; source = payload text (Python or JSON); timeout = seconds (connect AND read waits). Defaults: timeout 60.0; host/port/source required. Def: isaacsim_send.py:72; call sites isaacsim_send.py:229,301 (both pass `args.host: str, args.port: int, source: str, args.timeout: float`).
- `_parse_arg_value(value: str) -> Any` — `ast.literal_eval` with raw-string fallback. `"60"` -> int 60, `"True"` -> bool, `"play"` -> str. Param: value = raw CLI text after `=` (str, required, unitless). Returns `int | float | bool | None | list | dict | str`. Def: isaacsim_send.py:85; call sites isaacsim_send.py:106,123,145.
- `_inject_args(source: str, args: list[str]) -> str` — prepends `key = repr(parsed)` global lines for each `k=v`. Both params required, no defaults; unitless (Python source text; `k=v` CLI strings). Def: isaacsim_send.py:97; call sites isaacsim_send.py:251,257.
- `_wrap_isolated(source: str, args: list[str]) -> str` — wraps `--file` body in `async def _isolated_script():` + `await _isolated_script()`; args become function locals. Top-level `await` works inside. Both params required, no defaults; unitless. Def: isaacsim_send.py:110; call site isaacsim_send.py:253.
- `_parse_args_kv(arg_list: list[str]) -> dict[str, Any]` — k=v list to typed dict (envelope mode). Param required, no default; unitless. Def: isaacsim_send.py:138; call site isaacsim_send.py:277.
- `_needs_envelope(args: argparse.Namespace) -> bool` — True if `--json-envelope/--context/--fire-and-forget/--execution-timeout/--args-json/--introspect` present. Param required, no default; unitless. Def: isaacsim_send.py:149; call sites isaacsim_send.py:250,256,266.
- `async main() -> None` — CLI entry; no params, no return value (exits via `sys.exit(int)`); exit 0 iff `status == "ok"`. Def: isaacsim_send.py:161; entry isaacsim_send.py:335 `asyncio.run(main())`.

Knobs (CLI flags) + effect-of-change:
- `code` positional [probable]: type `str | None`; unit none (Python source text); default None (= omitted -> reads stdin). Omitted + no `--file` -> reads stdin. Empty after strip -> exit 1 "No code provided".
- `--file/-f <path>` [verified]: type `str | None` (filesystem path); unit none; default None (= inline/stdin mode). Script file to send. Pack sends w1/v8 builds + all 4 library scripts this way.
- `--arg/-a k=v` (repeatable) [verified]: type `list[str]`; unit none (`k=v` strings); default `[]`. Injected variable. Changing value changes the in-sim global (e.g. `output_path`, `action=set`, `position=3,-3,2`). Type inference via literal_eval: `num_steps=60` arrives as int. With `--file` + no envelope flags -> function-local via `_wrap_isolated`; with envelope flags -> global via `_inject_args`.
- `--host` (type str, IP/hostname, default `"127.0.0.1"`) / `--port` (type int, TCP port number, default `8226`) [probable]: endpoint. Wrong port -> `ConnectionRefusedError` -> exit 1.
- `--timeout <float>` (type float, unit seconds, default 60.0) [probable]: client TCP wait (connect AND read). Raising tolerates slow sim calls; exceeding raises `asyncio.TimeoutError` -> exit 1.
- `--raw` (type bool flag, default False) [verified]: prints raw JSON envelope (`json.dumps(result, indent=2)`). Without it, prints `output` human-readable + `=> result` + errors to stderr. Pack evidence files are raw envelopes.
- `--dry-run` (type bool flag, default False) [probable]: prints final payload (post wrap/inject/envelope), exits 0 without connecting. Payload inspection only.
- `--no-isolate` (type bool flag, default False) [probable]: skips function-wrap; script shares executor globals (state persists across calls). Default wrap prevents variable leakage.
- `--json-envelope/-j` (type bool flag, default False) [probable]: forces `{"code": ...}` envelope even with no other envelope flag.
- `--context/-c <name>` (type `str | None`, context name, default None) [probable]: persistent named namespace server-side; skips isolation, uses `_inject_args` globals.
- `--fire-and-forget/--ff` (type bool flag, default False) [probable]: immediate ACK with `task_id`, code runs in background. Non-raw prints `task_id` and exits 0.
- `--execution-timeout/-t <float>` (type `float | None`, unit seconds, default None = no server timeout; 0 = no limit) [probable]: server-side per-request timeout (`envelope["timeout"]`); 0 = no limit. Different knob from `--timeout` (client TCP).
- `--args-json '<json object>'` (type `str | None`, JSON object text, default None) [probable]: merges into `envelope["args"]` over `--arg` pairs. Non-object or bad JSON -> exit 1.
- `--introspect COMMAND` (type `str | None`, enum `status|contexts|context|tasks|task|delete_context`, default None) [probable]: no code execution; sends `{"introspect": CMD}` (+ `context`, + `task_id` from positional `code`). Commands: `status|contexts|context|tasks|task|delete_context`. Raw prints full envelope; non-raw prints `result` or ERROR + exit 1.

EKB rules:
- IF sending a `--file` script with `--arg k=v` and no envelope flags THEN the sim sees `k` as a function-local BECAUSE `_wrap_isolated` indents args + body into `_isolated_script` [probable].
- IF raw reply JSON is needed for a verifier THEN pass `--raw` and `json.loads` stdout, reading `body["output"]` + `body["traceback"]` BECAUSE raw mode prints the full envelope as JSON [verified].
- IF two scripts must not share state THEN use default isolation (no `--no-isolate`, no `--context`) BECAUSE the executor shares globals and wrapping scopes each script [probable].
- IF a call may take >60 s THEN raise `--timeout` BECAUSE both connect and read waits use it [probable].
- IF exit code is 1 THEN either sim returned `status == "error"` or the TCP layer failed BECAUSE `main` exits 0 iff `status == "ok"` [probable].

LIMITS:
- [verified] Reply contract this pack relies on: `status` key + `output` string markers ("Saved viewport screenshot", "Saved app screenshot", "Selected 1 prim(s)", "Position (x, y, z):"); `result` is null in all 13 evidence JSONs.
- [probable] `--file` read with bare `open(args.file)` (no encoding) — non-UTF8-default locales could misread exotic script bytes (source line 248).
- [probable] `--arg` without `=` yields `key = ''` (partition fallback) — silently injects an empty string, no error.
- [probable] Envelope mode `merged_args.update(json_args)`: `--args-json` keys silently override same-named `--arg` keys.
- [verified] Sim can crash mid-probe (one crash during a viewport screenshot; discovery.md "GUI vs headless") — recovery is taskkill tree + relaunch + health poll; evidence on disk survives.

UNKNOWN (theoretical): retry/backoff behavior on transient failure (zero hiccups observed); `--context` namespace lifetime across sim restarts; `--fire-and-forget` result retrieval beyond `task_id` ACK; max payload size; whether `--timeout` covers `--execution-timeout`-bound server work (client read still times out first).

## 2. viewport_screenshot.py (isaac-sim-remote library, in-sim via --arg)

DOES: [verified] Captures the viewport render to `output_path` as PNG. Evidence: `w1_viewport.png` 171821 B, `w2_before/after.png`, `w4_viewA/B.png`, `v8_viewport.png` 80105 B — all via `--arg output_path=...`.

Functions + full signatures ([probable] from source; behavior [verified]):
- `async _capture() -> None` — no params (reads injected global `output_path: str`); returns None. Enables `isaacsim.test.utils` extension if off (+ `await update_app_async(steps=5)`), calls `capture_viewport_screenshot_async(output_path)`, prints `Saved viewport screenshot: {output_path}`. Raises `RuntimeError` if extension enable fails or capture throws (chained `from exc`). Def: viewport_screenshot.py:33; call site: viewport_screenshot.py:55 `await _capture()`. Sub-calls: `app_utils.is_extension_enabled(name: str) -> bool` / `app_utils.enable_extension(name: str) -> bool` / `app_utils.update_app_async(steps: int) -> Coroutine[None]` [probable — inferred from call sites viewport_screenshot.py:41,42,44; name unitless, steps unit = app update steps, no defaults observed].
- Module level: `await _capture()` — runs on import; works because `_wrap_isolated` makes the body an async function [probable].
- Backend: `isaacsim.test.utils.image_capture.capture_viewport_screenshot_async(output_path: str) -> Coroutine[None]` [probable — signature inferred from call site viewport_screenshot.py:49, backend source not read]. Param: PNG path string (required, no default); awaited; no return value consumed.

Knobs + effect-of-change:
- `output_path: str` (injected global; default `str(Path(tempfile.gettempdir()) / "viewport_capture.png")`; unit = filesystem path, must end `.png`) [verified]: destination PNG. MUST be non-empty and end in `.png` or the script raises `ValueError` before any sim call [probable]. Changing it only changes where bytes land; capture size follows the viewport, not the path. Def: viewport_screenshot.py:26-27; gate: viewport_screenshot.py:29-30.
- No resolution knob exists in this script [probable]: output was fixed 1280x720 RGBA in GUI mode [verified] and headless alike (W1 ran headless) [verified].

EKB rules:
- IF the verifier needs the save marker THEN grep output for `Saved viewport screenshot` BECAUSE that exact `print` only runs after the backend await succeeds [verified].
- IF capture is the first call in a fresh sim THEN allow the extra 5 update steps BECAUSE the script auto-enables `isaacsim.test.utils` first [probable].
- IF output shows `Saved image to ... with shape (720, 1280, 4)` THEN the capture path ran end-to-end BECAUSE that line is printed by the backend before the script's own marker (seen in `w1_shot.json`) [verified].

LIMITS:
- [verified] Fixed 1280x720 RGBA in GUI mode; works identically headless (discovery.md; `w1_viewport.png` 171821 bytes).
- [verified] One sim crash observed during a viewport screenshot (discovery.md "GUI vs headless").
- [probable] `.png` suffix enforced (`ValueError` otherwise); no JPEG/other-format path.
- [probable] Captures the (single) active viewport — script takes no viewport selector.

UNKNOWN (theoretical): behavior with multiple viewports; non-default viewport resolution settings; capture-while-paused; whether the extension auto-enable persists for later calls in the session.

## 3. app_screenshot.py (isaac-sim-remote library, in-sim via --arg)

DOES: [verified] Captures the full application window including UI chrome to `output_path` as PNG via `omni.kit.renderer.capture` swapchain capture. Evidence: `w3_app.png` 164993 B, `v8_app.png` 215780 B.

Functions + full signatures ([probable] from source; behavior [verified]):
- `async _capture() -> None` — no params (reads injected global `output_path: str`); returns None. Identical shape to viewport variant: enables `isaacsim.test.utils` if off (+ 5 update steps), calls `capture_app_screenshot_async(output_path)`, prints `Saved app screenshot: {output_path}`. `RuntimeError` on enable/capture failure. Def: app_screenshot.py:36; call site: app_screenshot.py:58 `await _capture()`. Sub-calls: `app_utils.is_extension_enabled(name: str) -> bool` / `app_utils.enable_extension(name: str) -> bool` / `app_utils.update_app_async(steps: int) -> Coroutine[None]` [probable — inferred from call sites app_screenshot.py:44,45,47; same units as §2].
- Module level: `await _capture()` [probable].
- Backend: `isaacsim.test.utils.image_capture.capture_app_screenshot_async(output_path: str) -> Coroutine[None]` [probable — inferred from call site app_screenshot.py:52, backend source not read]. Param: PNG path string (required, no default); awaited; no return value consumed.

Knobs + effect-of-change:
- `output_path: str` (injected global; default `str(Path(tempfile.gettempdir()) / "app_capture.png")`; unit = filesystem path, must end `.png`) [verified]: destination PNG; same non-empty + `.png` `ValueError` gate [probable]. Def: app_screenshot.py:29-30; gate: app_screenshot.py:32-33.
- No resolution knob [probable]: output size follows the window — 958x981 in the GUI session [verified] (discovery.md; `w3_app.png`, `v8_app.png`).

EKB rules:
- IF the verifier needs the save marker THEN grep for `Saved app screenshot` BECAUSE it prints only after the backend await succeeds [verified].
- IF the PNG decodes at an odd size THEN compare against the live window size, not 1280x720, BECAUSE app capture follows the window while viewport capture is fixed [verified].
- IF choosing between the two capture scripts THEN viewport = render only (stable size), app = render + UI chrome (window-sized) BECAUSE they call different backends [verified].

LIMITS:
- [verified] Output size follows the window (958x981 GUI session; `w3_app.png` 164993 B, `v8_app.png` 215780 B).
- [probable] Same `.png`-only gate as viewport variant; no viewport/window selector knob.
- [probable] Docstring claims it works in `--no-window` headless too — but this pack never drilled that (see UNKNOWN).

UNKNOWN (theoretical): headless behavior in THIS pack's sim version (only GUI captures evidenced; library docstring says headless works — contradicts TOOLS.md's UNKNOWN framing, needs a live probe); multi-monitor/window-focus effects; whether UI overlays (menus, popups) appear deterministically.

## 4. camera_control.py (isaac-sim-remote library, in-sim via --arg)

DOES: [verified] Gets/sets the active viewport camera pose and aims it at a target. Drilled: `get` (pose exact to <0.05/axis), `look_at`/`set` with eye+target. `list_cameras` named in discovery.md but zero evidence samples.

Functions + full signatures ([probable] from source; drilled behavior [verified]):
- `_parse_floats(val: str | list | tuple | None) -> list[float] | None` — comma-split + float(). Accepts injected list/tuple (via literal_eval) or `"x,y,z"` string. Returns None only for None input. Param required, no default; units element-dependent (meters for position/target x,y,z). List/tuple elements: `float(x)`-coercible (`int | float | str`). Def (untyped in source): camera_control.py:52; body camera_control.py:59-63; call sites camera_control.py:108,109,141,142.
- `_get_active_camera_path() -> str` [probable] — no params. `omni.kit.viewport.utility.get_active_viewport().camera_path` (camera_control.py:72-75). The single source of "active camera". Return is str-able path (callers coerce via `str()`); observed `/OmniverseKit_Persp` in evidence. Call sites: camera_control.py:81,158. Sub-call `get_active_viewport() -> viewport` [probable — backend source not read; no params].
- `_resolve_camera() -> str` [probable] — no params; reads injected global `camera_path: str | None`. Returns injected `camera_path` if truthy else `_get_active_camera_path()` (camera_control.py:78-81). Call sites: camera_control.py:85,105,139.
- `action == "get"` branch — prints `Camera: {path}`, `Position (x, y, z): {numpy pos}`, `Orientation (w, x, y, z): {numpy quat}` via `xform.get_world_pose(path: str) -> tuple[pos: np.ndarray(3,), rot: np.ndarray(4,)]` [probable — inferred from call sites camera_control.py:87,163; pos unit meters, rot = quat (w,x,y,z) dimensionless]; then focal length + clipping range via `Camera(paths: str) -> Camera` [probable — call sites camera_control.py:94,129] `.get_focal_lengths() -> np.ndarray` (mm, `[0]`-indexed 1-D) / `.get_clipping_ranges() -> np.ndarray` [probable — call sites camera_control.py:95-96], with `prim_utils.get_prim_attribute_value(path: str, attr: str) -> Any` [probable — call site camera_control.py:98] fallback [verified output shape in `w2_get.json`, `w4_getA/B.json`, `v8_get.json`].
- `action == "set"` branch — parses `position` (-> eye) and `target`; calls `ViewportManager.set_camera_view(camera: str, eye: list[float] | None = None, target: list[float] | None = None) -> None` [probable — inferred from call site camera_control.py:117 `set_camera_view(cam_str, **kwargs)` with kwargs keys `eye`/`target`; eye/target units meters x,y,z] with whichever is not None, then `app_utils.update_app(steps: int = 30) -> None` [probable — call site camera_control.py:118; steps unit = app update steps]; optionally `cam_obj.set_focal_lengths(values: np.ndarray(1,) float) -> None` [probable — call site camera_control.py:130 `np.array([float(focal_length)])`; unit mm] [probable source; pose-set effect verified].
- `action == "look_at"` branch — REQUIRES `target` (raises `ValueError` without it); optional `position` as eye; same `set_camera_view(camera: str, eye: list[float] | None, target: list[float]) -> None` + 30 update steps (call sites camera_control.py:147-148) [verified via W2/W4/V8 poses].
- `action == "list_cameras"` branch — `stage_utils.get_current_stage() -> Usd.Stage` [probable — call site camera_control.py:156, no params]; traverses stage (`stage.Traverse() -> Iterator[Usd.Prim]` [probable — call site camera_control.py:157]) for `GetTypeName() -> str == "Camera"` [probable — call site camera_control.py:157], prints `Cameras (N):` + `  {path}[ (active)] — pos={pos}` per prim (`cam_prim.GetPath() -> Sdf.Path` [probable] + `str()` coercion, call site camera_control.py:161) [probable — never drilled in this pack].
- Unknown action -> prints `ERROR: Unknown action '...'` (exit still ok — it is a print, not raise) [probable].
- Backends (from imports; sources not read): `isaacsim.core.experimental.utils.app.update_app(steps: int) -> None`, `.utils.xform.get_world_pose(path: str) -> tuple[np.ndarray, np.ndarray]`, `.utils.prim.get_prim_attribute_value(path: str, attr: str) -> Any`, `.utils.stage.get_current_stage() -> Usd.Stage`, `.objects.Camera(paths: str) -> Camera`, `isaacsim.core.rendering_manager.ViewportManager.set_camera_view(camera: str, eye: list[float] | None, target: list[float] | None) -> None` [all probable — see bullets above for call sites].

Knobs (injected globals) + effect-of-change:
- `action: str` default `"get"` [verified]: type str; unit none (enum `get|set|look_at|list_cameras`). Unknown value -> ERROR print, no-op. Def: camera_control.py:38-39.
- `camera_path: str | None` default None [probable]: unit none (USD prim path). Overrides active camera. None -> active viewport camera (`/OmniverseKit_Persp` here [verified]). Non-existent path effect untested. Def: camera_control.py:40-41.
- `position: str | list | tuple | None` default None [verified]: unit meters (eye x,y,z). In `set`: omitted -> orientation/target-only update; in `look_at`: omitted -> re-aim in place. Format `"3,-3,2"` or injected list. Def: camera_control.py:42-43.
- `target: str | list | tuple | None` default None [verified]: unit meters (look-at x,y,z). Optional in `set`, MANDATORY in `look_at` (`ValueError` if missing). Def: camera_control.py:46-47.
- `orientation: str | list | tuple | None` default None [probable]: unit none (would-be quat w,x,y,z, dimensionless) — parsed by `_parse_floats`? NO — read but NEVER USED anywhere in the script body (dead knob; orientation can only change via eye/target aim). Def: camera_control.py:44-45.
- `focal_length: float | str | None` default None [probable]: unit mm (coerced via `float()` at camera_control.py:130). Only honored in `set`; calls `set_focal_lengths`. Ignored in `get`/`look_at`/`list_cameras`. Undrilled. Def: camera_control.py:48-49.
- Fixed internal: 30 update steps after every set/look_at [verified via discovery.md]; type int, unit app update steps, not a knob (hardcoded at camera_control.py:118,148).

EKB rules:
- IF parsing a `get` pose THEN regex `Position \(x, y, z\): \[\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)` with 0.05/axis tolerance BECAUSE numpy prints variable spacing (`[ 3. -3.  2.]` vs `[-3.   2.5  2.5]`) and verify_w2 proves the tolerance [verified].
- IF aiming the camera THEN prefer `look_at` with eye+target over `set` BECAUSE `look_at` guarantees the aim contract (target mandatory) while `set` allows eye-only moves that keep a stale orientation [verified].
- IF `set`/`look_at` reports success THEN still `get` + screenshot to confirm BECAUSE the ack prints the REQUESTED values, not a re-read (the 30 update steps are fire-and-forget settle) [probable].
- IF `orientation` seems ignored THEN that is correct — the script never consumes it; aim via eye/target instead [probable].
- IF focal length must change THEN use `action=set` with ONLY `focal_length` (no position/target) BECAUSE the `set` branch skips `set_camera_view` when both are None but still applies focal length [probable].

LIMITS:
- [verified] Active camera is the root-level default `/OmniverseKit_Persp` (README.md, discovery.md, all `*_get*.json`).
- [verified] Pose set is exact to <0.05 per axis (verify_w2 checks x~3, y~-3, z~2; `w4_getB` shows [-4,3,3] exact).
- [probable] `set`/`look_at` settle = fixed 30 update steps; no knob, no completion check.
- [probable] `orientation` knob is dead (accepted, never used).
- [probable] Unknown `action` is a printed ERROR, not an exception — envelope `status` stays "ok", so verifiers must grep output, not just status.

UNKNOWN (theoretical): `list_cameras` output format live (source shows `Cameras (N):` + ` — pos=` lines but zero evidence samples); behavior when a non-Persp camera is active or `camera_path` points at a missing prim; whether 30 steps suffice for heavy scenes; `set_focal_lengths` units/range validation; `orientation` dead-knob status in the 6.0-era script version (source read is 6.3).

## 5. select_prim.py (isaac-sim-remote library, in-sim via --arg)

DOES: [verified] Manipulates the USD stage selection set. Drilled: `set` + `get` round-trip exactly (`/World/W1Cube`, `/World/V8CubeB`). `clear`/`all` named in discovery.md, zero evidence samples.

Functions + full signatures ([probable] from source; set/get behavior [verified]):
- `action == "get"` — `sel.get_selected_prim_paths() -> list[str]` [probable — call sites select_prim.py:37,61; no params; unit none, USD prim paths]; prints `Selected (N):` + `  {p}` lines, or `No prims selected` when empty [verified shape in `w3_get.json`].
- `action == "set"` — REQUIRES `prim_path` (prints `ERROR: prim_path required...` WITHOUT raising if missing — envelope stays ok); splits on comma, strips, `sel.set_selected_prim_paths(paths: list[str], replace: bool) -> None` [probable — call site select_prim.py:50 `set_selected_prim_paths(paths, True)`; second arg bool, replace semantics inferred]; prints `Selected {N} prim(s):` + paths [verified in `w3_set.json`, `v8_sel.json`].
- `action == "clear"` — `sel.clear_selected_prim_paths() -> None` [probable — call site select_prim.py:56; no params]; prints `Selection cleared` [probable — undrilled].
- `action == "all"` — `sel.select_all_prims(stage_url: str) -> None` [probable — call site select_prim.py:60]; prints `Selected all prims (N):` + first 20 paths + `  ... and {N-20} more` if N>20 [probable — undrilled].
- Unknown action -> prints `ERROR: Unknown action '...'` (no raise) [probable].
- Backends: `omni.usd.get_context() -> UsdContext` (no params), `ctx.get_selection() -> Selection` (no params), `ctx.get_stage_url() -> str` (no params) [all probable — canonical types in §7; call sites select_prim.py:33,34,60].

Knobs (injected globals) + effect-of-change:
- `action: str` default `"get"` [verified]: unit none (enum `get|set|clear|all`). Unknown -> ERROR print, no-op, status still ok. Def: select_prim.py:26-27.
- `prim_path: str | None` default None [verified]: unit none (single USD path or comma-separated multi; split+strip at select_prim.py:49). Single path or comma-separated multi (`"a,b"` -> split+strip). Only consumed by `set`; missing/empty in `set` -> ERROR print (NOT an exception, unlike camera `look_at`'s ValueError) [probable]. Def: select_prim.py:28-29.

EKB rules:
- IF verifying a `set` THEN follow with `get` and grep for the prim path BECAUSE the `set` ack echoes the REQUEST (`Selected N prim(s):` + requested paths), proving only the call ran, while `get` reads live selection state [verified — verify_w3 checks both].
- IF selecting several prims THEN pass one comma-separated `prim_path` BECAUSE the script splits on `,` itself [probable].
- IF the ERROR print appears THEN check `status` anyway BECAUSE both `set`-without-path and unknown-action are prints, so the envelope still reports ok [probable].
- IF output is `No prims selected` THEN selection is genuinely empty BECAUSE `get` prints that only when the path list is falsy [probable].

LIMITS:
- [verified] Set/get round-trips exactly (verify_w3: set W1Cube -> get shows W1Cube; verify_v8: `/World/V8CubeB`).
- [probable] `set` replaces selection (`set_selected_prim_paths(paths, True)` — second arg True), it does not add; multi-set ordering = request order echo, live order unverified.
- [probable] `all` prints at most 20 paths (+ overflow line) — full list truncated in output.
- [probable] Missing-`prim_path` and unknown-action failures are silent at the envelope level (prints, status ok).

UNKNOWN (theoretical): `clear`/`all` live output contracts (source-read, zero evidence); multi-prim live ordering; behavior on invalid/nonexistent paths (ack echo vs real selection); `set_selected_prim_paths(paths, True)` second-arg semantics (source-inferred replace flag).

## 6. w1_build.py / v8_build.py (pack-local scene authorship, in-sim)

DOES: [verified] Build the screenshot scenes idempotently: cleanup stale prims -> dome + sun -> ground -> cube(s) -> marker print. W1: 1 cube (1.0 at (0,0,0.5)); V8: 2 cubes (0.5 at (0.9,0,0.25); 1.0 at (-0.8,0.4,0.5)). Markers `W1-BUILD-OK ...` / `V8-BUILD-OK ...` captured in `w1_build.json` / `v8_build.json`.

Functions + full signatures ([verified] — both scripts read fully; straight-line, no defs; canonical USD API types in §7-§8):
- Cleanup loop: `for p in tuple[str, ...]: o = stage.GetPrimAtPath(p: str) -> Usd.Prim [probable]; if o and o.IsValid() -> bool: stage.RemovePrim(p: str) -> bool [probable, return unused]` — W1 list has 18 paths (V7*, W1*, M4*, PhysicsScene), V8 list has 17 (W1*, V8*, M4*, PhysicsScene). Idempotent rebuild [verified]. Call sites: w1_build.py:11-21, v8_build.py:10-20.
- `UsdLux.DomeLight.Define(stage: Usd.Stage, path: str) -> DomeLight [probable]` + `GetIntensityAttr() -> Usd.Attribute [probable]` `.Set(value: float) -> bool [probable]` (intensity unitless multiplier; all params required) [verified]. Call sites: w1_build.py:23-24, v8_build.py:22-23.
- `UsdLux.DistantLight.Define(stage: Usd.Stage, path: str) -> DistantLight [probable]` + intensity `.Set(1500.0|1200.0: float) -> bool [probable]` + `UsdGeom.Xformable(prim: Usd.Prim) -> Xformable [probable]` `(sun.GetPrim() -> Usd.Prim [probable], no params)` `.AddRotateXYZOp() -> XformOp [probable]` `.Set(value: Gf.Vec3f) -> bool [probable]` (unit degrees XYZ) [verified]. Call sites: w1_build.py:25-27, v8_build.py:24-26.
- `UsdGeom.Plane.Define(stage: Usd.Stage, path: str) -> Plane [probable]` + `CreateWidthAttr() -> Usd.Attribute [probable]` `.Set(value: float meters) -> bool [probable]` + `CreateLengthAttr() -> Usd.Attribute [probable]` `.Set(value: float meters) -> bool [probable]` [verified]. Call sites: w1_build.py:28-30, v8_build.py:27-29.
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: str) -> Cube [probable]` + `GetSizeAttr() -> Usd.Attribute [probable]` `.Set(size: float meters) -> bool [probable]` — edge length in meters (size 1.0 = 1m cube) [verified] + `UsdGeom.Xformable(cube.GetPrim()).AddTranslateOp() -> XformOp [probable]` `.Set(value: Gf.Vec3d(x: float, y: float, z: float)) -> bool [probable]` (unit meters, double-precision) [verified]. Call sites: w1_build.py:31-33, v8_build.py:30-34.

Knobs (hardcoded constants) + effect-of-change:
- Dome intensity (type float, unit USD intensity multiplier [probable]; defaults 400.0 W1 / 300.0 V8; set at w1_build.py:24, v8_build.py:23) [verified]: ambient fill. Lowered in V8 vs W1; both scenes verify (mean gates pass) — exact lux-to-mean mapping uncalibrated.
- Sun intensity (type float, same unit; defaults 1500.0 W1 / 1200.0 V8; set at w1_build.py:26, v8_build.py:25) [verified]: key light. Same caveat.
- Sun angle `Gf.Vec3f(-50, 20, 0)` (type Gf.Vec3f of float, unit degrees XYZ, same both builds; set at w1_build.py:27, v8_build.py:26) [verified]: elevation/azimuth of the distant light. Changing it moves shadows/highlights; symmetric-scene R2 risk if it flattens contrast.
- Ground 20.0 x 20.0 (type float each, unit meters, same both builds; set at w1_build.py:29-30, v8_build.py:28-29) [verified]: plane extent. Shrink below camera frustum -> background/void pixels shift mean/std.
- Cube size/pos: W1 size 1.0 (float, meters) @ (0,0,0.5) (floats, meters); V8 0.5@(0.9,0,0.25) + 1.0@(-0.8,0.4,0.5) [verified]: z = size/2 rests the cube on the ground plane. Raising z floats it; lowering sinks it. Set at w1_build.py:32-33, v8_build.py:30-34.
- Cleanup path tuples (type `tuple[str, ...]`, unit none — USD prim paths; W1 18 entries / V8 17 entries, no default — hardcoded at w1_build.py:11-18, v8_build.py:10-17) [verified]: W1 still cleans V7* leftovers (cross-drill hygiene); V8 cleans W1* (exam isolation). Omitting a stale path leaves ghost prims in frame.

EKB rules:
- IF rebuilding a scene THEN run the full cleanup loop first BECAUSE anonymous-stage recovery rebuilds from scripts and stale prims (V7/W1/M4) would otherwise photobomb the frame [verified].
- IF a build marker is missing THEN the build did not complete BECAUSE the `print` is the last statement (any exception above aborts it) [verified].
- IF the exam needs a NEW layout THEN copy the build with new paths + new marker tokens (V8 pattern) BECAUSE verify_v8 greps `dome=/sun=/sizeA=/sizeB=` to prove the exam scene is distinct [verified].

LIMITS:
- [verified] No materials/physics/articulation in these builds (other packs own those); gray default-shaded cubes only.
- [verified] Cleanup is a fixed path list, not a traversal — prims outside the list survive.
- [probable] `RemovePrim` on a valid prim is unconditional; no undo recorded.

UNKNOWN (theoretical): light-intensity-to-pixel-mean transfer curve (two samples only: 400/1500 and 300/1200); behavior if `Define` runs twice without cleanup (overwrite vs duplicate op stacking — `AddTranslateOp` could stack a second op); PhysicsScene removal side effects on a running sim.

## 7. omni.usd (in-sim Python API)

DOES: [verified] Provides stage + selection access for scene authorship inside build scripts (and inside select_prim.py).

Functions + full signatures ([verified] call patterns from pack scripts; full API [probable]):
- `omni.usd.get_context() -> UsdContext` [probable — type name; no params, no default] [verified in w1_build.py:10, v8_build.py:9, select_prim.py:33].
- `ctx.get_stage() -> Usd.Stage` [probable — type name; no params] [verified in w1_build.py:10, v8_build.py:9].
- `stage.GetPrimAtPath(path: str) -> Usd.Prim` [probable — type name; invalid prim (not None) when missing; unit none] [verified in w1_build.py:19, v8_build.py:18].
- `prim.IsValid() -> bool` [verified in w1_build.py:20, v8_build.py:19; no params, unitless].
- `stage.RemovePrim(path: str) -> bool` [probable — return unused at call sites w1_build.py:21, v8_build.py:20; unit none].
- `ctx.get_selection() -> Selection` [probable — type name; no params; used by select_prim.py:34, not by pack-authored code].
- `ctx.get_stage_url() -> str` [probable — no params; used by select_prim.py:60, not by pack-authored code].

Knobs: none in this pack — all calls use fixed paths; the only variable is the cleanup path tuple (see tool 6) [verified].

EKB rules:
- IF cleaning before rebuild THEN guard `RemovePrim` with `GetPrimAtPath` + `IsValid` BECAUSE removing a missing path is an error the guard avoids (both builds use it) [verified].
- IF touching selection THEN go through `ctx.get_selection()`, not stage APIs, BECAUSE selection is context state, not stage state (select_prim.py pattern) [probable].

LIMITS:
- [verified] Cleanup loop never failed in this pack (TOOLS.md: none recorded).
- [probable] Pack exercises 5 call patterns only; the rest of omni.usd is out of scope.

UNKNOWN (theoretical): undo/redo interaction; behavior on locked or instance-proxy prims; `get_stage()` when no stage is open.

## 8. pxr UsdGeom / UsdLux / Gf (in-sim Python API)

DOES: [verified] Authors lights, ground, and cubes for screenshot scenes. Six call patterns in this pack.

Functions + full signatures ([verified] from both builds; USD type names [probable]):
- `UsdLux.DomeLight.Define(stage: Usd.Stage, path: str) -> DomeLight` [probable]; `dome.GetIntensityAttr() -> Usd.Attribute` [probable] `.Set(value: float) -> bool` [probable] (value unitless multiplier; all params required, no defaults) [verified]. Call sites: w1_build.py:23-24, v8_build.py:22-23.
- `UsdLux.DistantLight.Define(stage: Usd.Stage, path: str) -> DistantLight` [probable]; `sun.GetIntensityAttr() -> Usd.Attribute` [probable] `.Set(value: float) -> bool` [probable] (called with `1500.0|1200.0`) [verified]. Call sites: w1_build.py:25-26, v8_build.py:24-25.
- `UsdGeom.Xformable(prim: Usd.Prim) -> Xformable` [probable]; `.AddRotateXYZOp() -> XformOp` [probable] (no params passed); `.Set(value: Gf.Vec3f) -> bool` [probable] (unit degrees XYZ); `sun.GetPrim() -> Usd.Prim` [probable] (no params) [verified]. Call sites: w1_build.py:27, v8_build.py:26.
- `UsdGeom.Plane.Define(stage: Usd.Stage, path: str) -> Plane` [probable]; `CreateWidthAttr() -> Usd.Attribute` [probable] `.Set(value: float meters) -> bool` [probable]; `CreateLengthAttr() -> Usd.Attribute` [probable] `.Set(value: float meters) -> bool` [probable] [verified]. Call sites: w1_build.py:28-30, v8_build.py:27-29.
- `UsdGeom.Cube.Define(stage: Usd.Stage, path: str) -> Cube` [probable]; `cube.GetSizeAttr() -> Usd.Attribute` [probable] `.Set(size: float meters) -> bool` [probable] — edge length in meters (size 1.0 = 1m cube) [verified]. Call sites: w1_build.py:31-32, v8_build.py:32-33.
- `UsdGeom.Xformable(cube.GetPrim() -> Usd.Prim [probable]).AddTranslateOp() -> XformOp` [probable] (no params passed); `.Set(value: Gf.Vec3d(x: float, y: float, z: float)) -> bool` [probable] (unit meters, double-precision) [verified]. Call sites: w1_build.py:33, v8_build.py:34.
- `Gf.Vec3f(x: float, y: float, z: float) -> Gf.Vec3f` (float, rotation degrees) vs `Gf.Vec3d(x: float, y: float, z: float) -> Gf.Vec3d` (double, translation meters) — type choice matches USD attr types [probable]. Call sites: w1_build.py:27,33; v8_build.py:26,34.

Knobs + effect-of-change: dome/sun intensities (float, unitless multiplier), sun angle (Gf.Vec3f, degrees XYZ), ground W/L (float, meters), cube size/pos (float, meters) — see tool 6 (same constants, typed there) [verified].

EKB rules:
- IF placing a cube on the ground THEN set translate z = size/2 BECAUSE UsdGeom.Cube is centered at origin, so z=size/2 rests its base on z=0 (both builds do this: 1.0->0.5, 0.5->0.25) [verified].
- IF the sun must rake across the scene THEN rotate the DistantLight prim (not position it) BECAUSE distant lights shine along their local axis; both builds use AddRotateXYZOp(-50,20,0) [verified].
- IF re-running a build THEN rely on the cleanup loop, not Define-idempotence, BECAUSE re-Define plus AddTranslateOp could stack a second translate op (unverified — see UNKNOWN) [theoretical].

LIMITS:
- [verified] None recorded in this pack (TOOLS.md) — all six patterns worked first try in both builds.
- [verified] Scope is exactly these six patterns; materials, physics, articulation live in other packs.

UNKNOWN (theoretical): re-Define + Add*Op stacking semantics without cleanup; DomeLight texture/visibility attrs; DistantLight angle/shadow attrs; Cube double-sided/render attrs; Gf.Vec3f-vs-Vec3d strictness (would Vec3f translate work?).

## 9. pngstats.py (pack-local stdlib PNG reader)

DOES: [verified] Decodes Kit PNGs and compares views without PIL (local env has no PIL — failures.md R1). Returns dimensions + RGB mean/std + raw buffer + pixel diffs. Sole image-analysis lib for all 5 verifiers.

Functions + full signatures ([verified] — script read fully; defs untyped in source, types grounded in call sites):
- `png_stats(path: str) -> dict[str, Any]` with keys `{w: int (px), h: int (px), mean: float (0-255 RGB levels), std: float (0-255 levels), bytes: int (file bytes), raw: bytes (full de-interleaved RGB(A) buffer), ch: int (3|4 channels)}` — param required, no default; unit = filesystem path. Reads file bytes; asserts 8-byte PNG magic; chunk-walk with `struct.unpack(">I")` lengths: IHDR -> `struct.unpack(">IIBBBBB", dat)` = w,h,bitdepth,ctype,compression,filter,interlace, asserts `bd == 8 and ctype in (2, 6)`; IDAT -> collects blobs; IEND -> break (other chunks skipped); `ch = 3 if ctype == 2 else 4`; `zlib.decompress`; per-scanline unfilter (filter byte 0=None,1=Sub,2=Up,3=Average,4=Paeth with bpp=ch); RGB-only stats (alpha skipped): mean = tot/k, std = sqrt(tot2/k - mean^2) over k = h*w*3 samples. `bytes` = file length, `raw` = full de-interleaved buffer incl. alpha. Def: pngstats.py:11; call sites (all pass `str`): pngstats.py:75, verify_w1.py:15, verify_w2.py:19, verify_w3.py:17, verify_w4.py:15, verify_v8.py:25.
- `mean_abs_diff(a_path: str, b_path: str) -> float` — both params required str paths, no defaults; returns mean |ra-rb| in 0-255 RGB levels (0.0 for identical files). `png_stats` both; asserts equal (w,h) ("size mismatch"); mean |ra-rb| over RGB bytes only (steps `ch` from file A, first 3 bytes each pixel). Def: pngstats.py:73; call site: verify_w4.py:20.

Knobs + effect-of-change:
- `path: str` (unit filesystem path; required, no default) [verified]: any filesystem PNG. Non-PNG magic -> AssertionError "not a PNG". No knob for color handling — RGB-only stats hardcoded; alpha affects NOTHING except stride. Call sites: pngstats.py:75, verify_w1.py:15, verify_w2.py:19, verify_w3.py:17, verify_w4.py:15, verify_v8.py:25.
- No thresholds inside the lib [verified]: all gates live in the verifiers (tool 10). `mean_abs_diff > 3.0` is a verifier constant, not a default here. (Absence documented — no type.)
- Filter-type support 0-4 incl. Paeth [verified]: filter byte type int (0=None,1=Sub,2=Up,3=Average,4=Paeth; unit none; read from stream, no default): covers all zlib-PNG encoders Kit uses. Unknown filter byte -> line copied raw (silent fallthrough — `if/elif` with no `else`) [probable from code read pngstats.py:38-56].

EKB rules:
- IF comparing two views THEN gate on `mean_abs_diff > 3.0`, never on mean delta, BECAUSE symmetric opposite views had means 183.4 vs 183.8 (delta 0.4) with clearly different content (failures.md R2; measured MAD 7.59) [verified].
- IF `png_stats` asserts `(bd, ctype)` THEN the file is not 8-bit truecolor(+alpha) BECAUSE the decoder supports only ctype 2/6 at bd 8 (what Kit screenshots write) [verified].
- IF `mean_abs_diff` asserts "size mismatch" THEN the two captures differ in dimensions (viewport vs app shot mix-up) BECAUSE it requires equal (w,h) [verified].
- IF std reads ~0 THEN the frame is a flat field (void/black) BECAUSE std aggregates all RGB samples; verifiers floor it at 1.0/5.0 [verified].

LIMITS:
- [verified] Supports 8-bit truecolor / truecolor+alpha only; asserts otherwise (code + failures.md R1).
- [verified] Mean-only comparison is UNSOUND: symmetric opposite views means 183.4 vs 183.8 (delta 0.4), bytes 46309 vs 34517, std 21.5 vs 18.2 — always gate on `mean_abs_diff > 3.0` (measured 7.59; failures.md R2).
- [verified] Validated against a 1280x720 Kit screenshot (failures.md R1; `w1_viewport.png` 171821 B).
- [probable] Unknown PNG filter byte falls through silently (no `else` clause) — corrupt/extension filters decode wrong without error.
- [probable] `raw` buffer holds the whole image in memory twice over (bytearray + bytes) — fine at 1280x720x4 (~3.7MB), untested at 4K+.
- [probable] No interlace handling: IHDR interlace byte parsed and ignored; interlaced PNGs would decode to garbage stats, not an error.

UNKNOWN (theoretical): performance on very large (>4K) captures; behavior on 16-bit/grayscale/paletted PNGs (asserts, untested); Adam7-interlaced input (silently wrong stats, untested).

## 10. verify_w1 / verify_w2 / verify_w3 / verify_w4 / verify_v8 (pack-local evaluators)

DOES: [verified] Local pass/fail gates over evidence JSON + PNGs; exit text `WN-PASS/WN-FAIL` (printed; note: scripts do NOT set process exit codes — pass/fail is stdout text only). 5/5 green at graduation per README.md.

Functions + full signatures ([verified] — all 5 scripts read fully; straight-line + local helpers):
- verify_w1 (6 checks, no defs; module straight-line, no params/return): `EV=status==ok` + `saved message` ("Saved viewport screenshot" in output) + `png exists >50KB` + (via pngstats) `min size 640x480` + `mean 10..245` + `non-uniform std>1.0`. Prints `INFO size=WxH mean=M std=S`. Wraps pngstats import+read in try/except -> `png read`=False on ANY exception [verified].
- verify_w2 (5 checks): local `f(pat: str, i: int = 1) -> float` — regex-float helper (NaN on no-match); pat = regex string with capture group i (required), i = group index (int, default 1); returns parsed float (unit = whatever the group holds: meters for poses; NaN float on no-match). Def: verify_w2.py:11 (`re.search(pattern: str, string: str) -> Match | None` [probable stdlib] at verify_w2.py:12); call sites verify_w2.py:16,17,18 (all default i=1). `cam x~3` + `cam y~-3` + `cam z~2` (each |got-expected|<0.05 on `Position (x, y, z):` floats) + `frames differ` (|meanA-meanB|>2.0 — mean delta, the R2-unsound gate, kept because W2's before/after differ hugely: std 3.0->21.5) + `aimed has contrast` (after std>5.0) [verified].
- verify_w3 (7 checks, no defs): `set ack` ("Selected 1 prim(s)" in SET) + `get shows cube` ("/World/W1Cube" in GET) + `shot ok` (status ok + "Saved app screenshot") + `png exists >50KB` + `min size 640x480` + `mean 5..250` + `non-uniform std>1.0` [verified].
- verify_w4 (5 checks, no defs): `pose A set` (`"[ 3."` and `"-3."` substring in getA) + `pose B set` (`"[-4."` or `"-4."` substring in getB) + `A valid` (w>=640, mean 5..250, std>5.0) + `B valid` (same) + `views differ` (`mean_abs_diff>3.0`, the R2-sound gate; measured 7.59) [verified].
- verify_v8 (9 checks): local `f(pat: str, s: str, i: int = 1) -> float` — same contract as W2's; s = haystack string (required). Def: verify_v8.py:14; call sites verify_v8.py:19,20,21,22 (all default i=1). `EXAM dome 300` + `EXAM sun 1200` + `EXAM sizeA 0.5` + `EXAM sizeB 1.0` (each |got-expected|<1e-6 on build marker) + `cam at new eye` (`"[-3."` and `"2.5"` substrings) + `select V8CubeB` + `viewport valid` (w>=640, mean 5..250, std>5.0) + `app valid` (same but std>1.0) + `pngs exist` (both >20KB) [verified].
- Shared imports: `json.load(fp: TextIO) -> Any` [probable stdlib] (load evidence; all calls `json.load(open(path: str))` at verify_w1.py:4, verify_w2.py:7, verify_w3.py:7-9, verify_w4.py:9-10, verify_v8.py:8-10), `os.path.getsize(path: str) -> int` [probable stdlib] (unit bytes; call sites verify_w1.py:10, verify_w3.py:16, verify_v8.py:30), `re` (pose/marker parse via `re.search` above), `sys.path.insert(index: int, obj: str) -> None` [probable stdlib] (all calls `insert(0, "action-reasoner/skills/viewport-ui/scripts")` at verify_w1.py:13, verify_w2.py:4, verify_w3.py:4, verify_w4.py:4, verify_v8.py:4) + `pngstats` import [verified].

Knobs (threshold constants) + effect-of-change:
- PNG byte floors (type int, unit bytes; defaults 50000 W1/W3, 20000 V8-exam) [verified]. Raising risks false FAIL on dark/simple scenes (`w2_before.png` is only 21777 B — would FAIL a 50KB floor); lowering admits truncated writes.
- Min size (type int each, unit px; defaults w>=640 and h>=480 W1/W3, w>=640 only W4/V8 with h unchecked) [verified]. Below -> FAIL; guards against degenerate captures.
- Mean bands (type float, unit 0-255 RGB levels; defaults 10..245 W1, 5..250 W3/W4/V8) [verified]. W1's tighter band reflects its bright lit scene (mean 185.1); edges catch black/white-out frames.
- Std floors (type float, unit 0-255 levels; defaults 1.0 existence/non-uniform, 5.0 aimed-view contrast: W2-after, W4 A/B, V8 viewport) [verified]. W2 before->after std 3.0->21.5 shows why aimed views get the stricter floor.
- Diff gates (type float, unit 0-255 levels; defaults mean-delta >2.0 W2, MAD >3.0 W4) [verified]: mean-delta >2.0 (W2 only — justified by the huge before/after gap) vs MAD >3.0 (W4 — the R2-sound gate).
- Pose tolerance (type float, unit meters, default 0.05/axis W2 regex) vs substring match (type str patterns, e.g. `"[ 3."`, `"[-4."`, `"2.5"`) [verified]. Substring is looser (no axis isolation); W2's regex is the strict proof of <0.05 exactness.
- Build-marker tolerance (type float, unit none — exact float match, default 1e-6) [verified]: V8 exact float match on dome/sun/sizeA/sizeB.

EKB rules:
- IF writing a new verifier THEN copy the `checks` dict + `all()` + `PASS/FAIL per line` + `WN-PASS/WN-FAIL` pattern BECAUSE all 5 verifiers share it and graduation tooling greps the final line [verified].
- IF gating view-difference THEN use MAD >3.0 (W4 pattern), not mean delta, BECAUSE R2 proves mean delta unsound (0.4 on different content); W2's mean gate survives only via its huge 2.0 margin on a chalk-and-cheese pair [verified].
- IF the script prints WN-FAIL THEN read the per-check lines BECAUSE each check name isolates the failing gate (pose vs pixels vs markers) [verified].
- IF parsing poses strictly THEN use W2's 3-regex pattern, not W4/V8 substrings, BECAUSE substrings (`"-3."`) can match the wrong axis or the orientation line [verified].
- IF checking pass/fail programmatically THEN grep stdout, not the exit code, BECAUSE these scripts never `sys.exit(1)` — failure is text-only [probable from code read].

LIMITS:
- [verified] 5/5 green at graduation (README.md); thresholds calibrated on one machine/GPU (TOOLS.md Unverified — portability unproven).
- [probable] No `sys.exit` non-zero on failure — CI-style exit-code gating silently passes; must grep `WN-PASS`.
- [verified] W1's pngstats block swallows ALL exceptions into `png read`=False (try/except Exception) — masks the real error; W2/W3/W4/V8 let pngstats exceptions crash (traceback, no WN line).
- [verified] Hardcoded relative evidence paths (`action-reasoner/skills/viewport-ui/evidence/...`) — must run from repo root.
- [probable] `cross-val x8_live.py + verify_x8.py` mentioned in README.md Tools but no such files exist in scripts/ — co-validation snapshot not present in this pack.

UNKNOWN (theoretical): threshold robustness across GPUs/tone-mapping/resolutions; W2 mean-gate margin on less contrasting pairs; V8 20KB floor vs heavily compressed dark frames.

## Consolidated UNKNOWN (theoretical-only, needs live probes)
- `camera_control.py list_cameras` live output + multi/non-Persp camera behavior.
- `select_prim.py clear`/`all` live contracts; invalid-path behavior.
- `app_screenshot.py` headless behavior in 6.0 (6.3 docstring claims support).
- isaacsim_send.py `--context`/`--fire-and-forget`/retry/max-payload semantics.
- Verifier threshold portability across GPUs; WN-PASS exit-code convention.
- `x8_live.py + verify_x8.py` co-validation snapshot (files absent).
- Light-intensity-to-pixel-mean transfer curve; Define-without-cleanup op stacking.
- pngstats on >4K / 16-bit / interlaced PNGs.

## Sources-read (13 scripts, all full)
- action-reasoner/skills/viewport-ui/README.md (pack doc; SKILL.md absent)
- action-reasoner/skills/viewport-ui/failures.md (R1-R2)
- action-reasoner/skills/viewport-ui/discovery.md
- action-reasoner/skills/viewport-ui/scripts/pngstats.py (full)
- action-reasoner/skills/viewport-ui/scripts/w1_build.py (full)
- action-reasoner/skills/viewport-ui/scripts/v8_build.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w1.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w2.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w3.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_w4.py (full)
- action-reasoner/skills/viewport-ui/scripts/verify_v8.py (full)
- Downloads/IsaacSim-release-6.3/.../skills/isaac-sim-remote/scripts/isaacsim_send.py (full, 335 lines)
- .../isaac-sim-remote/scripts/viewport_screenshot.py (full)
- .../isaac-sim-remote/scripts/app_screenshot.py (full)
- .../isaac-sim-remote/scripts/camera_control.py (full)
- .../isaac-sim-remote/scripts/select_prim.py (full)
- action-reasoner/skills/viewport-ui/evidence/*.json (all 13 replies read)
