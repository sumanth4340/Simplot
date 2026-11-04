"""V6 capture (runs INSIDE Isaac Sim): exam frame + PNG + stats.

RtxCamera at the V6 eye/target, 320x240 rgb, filmIso pinned 100,
dome/sun pinned to exam values, 120 settle, save PNG, report.
"""
import os
import carb
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor
from pxr import UsdLux

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/rendering-lighting/evidence/v6_frame.png"

eye = np.array([-3.5, 2.5, 2.5])
tgt = np.array([0.0, 0.0, 0.5])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
R = np.column_stack([right, up, -fwd])


def _mat_to_wxyz(m):
    t = float(np.trace(m))
    if t > 0.0:
        s = (t + 1.0) ** 0.5 * 2.0
        return [0.25 * s, (m[2, 1] - m[1, 2]) / s,
                (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = (1.0 + m[0, 0] - m[1, 1] - m[2, 2]) ** 0.5 * 2.0
        return [(m[2, 1] - m[1, 2]) / s, 0.25 * s,
                (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s]
    if m[1, 1] > m[2, 2]:
        s = (1.0 + m[1, 1] - m[0, 0] - m[2, 2]) ** 0.5 * 2.0
        return [(m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s,
                0.25 * s, (m[1, 2] + m[2, 1]) / s]
    s = (1.0 + m[2, 2] - m[0, 0] - m[1, 1]) ** 0.5 * 2.0
    return [(m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s,
            (m[1, 2] + m[2, 1]) / s, 0.25 * s]


stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/V6Cap")
if o and o.IsValid():
    stage.RemovePrim("/World/V6Cap")
cam = RtxCamera("/World/V6Cap", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
UsdLux.DomeLight.Get(stage, "/World/V6Dome").GetIntensityAttr().Set(300.0)
UsdLux.DistantLight.Get(stage, "/World/V6Sun").GetIntensityAttr().Set(1200.0)
carb.settings.get_settings().set("/rtx/post/tonemap/filmIso", 100.0)
app_utils.play(commit=True)
sensor = CameraSensor(cam, resolution=[240, 320], annotators=["rgb"])
await app_utils.update_app_async(steps=120)
d = sensor.get_data("rgb")
if isinstance(d, (list, tuple)):
    d = d[0]
rgb = np.asarray(d.numpy() if isinstance(d, wp.array) else d)
from PIL import Image
Image.fromarray(rgb.astype(np.uint8)).save(EV)
print("V6-REPORT shape=%s mean=%.1f max=%d size=%d iso=100.0" % (
    list(rgb.shape), float(rgb.mean()), int(rgb.max()),
    os.path.getsize(EV)))
