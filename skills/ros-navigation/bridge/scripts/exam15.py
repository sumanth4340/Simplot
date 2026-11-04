"""V15 exam runner (runs LOCALLY): replays one drill by name.

Usage: python exam15.py r1|r2|r3|r4|all
Appends {drill, rc} to exam15.json. 'all' runs the full set (~15 min).
"""
import json
import subprocess
import sys

EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"
J = EVD + "exam15.json"
DRILLS = {"r1": ("r1_drive.py", "verify_r1.py"),
          "r2": ("r2_drive.py", "verify_r2.py"),
          "r3": ("r3_drive.py", "verify_r3.py"),
          "r4": ("r4_drive.py", "verify_r4.py")}

which = sys.argv[1] if len(sys.argv) > 1 else "all"
names = list(DRILLS) if which == "all" else [which]
try:
    rec = json.load(open(J))
except OSError:
    rec = []
for n in names:
    drive, ver = DRILLS[n]
    d = subprocess.run([sys.executable,
                        "action-reasoner/skills/ros-navigation/bridge/scripts/" + drive],
                       capture_output=True, text=True, timeout=900)
    v = subprocess.run([sys.executable,
                        "action-reasoner/skills/ros-navigation/bridge/scripts/" + ver],
                       capture_output=True, text=True, timeout=120)
    rec.append({"drill": n, "drive_rc": d.returncode,
                "verify_rc": v.returncode,
                "verify_tail": v.stdout.strip().splitlines()[-1:]})
    json.dump(rec, open(J, "w"))
    print("EXAM %s drive=%d verify=%d %s"
          % (n, d.returncode, v.returncode, rec[-1]["verify_tail"]))
    if v.returncode != 0:
        sys.exit(1)
print("EXAM-DONE")
