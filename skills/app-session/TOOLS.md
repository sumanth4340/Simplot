# App-Session Tool Knowledge (2026-11-04)

> Full mastery reference: [TOOLS_REF.md](TOOLS_REF.md) — 14 tools, ~85 functions/actions, ~35 knobs, 36 EKB rules, 33 limits, ~49 unknowns (all claims tagged verified/probable/theoretical).

## Tools

### isaacsim_send.py (bridge CLI, external library)
- DOES: Sends in-sim Python scripts + key=value args from OUTSIDE into the running sim and returns a JSON envelope.
- FUNCTIONS USED:
  - `--file <script>`: script to run inside the sim (library scripts and pack snippets alike).
  - `--arg k=v`: repeated action/parameter args (e.g. `action=play`, `num_steps=60`, `usd_path=<abs-fwd-slash>`).
  - `--raw --timeout N`: raw JSON envelope mode with N-second timeout.
  - Envelope parse: `body["output"]` + `body["traceback"]` concatenated into transcripts.
  - Shelled via `subprocess.run(SEND + args, capture_output=True, text=True, timeout=...)`.

### simulation_control.py (bridge library, in-sim)
- DOES: Drives the timeline state machine and reports session status.
- FUNCTIONS USED:
  - `action=status`: reports state + physics dt + sim time + steps + backend + device + scenes.
  - `action=play`, `action=pause`, `action=stop`: state transitions; verified cycle STOPPED->PLAYING->PAUSED->STOPPED.
  - `action=step` + `num_steps=N`: advances N steps (auto-plays first); 60 steps ~= 1.0 sim-second at dt 1/60.
  - Drivers always end STOPPED for clean handoff to the next drill.

### open_stage.py (bridge library, in-sim)
- DOES: Stage lifecycle: new/open/save/info over absolute USD paths.
- FUNCTIONS USED:
  - `action=new` (+ optional template): fresh stage; wipes authored prims (prim count drops).
  - `action=save` / `action=open` + `usd_path=<absolute forward-slash path>`: `save_as_stage` returns bool, prints "Saved as:".
  - `action=info`: URL, up-axis, units, prim count, loading state; used to compare wiped-vs-loaded counts.

### stage_info.py (bridge library, in-sim)
- DOES: Inspects stage contents: full tree, type-filtered list, single-prim detail.
- FUNCTIONS USED:
  - Default `tree` mode: whole-stage tree, excludes `/Render`.
  - `mode=list` + `filter_type=Cube`: type queries (located A2Marker).
  - `prim_path=/World/...`: "Path:" detail block for one prim.
- LIMITS-live-verified:
  - Tree transcripts MUST use `open(..., encoding="utf-8")` for write AND read on Windows; default cp1252 raises UnicodeEncodeError on box-drawing chars (failures.md R2).

### viewport_screenshot.py (bridge library, in-sim, Skill 8 reuse)
- DOES: Captures the viewport to a PNG file after reopen+step with no extra warm-up.
- FUNCTIONS USED:
  - `output_path=<absolute forward-slash path>`: 1280x720 shot verified non-black via png_stats (V13 9/9).

### omni.timeline (in-sim API)
- DOES: Direct timeline time control from inside the sim.
- FUNCTIONS USED:
  - `omni.timeline.get_timeline_interface()`: handle.
  - `set_current_time(2.5)` / `get_current_time()`: set/get round-trip, exact 2.500 after pump.
- LIMITS-live-verified:
  - `set_current_time` applies on the NEXT frame pump, not instantly: set(2.5) then immediate get returned 0.000; pump 2 steps between set and get (failures.md R1).

### isaacsim.core.experimental.utils.app (in-sim API)
- DOES: Pumps the Kit app forward so deferred changes (timeline time) apply.
- FUNCTIONS USED:
  - `await app_utils.update_app_async(steps=2)`: async pump used between set and get (R1 recovery).
  - Sync `update_app` inside short library calls is fine (simulation_control pattern).
- LIMITS-live-verified:
  - 2 pumped steps required between `set_current_time` and `get_current_time` or the get reads stale time (failures.md R1).

### omni.usd (in-sim API)
- DOES: Stage access for marker/scene authoring and validity checks.
- FUNCTIONS USED:
  - `omni.usd.get_context().get_stage()`: stage handle (a2_marker, v13_build, a2_check, v13_check).
  - `stage.GetPrimAtPath(path).IsValid()`: post-reopen validity gates.

### pxr UsdGeom / UsdLux / Gf (in-sim API)
- DOES: Defines the round-trip marker and V13 exam scene prims.
- FUNCTIONS USED:
  - `UsdGeom.Cube.Define(stage, path)` + `GetSizeAttr().Set/Get`: 0.70 marker survives save/wipe/reopen (A2 8/8).
  - `UsdLux.DomeLight.Define(stage, path)` + `GetIntensityAttr().Set(3000.0)`: exam-scene lighting.
  - `UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(x, y, z))`: prim placement.

### omni.kit.app extension manager (in-sim API)
- DOES: Proves the bridge's own dependency (python_server) is enabled; counts loaded extensions.
- FUNCTIONS USED:
  - `omni.kit.app.get_app().get_extension_manager()`: manager handle.
  - `is_extension_enabled("isaacsim.code_editor.python_server")`: True (else no bridge at all; A3 doubles as bridge self-check).
  - `is_extension_enabled("no.such.extension-0.0.0")`: False (negative control).
  - `len(get_extensions())`: 659 on this build.

### carb.settings (in-sim API)
- DOES: Settings key round-trip probe.
- FUNCTIONS USED:
  - `carb.settings.get_settings()`: handle.
  - `set("/app/muse_drill_probe", "hello-a3")` / `get(...)`: custom-key round-trip echoes back.

### Python stdlib driver stack (local)
- DOES: Local multi-send session flows: each send is one action, transcript is the evidence.
- FUNCTIONS USED:
  - `subprocess.run`, `json` (envelope parse), `sys` (executable), `os` (USD/PNG exists/size gates), `re` (verify_* gates).
  - `open(..., encoding="utf-8")` on ALL transcript IO (a4/v13 pattern).
- LIMITS-live-verified:
  - Any transcript that may contain tree art must use UTF-8 file IO on both write and read (failures.md R2).

### verify_a1/a2/a3/a4/verify_v13 + png_stats (pack-local evaluators)
- DOES: Local pass/fail gates over evidence transcripts; exit 0 on pass.
- FUNCTIONS USED:
  - `verify_aN.py` / `verify_v13.py`: regex gates (transition ORDER, LAST sim-time line, marker echo, counts).
  - `png_stats.png_stats`: V13 screenshot non-black check.

## Unverified

- UNKNOWN: Headless (`--no-window`) session behavior; all drills ran windowed GUI.
- UNKNOWN: Enabling/disabling extensions (`enable_extension` etc.); only `is_extension_enabled` + `get_extensions` probed.
- UNKNOWN: `carb.settings` on non-custom (built-in) keys; only `/app/muse_drill_probe` round-tripped.
- UNKNOWN: `open_stage` template variants for `action=new`; only the default template drilled.
- UNKNOWN: `viewport_screenshot` resolution/format args beyond `output_path`; only the default 1280x720 PNG drilled.
- UNKNOWN: Multi-scene `status` fields and non-PhysX backend/device strings; single local PhysX session only.
- UNKNOWN: Bridge timeout/retry behavior; zero bridge hiccups observed this skill, so no failure path drilled.
- UNKNOWN: USD paths with backslashes or relative paths; only absolute forward-slash paths drilled.

## Sources-read

- action-reasoner/skills/app-session/README.md (full; no SKILL.md present)
- action-reasoner/skills/app-session/failures.md (full)
- action-reasoner/skills/app-session/discovery.md (full)
- action-reasoner/skills/app-session/scripts/a1_run.py (full)
- action-reasoner/skills/app-session/scripts/a1_time.py (full)
- action-reasoner/skills/app-session/scripts/a2_run.py (full)
- action-reasoner/skills/app-session/scripts/a2_marker.py (full)
- action-reasoner/skills/app-session/scripts/a3_probe.py (full)
- action-reasoner/skills/app-session/scripts/a4_run.py (full)
- action-reasoner/skills/app-session/scripts/v13_build.py (full)
- action-reasoner/skills/app-session/scripts/v13_run.py (full)
- Skimmed by name + imports only: a2_check.py (omni.usd), v13_check.py (omni.usd), verify_a1.py (re), verify_a2.py (re), verify_a3.py (json, re), verify_a4.py (re), verify_v13.py (re, sys, png_stats)
