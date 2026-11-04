# Viewport & UI — Discovery Notes (live-verified, Isaac Sim 6.0.0)

## Reused library scripts (isaac-sim-remote, via --arg)
- viewport_screenshot.py (output_path): 1280x720 RGBA in GUI mode.
  Works headless too (W1 ran headless). ~170KB for lit scenes.
- app_screenshot.py (output_path): full window incl. UI (958x981 in
  this GUI session; size follows the window).
- camera_control.py: get/set/look_at/list_cameras. Active camera is
  /OmniverseKit_Persp (root-level default). set/look_at via
  ViewportManager.set_camera_view(eye/target) + 30 update steps.
- select_prim.py: set/get/clear/all on the USD selection. Round-trip
  verified (set W1Cube -> get shows W1Cube).

## GUI vs headless
- User asked to watch: sim now runs WINDOWED (pid tracked per
  session; relaunch on crash with --enable python_server, no
  --no-window). Screenshots work identically in both modes.
- Second sim crash observed (during a viewport screenshot; first was
  during a lidar probe). Recovery: taskkill tree + relaunch + health
  poll; anonymous stage rebuilds from scripts. Evidence on disk is
  never lost.

## Verification without PIL
- Local env has no PIL: scripts/pngstats.py (stdlib PNG decode:
  IHDR + IDAT + scanline unfilter) gives w/h/mean/std + raw buffer.
- Compare views with mean_abs_diff (pixels), never means alone:
  symmetric scenes coincide in mean (183.4 vs 183.8) while pixels
  differ (7.59).
