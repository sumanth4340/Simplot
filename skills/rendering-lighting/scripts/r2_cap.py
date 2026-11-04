"""R2 capture (runs INSIDE Isaac Sim): RGB frame via RtxCamera+CameraSensor.

Builds on the R1 lit scene (no clean slate): RtxCamera at the R1
eye/target pose, 320x240 rgb annotator, play + 120 settle steps,
get_data('rgb'), save PNG to evidence. Reports shape/mean/max/size.
"""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/rendering-lighting/evidence/r2_frame.png"

eye = np.array([3.0, -3.0, 2.0])
tgt = np.array([0.0, 0.0, 0.5])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
right /= np.linalg.norm(right)
up = np.cross(right, fwd)
R = np.column_stack([right, up, -fwd])  # local axes in world


def _mat_to_wxyz(m):
    t = float(np.trace(m))
    if t > 0.0:
        s = (t + 1.0) ** 0.5 * 2.0
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = (1.0 + m[0, 0] - m[1, 1] - m[2, 2]) ** 0.5 * 2.0
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = (1.0 + m[1, 1] - m[0, 0] - m[2, 2]) ** 0.5 * 2.0
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = (1.0 + m[2, 2] - m[0, 0] - m[1, 1]) ** 0.5 * 2.0
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    return [w, x, y, z]


cam = RtxCamera("/World/R2Cam", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
# 6.0.0 quirk: resolution must be a LIST; a tuple crashes broadcast_to.
sensor = CameraSensor(cam, resolution=[240, 320], annotators=["rgb"])
app_utils.play(commit=True)
await app_utils.update_app_async(steps=120)
# get_data returns a per-camera LIST of warp arrays: unwrap [0], then
# Skill 5 R2 rule (.numpy(), never np.asarray on warp).
_d = sensor.get_data("rgb")
if isinstance(_d, (list, tuple)):
    _d = _d[0]
rgb = np.asarray(_d.numpy() if isinstance(_d, wp.array) else _d)
from PIL import Image
Image.fromarray(rgb.astype(np.uint8)).save(EV)
import os
print("R2-REPORT shape=%s mean=%.1f max=%d size=%d" % (
    list(rgb.shape), float(rgb.mean()), int(rgb.max()),
    os.path.getsize(EV)))
