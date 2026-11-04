"""R4 verifier: graph valid, 4 nodes, rels set, playing, >=5 TF
msgs, >=2 distinct child frames, finite translations, one frame's
translation moves across samples, stopped."""
import json
import math
import sys

EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


b = json.load(open(EVD + "r4_build.json"))["output"]
check("build ok", "R4-BUILD-OK" in b)
check("4 nodes", all(n in b for n in ("OnPB", "Time", "'TF'", "'CTL'")))
check("parent set", "/World" in b)
check("3 targets", "targets=3" in b)
d = open(EVD + "r4_drive.txt").read()
check("playing", "PLAYING-60" in d)
check("stopped", "STOPPED" in d)
T = json.load(open(EVD + "r4_tf.json"))["stamps"]
check("msgs >= 5", len(T) >= 5)
kids = set(t["child"] for m in T for t in m)
check("frames >= 2", len(kids) >= 2)
check("finite xyz", all(math.isfinite(v) for m in T for t in m
                        for v in t["xyz"]))
by = {}
for m in T:
    for t in m:
        by.setdefault(t["child"], []).append(t["xyz"])
moved = any(max(abs(a - b) for a, b in zip(v[0], v[-1])) > 1e-4
            for v in by.values() if len(v) >= 2)
check("a frame moved", moved)
print("R4-PASS" if not fails else "R4-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
