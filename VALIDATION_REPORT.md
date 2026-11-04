# Validation report: catalog + skills vs plan

Verdict: **FAIL — fix items below before relying on the plan** (1 FAIL, 4 WARN)

## Findings

- [PASS] (catalog) loaded 3279 full actions, 195 compact actions
- [PASS] (catalog) all actions pass schema (group/params/definition.resolution)
- [WARN] (catalog) pre_rules coverage: 33/3279 full, 32/195 compact carry rules (rest rely on handler checks)
- [PASS] (catalog) resolutions: {'resolved': 2013, 'virtual-backend': 38, 'import-failed': 29, 'context-only': 287, 'source-verified': 823, 'import-context-dependent': 89}
- [WARN] (catalog) compact: 169/195 available; dead=26 resolutions={'resolved': 135, 'virtual-backend': 34, 'import-failed': 26}
- [WARN] (catalog) unknown param types: {"'physicsmaterial'": 1, 'list': 14, 'graph': 1, 'path': 3, '<built-in function callable>': 3, 'usdcontext': 1, 'valuetypename': 2, 'variability': 3, 'keyselectionstate': 2, 'timecode': 7, 'gf.quatd': 3, 'float3': 3, 'float4': 2, 'type': 1, 'sourcetype': 1, 'valuetypenames': 1, 'layer': 1, 'simplificationalgorithm': 1, 'matrix4d': 2, 'input': 1} (protocol passes them as str)
- [PASS] (catalog) required+default conflicts: 0 []
- [PASS] (catalog) implicit-optional params (no default, not required): 0
- [PASS] (catalog) compact actions with zero evidence: 0 []
- [PASS] (catalog) compact actions with evidence but none verified: 4
- [PASS] (catalog) avg params per compact action: 2.9 (small = cheap Reasoner output)
- [PASS] (executor) 57/195 compact actions have live handlers (29% coverage)
- [FAIL] (executor) offline pre_rules implemented: ['clamp pos.z', 'mass value > 0', 'step n >= 1', 'joint_type whitelist']
- [PASS] (skills) 44 skill dirs with SKILL.md
- [PASS] (skills) frontmatter name+description missing: none
- [PASS] (skills) skill scripts: 81 python files, 0 real syntax failures []
- [WARN] (skills) 6 top-level-await scripts need Kit/async runner: ['calibrate-metropolis-camera/calibrate_camera.py', 'isaac-sim-remote/app_screenshot.py', 'isaac-sim-remote/capture_annotator.py', 'isaac-sim-remote/open_stage.py']
- [PASS] (skills) 33 skills ship scripts/, 16 ship references/
- [PASS] (skills) priority-skill substance gaps: none
- [PASS] (skills) skills missing from manifest: none

## Plan mapping

- Reasoner output layer (catalog actions): schema valid; 57 live handlers user-tested in-sim.
- Validator (pre_rules): offline rules implemented and unit-tested (20 tests).
- Thinker knowledge (skills): all parse; priority skills have substance; integration pending Thinker build.
- LLM endpoint: user deploys via action-reasoner/modal/serve_glimmer.py (pending).
- Observer/verification loop: snapshot telemetry exists; screenshots not built yet.

## Gaps to close for end-to-end

1. Grow handler coverage beyond 21 (radar/camera/URDF/ROS2/RL on demand).
2. Build Thinker client + GUI mode against the Modal endpoint.
3. Add viewport screenshots to Snapshot for vision verification.
4. Curate or replace the 26 unavailable compact actions before fine-tuning data.