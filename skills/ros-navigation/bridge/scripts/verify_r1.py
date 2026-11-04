"""verify_r1 (runs LOCALLY): clock bridge gates."""
import json

B = json.load(open("action-reasoner/skills/ros-navigation/bridge/evidence/r1_build.json"))["output"]
C = json.load(open("action-reasoner/skills/ros-navigation/bridge/evidence/r1_clock.json"))
D = open("action-reasoner/skills/ros-navigation/bridge/evidence/r1_drive.txt").read()
st = C["stamps"]
mono = all(b > a for a, b in zip(st, st[1:]))

checks = {}
checks["graph valid"] = "graph=True" in B
checks["3 nodes"] = all(n in B for n in ("OnPB", "Time", "Clock"))
checks["time linked"] = "linked=True" in B
checks["playing"] = "PLAYING-60" in D
checks["msgs >= 5"] = C["count"] >= 5
checks["stamps increase"] = mono and len(st) >= 5
checks["span > 0"] = (max(st) - min(st)) > 0.0 if st else False
checks["stopped"] = "STOPPED" in D

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("R1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
