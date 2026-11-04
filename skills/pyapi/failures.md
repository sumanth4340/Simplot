# pyapi P1 -- Notes (live-verified, Isaac Sim 6.0 / Kit 110)

Contract (per isaac-sim-workflow scoping): Technical reference --
probe the named API gaps in-session, gate measured behavior.

## kit commands (3/3)
- `omni.kit.commands.execute("CreatePrim", prim_path=..., prim_type=...)`
  works live; roundtrip undo/redo verified.
- Undo lives in `omni.kit.undo` (`undo()`/`redo()`), NOT in
  `omni.kit.commands` (no `undo` attr there) -- first probe failed on
  this assumption.
- `omni.kit.commands` has no `get_command_names` either; command
  discovery by name-listing is unavailable (dropped, not gated).

## omni.client (3/3)
- `stat`/`list` are SYNCHRONOUS tuple APIs `(Result, payload)` -- not
  awaitable (first probe failed awaiting a tuple).
- stat(hosted root) -> OK; list(.../Sensors/NVIDIA) -> 8 entries incl.
  Example_Rotary_2D; stat(bogus) -> ERROR_NOT_FOUND (clean miss).
- Complements G2 (Ar resolver): client-level file ops agree.

## timeline / app (3/3)
- `app_utils.play()` + `update_app_async(10)` + `app_utils.stop()`:
  stopped -> playing, sim time advances, back to stopped.
  (Drives R1/R2/D1 already relied on this; P1 pins it explicitly.)
