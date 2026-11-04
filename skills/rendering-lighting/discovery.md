# Rendering & Lighting — Discovery Notes (live-verified, Isaac Sim 6.0.0)

## Capture path (RtxCamera + CameraSensor)
- Canonical per isaac-camera: `RtxCamera(path, positions=, orientations=)`
  then `CameraSensor(cam, resolution=[H, W], annotators=["rgb"])`,
  `app_utils.play(commit=True)`, settle, `sensor.get_data("rgb")`.
- Installed-6.0.0 deviations from skill sketches: no `aux_output_level`
  kwarg; resolution must be a LIST (tuple crashes broadcast_to); see R3.
- `get_data` returns a per-camera LIST of warp arrays: unwrap [0] +
  `.numpy()` (see R4, Skill 5 R2 rule).

## Light levers (320x240, filmIso 100, op=6, RealTimePathTracing)
- Dome is the proven lever: 100->400 moved mean 110.2->143.4 (1.30x).
- filmIso is strong: 100->400 moved mean 143.6->213.2 (1.49x).
- DistantLight 3x moved only ~7% (OPEN puzzle, see R5). Prove each
  light's leverage with a ratio gate before building drills on it.
- During-play light-intensity sets apply live (dome proven; sun sets
  apply but contribute little). Re-parse legs add nothing for lights
  but spam stale-handle warnings on sensor re-creation.

## Determinism
- Identical captures repeat bit-exactly (143.6 baseline hit 3x across
  runs; R3 legs repeated 94.8/101.3 across script variants). Any
  divergence means changed inputs, not renderer noise.

## Renderer state notes
- Default headless: rendermode=RealTimePathTracing, tonemap op=6,
  filmIso=100. No autoExposure key present.
- 120 settle steps suffice for these small scenes (skill's 200 is for
  warehouses); 90 after a light/exposure change.
- R4 restores filmIso 100; V6 pins its own exposure. Drills must pin
  (not inherit) render settings.
