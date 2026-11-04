"""S4 run (runs INSIDE Isaac Sim): depth follows known cube motion.

Fixed camera eye=(0,-4,2) target=(0,0,0.5). Leg 1: cube (0,0,0.5),
center depth ~3.738. Leg 2: slide cube to (0,1.0,0.5) live, center
depth ~4.806 (delta ~1.068). Reports both + delta.
"""
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor
from pxr import UsdGeom, Gf

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


def _grab(sensor):
    d = sensor.get_data("distance_to_image_plane")
    if isinstance(d, (list, tuple)):
        d = d[0]
    return np.asarray(d.numpy() if isinstance(d, wp.array) else d)


def _center(dep):
    return float(dep[dep.shape[0] // 2, dep.shape[1] // 2])


stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/S4Cam")
if o and o.IsValid():
    stage.RemovePrim("/World/S4Cam")
cam = RtxCamera("/World/S4Cam", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
app_utils.play(commit=True)
sensor = CameraSensor(cam, resolution=[240, 320],
                      annotators=["distance_to_image_plane"])
await app_utils.update_app_async(steps=120)
d1 = _center(_grab(sensor))
xp = UsdGeom.Xformable(stage.GetPrimAtPath("/World/S4Cube"))
for op in xp.GetOrderedXformOps():
    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
        op.Set(Gf.Vec3d(0, 1.0, 0.5))
await app_utils.update_app_async(steps=90)
d2 = _center(_grab(sensor))
print("S4-REPORT d1=%.3f d2=%.3f delta=%.3f" % (d1, d2, d2 - d1))
