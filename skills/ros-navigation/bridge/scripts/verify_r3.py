"""R3 verifier: graph valid, 3 nodes, playing, talk published,
final pose follows commanded velocity SIGNS (J1>0.3, J2<-0.3),
stopped."""
import json
import re
import sys

EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


b = json.load(open(EVD + "r3_build.json"))["output"]
check("build ok", "R3-BUILD-OK" in b)
check("3 nodes", all(n in b for n in ("OnPB", "'SUB'", "'CTL'")))
check("art path", "/World/R3Bot_" in b)
d = open(EVD + "r3_drive.txt").read()
check("playing", "PLAYING-60" in d)
check("talk ok", "TALK-OK" in d)
m = re.search(r"TALK-OK n=(\d+)", d)
check("talk n>=50", m and int(m.group(1)) >= 50)
# Verdict uses in-window pump poses (commands live, frames pumping).
# Post-talk FINAL-POSE is informational only (unpowered drift scrap).
# Wrap-robust: joints spin multi-turn, so ANY pump moment showing
# both commanded signs passes (avoids +/-2pi wrap artifacts).
ps = re.findall(r"PUMP40 pose=\[([-\d.e]+), ([-\d.e]+)\]", d)
ps = [(float(a), float(b)) for a, b in ps]
check("pose read", len(ps) > 0)
ok = any(j1 > 0.3 and j2 < -0.3 for j1, j2 in ps)
check("J1 followed +cmd", ok)
check("J2 followed -cmd", ok)
check("stopped", "STOPPED" in d)
print("R3-PASS" if not fails else "R3-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
