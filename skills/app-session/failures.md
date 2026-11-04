# App & Session — Failure Catalog (live-verified)

## R2: stage_info tree needs UTF-8 file IO on Windows
- FAILURE: Writing the tree report with default cp1252 raised
  UnicodeEncodeError on box-drawing characters.
- RECOVERY: open(..., encoding="utf-8") on both write and read
  for any transcript that may contain tree art.

## R1: timeline set_current_time applies on next pump, not instantly
- FAILURE: set(2.5) then immediate get returned 0.000.
- CAUSE: The time change is deferred to the next frame update.
- RECOVERY: Pump 2 steps between set and get; then 2.500 exact.
