"""A4 run (runs LOCALLY): inspect the reopened A2 stage.

Shells library stage_info.py: tree (default) -> list filtered to
Cube -> prim detail for /World/A2Marker. Writes a4_report.txt.
"""
import json
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "120"]
INFO = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/stage_info.py")
OUT = []


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=150)
    body = json.loads(p.stdout)
    out = body.get("output", "") + "".join(
        body.get("traceback", []) or [])
    OUT.append("$ send %s\n%s" % (" ".join(args[-2:]), out.strip()))
    return out


_send(["--file", INFO])
_send(["--file", INFO, "--arg", "mode=list", "--arg",
       "filter_type=Cube"])
_send(["--file", INFO, "--arg", "prim_path=/World/A2Marker"])
open("action-reasoner/skills/app-session/evidence/a4_report.txt",
     "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("A4-REPORT queries=%d" % len(OUT))
