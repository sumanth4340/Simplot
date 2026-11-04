"""V7 run (runs INSIDE Isaac Sim): depth + IMU + contact, one settle.

Depth cam eye=(4,0,2) target=(0,0,0.6) (center ~3.602); IMU and
Contact on the 2kg cube (force ~19.62). Play, settle 180, read all.
"""
import numpy as np
import warp as wp
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import RtxCamera, CameraSensor
from isaacsim.sensors.experimental.physics import (
    IMU, IMUSensor, Contact, ContactSensor)

eye = np.array([4.0, 0.0, 2.0])
tgt = np.array([0.0, 0.0, 0.6])
fwd = (tgt - eye) / np.linalg.norm(tgt - eye)
up0 = np.array([0.0, 0.0, 1.0])
right = np.cross(fwd, up0)
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


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


stage = omni.usd.get_context().get_stage()
o = stage.GetPrimAtPath("/World/V7Cam")
if o and o.IsValid():
    stage.RemovePrim("/World/V7Cam")
cam = RtxCamera("/World/V7Cam", positions=[eye.tolist()],
                orientations=[_mat_to_wxyz(R)])
cam.camera.set_focal_lengths(24.0)
cam.camera.set_clipping_ranges(0.01, 1000.0)
imu = IMU.create(path="/World/V7Cube/imu")
isens = IMUSensor(imu)
con = Contact.create(path="/World/V7Cube/contact",
                     min_threshold=0.0, max_threshold=1e6, radius=-1)
csens = ContactSensor(con)
app_utils.play(commit=True)
dsens = CameraSensor(cam, resolution=[240, 320],
                     annotators=["distance_to_image_plane"])
csens.get_data()  # prime: first read can return a partial frame
await app_utils.update_app_async(steps=180)
d = dsens.get_data("distance_to_image_plane")
if isinstance(d, (list, tuple)):
    d = d[0]
dep = _w(d)
ctr = float(dep[dep.shape[0] // 2, dep.shape[1] // 2])
iframe = isens.get_data()
cframe = csens.get_data()
for _ in range(3):  # retry: contact frame keys can lag creation
    if "in_contact" in cframe:
        break
    await app_utils.update_app_async(steps=30)
    cframe = csens.get_data()
acc = _w(iframe["linear_acceleration"]).flatten()
ic = _w(cframe["in_contact"]).flatten()
fc = _w(cframe["force"]).flatten()
nc = _w(cframe["number_of_contacts"]).flatten()
print("V7-REPORT dctr=%.3f amag=%.4f in_contact=%s force=%.4f "
      "ncontacts=%.0f dshape=%s" % (
          ctr, float((acc ** 2).sum() ** 0.5), bool(ic[0]),
          float(fc[0]), float(nc[0]), list(dep.shape)))
