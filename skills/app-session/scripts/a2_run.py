"""A2 run (runs LOCALLY): stage save/reopen round-trip.

new -> define A2Marker -> save to a2_stage.usd -> new (wipe) ->
info count -> open saved -> marker check. Writes a2_report.txt.
"""
import json
import os
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "150"]
OPEN = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/open_stage.py")
USD = "C:/Users/sruja_ob3di74/action-reasoner/skills/app-session/evidence/a2_stage.usd"
if os.path.exists(USD):
    os.remove(USD)
OUT = []


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=180)
    body = json.loads(p.stdout)
    out = body.get("output", "") + "".join(
        body.get("traceback", []) or [])
    OUT.append("$ send %s\n%s" % (" ".join(args[-3:]), out.strip()))
    return out


def _open(action, extra=()):
    return _send(["--file", OPEN, "--arg", "action=" + action, *extra])


_open("new")
_send(["--file", "action-reasoner/skills/app-session/scripts/a2_marker.py"])
_open("save", ("--arg", "usd_path=" + USD))
_open("new")
wiped = _open("info")
_open("open", ("--arg", "usd_path=" + USD))
loaded = _open("info")
_send(["--file", "action-reasoner/skills/app-session/scripts/a2_check.py"])
OUT.append("USD_EXISTS=%s" % os.path.exists(USD))
OUT.append("USD_BYTES=%d" % (os.path.getsize(USD) if os.path.exists(USD) else 0))
open("action-reasoner/skills/app-session/evidence/a2_report.txt",
     "w").write("\n".join(OUT) + "\n")
print("A2-REPORT steps_logged=%d" % len(OUT))
