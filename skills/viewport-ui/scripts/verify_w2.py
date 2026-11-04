"""verify_w2 (runs LOCALLY): camera moved + aimed frame differs."""
import json, re, sys

sys.path.insert(0, "action-reasoner/skills/viewport-ui/scripts")
from pngstats import png_stats

GET = json.load(open("action-reasoner/skills/viewport-ui/evidence/w2_get.json"))["output"]
S1 = "action-reasoner/skills/viewport-ui/evidence/w2_before.png"
S2 = "action-reasoner/skills/viewport-ui/evidence/w2_after.png"

def f(pat, i=1):
    m = re.search(pat, GET)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["cam x~3"] = abs(f(r"Position \(x, y, z\): \[\s*([-\d.eE+]+)") - 3.0) < 0.05
checks["cam y~-3"] = abs(f(r"Position \(x, y, z\): \[\s*[-\d.eE+]+\s+([-\d.eE+]+)") - -3.0) < 0.05
checks["cam z~2"] = abs(f(r"Position \(x, y, z\): \[\s*[-\d.eE+]+\s+[-\d.eE+]+\s+([-\d.eE+]+)") - 2.0) < 0.05
a, b = png_stats(S1), png_stats(S2)
print("INFO before mean=%.1f std=%.1f | after mean=%.1f std=%.1f" % (
    a["mean"], a["std"], b["mean"], b["std"]))
checks["frames differ"] = abs(a["mean"] - b["mean"]) > 2.0
checks["aimed has contrast"] = b["std"] > 5.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("W2-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
