"""Contact drill mega-probe P4 (runs INSIDE Isaac Sim). No globals (STATE dict only).

Context: MEGA3 T1 proved in_contact=True force=9.81 n=4 while AWAKE (steps 9-16),
silent at rest (steps 34+) -> sleep hypothesis. Threshold-impulse secondary suspect
(resting per-contact impulse ~= 0.049 N.s << old threshold 1.0).

A: disableSleeping True; drop; read s12/s90/s180 (expect True/9.81 at ALL incl long rest).
B (if A-s90 True): remove ground report API; drop; read s90 (both-bodies ablation).
D (if A worked): cube threshold 1.0 (+ground report 0.0); drop; read s12 awake
   (expect FALSE -> proves impulse-threshold filtering); then restore cube 0.0.
C: disableSleeping False again; drop; read s90 (expect FALSE -> sleep is the switch);
   then disableSleeping True + final confirm s90 (expect True). Leave scene WORKING.
"""
import traceback

STATE = {"sensor": "/World/S3Cube/contact", "hit": False, "where": None}
CUBE = "/World/S3Cube"
GROUND = "/World/S3Ground"


def log(m):
    print(m, flush=True)


import omni.usd
from pxr import Usd, UsdGeom, Gf, Sdf

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.sensors.experimental.physics as _pm

ContactSensor = _pm.ContactSensor
stage = omni.usd.get_context().get_stage()


def schemas(p):
    prim = stage.GetPrimAtPath(p)
    if not prim or not prim.IsValid():
        return ["MISSING"]
    try:
        return sorted([str(a) for a in prim.GetAppliedSchemas()])
    except Exception as e:
        return ["ERR %s" % e]


def read_sensor(label):
    try:
        d = ContactSensor(STATE["sensor"]).get_data()
        log("READ %s in_contact=%s force=%s n=%s t=%.3f step=%s" % (
            label, d.get("in_contact"), d.get("force"), d.get("number_of_contacts"),
            d.get("time"), d.get("physics_step")))
        try:
            f = d.get("force")
            if d.get("in_contact") is True and isinstance(f, float) and 5.0 < f < 15.0 \
                    and not STATE["hit"]:
                STATE["hit"] = True
                STATE["where"] = label
                log("READ %s *** REST-SUCCESS f=%.4f ***" % (label, f))
        except Exception as e:
            log("READ %s check ERR %s" % (label, e))
        return d
    except Exception as e:
        log("READ %s FAILED %s\n%s" % (label, e, traceback.format_exc()))
        return None


def stop_all(label):
    try:
        app_utils.stop()
        app_utils.update_app(steps=5)
    except Exception as e:
        log("%s stop ERR %s" % (label, e))


def drop_play(drop_z=0.6):
    UsdGeom.XformCommonAPI(stage.GetPrimAtPath(CUBE)).SetTranslate(Gf.Vec3d(0, 0, drop_z))
    app_utils.play()


def cycle(label, reads=(12, 78, 90)):
    """Fresh drop; reads after cumulative step counts given. Returns dict idx->data."""
    stop_all(label)
    drop_play(0.6)
    out = {}
    total = 0
    for i, n in enumerate(reads):
        app_utils.update_app(steps=n)
        total += n
        out[total] = read_sensor("%s-s%d" % (label, total))
    return out


def set_scene_attr(label, name, value):
    try:
        a = stage.GetPrimAtPath("/World/PhysicsScene").GetAttribute(name)
        a.Set(value)
        log("%s scene %s -> %s" % (label, name, a.Get()))
    except Exception as e:
        log("%s scene %s ERR %s" % (label, name, e))


def set_report(label, path, threshold):
    try:
        from pxr import PhysxSchema
        PhysxSchema.PhysxContactReportAPI.Apply(stage.GetPrimAtPath(path))
        PhysxSchema.PhysxContactReportAPI(stage.GetPrimAtPath(path)).CreateThresholdAttr(threshold)
        log("%s %s report=%.2f schemas=%s" % (label, path, threshold, schemas(path)))
    except Exception as e:
        log("%s %s report ERR %s" % (label, path, e))


log("P4-INIT cube=%s ground=%s scene=%s" % (schemas(CUBE), schemas(GROUND),
                                            schemas("/World/PhysicsScene")))

# ================= A no-sleep =================
log("A ==== disableSleeping True, long-rest reads ====")
stop_all("A")
set_scene_attr("A", "physxScene:disableSleeping", True)
set_report("A", CUBE, 0.0)
set_report("A", GROUND, 0.0)
drop_play(0.6)
app_utils.update_app(steps=12)
dA12 = read_sensor("A-s12")
app_utils.update_app(steps=78)
dA90 = read_sensor("A-s90")
app_utils.update_app(steps=90)
dA180 = read_sensor("A-s180")
a_rest_ok = (dA90 and dA90.get("in_contact") is True) and (dA180 and dA180.get("in_contact") is True)
log("A-VERDICT long-rest-stable=%s" % a_rest_ok)

# ================= B ground-report ablation =================
b_ground_needed = None
if a_rest_ok:
    log("B ==== remove GROUND report (cube keeps 0.0) ====")
    stop_all("B")
    try:
        r = stage.GetPrimAtPath(GROUND).RemoveAPI("PhysxContactReportAPI")
        log("B ground RemoveAPI -> %s; schemas=%s" % (r, schemas(GROUND)))
    except Exception as e:
        log("B remove ERR %s" % e)
    drop_play(0.6)
    app_utils.update_app(steps=90)
    dB = read_sensor("B-s90-cube-only")
    b_ground_needed = not (dB and dB.get("in_contact") is True)
    log("B-VERDICT ground-report-needed=%s" % b_ground_needed)
else:
    log("B SKIP (A failed)")

# ================= D threshold-1.0 awake filter proof =================
if a_rest_ok:
    log("D ==== cube threshold 1.0, awake read (expect FALSE) ====")
    stop_all("D")
    set_report("D", GROUND, 0.0)
    set_report("D", CUBE, 1.0)
    drop_play(0.6)
    app_utils.update_app(steps=12)
    dD = read_sensor("D-s12-awake-thr1")
    d_awake_silent = not (dD and dD.get("in_contact") is True)
    log("D-VERDICT threshold1.0-filters-awake=%s" % d_awake_silent)
    stop_all("D-restore")
    set_report("D-restore", CUBE, 0.0)
else:
    log("D SKIP (A failed)")

# ================= C sleep switch causal proof =================
if a_rest_ok:
    log("C ==== sleeping RE-ENABLED (expect silence returns) ====")
    stop_all("C")
    set_scene_attr("C", "physxScene:disableSleeping", False)
    drop_play(0.6)
    app_utils.update_app(steps=90)
    dC = read_sensor("C-s90-sleep-on")
    c_silent = not (dC and dC.get("in_contact") is True)
    log("C-VERDICT sleep-re-silences=%s" % c_silent)
    log("C ==== restore WORKING state + final confirm ====")
    stop_all("C-restore")
    set_scene_attr("C-restore", "physxScene:disableSleeping", True)
    set_report("C-restore", CUBE, 0.0)
    set_report("C-restore", GROUND, 0.0)
    drop_play(0.6)
    app_utils.update_app(steps=90)
    read_sensor("FINAL-s90-working")
    app_utils.update_app(steps=90)
    read_sensor("FINAL-s180-working")
else:
    log("C SKIP (A failed)")

log("P4-FINAL scene-deltas cube=%s ground=%s" % (schemas(CUBE), schemas(GROUND)))
try:
    sc = stage.GetPrimAtPath("/World/PhysicsScene")
    log("P4-FINAL disableSleeping=%s gpuDyn=%s scene-schemas=%s" % (
        sc.GetAttribute("physxScene:disableSleeping").Get(),
        sc.GetAttribute("physxScene:enableGPUDynamics").Get(), schemas("/World/PhysicsScene")))
    sp = stage.GetPrimAtPath(STATE["sensor"])
    log("P4-FINAL sensor radius=%s period=%s threshold=%s enabled=%s" % (
        sp.GetAttribute("radius").Get(), sp.GetAttribute("sensorPeriod").Get(),
        sp.GetAttribute("threshold").Get(), sp.GetAttribute("enabled").Get()))
except Exception as e:
    log("P4-FINAL dump ERR %s" % e)
log("MEGA4-DONE")
