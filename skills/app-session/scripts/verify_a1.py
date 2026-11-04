"""verify_a1 (runs LOCALLY): timeline state gates."""
import re

T = open("action-reasoner/skills/app-session/evidence/a1_report.txt").read()

def f(pat, i=1):
    m = re.search(pat, T)
    return float(m.group(i)) if m else float("nan")

checks = {}
checks["stop works"] = "STOPPED_SEEN=True" in T
checks["play works"] = "PLAYING_SEEN=True" in T
checks["pause works"] = "PAUSED_SEEN=True" in T
checks["cycle order"] = (T.index("PLAYING_SEEN") > T.index("STOPPED_SEEN")
    and T.index("PAUSED_SEEN") > T.index("PLAYING_SEEN"))
checks["time round-trip"] = abs(f(r"TIME-SET-GET ([\d.]+)") - 2.5) < 1e-6
checks["step advanced"] = "Advanced 60 simulation step(s)" in T
checks["sim time > 0.5"] = float(
    re.findall(r"Simulation time: ([\d.]+)", T)[-1]) > 0.5

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("A1-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
