"""A1 run (runs LOCALLY): drive the timeline state machine.

Shells library simulation_control.py through isaacsim_send.py:
stop -> status -> play -> status -> pause -> status -> stop,
then a time set/get round-trip (2.5s) and a 60-step advance.
Writes a1_report.txt transcript.
"""
import json
import subprocess
import sys

SEND = [sys.executable,
        "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
        "skills/isaac-sim-remote/scripts/isaacsim_send.py",
        "--raw", "--timeout", "120"]
SIMCTL = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
          "skills/isaac-sim-remote/scripts/simulation_control.py")
OUT = []


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=150)
    body = json.loads(p.stdout)
    out = body.get("output", "") + "".join(
        body.get("traceback", []) or [])
    OUT.append("$ send %s\n%s" % (" ".join(args), out.strip()))
    return out


def _ctl(action, extra=()):
    return _send(["--file", SIMCTL, "--arg", "action=" + action,
                  *extra])


_ctl("stop")
st_stop = _ctl("status")
_ctl("play")
st_play = _ctl("status")
_ctl("pause")
st_pause = _ctl("status")
_ctl("stop")
OUT.append("STOPPED_SEEN=%s" % ("STOPPED" in st_stop))
OUT.append("PLAYING_SEEN=%s" % ("PLAYING" in st_play))
OUT.append("PAUSED_SEEN=%s" % ("PAUSED" in st_pause))
t = _send(["--file",
           "action-reasoner/skills/app-session/scripts/a1_time.py"])
s = _ctl("step", ("--arg", "num_steps=60"))
_ctl("stop")
open("action-reasoner/skills/app-session/evidence/a1_report.txt",
     "w").write("\n".join(OUT) + "\n")
print("A1-REPORT states_logged=%d" % len(OUT))
