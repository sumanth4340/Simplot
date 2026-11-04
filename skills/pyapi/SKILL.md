---
name: pyapi
description: Kit Python API gap drills (P1) — command execute/undo map, omni.client sync-tuple contract, and the timeline play/advance/stop roundtrip. Use when scripting Kit commands with undo, doing omni.client file ops, or driving the timeline.
metadata:
  validated: 2026-11-04
  validated_by: P1 verifier 9/9 green on Isaac Sim 6.0.0/Kit 110
---

# pyapi

## Purpose

Pin the Kit API surface other drills rely on but never gate: kit
commands with undo (P1), `omni.client` file ops on the hosted root
(P1), and the timeline/app stepping roundtrip (P1). Validated live
on Isaac Sim 6.0.0 / Kit 110 (P1-PASS 9/9).

## Prerequisites

- None beyond a live sim + bridge.

## Limitations

- Command discovery by name-listing is unavailable
  (`omni.kit.commands` exposes no `get_command_names`); address
  commands by known name.

## Key procedures

### Command execute/undo map

`omni.kit.commands.execute("CreatePrim", prim_path=...,
prim_type=...)` authors live; undo/redo live in the SEPARATE
`omni.kit.undo` module (`undo()`/`redo()`), not in
`omni.kit.commands`. Roundtrip verified: create -> undo removes ->
redo restores.

### omni.client sync-tuple contract

`stat`/`list` are SYNCHRONOUS `(Result, payload)` calls, not
awaitable. stat(hosted root) -> OK; list(.../Sensors/NVIDIA) -> 8
entries incl. Example_Rotary_2D; stat(bogus) -> ERROR_NOT_FOUND
(clean miss). Agrees with G2's Ar-resolver layer one level down.

### Timeline roundtrip

`app_utils.play()` + `update_app_async(steps)` + `app_utils.stop()`:
stopped -> playing, sim time advances, back to stopped. Every
drive in every pack relies on this; P1 gates it explicitly.

## Related skills

- RECEIVES from: `isaac-sim-remote` (in-sim execution carrier).
- PRODUCES for: all packs (API patterns).

## Failure index

`failures.md` (P1 notes: undo location, sync tuples, roundtrip).

## References

- Scripts: `scripts/p1_probe.py`, `p1_fix.py`, `verify_p1.py`.
- Evidence: `evidence/p1_api.json`.

## Iteration Log

- v0.1 2026-11-04: distilled from P1 drill (MSF Capture).
