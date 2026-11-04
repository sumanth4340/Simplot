"""V14 run (runs LOCALLY): exam equivalence driver.

Mirrors P2 on V14Cube (z=3): per engine reset -> switch ->
shot A -> play 150 -> shot B -> USD read. 150 steps cover the
higher drop. Writes v14_report.txt.
"""
import json
import subprocess
import sys

sys.path.insert(0, "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/isaac-sim-remote/scripts")
from png_stats import mean_abs_diff

LIB = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
       "skills/isaac-sim-remote/scripts/")
SEND = [sys.executable, LIB + "isaacsim_send.py", "--raw",
        "--timeout", "200"]
EVD = "action-reasoner/skills/physics/engines/evidence/"
OUT = []


def _send(args):
    for attempt in (1, 2, 3):
        p = subprocess.run(SEND + args, capture_output=True, text=True,
                           timeout=240)
        try:
            body = json.loads(p.stdout)
        except Exception:
            body = {}
        out = body.get("output", "") if body.get("status") == "ok" else ""
        if out.strip():
            return out
    raise RuntimeError("send failed 3x: %s" % " ".join(args[-2:]))


RESET = ("import omni.usd, omni.timeline,"
         "isaacsim.core.experimental.utils.app as app_utils;"
         "from pxr import UsdGeom, Gf;"
         "from isaacsim.core.simulation_manager import SimulationManager as S;"
         "s=omni.usd.get_context().get_stage();app_utils.stop();"
         "await app_utils.update_app_async(steps=5);"
         "UsdGeom.Xformable(s.GetPrimAtPath('/World/V14Cube'))"
         ".GetOrderedXformOps()[0].Set(Gf.Vec3d(0,0,3.0));"
         "omni.timeline.get_timeline_interface().set_current_time(0.0);"
         "S.switch_physics_engine('{e}');"
         "await app_utils.update_app_async(steps=10);"
         "print('ACTIVE-' + str(S.get_active_physics_engine()))")
PLAY = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.play();await app_utils.update_app_async(steps=150);"
        "print('PLAYED-150')")
USDZ = ("import omni.usd;from pxr import UsdGeom;"
        "p=omni.usd.get_context().get_stage().GetPrimAtPath('/World/V14Cube');"
        "print('USDZ=%.4f' % float(UsdGeom.Xformable(p)"
        ".GetOrderedXformOps()[0].Get()[2]))")


def _shot(name):
    _send(["--file", LIB + "viewport_screenshot.py", "--arg",
           "output_path=C:/Users/sruja_ob3di74/" + EVD + name])


def _protocol(engine, tag):
    OUT.append(_send([RESET.format(e=engine)]).strip())
    _shot("v14_%s_A.png" % tag)
    OUT.append(_send([PLAY]).strip())
    _shot("v14_%s_B.png" % tag)
    OUT.append(_send([USDZ]).strip())


_protocol("newton", "n")
_protocol("physx", "p")
n_d = mean_abs_diff(EVD + "v14_n_A.png", EVD + "v14_n_B.png")
p_d = mean_abs_diff(EVD + "v14_p_A.png", EVD + "v14_p_B.png")
e_d = mean_abs_diff(EVD + "v14_n_B.png", EVD + "v14_p_B.png")
OUT.append("N_DIFF=%.4f P_DIFF=%.4f END_DIFF=%.4f" % (n_d, p_d, e_d))
open(EVD + "v14_report.txt", "w").write("\n".join(OUT) + "\n")
print("V14-REPORT newton=%.4f physx=%.4f end=%.4f" % (n_d, p_d, e_d))
