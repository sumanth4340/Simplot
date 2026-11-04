"""N1 drive (runs LOCALLY): build -> play -> pumped listen -> stop."""
import json
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "180"]
EVD = "action-reasoner/skills/ros-navigation/bringup/evidence/"


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=220)
    return json.loads(p.stdout).get("output", "")


# CTL runtime commands wipe on every timeline stop: re-set them
# after stop() so EVERY play (not just first-after-build) drives.
PLAY = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "import omni.graph.core as og;"
        "app_utils.stop();await app_utils.update_app_async(steps=5);"
        "og.Controller.attribute('/ROS2/N1/CTL.inputs:velocityCommand')"
        ".set([1.0]*4);"
        "app_utils.play();await app_utils.update_app_async(steps=60);"
        "print('PLAYING-60')")
STOP = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.stop();print('STOPPED')")

STOP0 = ("import isaacsim.core.experimental.utils.app as app_utils;"
         "app_utils.stop();print('STOPPED-0')")
open(EVD + "n1_drive.txt", "w").write(
    "STOP0: " + _send([STOP0]).strip() + "\n")
b = _send(["--file", "action-reasoner/skills/ros-navigation/bringup/scripts/n1_build.py"])
open(EVD + "n1_build.json", "w").write(json.dumps({"output": b}))
open(EVD + "n1_drive.txt", "a").write("BUILD: " + b.strip() + "\n")
open(EVD + "n1_drive.txt", "a").write(
    "PLAY: " + _send([PLAY]).strip() + "\n")
l = subprocess.run(
    ["powershell", "-ExecutionPolicy", "Bypass", "-File",
     "action-reasoner/skills/ros-navigation/bringup/scripts/n1_pumped_listen.ps1"],
    capture_output=True, text=True, timeout=600)
open(EVD + "n1_drive.txt", "a").write("LISTEN: " + l.stdout.strip()
                                      + "\n" + l.stderr.strip() + "\n")
open(EVD + "n1_drive.txt", "a").write(
    "STOP: " + _send([STOP]).strip() + "\n")
print("N1-DRIVE done rc=%d" % l.returncode)
