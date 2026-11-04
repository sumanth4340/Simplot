"""verify_w4 (runs LOCALLY): two aimed views, both valid, differ."""
import json, os, sys

sys.path.insert(0, "action-reasoner/skills/viewport-ui/scripts")
from pngstats import png_stats, mean_abs_diff

A = "action-reasoner/skills/viewport-ui/evidence/w4_viewA.png"
B = "action-reasoner/skills/viewport-ui/evidence/w4_viewB.png"
GA = json.load(open("action-reasoner/skills/viewport-ui/evidence/w4_getA.json"))["output"]
GB = json.load(open("action-reasoner/skills/viewport-ui/evidence/w4_getB.json"))["output"]

checks = {}
checks["pose A set"] = "[ 3." in GA and "-3." in GA
checks["pose B set"] = "[-4." in GB or "-4." in GB
sa, sb = png_stats(A), png_stats(B)
print("INFO A mean=%.1f std=%.1f | B mean=%.1f std=%.1f" % (
    sa["mean"], sa["std"], sb["mean"], sb["std"]))
checks["A valid"] = sa["w"] >= 640 and 5.0 < sa["mean"] < 250.0 and sa["std"] > 5.0
checks["B valid"] = sb["w"] >= 640 and 5.0 < sb["mean"] < 250.0 and sb["std"] > 5.0
mad = mean_abs_diff(A, B)
print("INFO mean-abs-diff=%.2f" % mad)
checks["views differ"] = mad > 3.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("W4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
