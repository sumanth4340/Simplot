# Viewport & UI — Failure Catalog (live-verified)

## R2: symmetric scenes defeat mean-based differ gates
- FAILURE: Opposite views of a symmetric cube scene had means 183.4
  vs 183.8 (delta 0.4) despite clearly different content (file bytes
  46309 vs 34517, std 21.5 vs 18.2).
- RECOVERY: pngstats.mean_abs_diff pixel gate (>3.0; measured 7.59).
- PREVENTION: Compare views by pixels, never by means alone.

## R1: no local PIL; Kit PNGs need a stdlib reader
- FAILURE: Verifier died with ModuleNotFoundError PIL (local env).
- RECOVERY: scripts/pngstats.py - pure-stdlib PNG (IHDR + IDAT +
  scanline unfilter) returning w/h/mean/std. Validated against a
  1280x720 Kit screenshot (171821 bytes).
- PREVENTION: Screenshot drills verify via pngstats, never PIL.
