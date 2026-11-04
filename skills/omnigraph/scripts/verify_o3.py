"""verify_o3 (runs LOCALLY): graph drives joint at 10deg/s."""
import json, re

B = json.load(open("action-reasoner/skills/omnigraph/evidence/o3_build.json"))["output"]
R = json.load(open("action-reasoner/skills/omnigraph/evidence/o3_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["graph valid"] = "graph=True" in B
checks["3 nodes"] = all(n in B for n in ("OnPB", "Mul", "Write"))
checks["dt ~10deg"] = abs(f(r"dt=([-\d.]+)", R) - 10.0) < 1.5
checks["q follows"] = f(r"dq=([-\d.]+)", R) > 0.05

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("O3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
