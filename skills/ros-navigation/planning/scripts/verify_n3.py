"""verify_n3 (runs LOCALLY): footprint + validation gates."""
import json, re

B = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n3_build.json"))["output"]
R = json.load(open("action-reasoner/skills/ros-navigation/planning/evidence/n3_run.json"))["output"]
V = open("action-reasoner/skills/ros-navigation/planning/evidence/n3_validate.txt").read()

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["bot valid"] = "bot=True" in B
checks["link valid"] = "link=True" in B
checks["size 0.4^3"] = abs(f(r"sx=([-\d.]+)", R) - 0.4) < 0.01 \
    and abs(f(r"sy=([-\d.]+)", R) - 0.4) < 0.01 \
    and abs(f(r"sz=([-\d.]+)", R) - 0.4) < 0.01
checks["z_offset 0.4"] = abs(f(r"zoff=([-\d.]+)", R) - 0.4) < 0.01
checks["inscribed 0.2"] = abs(f(r"ins=([-\d.]+)", R) - 0.2) < 0.005
checks["circumscribed .2828"] = abs(f(r"cir=([-\d.]+)", R) - 0.2828) < 0.005
checks["start free"] = "a=0" in V
checks["A clips yaw0"] = "b=1" in V
checks["A clips yaw45"] = "c=1" in V
checks["path clip-free"] = re.search(r"bad=0/\d+", V) is not None

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("N3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
