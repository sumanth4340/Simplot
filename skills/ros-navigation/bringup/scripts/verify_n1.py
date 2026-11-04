"""N1 verifier: graph valid, 5 nodes, playing, >=5 odom msgs on
odom/base_link, x integrates forward, forward speed > 0, stamps
increase, stopped."""
import json
import sys

EVD = "action-reasoner/skills/ros-navigation/bringup/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


b = json.load(open(EVD + "n1_build.json"))["output"]
check("build ok", "N1-BUILD-OK" in b)
check("5 nodes", all(n in b for n in ("OnPB", "Time", "'ODO'",
                                      "'PUB'", "'CTL'")))
d = open(EVD + "n1_drive.txt").read()
check("playing", "PLAYING-60" in d)
check("stopped", "STOPPED" in d)
O = json.load(open(EVD + "n1_odom.json"))["stamps"]
check("msgs >= 5", len(O) >= 5)
check("frames", all(m["frame"] == "odom" and m["child"] == "base_link"
                    for m in O))
check("x integrates", O[-1]["xyz"][0] - O[0]["xyz"][0] > 0.01)
check("forward speed", all(m["vxyz"][0] > 0.01 for m in O))
ts = [m["t"] for m in O]
check("stamps increase", all(x < y for x, y in zip(ts, ts[1:])))
print("N1-PASS" if not fails else "N1-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
