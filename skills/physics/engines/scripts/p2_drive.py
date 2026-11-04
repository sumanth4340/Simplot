"""P2 run (runs LOCALLY): Newton/PhysX render-equivalence driver.

Per engine (newton, physx): reset z=2 -> switch -> shot A ->
play 120 -> shot B -> USD read. Compares A/B motion diffs and
end frames across engines. Writes p2_report.txt.
"""
import json
import subprocess
import sys

sys.path.insert(0, "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
                   "skills/isaac-sim-remote/scripts")
from png_stats import mean_abs_diff, png_stats

LIB = ("Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/"
       "skills/isaac-sim-remote/scripts/")
SEND = [sys.executable, LIB + "isaacsim_send.py", "--raw",
        "--timeout", "200"]
EVD = "action-reasoner/skills/physics/engines/evidence/"
OUT = []


def _send(args):
    p = subprocess.run(SEND + args, capture_output=True, text=True,
                       timeout=240)
    body = json.loads(p.stdout)
    return body.get("output", "")


RESET = ("import omni.usd, omni.timeline,"
         "isaacsim.core.experimental.utils.app as app_utils;"
         "from pxr import UsdGeom, Gf;"
         "from isaacsim.core.simulation_manager import SimulationManager as S;"
         "s=omni.usd.get_context().get_stage();app_utils.stop();"
         "await app_utils.update_app_async(steps=5);"
         "UsdGeom.Xformable(s.GetPrimAtPath('/World/P1Cube'))"
         ".GetOrderedXformOps()[0].Set(Gf.Vec3d(0,0,2.0));"
         "omni.timeline.get_timeline_interface().set_current_time(0.0);"
         "S.switch_physics_engine('{e}');"
         "await app_utils.update_app_async(steps=10);"
         "print('ACTIVE-' + str(S.get_active_physics_engine()))")
PLAY = ("import isaacsim.core.experimental.utils.app as app_utils;"
        "app_utils.play();await app_utils.update_app_async(steps=120);"
        "print('PLAYED-120')")
USDZ = ("import omni.usd;from pxr import UsdGeom;"
        "p=omni.usd.get_context().get_stage().GetPrimAtPath('/World/P1Cube');"
        "print('USDZ=%.4f' % float(UsdGeom.Xformable(p)"
        ".GetOrderedXformOps()[0].Get()[2]))")


def _shot(name):
    _send(["--file", LIB + "viewport_screenshot.py", "--arg",
           "output_path=C:/Users/sruja_ob3di74/" + EVD + name])


def _protocol(engine):
    OUT.append(_send([RESET.format(e=engine)]).strip())
    _shot("%s_A.png" % engine)
    OUT.append(_send([PLAY]).strip())
    _shot("%s_B.png" % engine)
    OUT.append(_send([USDZ]).strip())


_protocol("newton")
_protocol("physx")
n_d = mean_abs_diff(EVD + "newton_A.png", EVD + "newton_B.png")
p_d = mean_abs_diff(EVD + "physx_A.png", EVD + "physx_B.png")
e_d = mean_abs_diff(EVD + "newton_B.png", EVD + "physx_B.png")
OUT.append("N_DIFF=%.4f P_DIFF=%.4f END_DIFF=%.4f" % (n_d, p_d, e_d))
open(EVD + "p2_report.txt", "w").write("\n".join(OUT) + "\n")
print("P2-REPORT newton=%.4f physx=%.4f end=%.4f" % (n_d, p_d, e_d))
