"""verify_v9 (runs LOCALLY): exam gates for the 4-node chain."""
import json, re

B = json.load(open("action-reasoner/skills/omnigraph/evidence/v9_build.json"))["output"]
R = json.load(open("action-reasoner/skills/omnigraph/evidence/v9_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

t1, t2, t3 = (f(r"t%d=([-\d.]+)" % i, R) for i in (1, 2, 3))
q1, q3 = f(r"q1=([-\d.]+)", R), f(r"q3=([-\d.]+)", R)

checks = {}
checks["graph valid"] = "graph=True" in B
checks["4 nodes"] = all(n in B for n in ("OnPB", "Mul", "Add", "Write"))
checks["value linked"] = "linked=True" in B
checks["no rivals"] = "rivals=[]" in B
checks["live t1~3.5"] = abs(t1 - 3.5) < 1.0
checks["frozen == 0"] = abs(f(r"frozen=([-\d.]+)", R) - 0.0) < 1e-9
checks["catch-up ~10"] = abs((t3 - t2) - 10.0) < 1.5
import math
checks["q tracks"] = abs(q3 - t3 * math.pi / 180.0) < 0.15 \
    and (q3 - q1) > 0.05
checks["disabled state"] = "dis=True" in R
checks["enabled state"] = "en=False" in R

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V9-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
