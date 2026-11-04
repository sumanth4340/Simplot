"""R3 drive (runs LOCALLY): build -> play -> pumped talk -> read -> stop."""
import json
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "180"]
EVD = "action-reasoner/skills/ros-navigation/bridge/evidence/"


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=220)
    return json.loads(p.stdout).get("output", "")


PLAY = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();await app_utils.update_app_async(steps=5);"
        "app_utils.play();await app_utils.update_app_async(steps=60);"
        "print('PLAYING-60')")
READ = ("import numpy as np, omni.usd as U;"
        "from isaacsim.core.experimental.prims import Articulation;"
        "st=U.get_context().get_stage();"
        "art=[c.GetPath().pathString for c in st.GetPrimAtPath('/World')"
        ".GetChildren() if c.GetName().startswith('R3Bot')][0];"
        "p=np.asarray(Articulation(art).get_dof_positions())"
        ".flatten().tolist();"
        "print('FINAL-POSE='+str(p))")
STOP = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();print('STOPPED')")

b = _send(["--file", "action-reasoner/skills/ros-navigation/bridge/scripts/r3_build.py"])
open(EVD + "r3_build.json", "w").write(json.dumps({"output": b}))
open(EVD + "r3_drive.txt", "w").write("BUILD: " + b.strip() + "\n")
open(EVD + "r3_drive.txt", "a").write(
    "PLAY: " + _send([PLAY]).strip() + "\n")
l = subprocess.run(
    ["powershell", "-ExecutionPolicy", "Bypass", "-File",
     "action-reasoner/skills/ros-navigation/bridge/scripts/r3_pumped_talk.ps1"],
    capture_output=True, text=True, timeout=600)
open(EVD + "r3_drive.txt", "a").write("TALK: " + l.stdout.strip()
                                      + "\n" + l.stderr.strip() + "\n")
open(EVD + "r3_drive.txt", "a").write(
    "READ: " + _send([READ]).strip() + "\n")
open(EVD + "r3_drive.txt", "a").write(
    "STOP: " + _send([STOP]).strip() + "\n")
print("R3-DRIVE done rc=%d" % l.returncode)
