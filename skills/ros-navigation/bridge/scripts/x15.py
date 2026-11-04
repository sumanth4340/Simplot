"""X15 cross-val (runs LOCALLY): co-validate with graduated skills.

- workspace-sense: live stage audit (<=1 articulation, no stale
  R*Bot refs, no leftover R2/R3 graphs).
- physics/bridge: no NEW [Error] lines in the Kit log in the last
  25 minutes (exam window).
Writes x15.json {audit_ok, errors_ok}.
"""
import datetime
import json
import os
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "120"]
EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


p = subprocess.run(
    SEND + ["--file", "action-reasoner/skills/ros-navigation/bridge/scripts/audit_stage.py"],
    capture_output=True, text=True, timeout=180)
aud = json.loads(p.stdout).get("output", "")
check("audit ran", aud.startswith("AUDIT="))
n_arts = aud.count("/World/R")
check("<=1 articulation", n_arts <= 1)
check("no stale refs", "'stale': []" in aud)
check("no R2/R3 graphs", "'R2'" not in aud and "'R3'" not in aud)

home = os.path.expanduser("~")
logd = os.path.join(home, ".nvidia-omniverse", "logs", "Kit",
                    "Isaac-Sim Full", "6.0")
logs = sorted(f for f in os.listdir(logd) if f.startswith("kit_"))
lines = open(os.path.join(logd, logs[-1]),
             errors="replace").read().splitlines()
# Exam window: from the oldest drill-evidence mtime (exam rewrites
# all four) to now. Pre-exam history (e.g. the benign first-tick
# CTL race) must not fail the gate.
ev = [os.path.getmtime(EVD + f"r{n}_build.json") for n in (1, 2, 3, 4)]
cut = datetime.datetime.fromtimestamp(min(ev), datetime.timezone.utc)
new_errs = [l for l in lines if "[Error]" in l and l[:10] >= "2026"
            and datetime.datetime.fromisoformat(l[:19] + "+00:00") > cut]
check("no new errors", len(new_errs) == 0)
for l in new_errs[:5]:
    print("  NEW-ERR " + l[:200])
json.dump({"audit_ok": n_arts <= 1, "errors_ok": len(new_errs) == 0},
          open(EVD + "x15.json", "w"))
print("X15-PASS" if not fails else "X15-FAIL " + ",".join(fails))
sys.exit(1 if fails else 0)
