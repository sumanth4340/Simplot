"""verify_v6 (runs LOCALLY): exam scene differs, frame valid, rig exact."""
import json, os, re

B = json.load(open("action-reasoner/skills/rendering-lighting/evidence/v6_build.json"))["output"]
C = json.load(open("action-reasoner/skills/rendering-lighting/evidence/v6_cap.json"))["output"]
PNG = "action-reasoner/skills/rendering-lighting/evidence/v6_frame.png"

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["EXAM new dome 300"] = abs(f(r"dome=([\d.]+)", B) - 300.0) < 1e-6
checks["EXAM new sun 1200"] = abs(f(r"sun=([\d.]+)", B) - 1200.0) < 1e-6
checks["EXAM cubeA 0.5"] = abs(f(r"sizeA=([\d.]+)", B) - 0.5) < 1e-6
checks["EXAM cubeB 1.2"] = abs(f(r"sizeB=([\d.]+)", B) - 1.2) < 1e-6
checks["EXAM new eye"] = abs(f(r"eye=\[([-\d.]+)", B) - -3.5) < 1e-6
checks["frame shape"] = C.find("shape=[240, 320, 3]") >= 0
checks["frame lit 10..220"] = 10.0 < f(r"mean=([\d.]+)", C) < 220.0
checks["frame max>100"] = f(r"max=(\d+)", C) > 100
checks["png >20KB"] = os.path.exists(PNG) and os.path.getsize(PNG) > 20000
checks["iso pinned 100"] = abs(f(r"iso=([\d.]+)", C) - 100.0) < 1e-6

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V6-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
