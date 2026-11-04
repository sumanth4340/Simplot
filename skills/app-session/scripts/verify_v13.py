"""verify_v13 (runs LOCALLY): session loop gates."""
import re
import sys

sys.path.insert(0, "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/isaac-sim-remote/scripts")
from png_stats import png_stats

T = open("action-reasoner/skills/app-session/evidence/v13_report.txt",
         encoding="utf-8").read()

def f(pat, i=1):
    m = re.search(pat, T)
    return float(m.group(i)) if m else float("nan")

shot = "action-reasoner/skills/app-session/evidence/v13_view.png"
s = png_stats(shot)

checks = {}
checks["built"] = "V13-BUILD-OK valid=True" in T
checks["saved"] = "Saved as: " in T and f(r"USD_BYTES=(\d+)") > 0
checks["reopened"] = "Opened: " in T
checks["props survive"] = "V13-CHECK valid=True" in T
checks["stepped 60"] = "Advanced 60 simulation step(s)" in T
checks["shot saved"] = f(r"SHOT_BYTES=(\d+)") > 20000
checks["shot 1280x720"] = s["w"] == 1280 and s["h"] == 720
checks["shot non-black"] = s["mean"] > 30.0
checks["ends stopped"] = T.rstrip().splitlines()[-3].strip() == "Simulation: STOPPED"

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V13-" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
