"""Build Action Reasoner starter pack: compact actions + skill routing map."""
import json
import re
from collections import Counter
from pathlib import Path

root = Path(r"C:\Users\sruja_ob3di74")
catalog_path = root / "Downloads" / "isaacs" / "catalog_v3.json"
skills_dir = root / "Downloads" / "IsaacSim-release-6.3" / "IsaacSim-release-6.3" / "skills"
out_dir = root / "action-reasoner"
out_dir.mkdir(exist_ok=True)

# --- 1. Compact model-facing actions from catalog ---
cat = json.loads(catalog_path.read_text(encoding="utf-8"))
actions = cat.get("actions", {})
KEEP = {"create", "physics", "joint", "sensor", "robot", "sim", "rl", "scene",
        "material", "camera", "light", "stage", "prim", "anim", "import",
        "export", "mesh", "ros2"}
compact = {}
for key, v in actions.items():
    if v.get("group") not in KEEP:
        continue
    res = (v.get("definition") or {}).get("resolution", "?")
    params = {}
    for pn, p in (v.get("params") or {}).items():
        if isinstance(p, dict):
            params[pn] = {k: p.get(k) for k in ("type", "default", "required") if k in p}
        else:
            params[pn] = p
    rules = v.get("pre_rules")
    compact[key] = {
        "group": v.get("group"),
        "available": res != "import-failed",
        "resolution": res,
        "params": params,
        "pre_rules": rules if isinstance(rules, list) else [],
    }
(out_dir / "actions_compact.json").write_text(json.dumps(compact, indent=1), encoding="utf-8")
print("compact actions:", len(compact))
print(dict(Counter(v["group"] for v in compact.values())))
print("unavailable (import-failed):", sum(1 for v in compact.values() if not v["available"]))

# --- 2. Skill routing map for the Thinker ---
routing = []
for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fm = m.group(1) if m else ""
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    routing.append({
        "skill": skill_md.parent.name,
        "name": name.group(1).strip() if name else skill_md.parent.name,
        "description": desc.group(1).strip().strip('"') if desc else "",
        "path": str(skill_md),
        "has_scripts": (skill_md.parent / "scripts").is_dir(),
        "has_references": (skill_md.parent / "references").is_dir(),
    })
(out_dir / "skills_routing.json").write_text(json.dumps(routing, indent=1), encoding="utf-8")
lines = ["# Skill routing map", "",
         "| Skill | When to use | Extras |", "|---|---|---|"]
for r in routing:
    extras = "+".join(x for x, f in
                      (("scripts", r["has_scripts"]), ("refs", r["has_references"])) if f) or "-"
    lines.append(f"| `{r['skill']}` | {r['description'][:160]} | {extras} |")
(out_dir / "skills_routing.md").write_text("\n".join(lines), encoding="utf-8")
print("skills:", len(routing))
