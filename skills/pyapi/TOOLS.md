# PyAPI Tool Knowledge (2026-11-04)

Exhaustive companion: `TOOLS_REF.md` — 8 tools, 33 functions, 13 knobs, 24 EKB rules, 26 limits, 21 unknowns.

Pack: `action-reasoner/skills/pyapi/` (P1 drill, Isaac Sim 6.0.0 / Kit 110).

## Tools

### omni.kit.commands
- DOES: Execute named Kit commands that author USD live (command-pattern authoring with undo-stack integration).
- FUNCTIONS USED:
  - `execute("CreatePrim", prim_path=..., prim_type=...)` — authors a prim live (p1_probe.py, p1_fix.py).
  - `hasattr(kc, "get_command_names")` — capability probe only (p1_probe.py).
- LIMITS-live-verified:
  - Exposes NO `undo`/`redo` attributes — first probe failed calling `kc.undo()` (failures.md: kit commands, "Undo lives in omni.kit.undo ... NOT in omni.kit.commands").
  - Exposes NO `get_command_names` — command discovery by name-listing unavailable; address commands by known name (failures.md: kit commands entry 3; SKILL.md Limitations; evidence/p1_api.json `n_commands: 0`).
  - `dir(kc)` filtered for undo/redo shows only `POST_UNDO_CALLBACK` / `PRE_UNDO_CALLBACK` constants, no callables (evidence/p1_api.json `cmd_dir_undo`).
- UNKNOWN:
  - Which other named commands exist / their signatures (only `CreatePrim` drill-proven; `DeletePrims` untested).
  - Whether every `execute` call pushes an undo entry or only some commands do.

### omni.kit.undo
- DOES: Owns the Kit undo/redo stack; undoes and redoes command-pattern edits made via omni.kit.commands.
- FUNCTIONS USED:
  - `undo()` — removes the last command edit (p1_fix.py; roundtrip create -> undo removes verified).
  - `redo()` — restores the undone edit (p1_fix.py; redo restores verified).
- LIMITS-live-verified:
  - Undo/redo live ONLY here, not in `omni.kit.commands` — first probe failed on the wrong-module assumption (failures.md: kit commands, "first probe failed on this assumption").
- UNKNOWN:
  - Grouping/history APIs observed via `dir()` but NOT drill-proven: `begin_group`, `end_group`, `can_undo`, `can_redo`, `can_repeat`, `clear_history`, `clear_stack`, `begin_disabled`, `end_disabled`, `disabled`, `execute`, `get_history` (evidence/p1_api.json `undo_mod`, truncated at 12 names).
  - Interop with direct USD edits (`RemovePrim`) — probe used `RemovePrim` for setup/teardown outside the undo stack; whether those pollute the stack is untested.

### omni.client
- DOES: Synchronous low-level file operations against the hosted Nucleus/S3 asset root (stat/list).
- FUNCTIONS USED:
  - `stat(path)` — returns `(Result, payload)` tuple synchronously (p1_fix.py).
  - `list(dir_path)` — returns `(Result, [entries])` tuple synchronously; entries expose `relative_path` (p1_fix.py).
- LIMITS-live-verified:
  - `stat`/`list` are SYNCHRONOUS tuple APIs `(Result, payload)`, NOT awaitable — first probe failed awaiting a tuple (failures.md: omni.client entry 1).
  - `stat(hosted root)` -> `Result.OK`; `list(.../Isaac/Sensors/NVIDIA)` -> 8 entries incl. `Example_Rotary_2D` (failures.md: omni.client entry 2; evidence/p1_api.json).
  - `stat(bogus path)` -> `Result.ERROR_NOT_FOUND`, a clean miss not an exception (failures.md: omni.client entry 2; evidence/p1_api.json `stat_missing`).
- UNKNOWN:
  - All other omni.client ops (copy/move/delete/write/mkdir, recursive list, watch/subscribe) — none probed.
  - Behavior on unreachable/offline root (timeouts, error codes) — only the happy path + clean miss are gated.
  - Payload shape of `stat` success beyond `Result` (probe recorded only `r[0]`).

### isaacsim.storage.native.get_assets_root_path
- DOES: Returns the hosted Isaac Sim assets root URL used as the base for omni.client ops.
- FUNCTIONS USED:
  - `get_assets_root_path()` — no-arg root lookup (p1_probe.py, p1_fix.py).
- LIMITS-live-verified:
  - Live value ended `us-west-2.amazonaws.com/Assets/Isaac/6.0` at validation time (evidence/p1_api.json `root_tail`; SKILL.md omni.client section).
  - File ops built on this root agree with the G2 Ar-resolver layer one level down (failures.md: omni.client entry 3).
- UNKNOWN:
  - Return value when offline / no Nucleus configured (exception? empty string? local fallback?) — not probed.
  - Whether the root is configurable per-session and how that interacts with the 8-entry NVIDIA listing gate.

### omni.timeline.get_timeline_interface
- DOES: Timeline state readback — playing flag and current sim time for gating drive roundtrips.
- FUNCTIONS USED:
  - `get_timeline_interface()` — obtain the timeline singleton (p1_probe.py).
  - `is_playing()` — playing-state readback (p1_probe.py).
  - `get_current_time()` — sim-time readback before/after stepping (p1_probe.py).
- LIMITS-live-verified:
  - Roundtrip gated: `was_playing False` -> `playing True` after `play()`+steps -> `stopped True` after `stop()` (failures.md: timeline/app; evidence/p1_api.json).
- UNKNOWN:
  - `pause()` vs `stop()` semantics, `set_current_time`, playback rate / time-codes-per-second APIs — none probed.
  - Behavior of `is_playing()` immediately after `play()` without stepping (bridge read artifact: state may lag one result — see personal memory, but NOT proven by this pack's drill).

### isaacsim.core.experimental.utils.app
- DOES: Drive the Kit app/timeline — start playback, pump frames asynchronously, stop playback.
- FUNCTIONS USED:
  - `play()` — start timeline playback (p1_probe.py).
  - `update_app_async(steps=10)` — awaitable frame pump; advances sim time while playing (p1_probe.py).
  - `stop()` — stop timeline playback (p1_probe.py).
- LIMITS-live-verified:
  - `play()` + `update_app_async(10)` + `stop()`: stopped -> playing, sim time advances (`time_adv True`), back to stopped (failures.md: timeline/app; evidence/p1_api.json).
  - Every drive in every pack relies on this pattern; P1 gates it explicitly (failures.md: timeline/app parenthetical).
- UNKNOWN:
  - Minimum/typical step counts for a stable read (only `steps=10` proven).
  - `update_app_async` behavior while stopped (does time advance? error?) — not probed.
  - Other app-utils helpers (pause, reset, async step variants) — none probed.

### omni.usd (stage access helper)
- DOES: Stage handle + prim existence checks used as the assertion layer for the command roundtrip.
- FUNCTIONS USED:
  - `get_context().get_stage()` — stage handle (p1_probe.py, p1_fix.py).
  - `stage.GetPrimAtPath(path).IsValid()` — existence assertion (p1_probe.py, p1_fix.py).
  - `stage.RemovePrim(path)` — setup/teardown cleanup (p1_probe.py, p1_fix.py).
- LIMITS-live-verified:
  - None beyond successful use as the assertion layer in the 9/9 P1 pass (evidence/p1_api.json `cmd_create/undo/redo True`).
- UNKNOWN:
  - Full omni.usd API surface is out of this pack's scope — only the three calls above were exercised.

### Local verifier stack (json / sys)
- DOES: Host-side (non-sim) evidence gating — reads the in-sim JSON artifact and PASS/FAILs 9 gates.
- FUNCTIONS USED:
  - `json.load(open(EV))` — load evidence artifact (verify_p1.py).
  - `sys.exit(0/1)` — gate exit code (verify_p1.py).
- LIMITS-live-verified:
  - 9 gates: cmd-create/undo/redo, stat-root, list-nvidia, stat-missing, tl-play/advance/stop (verify_p1.py; SKILL.md validated P1-PASS 9/9).
- UNKNOWN:
  - None — trivial local harness, fully read.

## Unverified

- Kit command catalog beyond `CreatePrim`: `DeletePrims` and all other named commands (names, signatures, undo behavior) — no listing API exists to enumerate them.
- `omni.kit.undo` grouping/history/disabled APIs (`begin_group`, `can_undo`, `get_history`, etc.) — observed via `dir()`, never executed.
- `omni.client` write/mutating ops and offline/unreachable behavior — only stat/list happy path + clean miss are gated.
- Timeline `pause()` vs `stop()`, `set_current_time`, playback-rate APIs — unprobed.
- `update_app_async` step-count sensitivity and stopped-state behavior — only `steps=10`-while-playing proven.
- `get_assets_root_path()` offline/no-Nucleus behavior — unprobed.
- Bridge read-lag artifact (pausing batch's own snapshot vs next result) — known from live-loop memory, not proven by this pack.
- `discovery.md` absent from pack — no discovery notes to verify against.
- `__pycache__/` present in scripts/ — stale bytecode only, not a knowledge source.

## Sources-read

- `action-reasoner/skills/pyapi/SKILL.md` (full, 67 lines)
- `action-reasoner/skills/pyapi/failures.md` (full, 25 lines)
- `action-reasoner/skills/pyapi/scripts/p1_probe.py` (full, 68 lines)
- `action-reasoner/skills/pyapi/scripts/p1_fix.py` (full, 49 lines)
- `action-reasoner/skills/pyapi/scripts/verify_p1.py` (full, 35 lines)
- `action-reasoner/skills/pyapi/evidence/p1_api.json` (full, 34 lines)
- Directory listings: pack root, scripts/, evidence/ (via ls)
- Import grep attempted via muse.search on scripts/ (returned empty; imports taken from full reads instead — all 3 scripts read fully, so no gap)
