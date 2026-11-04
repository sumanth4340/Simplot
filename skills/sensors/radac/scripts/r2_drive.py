# R2 drive (runs INSIDE Isaac Sim): single AcousticSensor + GMO
# writer capture + evidence. Mirrors the R1 proven recipe (one sensor,
# created and played in this script, never pre-created at birth).
import json
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import Writer
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.sensors.experimental.rtx import (
    Acoustic, AcousticSensor, parse_generic_model_output_data)

EV = "C:/Users/sruja_ob3di74/action-reasoner/skills/sensors/radac/evidence/r2_gmo.json"
FRAMES = []


class R2GmoWriter(Writer):
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
            try:
                rec["modality"] = str(g.modality)
                rec["coords"] = str(g.elementsCoordsType)
                rec["sgw"] = int(g.numSamplesPerSgw)
                rec["t0"] = int(g.frameStart.timestampNs)
                rec["t1"] = int(g.frameEnd.timestampNs)
            except Exception as e:
                rec["hdr_err"] = repr(e)[:150]
            if n > 0:
                k = min(n, 4000)
                sc = np.asarray(g.scalar[:k]).ravel()
                to = np.asarray(g.timeOffsetNs[:k]).ravel()
                rec["finite_frac"] = float(np.isfinite(sc).mean())
                rec["smax"] = float(np.abs(sc).max())
                rec["to_min"] = int(to.min())
                rec["to_max"] = int(to.max())
                rec["x"] = [float(v)
                            for v in np.asarray(g.x[:k]).ravel()]
                rec["y"] = [float(v)
                            for v in np.asarray(g.y[:k]).ravel()]
                rec["z"] = [float(v)
                            for v in np.asarray(g.z[:k]).ravel()]
            FRAMES.append(rec)


try:
    rep.WriterRegistry.register(R2GmoWriter)
except Exception as e:
    print("REG-NOTE", repr(e)[:120])
acoustic = Acoustic("/World/R2Acous")
sensor = AcousticSensor(acoustic, annotators=["generic-model-output"])
sensor.attach_writer("R2GmoWriter")
app_utils.play()
await app_utils.update_app_async(steps=90)
app_utils.stop()
nonempty = [f for f in FRAMES if f["n"] > 0]
out = {"frames": len(FRAMES),
       "nonempty": len(nonempty),
       "counts": [f["n"] for f in FRAMES[:12]],
       "sample": nonempty[len(nonempty) // 2] if nonempty else None}
with open(EV, "w") as f:
    json.dump(out, f)
tot = sum(f["n"] for f in FRAMES)
print("R2-DRIVE-OK frames=%d nonempty=%d total=%d" % (
    len(FRAMES), len(nonempty), tot))
