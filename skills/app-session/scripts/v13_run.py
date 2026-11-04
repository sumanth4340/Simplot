"""V13 run (runs LOCALLY): full session loop exam.

new -> build V13 scene -> save -> wipe -> reopen -> verify
props -> step 60 -> viewport screenshot (Skill 8 reuse) -> stop.
Writes v13_report.txt.
"""
import json
import os
import subprocess
import sys

LIB = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
       "skills/isaac-sim-remote/scripts/")
SEND = [sys.executable, LIB + "isaacsim_send.py", "--raw",
        "--timeout", "150"]
USD = "C:/Users/sruja_ob3di74/action-reasoner/skills/app-session/evidence/v13_stage.usd"
SHOT = "C:/Users/sruja_ob3di74/action-reasoner/skills/app-session/evidence/v13_view.png"
for p in (USD, SHOT):
    if os.path.exists(p):
        os.remove(p)
OUT = []


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=180)
    body = json.loads(p.stdout)
    out = body.get("output", "") + "".join(
        body.get("traceback", []) or [])
    OUT.append("$ send %s\n%s" % (" ".join(args[-3:]), out.strip()))
    return out


_send(["--file", LIB + "open_stage.py", "--arg", "action=new"])
_send(["--file", "action-reasoner/skills/app-session/scripts/v13_build.py"])
_send(["--file", LIB + "open_stage.py", "--arg", "action=save",
       "--arg", "usd_path=" + USD])
_send(["--file", LIB + "open_stage.py", "--arg", "action=new"])
_send(["--file", LIB + "open_stage.py", "--arg", "action=open",
       "--arg", "usd_path=" + USD])
_send(["--file", "action-reasoner/skills/app-session/scripts/v13_check.py"])
_send(["--file", LIB + "simulation_control.py", "--arg", "action=step",
       "--arg", "num_steps=60"])
_send(["--file", LIB + "viewport_screenshot.py", "--arg",
       "output_path=" + SHOT])
_send(["--file", LIB + "simulation_control.py", "--arg", "action=stop"])
OUT.append("USD_BYTES=%d" % (os.path.getsize(USD) if os.path.exists(USD) else 0))
OUT.append("SHOT_BYTES=%d" % (os.path.getsize(SHOT) if os.path.exists(SHOT) else 0))
open("action-reasoner/skills/app-session/evidence/v13_report.txt",
     "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("V13-REPORT steps=%d" % len(OUT))
