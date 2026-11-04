# R1 drive (runs INSIDE Isaac Sim): GMO writer capture + evidence.
import json
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Radar, RadarSensor, parse_generic_model_output_data)

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/sensors/radac/evidence/r1_gmo.json"
FRAMES = []


class R1GmoWriter(Writer):
    def __init__(self):
        self.data_structure = "renderProduct"
        self.annotators = [rep.annotators.get("GenericModelOutput")]

    def write(self, data):
        for _name, rp in data.get("renderProducts", {}).items():
            raw = rp.get("GenericModelOutput")
            if isinstance(raw, dict):
                raw = raw.get("data")
            g = parse_generic_model_output_data(raw)
            n = int(g.numElements)
            rec = {"n": n}
            for hf in ("maxRangeM", "minAzRad", "maxAzRad",
                       "minElRad", "maxElRad", "minVelMps",
                       "maxVelMps"):
                try:
                    rec[hf] = float(getattr(g, hf))
                except Exception:
                    pass
            if n > 0:
                k = min(n, 400)
                rec["x"] = [float(v) for v in np.asarray(g.x[:k]).ravel()]
                rec["y"] = [float(v) for v in np.asarray(g.y[:k]).ravel()]
                rec["z"] = [float(v) for v in np.asarray(g.z[:k]).ravel()]
                rv = getattr(g, "rv_ms", None)
                if rv is not None:
                    rec["rv"] = [float(v)
                                 for v in np.asarray(rv[:k]).ravel()]
                sc = getattr(g, "scalar", None)
                if sc is not None:
                    rec["s"] = [float(v)
                                for v in np.asarray(sc[:k]).ravel()]
            FRAMES.append(rec)


try:
    rep.WriterRegistry.register(R1GmoWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:120])
# Radar.create(config=...) leaves an Xform at the path with the real
# OmniRadar nested inside: find and wrap the child.
import omni.usd as _usd
_stage = _usd.get_context().get_stage()
_radar_path = None
for _c in _stage.GetPrimAtPath("/World/R1Radar").GetChildren():
    if _c.GetTypeName() == "OmniRadar":
        _radar_path = _c.GetPath().pathString
        break
assert _radar_path, "no OmniRadar child under /World/R1Radar"
print("WRAP:", _radar_path)
radar = Radar(_radar_path)
sensor = RadarSensor(radar, annotators=["generic-model-output"])
sensor.attach_writer("R1GmoWriter")
app_utils.play()
await app_utils.update_app_async(steps=60)
app_utils.stop()
nonempty = [f for f in FRAMES if f["n"] > 0]
out = {"frames": len(FRAMES),
       "nonempty": len(nonempty),
       "sample": nonempty[len(nonempty) // 2] if nonempty else None}
with open(EV, "w") as f:
    json.dump(out, f)
tot = sum(f["n"] for f in FRAMES)
print("R1-DRIVE-OK frames=%d nonempty=%d total_det=%d" % (
    len(FRAMES), len(nonempty), tot))
