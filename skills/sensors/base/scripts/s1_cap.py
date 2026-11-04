"""S1 capture (runs INSIDE Isaac Sim): rgb + depth, geometry-checked.

RtxCamera at eye=(0,-4,2) looking at (0,0,0.5). Center ray hits the
cube face (y=-0.5) at t=3.5/0.9363=3.738 along the optical axis, so
distance_to_image_plane center must read ~3.74. Reports rgb + depth.
"""
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor

eye = np.array([0.0, -4.0, 2.0])
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


def _grab(sensor, name):
    d = sensor.get_data(name)
    if isinstance(d, (list, tuple)):
        d = d[0]
    return np.asarray(d.numpy() if isinstance(d, wp.array) else d)


stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/S1Cam")
if o and o.IsValid():
    stage.RemovePrim("/World/S1Cam")
cam = RtxCamera("/World/S1Cam", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
app_utils.play(commit=True)
sensor = CameraSensor(cam, resolution=[240, 320],
                      annotators=["rgb", "distance_to_image_plane"])
await app_utils.update_app_async(steps=120)
rgb = _grab(sensor, "rgb")
dep = _grab(sensor, "distance_to_image_plane")
h, w = dep.shape[0], dep.shape[1]
ctr = float(dep[h // 2, w // 2])
print("S1-REPORT rgbmean=%.1f rgbmax=%d dshape=%s dctr=%.3f dmin=%.3f "
      "dmax=%.3f" % (float(rgb.mean()), int(rgb.max()),
                     list(dep.shape), ctr, float(dep.min()),
                     float(dep.max())))
