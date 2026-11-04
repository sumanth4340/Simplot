"""R2 verifier: graph valid, 3 nodes, target set, playing, >=5 joint
states with >=2 joints, lens match, stamps increase, span>0, stopped."""
import json
import sys

EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


b = json.load(open(EVD + "r2_build.json"))["output"]
check("build ok", "R2-BUILD-OK" in b)
check("4 nodes", all(n in b for n in ("OnPB", "Time", "'JS'", "'CTL'")))
check("target set", "/World/R2Bot" in b)
d = open(EVD + "r2_drive.txt").read()
check("playing", "PLAYING-60" in d)
check("stopped", "STOPPED" in d)
J = json.load(open(EVD + "r2_js.json"))["stamps"]
check("msgs >= 5", len(J) >= 5)
n0 = J[0]["names"] if J else []
check("joints >= 2", len(n0) >= 2)
check("lens match", all(len(m["names"]) == len(m["pos"]) for m in J))
ts = [m["t"] for m in J]
check("stamps increase", all(x < y for x, y in zip(ts, ts[1:])))
check("span > 0", ts[-1] - ts[0] > 0 if ts else False)
moved = (abs(J[-1]["pos"][0] - J[0]["pos"][0]) > 1e-4) if J else False
check("joint moved", moved)
print("R2-PASS" if not fails else "R2-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
