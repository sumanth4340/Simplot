"""R4 exposure cause-effect (runs INSIDE Isaac Sim): filmIso 100 -> 400.

Fresh R4Cam on the R1 scene (dome 400, sun 1500 fixed): capture at
filmIso 100, raise to 400 live, re-settle, capture. Expect ratio >1.15.
Restores filmIso 100 at the end so later drills start clean.
"""
import carb
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor

eye = np.array([3.0, -3.0, 2.0])
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


def _grab(sensor):
    d = sensor.get_data("rgb")
    if isinstance(d, (list, tuple)):
        d = d[0]
    return np.asarray(d.numpy() if isinstance(d, wp.array) else d)


stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/R4Cam")
if o and o.IsValid():
    stage.RemovePrim("/World/R4Cam")
cam = RtxCamera("/World/R4Cam", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
s = carb.settings.get_settings()
s.set("/rtx/post/tonemap/filmIso", 100.0)
app_utils.play(commit=True)
sensor = CameraSensor(cam, resolution=[240, 320], annotators=["rgb"])
await app_utils.update_app_async(steps=120)
m1 = float(_grab(sensor).mean())
s.set("/rtx/post/tonemap/filmIso", 400.0)
await app_utils.update_app_async(steps=90)
rgb2 = _grab(sensor)
m2 = float(rgb2.mean())
s.set("/rtx/post/tonemap/filmIso", 100.0)
print("R4-REPORT mean1=%.1f mean2=%.1f ratio=%.3f max2=%d shape=%s"
      % (m1, m2, m2 / m1, int(rgb2.max()), list(rgb2.shape)))
