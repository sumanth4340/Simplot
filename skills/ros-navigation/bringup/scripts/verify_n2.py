"""N2 verifier: graph valid, 5 nodes, playing, >=5 scan msgs on
base_scan, beam count sane + consistent, rmin ~ cube face (1.5m),
stamps increase, stopped."""
import json
import sys

EVD = "action-reasoner/skills/ros-navigation/bringup/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


m = json.load(open(EVD + "n2_mount.json"))["output"]
check("mount ok", "N2-MOUNT-OK" in m)
check("2 nodes", all(n in m for n in ("OnPB", "'HELP'")))
check("render product", "rp=/Render/" in m)
d = open(EVD + "n2_drive.txt").read()
check("playing", "PLAYING-60" in d)
check("stopped", "STOPPED" in d)
S = json.load(open(EVD + "n2_scan.json"))["stamps"]
check("msgs >= 5", len(S) >= 5)
HAVE = len(S) >= 5
check("frame", HAVE and all(s["frame"] == "base_scan" for s in S))
check("beams sane", HAVE and all(s["n"] >= 100 for s in S))
check("beams consistent", HAVE and len(set(s["n"] for s in S)) == 1)
check("rmin ~ cube face",
      HAVE and all(s["rmin_valid"] is not None
                    and abs(s["rmin_valid"] - 1.5) < 0.3 for s in S))
check("ring sees cube only",
      HAVE and all(1.2 < s["rmax"] < 2.0 for s in S))
ts = [s["t"] for s in S]
check("stamps increase",
      HAVE and all(x < y for x, y in zip(ts, ts[1:])))
print("N2-PASS" if not fails else "N2-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
