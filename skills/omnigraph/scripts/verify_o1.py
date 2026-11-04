"""verify_o1 (runs LOCALLY): graph authored, ticks wrote z=1.5."""
import json, re

B = json.load(open("action-reasoner/skills/omnigraph/evidence/o1_build.json"))["output"]
R = json.load(open("action-reasoner/skills/omnigraph/evidence/o1_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["graph valid"] = "graph=True" in B
checks["both nodes"] = "OnPB" in B and "Write" in B
checks["authoring wrote (R1)"] = abs(f(r"z0a=([\d.]+)", R) - 1.5) < 1e-6
checks["reset z=0.5"] = abs(f(r"z0=([\d.]+)", R) - 0.5) < 1e-6
checks["ticks rewrote z=1.5"] = abs(f(r"z1=([\d.]+)", R) - 1.5) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("O1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
