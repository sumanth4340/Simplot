# pyapi TOOLS_REF — exhaustive tool reference (2026-11-04)

Pack: `action-reasoner/skills/pyapi/` (P1 drill, Isaac Sim 6.0.0 / Kit 110).
Parent: [TOOLS.md](action-reasoner/skills/pyapi/TOOLS.md) (summary); this file is the exhaustive companion.
`discovery.md`: ABSENT from pack [verified — directory listing 2026-11-04].

Claim tags: `[verified]` = measured live by this pack's drill and present in
`evidence/p1_api.json` or the scripts' executed paths; `[probable]` = strongly
implied by in-pack code/evidence but not directly asserted by a gate;
`[theoretical]` = inferred or unprobed — do not rely on without a new drill.

Tools covered: 8. Functions documented: 36 (21 executed/gated + 3 proven-absent + 12 observed-via-dir).
Knobs documented: 13. EKB rules: 24. LIMITS: 26. UNKNOWNs: 21.
DATATYPE pass (2026-11-04): signatures typed 36/36; knobs typed 13/13; still-unknown 23 (22 signatures with >=1 [theoretical] type component + 1 knob with unknown default: `steps`).

---

## T1 — omni.kit.commands

DOES: Executes named Kit commands that author USD live through the
command pattern, with edits landing on the Kit undo stack [verified —
`kc.execute("CreatePrim", ...)` authored `/World/P1Cmd` live, then
`ku.undo()` removed it: `scripts/p1_fix.py:17-20`, `evidence/p1_api.json:5,29`].

### Functions

- `execute(command_name: str, *, prim_path: str, prim_type: str) -> Any`
  [verified-call at `scripts/p1_probe.py:20-21` and `scripts/p1_fix.py:17`;
  return `Any` theoretical]:
  - `command_name: str` (positional, required, no default; unit N/A — name
    token) — the registered command name; only `"CreatePrim"` is
    drill-proven [verified].
  - `prim_path: str` (keyword, required, no default; unit N/A — USD path
    string) — prim to author; observed `"/World/P1Cmd"` [verified].
  - `prim_type: str` (keyword, required, no default; unit N/A — schema
    token) — observed `"Xform"` [verified].
  - Returns `Any`: ignored by both scripts; type/value unrecorded
    [theoretical — probable command-result object or `None`].
  - NOTE: kwarg names/types for any other command are [theoretical] (only
    `CreatePrim(prim_path, prim_type)` proven).
- `get_command_names() -> list[str]` — PROVEN ABSENT: `hasattr(kc,
  "get_command_names")` was False, so the probe recorded `n_commands: 0`,
  `has_create: false`, `has_delete: false` [verified —
  `scripts/p1_probe.py:12-16`, `evidence/p1_api.json:2-4`,
  `SKILL.md:24-26`, `failures.md:12-13`]. Hypothetical shape: zero params;
  returns `list[str]`; defaults N/A — whole signature [theoretical]
  (guarded expression at `scripts/p1_probe.py:12-13` never invoked it).
- `undo() -> NoReturn` — PROVEN ABSENT on this module: zero-arg `kc.undo()`
  raised (first probe failed on the wrong-module assumption) [verified —
  `scripts/p1_probe.py:23`, `failures.md:9-11`]. Params: none [verified
  from call site]. Return: never returns — raises; exception class
  [theoretical] (`commands_err` was deleted from final evidence).
- `redo() -> NoReturn` — PROVEN ABSENT on this module [verified-absent via
  `dir` — only `POST_UNDO_CALLBACK` / `PRE_UNDO_CALLBACK` constants,
  `scripts/p1_fix.py:9-10`, `evidence/p1_api.json:11-14`]. Params: none
  [verified-shape from call site `scripts/p1_probe.py:25`, which was
  present but UNREACHED — probe excepted at line 23]. Return: never
  returns [probable — by symmetry with `undo()`; unexecuted].

### Knobs + effect-of-change

- `command_name: str` (required positional, no default; unit N/A)
  [verified knob, 1 value proven]: `"CreatePrim"` authors a prim; any other
  name (e.g. `"DeletePrims"`) is untested — changing it may raise
  unknown-command or execute unknown semantics [theoretical].
- `prim_path: str` (required keyword, no default; unit N/A)
  [verified knob]: changing the path changes which prim is authored/asserted;
  the drill asserts existence at exactly this path via
  `GetPrimAtPath(path).IsValid()` [verified — `scripts/p1_fix.py:17-18`].
- `prim_type: str` (required keyword, no default; unit N/A)
  [verified knob]: `"Xform"` proven; another type string would author a
  different schema (untested) [probable — Kit CreatePrim semantics; values
  beyond Xform theoretical].

### EKB rules (IF/THEN/BECAUSE)

- IF scripting a reversible USD edit THEN call
  `omni.kit.commands.execute("CreatePrim", prim_path=..., prim_type=...)`
  BECAUSE it is the only command-pattern authoring call gated live 9/9
  [verified — `failures.md:7-8`].
- IF you need to undo that edit THEN call `omni.kit.undo.undo()`, NEVER
  `omni.kit.commands.undo()` BECAUSE undo/redo live only in
  `omni.kit.undo` and the first probe failed on the wrong-module assumption
  [verified — `failures.md:9-11`].
- IF you need to enumerate available commands THEN do not attempt
  `get_command_names` — address commands by known name BECAUSE the module
  exposes no listing API (`n_commands: 0`) [verified —
  `evidence/p1_api.json:2`, `SKILL.md:24-26`].

### LIMITS (with cites)

- L1. No `undo`/`redo` callables on `omni.kit.commands`
  (`scripts/p1_probe.py:23` raised; `failures.md:9-11`) [verified].
- L2. No `get_command_names`; command discovery by name-listing is
  unavailable (`scripts/p1_probe.py:12-14`, `evidence/p1_api.json:2-4`,
  `SKILL.md:24-26`, `failures.md:12-13`) [verified].
- L3. Only `CreatePrim` with `(prim_path, prim_type)` kwargs is proven;
  every other command name/signature is outside the gate
  (`scripts/p1_fix.py:17`, `failures.md:7-8`) [verified].
- L4. `dir(kc)` undo/redo filter yields only the two `*_UNDO_CALLBACK`
  constants, no callables (`scripts/p1_fix.py:9-10`,
  `evidence/p1_api.json:11-14`) [verified].

### UNKNOWN (theoretical)

- U1. Full Kit command catalog (names + signatures beyond `CreatePrim`;
  `DeletePrims` explicitly untested) [theoretical].
- U2. Whether EVERY `execute` pushes an undo entry or only some commands
  do [theoretical].
- U3. Return value of `execute` (scripts ignore it) and error behavior on
  unknown command name / bad kwargs [theoretical].

---

## T2 — omni.kit.undo

DOES: Owns the Kit undo/redo stack; `undo()` removes the last
command-pattern edit and `redo()` restores it [verified — roundtrip
create -> undo removes -> redo restores at `scripts/p1_fix.py:17-23`,
`evidence/p1_api.json:5,29-30`, `failures.md:7-8`].

### Functions

- `undo() -> Any` — params: none (zero-arg call) [verified —
  `scripts/p1_fix.py:19`]; unit N/A; defaults N/A. Removes the last command
  edit [verified]. Returns `Any` [theoretical — ignored by script; probable
  `None`].
- `redo() -> Any` — params: none (zero-arg call) [verified —
  `scripts/p1_fix.py:21`]; unit N/A; defaults N/A. Restores the undone edit
  [verified]. Returns `Any` [theoretical — ignored by script; probable
  `None`].
- Observed-via-`dir()` but NEVER executed — names [verified-observed —
  `scripts/p1_fix.py:13`, `evidence/p1_api.json:15-28`]; every signature
  below fully [theoretical] (zero call sites; arg counts, types, defaults,
  units, and returns all unknown — `(*args: Any, **kwargs: Any) -> Any`
  is the honest placeholder shape):
  - `begin_disabled(*args: Any, **kwargs: Any) -> Any` [theoretical]
  - `begin_group(*args: Any, **kwargs: Any) -> Any` [theoretical]
  - `can_redo(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> bool` from the `can_` prefix]
  - `can_repeat(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> bool`]
  - `can_undo(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> bool`]
  - `clear_history(*args: Any, **kwargs: Any) -> Any` [theoretical —
    probable shape `() -> None`]
  - `clear_stack(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> None`]
  - `disabled(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> bool`]
  - `end_disabled(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> None`]
  - `end_group(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> None`]
  - `execute(*args: Any, **kwargs: Any) -> Any` [theoretical — no shape
    guess; arg count fully unknown]
  - `get_history(*args: Any, **kwargs: Any) -> Any` [theoretical — probable
    shape `() -> list[Any]`]
  NOTE: the capture truncates at 12 names (`[:12]`), so further public
  names may exist beyond `get_history` alphabetically [probable].

### Knobs + effect-of-change

- None: `undo()` and `redo()` take zero arguments in the drilled calls; there
  is no knob to vary [verified — `scripts/p1_fix.py:19-21`].
- Grouping/history/disabled knobs (possible args to `begin_group`,
  `execute`, `get_history`, etc.) are unprobed — effect-of-change unknown
  [theoretical].

### EKB rules (IF/THEN/BECAUSE)

- IF a `kc.execute(...)` edit must be reverted THEN call
  `omni.kit.undo.undo()` with no args and assert absence via
  `GetPrimAtPath(path).IsValid() is False` BECAUSE the gated roundtrip
  proves removal [verified — `scripts/p1_fix.py:19-20`].
- IF an undone edit must be restored THEN call `omni.kit.undo.redo()` with
  no args BECAUSE the gated roundtrip proves restoration [verified —
  `scripts/p1_fix.py:21-22`].
- IF undo behavior looks wrong THEN check the import is `omni.kit.undo`
  (not `omni.kit.commands`) BECAUSE the first probe failed exactly on that
  confusion [verified — `failures.md:9-11`].

### LIMITS (with cites)

- L5. Undo/redo live ONLY in `omni.kit.undo`, not in `omni.kit.commands`
  (`failures.md:9-11`) [verified].
- L6. Only zero-arg `undo()`/`redo()` on a single `CreatePrim` edit are
  gated; multi-edit stacks, groups, and redo-after-new-edit are untested
  (`scripts/p1_fix.py:17-23`) [verified].
- L7. `undo_mod` capture is truncated at 12 sorted names, so the observed
  list is a lower bound on the module surface (`scripts/p1_fix.py:13`)
  [verified].

### UNKNOWN (theoretical)

- U4. Signatures/semantics of all 12 observed grouping/history/disabled APIs
  (`begin_group`/`end_group`, `can_undo`/`can_redo`/`can_repeat`,
  `clear_history`/`clear_stack`, `begin_disabled`/`end_disabled`/`disabled`,
  `execute`, `get_history`) [theoretical].
- U5. Whether direct USD edits (`stage.RemovePrim`, used for setup/teardown
  at `scripts/p1_fix.py:15-16,23`) interact with or pollute the undo stack
  [theoretical].
- U6. Error behavior of `undo()` with an empty stack / `redo()` with
  nothing undone (exception? silent no-op?) [theoretical].

---

## T3 — omni.client

DOES: Synchronous low-level file ops against the hosted asset root:
`stat(path)` and `list(dir)` return `(Result, payload)` tuples directly,
NOT awaitables [verified — sync calls at `scripts/p1_fix.py:32-40`;
`failures.md:16-17`].

### Functions

- `stat(path: str) -> tuple[Result, Any]` — SYNCHRONOUS [verified —
  `scripts/p1_fix.py:32-33,39-40`]:
  - `path: str` (positional, required, no default; unit N/A — URL string)
    — full URL to stat; observed: hosted root and root +
    `"/Isaac/Sensors/NOPE/Nope.usd"` [verified].
  - Returns `tuple[Result, Any]`: `r[0]: Result` is the status (`Result.OK`
    on hit, `Result.ERROR_NOT_FOUND` on miss) [verified —
    `evidence/p1_api.json:31,34`]; `r[1]: Any` success payload
    [theoretical — scripts index only `r[0]`, shape never recorded].
- `list(dir_path: str) -> tuple[Result, list[Entry]]` — SYNCHRONOUS
  [verified — `scripts/p1_fix.py:34-38`]:
  - `dir_path: str` (positional, required, no default; unit N/A — URL
    string) — observed: root + `"/Isaac/Sensors/NVIDIA"` [verified].
  - Returns `tuple[Result, list[Entry]]`: `r[0]: Result` status; `r[1]:
    list[Entry]` where each entry exposes `.relative_path: str` (accessed
    via `getattr(i, "relative_path", "?")`) [verified —
    `scripts/p1_fix.py:35-36`, 8 entries incl. `Example_Rotary_2D`,
    `evidence/p1_api.json:32-33`]; every other `Entry` attribute
    [theoretical].

### Knobs + effect-of-change

- `stat` `path: str` (required positional, no default; unit N/A)
  [verified knob]: hosted root -> `Result.OK`; bogus `.../NOPE/Nope.usd`
  -> `Result.ERROR_NOT_FOUND` (clean miss, no exception) [verified —
  `evidence/p1_api.json:31,34`].
- `list` `dir_path: str` (required positional, no default; unit N/A)
  [verified knob, 1 value proven]: `.../Isaac/Sensors/NVIDIA` -> 8 entries;
  other directories unprobed [verified for the one path; generalization
  theoretical].
- Entry `.relative_path: str` (read-only attribute, not settable; unit N/A;
  default N/A) [verified read knob]: the name accessor used for matching
  (`"Example_Rotary_2D" in n`); other entry attributes unprobed [verified
  — `scripts/p1_fix.py:36,38`].

### EKB rules (IF/THEN/BECAUSE)

- IF calling `oc.stat`/`oc.list` THEN call them WITHOUT `await` and unpack
  `r[0]`/`r[1]` as a tuple BECAUSE they are synchronous tuple APIs and the
  first probe failed awaiting a tuple [verified — `failures.md:16-17`,
  `scripts/p1_probe.py:37` vs `scripts/p1_fix.py:32`].
- IF checking asset existence THEN compare `r[0]` against `Result.OK` /
  `Result.ERROR_NOT_FOUND` strings BECAUSE misses surface as status codes,
  not exceptions [verified — `evidence/p1_api.json:31,34`].
- IF listing a directory THEN read names via `getattr(entry,
  "relative_path", "?")` BECAUSE that accessor is the drill-proven shape
  [verified — `scripts/p1_fix.py:36`].

### LIMITS (with cites)

- L8. `stat`/`list` are SYNCHRONOUS `(Result, payload)` tuples, not
  awaitable (`scripts/p1_fix.py:32-40`, `failures.md:16-17`) [verified].
- L9. Gated values: `stat(root) -> Result.OK`; `list(.../Sensors/NVIDIA) ->
  8 entries incl. Example_Rotary_2D`; `stat(bogus) ->
  Result.ERROR_NOT_FOUND` (`evidence/p1_api.json:31-34`,
  `failures.md:18-19`) [verified].
- L10. Client-level file ops agree with the G2 Ar-resolver layer one level
  down (`failures.md:20`) [verified].
- L11. Success payload of `stat` beyond `r[0]` was never recorded
  (`scripts/p1_fix.py:33` keeps only `r[0]`) [verified].

### UNKNOWN (theoretical)

- U7. All other `omni.client` ops (copy/move/delete/write/mkdir, recursive
  list, watch/subscribe) — none probed [theoretical].
- U8. Behavior on unreachable/offline root (timeouts, error codes beyond
  `ERROR_NOT_FOUND`) — only happy path + clean miss gated [theoretical].
- U9. Full `stat` success-payload and list-entry attribute shapes beyond
  `.relative_path` [theoretical].
- U10. Whether `list` on a missing directory returns `ERROR_NOT_FOUND` like
  `stat`, an empty list, or raises [theoretical].

---

## T4 — isaacsim.storage.native.get_assets_root_path

DOES: Returns the hosted Isaac Sim assets root URL string used as the base
for `omni.client` ops [verified — `scripts/p1_probe.py:34-36`,
`scripts/p1_fix.py:30-31`].

### Functions

- `get_assets_root_path() -> str` — params: none (zero-arg root lookup)
  [verified — called with no args at `scripts/p1_probe.py:35` and
  `scripts/p1_fix.py:31`]; unit N/A; defaults N/A. Returns the hosted root
  URL string; live value ended `"us-west-2.amazonaws.com/Assets/Isaac/6.0"`
  at validation time [verified — `evidence/p1_api.json:6`]. Import path:
  `from isaacsim.storage.native import get_assets_root_path` [verified].

### Knobs + effect-of-change

- None: zero-arg call; no knob to vary [verified]. The RETURNED string
  (`str`; unit N/A; not a settable default) is the effective knob for
  downstream `stat`/`list` path construction (`root + "/Isaac/..."`)
  [verified — `scripts/p1_fix.py:34,39`].

### EKB rules (IF/THEN/BECAUSE)

- IF building hosted-asset paths for `omni.client` THEN call
  `get_assets_root_path()` and append the subpath BECAUSE every gated file
  op in this pack is rooted there [verified — `scripts/p1_fix.py:31-39`].
- IF recording the root for evidence THEN keep at least the tail 40 chars
  (`root[-40:]`) BECAUSE that is the drill's proven fingerprint format
  [verified — `scripts/p1_probe.py:36`].

### LIMITS (with cites)

- L12. Live value tail `us-west-2.amazonaws.com/Assets/Isaac/6.0` at
  validation time (`evidence/p1_api.json:6`) [verified].
- L13. File ops built on this root agree with the G2 Ar-resolver layer
  (`failures.md:20`) [verified].
- L14. Only the no-arg call on a live hosted session is gated; no other
  signature or session state is proven (`scripts/p1_probe.py:34-35`)
  [verified].

### UNKNOWN (theoretical)

- U11. Return/exception behavior when offline or no Nucleus is configured
  (exception? empty string? local fallback?) [theoretical].
- U12. Whether the root is configurable per-session and how that interacts
  with the 8-entry NVIDIA listing gate [theoretical].

---

## T5 — omni.timeline (timeline interface)

DOES: Timeline state readback — the playing flag and current sim time used
to gate drive roundtrips [verified — `scripts/p1_probe.py:53-62`,
`evidence/p1_api.json:7-10`].

### Functions

- `get_timeline_interface() -> ITimeline` — params: none (zero-arg
  singleton accessor on `omni.timeline`) [verified —
  `scripts/p1_probe.py:51,53`]; unit N/A; defaults N/A. Returns the timeline
  object `tl` [verified]; type NAME `ITimeline` [probable — inferred; the
  object is verified only to expose `is_playing()`/`get_current_time()`].
- `is_playing() -> bool` — params: none (zero-arg state read on the timeline
  object) [verified — `scripts/p1_probe.py:54,59,62`]; unit N/A; defaults
  N/A. Observed `False` before `play()`, `True` after `play()`+steps,
  `False` after `stop()` [verified — `evidence/p1_api.json:7,8,10`].
- `get_current_time() -> float` — params: none (zero-arg sim-time read)
  [verified — `scripts/p1_probe.py:55,58`]; unit: seconds [probable — sim
  time; magnitude/rate ungated]; defaults N/A. Observed strictly increasing
  across 10 stepped frames while playing (`time_adv: true`) [verified —
  `evidence/p1_api.json:9`].

### Knobs + effect-of-change

- None: all three drilled calls are zero-arg; no knob to vary [verified].
  Effective upstream knobs are T6's `play()`/`update_app_async(steps)`/
  `stop()`, whose effects surface through these reads [verified —
  `scripts/p1_probe.py:56-62`].

### EKB rules (IF/THEN/BECAUSE)

- IF gating a drive roundtrip THEN snapshot `was_playing =
  tl.is_playing()` BEFORE `play()` and require `playing is True` after
  `play()`+steps BECAUSE the verifier gates exactly that transition
  [verified — `scripts/verify_p1.py:25-26`].
- IF proving sim time advanced THEN compare `get_current_time()` before vs
  after stepping and require `f1 > f0` BECAUSE that is the gated
  `tl-advance` check [verified — `scripts/p1_probe.py:55-60`,
  `scripts/verify_p1.py:28`].
- IF stopping THEN assert `not tl.is_playing()` AFTER `stop()` BECAUSE that
  is the gated `tl-stop` check [verified — `scripts/p1_probe.py:61-62`,
  `scripts/verify_p1.py:29`].

### LIMITS (with cites)

- L15. Gated roundtrip: `was_playing False` -> `playing True` after
  `play()`+10 steps -> `stopped True` after `stop()`
  (`evidence/p1_api.json:7-10`, `failures.md:23-24`) [verified].
- L16. Only `is_playing()` and `get_current_time()` reads are gated; no
  timeline WRITE call (`set_current_time`, rate, pause) was exercised
  (`scripts/p1_probe.py:53-62`) [verified].
- L17. `time_adv` proves only strict increase over 10 stepped frames while
  playing — no per-frame rate or magnitude is gated
  (`scripts/p1_probe.py:57-60`) [verified].

### UNKNOWN (theoretical)

- U13. `pause()` vs `stop()` semantics and what `is_playing()` reports for
  each [theoretical].
- U14. `set_current_time`, playback-rate / time-codes-per-second APIs —
  none probed [theoretical].
- U15. `is_playing()` immediately after `play()` WITHOUT stepping (possible
  bridge read-lag of one result — noted in TOOLS.md Unverified from live
  memory, NOT proven by this pack) [theoretical].

---

## T6 — isaacsim.core.experimental.utils.app (app_utils)

DOES: Drives the Kit app/timeline — start playback, pump frames
asynchronously, stop playback [verified — `scripts/p1_probe.py:56-62`,
`failures.md:23-24`].

### Functions

- `play() -> Any` — params: none (zero-arg playback start) [verified —
  `scripts/p1_probe.py:56`]; unit N/A; defaults N/A. Transitions stopped
  -> playing (with steps) [verified — `evidence/p1_api.json:7-8`]. Returns
  `Any` [theoretical — ignored by script; probable `None`].
- `update_app_async(*, steps: int = <unknown>) -> Coroutine[Any, Any, Any]` —
  MUST be awaited [verified — `await app_utils.update_app_async(steps=10)`
  at `scripts/p1_probe.py:57`]:
  - `steps: int` (keyword-passed, observed `10`; unit: frames, i.e. pumped
    app steps [probable]; default [theoretical] — the drill always passes
    10 explicitly so the true default is unprobed).
  - Returns an awaitable (coroutine) [verified — `await` succeeds]; the
    awaited RESULT value is ignored [theoretical]. Advances sim time while
    playing (`time_adv: true`) [verified — `evidence/p1_api.json:9`].
- `stop() -> Any` — params: none (zero-arg playback stop) [verified —
  `scripts/p1_probe.py:61`]; unit N/A; defaults N/A. Transitions playing ->
  stopped [verified — `evidence/p1_api.json:10`]. Returns `Any`
  [theoretical — ignored by script; probable `None`].
- Import path: `import isaacsim.core.experimental.utils.app as app_utils`
  [verified — `scripts/p1_probe.py:52`].

### Knobs + effect-of-change

- `steps: int` on `update_app_async` (keyword-passed; default [theoretical]
  — always passed explicitly; unit: frames [probable]) [verified knob, 1
  value proven]: `steps=10` while playing advances sim time and yields
  `playing True` [verified — `scripts/p1_probe.py:57-60`]. Fewer/more steps
  unprobed: minimum for a stable `is_playing`/`time_adv` read unknown
  [theoretical]; behavior while STOPPED unknown (time advance? no-op?
  error?) [theoretical].

### EKB rules (IF/THEN/BECAUSE)

- IF driving any sim activity THEN run the exact sequence `play()` ->
  `await update_app_async(steps=10)` -> `stop()` BECAUSE it is the P1-gated
  roundtrip every other pack's drives rely on [verified —
  `failures.md:23-25`].
- IF pumping frames THEN `await` the call — it is a coroutine, unlike
  `omni.client`'s sync tuple calls BECAUSE the probe awaits it successfully
  while awaiting `oc.stat` fails [verified — `scripts/p1_probe.py:37`
  (fails) vs `:57` (works)].
- IF the timeline must end clean THEN always call `stop()` and assert
  `not is_playing()` BECAUSE the `tl-stop` gate requires it [verified —
  `scripts/verify_p1.py:29`].

### LIMITS (with cites)

- L18. `play()` + `update_app_async(10)` + `stop()` proven: stopped ->
  playing, time advances, back to stopped (`evidence/p1_api.json:7-10`,
  `failures.md:23-24`) [verified].
- L19. Only `steps=10` while playing is proven; no other step count or
  stopped-state pump is gated (`scripts/p1_probe.py:57`) [verified].
- L20. `update_app_async` is awaitable (coroutine) — the ONLY awaited call
  in the pack that works (`scripts/p1_probe.py:57`) [verified].
- L21. Every drive in every pack relies on this pattern; P1 pins it
  explicitly (`failures.md:25`, `SKILL.md:47-49`) [verified].

### UNKNOWN (theoretical)

- U16. Minimum/typical step counts for a stable read (only `steps=10`
  proven); true default of `steps` if omitted [theoretical].
- U17. `update_app_async` behavior while stopped (time advance? no-op?
  error?) [theoretical].
- U18. Other app-utils helpers (pause, reset, sync step variants) — none
  probed [theoretical].

---

## T7 — omni.usd (stage access + assertion layer)

DOES: Stage handle plus prim existence checks and cleanup used as the
assertion layer for the command roundtrip [verified —
`scripts/p1_probe.py:17-27`, `scripts/p1_fix.py:14-23`].

### Functions

- `omni.usd.get_context() -> UsdContext` — params: none (zero-arg context
  accessor) [verified — `scripts/p1_probe.py:17`, `scripts/p1_fix.py:14`];
  unit N/A; defaults N/A. Type NAME `UsdContext` [probable — inferred; the
  object is verified only to expose `.get_stage()`]. Import: `import
  omni.usd` [verified — `scripts/p1_probe.py:4`].
- `get_context().get_stage() -> Usd.Stage` — params: none (zero-arg stage
  handle) [verified — same lines]; unit N/A; defaults N/A. Returns `st`
  used for all prim ops [verified]; type NAME `Usd.Stage` [probable —
  pxr convention, inferred].
- `stage.GetPrimAtPath(path: str) -> Usd.Prim`:
  - `path: str` (positional, required, no default; unit N/A — USD path
    string) — observed `"/World/P1Cmd"` [verified —
    `scripts/p1_fix.py:15,18,20,22`].
  - Returns the prim object [verified — `.IsValid()` invoked on it]; type
    NAME `Usd.Prim` [probable — pxr convention, inferred].
- `prim.IsValid() -> bool` — params: none (zero-arg existence check)
  [verified — `scripts/p1_fix.py:15,18,20,22`]; unit N/A; defaults N/A. The
  sole assertion primitive: `True` after create/redo, `False` after undo
  [verified — `scripts/p1_fix.py:18-22`, `evidence/p1_api.json:5,29-30`].
- `stage.RemovePrim(path: str) -> bool`:
  - `path: str` (positional, required, no default; unit N/A — USD path
    string) — observed `"/World/P1Cmd"` [verified].
  - Returns `bool` [probable — pxr `RemovePrim` convention; scripts ignore
    the return and its value was never recorded]. Used for setup/teardown
    cleanup (guarded by an `IsValid()` check on setup, unguarded on
    teardown) [verified — `scripts/p1_fix.py:15-16,23`].

### Knobs + effect-of-change

- `GetPrimAtPath`/`RemovePrim` `path: str` (required positional, no
  default; unit N/A) [verified knob]: must match the `prim_path` given to
  `kc.execute`; a mismatch silently asserts/cleans the wrong prim [probable
  — same `/World/P1Cmd` literal in all three roles at
  `scripts/p1_fix.py:15-23`].
- No knobs on `get_context`/`get_stage`/`IsValid` (all zero-arg) [verified].

### EKB rules (IF/THEN/BECAUSE)

- IF asserting a command roundtrip THEN use
  `st.GetPrimAtPath(path).IsValid()` after each leg (create True, undo
  False, redo True) BECAUSE that triple is exactly what the verifier gates
  [verified — `scripts/verify_p1.py:15-17`].
- IF a drill prim may pre-exist THEN guard setup with `if
  st.GetPrimAtPath(p).IsValid(): st.RemovePrim(p)` BECAUSE both scripts do
  this to guarantee a clean start [verified — `scripts/p1_fix.py:15-16`].
- IF tearing down THEN call `st.RemovePrim(path)` unconditionally last
  BECAUSE the drill leaves no `/World/P1Cmd` behind [verified —
  `scripts/p1_fix.py:23`].

### LIMITS (with cites)

- L22. Only the five calls above were exercised; the rest of the
  `omni.usd`/USD API surface is out of this pack's scope
  (`scripts/p1_fix.py:14-23`) [verified].
- L23. `RemovePrim` return value and behavior on a missing path were never
  recorded (setup guarded, teardown unguarded, both returns ignored)
  (`scripts/p1_fix.py:15-16,23`) [verified].
- L24. Assertion layer only — `omni.usd` proves command effects but no USD
  authoring call of its own is gated here [verified].

### UNKNOWN (theoretical)

- U19. Whether `RemovePrim` setup/teardown edits interact with the
  `omni.kit.undo` stack (see also U5) [theoretical].
- U20. Full `omni.usd` API surface (context options, stage events, notices)
  — untouched by this pack [theoretical].

---

## T8 — Local verifier stack (json / sys / gate)

DOES: Host-side (non-sim) evidence gating — loads the in-sim JSON artifact
and PASS/FAILs 9 gates with exit codes [verified — full read of
`scripts/verify_p1.py`, 35 lines].

### Functions

- `gate(name: str, ok: Any, detail: str = "") -> None` (local helper,
  `scripts/verify_p1.py:10-11`):
  - `name: str` (positional, required, no default; unit N/A) — gate label
    (`cmd-create`, `cmd-undo`, `cmd-redo`, `stat-root`, `list-nvidia`,
    `stat-missing`, `tl-play`, `tl-advance`, `tl-stop`) [verified —
    `scripts/verify_p1.py:15-29`].
  - `ok: Any` (positional, required, no default; unit N/A) — truthiness
    coerced via `bool(ok)`; call sites pass `bool` expressions [verified —
    `:11,15-29`].
  - `detail: str = ""` (default `""`; unit N/A) — free-form context printed
    after the verdict [verified — `:11,31-32`].
  - Returns `None`; appends `(name: str, bool(ok): bool, detail: str)` to
    module-level `gates: list[tuple[str, bool, str]]` [verified — `:7,11`].
- `json.load(fp: TextIO) -> dict[str, Any]` — `fp` is `open(EV)` with `EV =
  "action-reasoner/skills/pyapi/evidence/p1_api.json"` (repo-relative; run
  from repo root) [verified — `scripts/verify_p1.py:5,14`]; returns the
  evidence dict [verified]; unit N/A.
- `json.dump(obj: dict[str, Any], fp: TextIO, indent: int = 1) -> None` —
  in-sim evidence write with `obj=out`, `fp` the open evidence file,
  `indent=1` passed explicitly in both scripts [verified —
  `scripts/p1_probe.py:66-67`, `scripts/p1_fix.py:45-46`]; returns `None`
  [verified — stdlib; return ignored]. Stdlib default `indent=None`
  [probable — stdlib signature, out-of-pack]; unit N/A.
- `sys.exit(code: int = 0) -> NoReturn` — `code: int` (positional; observed
  values `{0, 1}`: `0` iff all 9 gates pass, else `1`) [verified —
  `scripts/verify_p1.py:30-35`]; stdlib default `0` [probable — stdlib,
  out-of-pack]; unit N/A; never returns. Prints `P1-PASS 9/9` / `P1-FAIL
  n/9` [verified — `:33-34`].

### Knobs + effect-of-change

- `gate` `name: str` / `ok: Any` / `detail: str = ""` (name/ok required,
  no default; detail defaults `""`; all unit N/A) [verified knobs]: `name`
  labels the line; `ok` decides PASS/FAIL; `detail` annotates (e.g.
  `"n=%s"`, `"omni.kit.undo"`, `str(stat)`) [verified —
  `scripts/verify_p1.py:15-32`].
- `EV: str` module constant `= "action-reasoner/skills/pyapi/evidence/
  p1_api.json"` (unit N/A; not a param default) [verified knob]:
  repo-relative; running from another cwd breaks the load [probable — plain
  relative `open()`, no path resolution].
- Gate predicates `-> bool` (exact boolean expressions, no defaults; unit
  N/A): `is True` for booleans, `== "Result.OK"` / `==
  "Result.ERROR_NOT_FOUND"` for stats, `n >= 1 and has_rotary2d` for the
  listing, `was_playing is False and playing is True` for tl-play [verified
  — `scripts/verify_p1.py:15-29`]. Relaxing any predicate weakens the P1
  contract [probable].

### EKB rules (IF/THEN/BECAUSE)

- IF validating P1 THEN run `verify_p1.py` from the repo root and require
  exit 0 / `P1-PASS 9/9` BECAUSE that is the pack's validated contract
  [verified — `SKILL.md:6,16`, `scripts/verify_p1.py:33-35`].
- IF adding a gate THEN append `gate(name, ok, detail)` before the `fails`
  computation BECAUSE verdict/count derive from the `gates` list
  [verified — `scripts/verify_p1.py:30-35`].
- IF debugging a FAIL THEN read the per-gate `detail` column first BECAUSE
  stat/list gates print the offending value there [verified —
  `scripts/verify_p1.py:18-24,31-32`].

### LIMITS (with cites)

- L25. Exactly 9 gates: cmd-create/undo/redo, stat-root, list-nvidia,
  stat-missing, tl-play/advance/stop (`scripts/verify_p1.py:15-29`,
  `SKILL.md:16` P1-PASS 9/9) [verified].
- L26. `tl-play` requires the pair (`was_playing is False`, `playing is
  True`); a drill starting from an already-playing timeline FAILs
  (`scripts/verify_p1.py:25-26`) [verified].

### UNKNOWN (theoretical)

- U21. None material — trivial local harness, fully read (35 lines);
  residual unknowns limited to off-nominal inputs (malformed JSON,
  missing keys all FAIL-safe via `.get`) [probable — `.get` defaults at
  `scripts/verify_p1.py:15-29`].

---

## Cross-tool notes

- Probe-then-fix flow [verified]: `p1_probe.py` wrote the first artifact
  (commands block failed at `kc.undo()`, client block failed at `await`
  on a tuple, timeline block passed); `p1_fix.py` loaded that JSON (`:6`),
  overwrote the command + client keys via the corrected APIs, deleted
  `commands_err` (`:24`), popped `client_err` (`:41`), and left
  probe-origin keys (`n_commands`, `root_tail`, `was_playing`, `playing`,
  `time_adv`, `stopped`) intact — all consistent with the final
  `evidence/p1_api.json` [verified — both scripts + evidence].
- Awaitability split [verified]: `update_app_async` MUST be awaited
  (`p1_probe.py:57` works) while `oc.stat`/`oc.list` must NOT
  (`p1_probe.py:37` fails, `p1_fix.py:32` works). This is the pack's
  sharpest API edge [verified].
- `__pycache__/` holds only `p1_fix.cpython-314.pyc` +
  `verify_p1.cpython-314.pyc` (stale bytecode, not a knowledge source)
  [verified — scripts listing].
- `discovery.md` absent; `failures.md` (25 lines) + `SKILL.md` (67 lines)
  are the only pack prose sources besides TOOLS.md [verified].

## Sources-read

- `action-reasoner/skills/pyapi/SKILL.md` (full, 67 lines)
- `action-reasoner/skills/pyapi/TOOLS.md` (full, 124 lines)
- `action-reasoner/skills/pyapi/failures.md` (full, 25 lines)
- `action-reasoner/skills/pyapi/discovery.md` (ABSENT — verified via failed
  read + directory listing)
- `action-reasoner/skills/pyapi/scripts/p1_probe.py` (full, 68 lines)
- `action-reasoner/skills/pyapi/scripts/p1_fix.py` (full, 49 lines)
- `action-reasoner/skills/pyapi/scripts/verify_p1.py` (full, 35 lines)
- `action-reasoner/skills/pyapi/evidence/p1_api.json` (full, 35 lines)
- Directory listings: pack root, scripts/, evidence/, __pycache__/
- Cited scripts: 3 total — all 3 read FULLY (none skimmed).
