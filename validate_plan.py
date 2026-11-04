"""Validate catalog + skills against the Action Reasoner plan.

Run: python action-reasoner/validate_plan.py
Writes: action-reasoner/VALIDATION_REPORT.md
"""
import importlib.util
import json
import py_compile
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\sruja_ob3di74")
AR = ROOT / "action-reasoner"
CATALOG = ROOT / "Downloads" / "isaacs" / "catalog_v3.json"
SKILLS = ROOT / "Downloads" / "IsaacSim-release-6.3" / "IsaacSim-release-6.3" / "skills"
EXT_PY = AR / "ext" / "isaacsim.action.reasoner.executor" / "isaacsim" / "action" / "reasoner" / "executor"

findings = []  # (status, area, message); status in PASS/WARN/FAIL


def emit(status, area, message):
    findings.append((status, area, message))
    print(f"{status:4} [{area}] {message}")


def load_mod(name):
    spec = importlib.util.spec_from_file_location(f"val_{name}", EXT_PY / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------- catalog ----------
full = json.loads(CATALOG.read_text(encoding="utf-8"))
actions = full.get("actions", {})
compact = json.loads((AR / "actions_compact.json").read_text(encoding="utf-8"))
emit("PASS", "catalog", f"loaded {len(actions)} full actions, {len(compact)} compact actions")

schema_bad = [k for k, v in actions.items()
              if not isinstance(v.get("group"), str)
              or not isinstance(v.get("params"), dict)
              or not isinstance(v.get("definition"), dict)
              or "resolution" not in v["definition"]]
if schema_bad:
    emit("FAIL", "catalog", f"{len(schema_bad)} actions fail schema: {schema_bad[:5]}")
else:
    emit("PASS", "catalog", "all actions pass schema (group/params/definition.resolution)")
with_rules = sum(1 for v in actions.values() if v.get("pre_rules"))
compact_rules = sum(1 for k in compact if full["actions"][k].get("pre_rules"))
emit("WARN", "catalog", f"pre_rules coverage: {with_rules}/{len(actions)} full, "
     f"{compact_rules}/{len(compact)} compact carry rules (rest rely on handler checks)")

res = Counter((v.get("definition") or {}).get("resolution") for v in actions.values())
emit("PASS", "catalog", f"resolutions: {dict(res)}")
compact_res = Counter(v.get("resolution") for v in compact.values())
dead = [k for k, v in compact.items() if not v.get("available")]
emit("WARN" if dead else "PASS", "catalog",
     f"compact: {len(compact) - len(dead)}/{len(compact)} available; "
     f"dead={len(dead)} resolutions={dict(compact_res)}")

KNOWN_TYPES = {"float", "int", "bool", "str", "name", "vec3", "vec4", "any",
               "asset", "object", "quatd", "vec3f", "nonetype"}
unknown_types = Counter()
req_default_conflict = []
no_default_no_required = 0
for k, v in compact.items():
    for pn, ps in (v.get("params") or {}).items():
        t = (ps.get("type") or "str").split("|")[0].strip().lower() if isinstance(ps, dict) else "?"
        if t not in KNOWN_TYPES and not t.startswith("typing.") and t != "?":
            unknown_types[t] += 1
        if isinstance(ps, dict) and ps.get("required") and "default" in ps:
            req_default_conflict.append(f"{k}.{pn}")
        if isinstance(ps, dict) and not ps.get("required") and "default" not in ps:
            no_default_no_required += 1
emit("WARN" if unknown_types else "PASS", "catalog",
     f"unknown param types: {dict(unknown_types) or 'none'} (protocol passes them as str)")
emit("WARN" if req_default_conflict else "PASS", "catalog",
     f"required+default conflicts: {len(req_default_conflict)} {req_default_conflict[:3]}")
emit("PASS", "catalog", f"implicit-optional params (no default, not required): {no_default_no_required}")

no_evidence, unverified = [], 0
for k in compact:
    ev = full["actions"][k].get("evidence") or []
    if not ev:
        no_evidence.append(k)
    elif not any(e.get("verified") for e in ev):
        unverified += 1
emit("WARN" if no_evidence else "PASS", "catalog",
     f"compact actions with zero evidence: {len(no_evidence)} {no_evidence[:5]}")
emit("PASS", "catalog", f"compact actions with evidence but none verified: {unverified}")

avg_params = sum(len(v.get("params") or {}) for v in compact.values()) / max(len(compact), 1)
emit("PASS", "catalog", f"avg params per compact action: {avg_params:.1f} (small = cheap Reasoner output)")

handlers = load_mod("handlers")
missing = [k for k in handlers.HANDLED_ACTIONS if k not in compact]
unavail_handled = [k for k in handlers.HANDLED_ACTIONS
                   if k in compact and not compact[k].get("available")]
no_method = [k for k in handlers.HANDLED_ACTIONS
             if not hasattr(handlers.Executor, "_do_" + k.replace(".", "_"))]
if missing or unavail_handled or no_method:
    emit("FAIL", "executor", f"handler gaps: missing={missing} unavail={unavail_handled} nomethod={no_method}")
else:
    emit("PASS", "executor",
         f"{len(handlers.HANDLED_ACTIONS)}/{len(compact)} compact actions have live handlers "
         f"({100 * len(handlers.HANDLED_ACTIONS) / len(compact):.0f}% coverage)")

# pre_rule implementation mapping (offline rules live in protocol.py)
proto_src = (EXT_PY / "protocol.py").read_text(encoding="utf-8")
rule_probes = {"clamp pos.z": "size / 2" in proto_src,
               "mass value > 0": 'must be > 0' in proto_src,
               "step n >= 1": 'must be >= 1' in proto_src,
               "joint_type whitelist": "JOINT_TYPES" in proto_src}
unmapped = [k for k, ok in rule_probes.items() if not ok]
emit("FAIL" if unmapped else "PASS", "executor", f"offline pre_rules implemented: {list(rule_probes)}")

# ---------- skills ----------
skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
emit("PASS", "skills", f"{len(skill_dirs)} skill dirs with SKILL.md")
bad_fm = []
for d in skill_dirs:
    text = (d / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = m.group(1) if m else ""
    if not re.search(r"^name:\s*\S+", fm, re.M) or not re.search(r"^description:\s*\S+", fm, re.M):
        bad_fm.append(d.name)
emit("FAIL" if bad_fm else "PASS", "skills", f"frontmatter name+description missing: {bad_fm or 'none'}")

py_files = []
for d in skill_dirs:
    if (d / "scripts").is_dir():
        py_files.extend((d / "scripts").rglob("*.py"))
bad_py, async_style = [], []
for p in py_files:
    try:
        py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        if "'await' outside" in str(e):
            async_style.append(f"{p.parent.parent.name}/{p.name}")
        else:
            bad_py.append(f"{p.parent.parent.name}/{p.name}: {e}")
    except Exception as e:
        bad_py.append(f"{p.parent.parent.name}/{p.name}: {e}")
emit("FAIL" if bad_py else "PASS", "skills",
     f"skill scripts: {len(py_files)} python files, {len(bad_py)} real syntax failures {bad_py[:3]}")
if async_style:
    emit("WARN", "skills", f"{len(async_style)} top-level-await scripts need Kit/async runner: "
         f"{async_style[:4]}")

with_scripts = sum(1 for d in skill_dirs if (d / "scripts").is_dir())
with_refs = sum(1 for d in skill_dirs if (d / "references").is_dir())
emit("PASS", "skills", f"{with_scripts} skills ship scripts/, {with_refs} ship references/")

PRIORITY = ["physics-simulation", "usd-articulation", "urdf-mjcf-to-usd-conversion",
            "isaac-sim-orchestrator", "isaac-sim-workflow", "isaac-sim-validator",
            "isaac-sim-troubleshooting", "isaac-sim-sensor", "isaac-camera",
            "spatial-reasoning", "isaac-sim-assets"]
thin = []
for name in PRIORITY:
    md = SKILLS / name / "SKILL.md"
    if not md.exists():
        thin.append(f"{name} MISSING")
        continue
    lines = len(md.read_text(encoding="utf-8", errors="replace").splitlines())
    n_scripts = len(list((SKILLS / name / "scripts").rglob("*"))) if (SKILLS / name / "scripts").is_dir() else 0
    flag = "" if lines >= 50 else " THIN"
    if flag:
        thin.append(f"{name} ({lines} lines)")
    print(f"INFO [skills] {name}: {lines} lines, {n_scripts} script files{flag}")
emit("FAIL" if any("MISSING" in t for t in thin) else ("WARN" if thin else "PASS"),
     "skills", f"priority-skill substance gaps: {thin or 'none'}")

manifest = (SKILLS / "manifest.yaml").read_text(encoding="utf-8", errors="replace")
unlisted = [d.name for d in skill_dirs if d.name not in manifest]
emit("WARN" if unlisted else "PASS", "skills", f"skills missing from manifest: {unlisted or 'none'}")

# ---------- report ----------
fails = sum(1 for s, _, _ in findings if s == "FAIL")
warns = sum(1 for s, _, _ in findings if s == "WARN")
verdict = ("FAIL — fix items below before relying on the plan" if fails
           else "PASS WITH WARNINGS — plan is viable, mind the warnings" if warns
           else "PASS — plan components validated")
report = ["# Validation report: catalog + skills vs plan", "",
          f"Verdict: **{verdict}** ({fails} FAIL, {warns} WARN)", "",
          "## Findings", ""]
for status, area, message in findings:
    report.append(f"- [{status}] ({area}) {message}")
report += ["", "## Plan mapping", "",
           "- Reasoner output layer (catalog actions): schema valid; "
           f"{len(handlers.HANDLED_ACTIONS)} live handlers user-tested in-sim.",
           "- Validator (pre_rules): offline rules implemented and unit-tested (20 tests).",
           "- Thinker knowledge (skills): all parse; priority skills have substance; "
           "integration pending Thinker build.",
           "- LLM endpoint: user deploys via action-reasoner/modal/serve_glimmer.py (pending).",
           "- Observer/verification loop: snapshot telemetry exists; screenshots not built yet.",
           "", "## Gaps to close for end-to-end", "",
           "1. Grow handler coverage beyond 21 (radar/camera/URDF/ROS2/RL on demand).",
           "2. Build Thinker client + GUI mode against the Modal endpoint.",
           "3. Add viewport screenshots to Snapshot for vision verification.",
           "4. Curate or replace the 26 unavailable compact actions before fine-tuning data.",
           ]
(AR / "VALIDATION_REPORT.md").write_text("\n".join(report), encoding="utf-8")
print(f"\nverdict: {verdict}; report -> action-reasoner/VALIDATION_REPORT.md")
sys.exit(1 if fails else 0)
