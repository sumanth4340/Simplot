"""Diag probe 2 (runs INSIDE Isaac Sim): one GMO scan, per-beam characterization.

Writer-based (never poll get_data for GMO). Attaches to existing /World/S2Lidar
if present, else creates it. Reports azimuth/elevation/range per elevation band,
cube-angular-box hits, near-nadir ground hits, and frame/world-frame evidence.
"""
import numpy as np
import warp as wp
import omni.replicator.core as rep
from omni.replicator.core import Writer
import omni.usd
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data

STATS = {"frames": 0, "points": 0}
ALL = {"x": [], "y": [], "z": []}


def _w(a):
    if isinstance(a, wp.array):
        a = a.numpy()
    return np.asarray(a, dtype=float)


class DiagWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        if "renderProducts" not in data:
            return
        for _rp, rp_data in data["renderProducts"].items():
            raw = rp_data.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            if raw is None:
                continue
            gmo = parse_generic_model_output_data(raw)
            n = int(gmo.numElements)
            if n <= 0:
                continue
            STATS["frames"] += 1
            STATS["points"] += n
            ALL["x"].append(_w(gmo.x).copy())
            ALL["y"].append(_w(gmo.y).copy())
            ALL["z"].append(_w(gmo.z).copy())


stage = omni.usd.get_context().get_stage()
# diag1 follow-up: BBoxCache with purpose 'render' alone returned empty boxes;
# retry with default+render and report authored purpose (ground truth bboxes).
from pxr import Usd as _Usd, UsdGeom as _UG
_bc = _UG.BBoxCache(_Usd.TimeCode.Default(), includedPurposes=["default", "render"], useExtentsHint=True)
for _p in ("/World/S2Ground", "/World/S2Cube"):
    _prim = stage.GetPrimAtPath(_p)
    try:
        _pur = _UG.Imageable(_prim).GetPurposeAttr().Get()
    except Exception as _e:
        _pur = "ERR %s" % _e
    try:
        _ab = _bc.ComputeWorldBound(_prim).ComputeAlignedBox()
        _mn, _mx = _ab.GetMin(), _ab.GetMax()
        print("DIAG2-BBOX %s purpose=%s min=(%.3f,%.3f,%.3f) max=(%.3f,%.3f,%.3f)"
              % (_p, _pur, _mn[0], _mn[1], _mn[2], _mx[0], _mx[1], _mx[2]))
    except Exception as _e:
        print("DIAG2-BBOX %s purpose=%s ERR %s" % (_p, _pur, _e))
lp = stage.GetPrimAtPath("/World/S2Lidar")
if lp and lp.IsValid():
    lidar = Lidar("/World/S2Lidar")
    print("DIAG2-LIDAR reuse existing prim")
else:
    lidar = Lidar.create(path="/World/S2Lidar", config="Example_Rotary",
                         tick_rate=10.0, accumulate_outputs=True,
                         positions=[[0.0, 0.0, 1.5]])
    print("DIAG2-LIDAR created fresh prim")
sensor = LidarSensor(lidar, annotators=[])
try:
    rep.WriterRegistry.register(DiagWriter)
except Exception:
    pass
sensor.attach_writer("DiagWriter")
app_utils.play(commit=True)
await app_utils.update_app_async(steps=150)
print("DIAG2-CAPTURE frames=%d points=%d" % (STATS["frames"], STATS["points"]))

if STATS["points"] > 0:
    x = np.concatenate(ALL["x"]); y = np.concatenate(ALL["y"]); z = np.concatenate(ALL["z"])
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    az = np.degrees(np.arctan2(y, x))
    el = np.degrees(np.arcsin(np.clip(z / np.maximum(r, 1e-9), -1.0, 1.0)))
    print("DIAG2-GLOBAL n=%d rmin=%.3f rmax=%.3f rmean=%.3f" % (len(r), r.min(), r.max(), r.mean()))
    print("DIAG2-GLOBAL xmin=%.3f xmax=%.3f ymin=%.3f ymax=%.3f zmin=%.3f zmax=%.3f zmean=%.3f"
          % (x.min(), x.max(), y.min(), y.max(), z.min(), z.max(), z.mean()))
    print("DIAG2-GLOBAL azmin=%.1f azmax=%.1f elmin=%.2f elmax=%.2f" % (az.min(), az.max(), el.min(), el.max()))
    bands = [(-90, -15), (-15, -10), (-10, -5), (-5, 0), (0, 5), (5, 10), (10, 90)]
    for lo, hi in bands:
        m = (el >= lo) & (el < hi)
        c = int(m.sum())
        if c:
            print("DIAG2-BAND el[%g,%g) n=%d rmin=%.3f rmax=%.3f rmean=%.3f zmean=%.3f"
                  % (lo, hi, c, r[m].min(), r[m].max(), r[m].mean(), z[m].mean()))
        else:
            print("DIAG2-BAND el[%g,%g) n=0" % (lo, hi))
    # cube angular box: lidar at (0,0,1.5), cube center (2,0,0.5), half-size .5
    # azimuth half-angle ~ atan(.5/1.5..2.5); use |az|<20deg, r<3m, plus z below sensor
    cube = (np.abs(az) < 20.0) & (r < 3.0)
    print("DIAG2-CUBEBOX hits=%d (az|.|<20deg & r<3m)" % int(cube.sum()))
    if int(cube.sum()):
        print("DIAG2-CUBEBOX rmin=%.3f rmax=%.3f zmin=%.3f zmax=%.3f" % (r[cube].min(), r[cube].max(), z[cube].min(), z[cube].max()))
    # near-nadir ground: steep down beams should hit ground at r in [1.5, 6)
    nadir = (el < -10.0) & (r < 6.0)
    print("DIAG2-NADIR hits=%d (el<-10deg & r<6m)" % int(nadir.sum()))
    # where ARE the close points, if any?
    close = r < 6.0
    print("DIAG2-CLOSE n=%d of %d (r<6m)" % (int(close.sum()), len(r)))
    if int(close.sum()):
        print("DIAG2-CLOSE azrange=[%.1f,%.1f] elrange=[%.1f,%.1f] zrange=[%.2f,%.2f]"
              % (az[close].min(), az[close].max(), el[close].min(), el[close].max(), z[close].min(), z[close].max()))
    # sample raw points: 5 closest + 5 farthest
    oi = np.argsort(r)
    for i in oi[:5]:
        print("DIAG2-SAMPLE-CLOSE x=%.3f y=%.3f z=%.3f r=%.3f az=%.1f el=%.1f" % (x[i], y[i], z[i], r[i], az[i], el[i]))
    for i in oi[-5:]:
        print("DIAG2-SAMPLE-FAR x=%.3f y=%.3f z=%.3f r=%.3f az=%.1f el=%.1f" % (x[i], y[i], z[i], r[i], az[i], el[i]))
    # frame check: are x/y/z sensor-local (z~0 plane at sensor) or world (ground z~0)?
    print("DIAG2-FRAME frac_z_below0=%.4f frac_z_near_sensorplane=%.4f(|z-1.5|<0.3)"
          % (float((z < 0).mean()), float((np.abs(z - 1.5) < 0.3).mean())))
print("DIAG2-DONE")
