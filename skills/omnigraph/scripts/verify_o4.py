"""verify_o4 (runs LOCALLY): disconnect freezes, reconnect resumes."""
import json, re

B = json.load(open("action-reasoner/skills/omnigraph/evidence/o4_build.json"))["output"]
R = json.load(open("action-reasoner/skills/omnigraph/evidence/o4_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["graph valid"] = "graph=True" in B
checks["3 nodes"] = all(n in B for n in ("OnPB", "Mul", "Write"))
checks["value linked"] = "linked=True" in B
checks["live first"] = f(r"t1=([-\d.]+)", R) > 0.0
checks["frozen == 0"] = abs(f(r"frozen=([-\d.]+)", R) - 0.0) < 1e-9
checks["resumed catch-up ~20"] = abs(f(r"resumed=([-\d.]+)", R) - 20.0) < 1.5
checks["disabled state"] = "dis=True" in R
checks["enabled state"] = "en=False" in R

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("O4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
