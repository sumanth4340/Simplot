"""N2 drive (runs LOCALLY): build -> mount -> play -> pumped scan
listen -> stop."""
import json
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "240"]
EVD = "action-reasoner/skills/ros-navigation/bringup/evidence/"
SCR = "action-reasoner/skills/ros-navigation/bringup/scripts/"


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=280)
    return json.loads(p.stdout).get("output", "")


PLAY = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();await app_utils.update_app_async(steps=5);"
        "app_utils.play();await app_utils.update_app_async(steps=60);"
        "print('PLAYING-60')")
STOP = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();print('STOPPED')")

STOP0 = ("import isaacsim.core.experimental.utils.app as app_utils;"
         "app_utils.stop();print('STOPPED-0')")
open(EVD + "n2_drive.txt", "w").write(
    "STOP0: " + _send([STOP0]).strip() + "\n")
b = _send(["--file", SCR + "n1_build.py"])
m = _send(["--file", SCR + "n2_mount.py"])
open(EVD + "n2_mount.json", "w").write(json.dumps({"output": m}))
open(EVD + "n2_drive.txt", "a").write("BUILD: " + b.strip() + "\n"
                                      + "MOUNT: " + m.strip() + "\n")
# NOTE: no keepalive needed: the rep render product persists in
# USD (the LidarSensor auto product does not survive --file call
# end, so mount does not create one).
open(EVD + "n2_drive.txt", "a").write(
    "PLAY: " + _send([PLAY]).strip() + "\n")
l = subprocess.run(
    ["powershell", "-ExecutionPolicy", "Bypass", "-File",
     SCR + "n2_pumped_listen.ps1"],
    capture_output=True, text=True, timeout=600)
open(EVD + "n2_drive.txt", "a").write("LISTEN: " + l.stdout.strip()
                                      + "\n" + l.stderr.strip() + "\n")
open(EVD + "n2_drive.txt", "a").write(
    "STOP: " + _send([STOP]).strip() + "\n")
print("N2-DRIVE done rc=%d" % l.returncode)
