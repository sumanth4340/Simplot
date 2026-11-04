"""R1 drive (runs LOCALLY): play -> system-ROS listen -> stop.

Sends build, plays + pumps 60 (leaves playing: bridge graphs
are play-gated), runs the system-ROS clock listener (8 msgs /
15 s), stops. Writes r1_clock.json + r1_drive.txt.
"""
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
STOP = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();print('STOPPED')")

b = _send(["--file", "action-reasoner/skills/ros-navigation/bridge/scripts/r1_build.py"])
open(EVD + "r1_build.json", "w").write(json.dumps({"output": b}))
open(EVD + "r1_drive.txt", "w").write("BUILD: " + b.strip() + "\n")
open(EVD + "r1_drive.txt", "a").write(
    "PLAY: " + _send([PLAY]).strip() + "\n")
l = subprocess.run(
    ["powershell", "-ExecutionPolicy", "Bypass", "-File",
     "action-reasoner/skills/ros-navigation/bridge/scripts/listen.ps1",
     "/clock", "clock", "8", "15", EVD + "r1_clock.json"],
    capture_output=True, text=True, timeout=120)
open(EVD + "r1_drive.txt", "a").write("LISTEN: " + l.stdout.strip()
                                      + "\n" + l.stderr.strip() + "\n")
open(EVD + "r1_drive.txt", "a").write(
    "STOP: " + _send([STOP]).strip() + "\n")
print("R1-DRIVE done rc=%d" % l.returncode)
