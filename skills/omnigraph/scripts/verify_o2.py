"""verify_o2 (runs LOCALLY): time flows through the graph per tick."""
import json, re

B = json.load(open("action-reasoner/skills/omnigraph/evidence/o2_build.json"))["output"]
R = json.load(open("action-reasoner/skills/omnigraph/evidence/o2_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["graph valid"] = "graph=True" in B
checks["both nodes"] = "OnPB" in B and "Write" in B
checks["s1 > 0"] = f(r"s1=([\d.]+)", R) > 0.0
checks["s2 > s1"] = f(r"s2=([\d.]+)", R) > f(r"s1=([\d.]+)", R)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("O2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
