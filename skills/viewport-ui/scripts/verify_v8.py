"""verify_v8 (runs LOCALLY): exam layout + capture + selection."""
import json, os, re, sys

sys.path.insert(0, "action-reasoner/skills/viewport-ui/scripts")
from pngstats import png_stats

EVD = "action-reasoner/skills/viewport-ui/evidence/"
B = json.load(open(EVD + "v8_build.json"))["output"]
GET = json.load(open(EVD + "v8_get.json"))["output"]
SEL = json.load(open(EVD + "v8_sel.json"))["output"]
VP = EVD + "v8_viewport.png"
AP = EVD + "v8_app.png"

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["EXAM dome 300"] = abs(f(r"dome=([\d.]+)", B) - 300.0) < 1e-6
checks["EXAM sun 1200"] = abs(f(r"sun=([\d.]+)", B) - 1200.0) < 1e-6
checks["EXAM sizeA 0.5"] = abs(f(r"sizeA=([\d.]+)", B) - 0.5) < 1e-6
checks["EXAM sizeB 1.0"] = abs(f(r"sizeB=([\d.]+)", B) - 1.0) < 1e-6
checks["cam at new eye"] = "[-3." in GET and "2.5" in GET
checks["select V8CubeB"] = "/World/V8CubeB" in SEL
sv, sa = png_stats(VP), png_stats(AP)
print("INFO vp mean=%.1f std=%.1f | app mean=%.1f std=%.1f" % (
    sv["mean"], sv["std"], sa["mean"], sa["std"]))
checks["viewport valid"] = sv["w"] >= 640 and 5.0 < sv["mean"] < 250.0 and sv["std"] > 5.0
checks["app valid"] = sa["w"] >= 640 and 5.0 < sa["mean"] < 250.0 and sa["std"] > 1.0
checks["pngs exist"] = os.path.getsize(VP) > 20000 and os.path.getsize(AP) > 20000

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V8-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
