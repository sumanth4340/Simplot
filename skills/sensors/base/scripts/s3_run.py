"""S3 run (runs INSIDE Isaac Sim): IMU + Contact on resting cube.

IMU child of the cube; Contact on the cube (radius -1 = shape).
Settle 120 steps, then dump both frames' fields + parsed values.
Resting expectations: |accel| ~ 9.81, |angvel| ~ 0, contact > 0.
"""
import numpy as np
import warp as wp
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.physics import (
    IMU, IMUSensor, Contact, ContactSensor)


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


def _fields(frame):
    out = []
    items = frame.items() if isinstance(frame, dict) else []
    for n, v in items:
        if callable(v):
            continue
        try:
            a = _w(v).flatten()
            if a.size <= 16:
                out.append("%s=%s" % (
                    n, [round(float(t), 4) for t in a]))
            else:
                out.append("%s[n=%d,mean=%.4g]" % (n, a.size, a.mean()))
        except Exception:
            out.append("%s=%s" % (n, str(v)[:60]))
    return " ".join(out) if out else "keys=" + str(
        list(frame.keys()) if isinstance(frame, dict) else type(frame))


imu = IMU.create(path="/World/S3Cube/imu")
isens = IMUSensor(imu)
con = Contact.create(path="/World/S3Cube/contact",
                     min_threshold=0.0, max_threshold=1e6, radius=-1)
csens = ContactSensor(con)
app_utils.play(commit=True)
await app_utils.update_app_async(steps=180)
iframe = isens.get_data()
cframe = csens.get_data()
print("S3-IMU " + _fields(iframe))
print("S3-CONTACT " + _fields(cframe))
acc = _w(iframe["linear_acceleration"]).flatten()
gyr = _w(iframe["angular_velocity"]).flatten()
ic = _w(cframe["in_contact"]).flatten()
fc = _w(cframe["force"]).flatten()
nc = _w(cframe["number_of_contacts"]).flatten()
print("S3-REPORT amag=%.4f wmag=%.4f in_contact=%s force=%.4f "
      "ncontacts=%.0f" % (float((acc ** 2).sum() ** 0.5),
                          float((gyr ** 2).sum() ** 0.5),
                          bool(ic[0]), float(fc[0]), float(nc[0])))
