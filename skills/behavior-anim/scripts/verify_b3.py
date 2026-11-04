"""verify_b3 (runs LOCALLY): state-machine phase gates."""
import json, re

B = json.load(open("action-reasoner/skills/behavior-anim/evidence/b3_build.json"))["output"]
R = json.load(open("action-reasoner/skills/behavior-anim/evidence/b3_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, R)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["bot valid"] = "bot=True" in B
checks["hinge valid"] = "hinge=True" in B
checks["EXTEND q~+0.5"] = abs(f(r"EXTEND_t=[-\d.]+_q=([-\d.]+)") - 0.5) < 0.1
checks["EXTEND echo"] = abs(f(r"EXTEND_t=[-\d.]+_q=[-\d.]+_e=([-\d.]+)") - 0.5) < 1e-6
checks["RETRACT q~-0.5"] = abs(f(r"RETRACT_t=[-\d.]+_q=([-\d.]+)") + 0.5) < 0.1
checks["RETRACT echo"] = abs(f(r"RETRACT_t=[-\d.]+_q=[-\d.]+_e=([-\d.]+)") + 0.5) < 1e-6
checks["HOME q~0"] = abs(f(r"HOME_t=[-\d.]+_q=([-\d.]+)") - 0.0) < 0.1
checks["HOME echo"] = abs(f(r"HOME_t=[-\d.]+_q=[-\d.]+_e=([-\d.]+)") - 0.0) < 1e-6
checks["sign flips"] = (f(r"EXTEND_t=[-\d.]+_q=([-\d.]+)") > 0.0
    and f(r"RETRACT_t=[-\d.]+_q=([-\d.]+)") < 0.0)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("B3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
