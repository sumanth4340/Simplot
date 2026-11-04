# Skill 13 APP & SESSION — Trained Pack (GRADUATED)

Verified live on Isaac Sim 6.0.0 / Kit 110, windowed GUI, Windows.
Co-validated with graduated skills (X13 gauntlet, 8/8).

## Verified facts (do not guess these)
- Drive the session from OUTSIDE: local python drivers shelling
  library scripts (simulation_control, open_stage, stage_info,
  viewport_screenshot) through isaacsim_send.py --arg.
- Timeline states cycle exactly: STOPPED->PLAYING->PAUSED->
  STOPPED; status reports physics dt/sim-time/steps/backend.
- set_current_time applies on the NEXT pump, not instantly:
  pump 2 steps between set and get (R1).
- Stage round-trip: new -> define -> save_as .usd -> new
  (wipe, prim count drops) -> open -> marker valid, file kept.
- Extension manager: is_extension_enabled("isaacsim.
  code_editor.python_server") True (659 extensions listed);
  carb.settings set/get round-trips on custom keys.
- stage_info tree/list/filter/prim-path all locate markers;
  tree transcripts need UTF-8 file IO on Windows (R2).

## Dataset (evidence/, replayable)
- A1 timeline: 7/7, full state cycle + time 2.500 + 60 steps.
- A2 round-trip: 8/8, marker 0.70 survives save/wipe/reopen.
- A3 ext/settings: 4/4, pyserver True, bogus False, 659 ext.
- A4 inspect: 4/4, tree + Cube filter + prim detail.
- V13 exam (session loop + shot): 9/9, save/reopen/step-60/
  1280x720 non-black shot, ends stopped.
- X13 cross-val: 8/8 across stage/model/sense/rig/app/session.

## Tools (scripts/, LOCAL drivers unless noted)
- a1_run (+a1_time), a2_run (+a2_marker/a2_check), a3_probe
  (in-sim), a4_run, v13_run (+v13_build/v13_check in-sim).
- verify_aN / verify_v13: local evaluators, exit 0 on pass.
- cross-val x13_live.py + verify_x13.py: co-validation snapshot.

## Eval
Suite: A1 A2 A3 A4 V13 (5/5 green) + X13 co-val (8/8).

## Failure catalog
See failures.md (R1-R2).
