"""Contact drill mega-probe P2 (runs INSIDE Isaac Sim). Fixed STATE handling (no globals).

P0b: deeper source-dive (Contact.__init__ kwargs, _check_sensor_prim_type,
     get_sensor_reading, iface methods, SensorStepManager, scene solver attrs).
P1: baseline live read.
P2a1: suspect-1i cube report threshold 1.0 -> 0.0 (impulse-filter hypothesis).
P2a2: suspect-1ii + ground report threshold 0.0 (both-bodies hypothesis).
P2b: suspect-1b ground kinematic rigid + report (only if still zero).
P4a: suspect-2 sensor recreate child-path radius unset (only if still zero).
P4b: suspect-2b sibling placement negative control (only if still zero).
P3: suspect-3 sensorPeriod 0.02s (only if still zero).
PN: Newton-vs-PhysX solver dump + best-effort PhysX force (LAST, only if still zero).
Stops experimenting at first in_contact=True + force~=9.81; ends with confirm read.
"""
import traceback
import inspect

STATE = {"sensor": "/World/S3Cube/contact", "hit": False, "where": None}
CUBE = "/World/S3Cube"
GROUND = "/World/S3Ground"


def log(m):
    print(m, flush=True)


import omni.usd
from pxr import Usd, UsdGeom, Gf, Sdf

try:
    from pxr import UsdPhysics
    log("IMP UsdPhysics OK")
except Exception as e:
    UsdPhysics = None
    log("IMP UsdPhysics FAIL %s" % e)

try:
    from pxr import PhysxSchema
    log("IMP PhysxSchema OK")
except Exception as e:
    PhysxSchema = None
    log("IMP PhysxSchema FAIL %s" % e)

import isaacsim.core.experimental.utils.app as app_utils
log("IMP app_utils OK")

try:
    from isaacsim.core.simulation_manager import SimulationManager as SM
    log("IMP SM dt=%s backend=%s" % (SM.get_physics_dt(), SM.get_backend()))
    try:
        log("IMP SM methods=%s" % sorted([n for n in dir(SM) if not n.startswith("_")]))
    except Exception as e:
        log("IMP SM methods ERR %s" % e)
except Exception as e:
    SM = None
    log("IMP SimulationManager FAIL %s" % e)

Contact = None
ContactSensor = None
contact_mod = None
get_iface_fn = None
try:
    import isaacsim.sensors.experimental.physics as _pm
    contact_mod = _pm
    Contact = getattr(_pm, "Contact", None)
    ContactSensor = getattr(_pm, "ContactSensor", None)
    get_iface_fn = getattr(_pm, "get_contact_sensor_interface", None)
    log("IMP physics-mod OK Contact=%s ContactSensor=%s get_iface=%s" % (
        Contact is not None, ContactSensor is not None, get_iface_fn is not None))
except Exception as e:
    log("IMP physics-mod FAIL %s" % e)

IFACE = {"obj": None}
if get_iface_fn is not None:
    try:
        IFACE["obj"] = get_iface_fn()
        log("IMP iface=%s methods=%s" % (
            IFACE["obj"], sorted([n for n in dir(IFACE["obj"]) if not n.startswith("_")])))
    except Exception as e:
        log("IMP iface FAIL %s" % e)

stage = omni.usd.get_context().get_stage()


def schemas(p):
    prim = stage.GetPrimAtPath(p)
    if not prim or not prim.IsValid():
        return ["MISSING"]
    try:
        return sorted([str(a) for a in prim.GetAppliedSchemas()])
    except Exception as e:
        return ["ERR %s" % e]


def dump_attrs(label, p, filt=None, authored_only=True):
    prim = stage.GetPrimAtPath(p)
    if not prim or not prim.IsValid():
        log("%s %s MISSING" % (label, p))
        return
    try:
        log("%s %s type=%s schemas=%s" % (label, p, prim.GetTypeName(), schemas(p)))
        attrs = prim.GetAuthoredAttributes() if authored_only else prim.GetAttributes()
        for a in attrs:
            n = a.GetName()
            if filt and not any(k.lower() in n.lower() for k in filt):
                continue
            try:
                v = a.Get()
                s = str(v)
                if len(s) > 300:
                    s = s[:300] + "...<%d>" % len(s)
                log("%s %s attr %s = %s" % (label, p, n, s))
            except Exception as e:
                log("%s %s attr %s ERR %s" % (label, p, n, e))
    except Exception:
        traceback.print_exc()


def sim_state(label):
    try:
        log("%s playing=%s paused=%s stopped=%s" % (
            label, app_utils.is_playing(), app_utils.is_paused(), app_utils.is_stopped()))
    except Exception as e:
        log("%s state ERR %s" % (label, e))
    if SM is not None:
        try:
            log("%s t=%.4f steps=%s dt=%s simulating=%s" % (
                label, SM.get_simulation_time(), SM.get_num_physics_steps(),
                SM.get_physics_dt(), SM.is_simulating()))
        except Exception as e:
            log("%s SM ERR %s" % (label, e))


def read_sensor(label):
    sp = STATE["sensor"]
    log("READ %s sensor=%s" % (label, sp))
    prim = stage.GetPrimAtPath(sp)
    log("READ %s valid=%s type=%s" % (
        label, bool(prim and prim.IsValid()), prim.GetTypeName() if prim else "?"))
    if ContactSensor is None:
        log("READ %s SKIP no ContactSensor class" % label)
        return None
    try:
        s = ContactSensor(sp)
    except Exception:
        log("READ %s ContactSensor() ctor FAILED" % label)
        traceback.print_exc()
        return None
    try:
        r = s.get_sensor_reading()
        log("READ %s reading=%s" % (label, str(r)[:500]))
    except Exception as e:
        log("READ %s get_sensor_reading ERR %s" % (label, e))
    try:
        d = s.get_data()
    except Exception:
        log("READ %s get_data FAILED" % label)
        traceback.print_exc()
        return None
    try:
        if isinstance(d, dict):
            for k in sorted(d.keys()):
                sv = str(d[k])
                if len(sv) > 400:
                    sv = sv[:400] + "...<%d>" % len(sv)
                log("READ %s data[%s] = %s" % (label, k, sv))
            ic = d.get("in_contact", None)
            f = d.get("force", None)
            log("READ %s SUMMARY in_contact=%s force=%s n=%s t=%s step=%s" % (
                label, ic, f, d.get("number_of_contacts"), d.get("time"), d.get("physics_step")))
            try:
                import math as _m
                fmag = None
                if isinstance(f, (list, tuple)) and len(f) == 3:
                    fmag = _m.sqrt(sum(x * x for x in f))
                elif isinstance(f, (int, float)):
                    fmag = abs(f)
                if ic is True and fmag is not None and 5.0 < fmag < 15.0 and not STATE["hit"]:
                    STATE["hit"] = True
                    STATE["where"] = label
                    log("READ %s *** SUCCESS fmag=%.4f ***" % (label, fmag))
            except Exception as e:
                log("READ %s success-check ERR %s" % (label, e))
        else:
            log("READ %s get_data non-dict %s" % (label, str(d)[:400]))
    except Exception:
        traceback.print_exc()
    try:
        raw = s.get_raw_data()
        log("READ %s raw_data len=%d head=%s" % (label, len(raw), str(raw)[:700]))
    except Exception as e:
        log("READ %s raw_data ERR %s" % (label, e))
    if IFACE["obj"] is not None:
        for target in (sp, CUBE):
            try:
                rc = IFACE["obj"].get_raw_contacts(target)
                log("READ %s iface.get_raw_contacts(%s) len=%s head=%s" % (
                    label, target, len(rc) if hasattr(rc, "__len__") else "?", str(rc)[:500]))
            except Exception as e:
                log("READ %s iface.get_raw_contacts(%s) ERR %s" % (label, target, e))
        try:
            cpr = IFACE["obj"].get_sensor_reading(sp)
            log("READ %s iface.get_sensor_reading=%s" % (label, str(cpr)[:500]))
            log("READ %s iface reading dir=%s" % (
                label, sorted([n for n in dir(cpr) if not n.startswith("_")])))
        except Exception as e:
            log("READ %s iface.get_sensor_reading ERR %s" % (label, e))
    return d


def stop_all(label):
    try:
        app_utils.stop()
        app_utils.update_app(steps=5)
    except Exception as e:
        log("%s stop ERR %s" % (label, e))
    sim_state(label + "-stopped")


def play_settle(label, steps=90, drop_z=0.6):
    try:
        prim = stage.GetPrimAtPath(CUBE)
        UsdGeom.XformCommonAPI(prim).SetTranslate(Gf.Vec3d(0, 0, drop_z))
        log("%s drop cube z->%.2f" % (label, drop_z))
    except Exception as e:
        log("%s drop ERR %s" % (label, e))
    try:
        app_utils.play()
        app_utils.update_app(steps=steps)
    except Exception as e:
        log("%s play/settle ERR %s" % (label, e))
    sim_state(label)


def apply_contact_report(label, prim_path, threshold):
    prim = stage.GetPrimAtPath(prim_path)
    if PhysxSchema is not None:
        try:
            PhysxSchema.PhysxContactReportAPI.Apply(prim)
            log("%s %s PhysxContactReportAPI.Apply OK" % (label, prim_path))
        except Exception as e:
            log("%s %s Apply ERR %s" % (label, prim_path, e))
        try:
            api = PhysxSchema.PhysxContactReportAPI(prim)
            if hasattr(api, "CreateThresholdAttr"):
                api.CreateThresholdAttr(threshold)
                log("%s %s CreateThresholdAttr(%s) OK" % (label, prim_path, threshold))
            else:
                log("%s %s no CreateThresholdAttr; api-dir=%s" % (
                    label, prim_path, [n for n in dir(api) if "hresh" in n or "reate" in n]))
        except Exception as e:
            log("%s %s threshold ERR %s" % (label, prim_path, e))
    try:
        a = prim.GetAttribute("physxContactReport:threshold")
        log("%s %s threshold now=%s valid=%s" % (
            label, prim_path, a.Get() if a and a.IsValid() else "?", bool(a and a.IsValid())))
    except Exception as e:
        log("%s %s threshold-read ERR %s" % (label, prim_path, e))
    log("%s %s schemas=%s" % (label, prim_path, schemas(prim_path)))


def create_sensor_filtered(label, path, **desired):
    if Contact is None:
        log("%s SKIP no Contact class" % label)
        return False
    try:
        sig = inspect.signature(Contact.__init__)
        log("%s Contact.__init__ sig=%s" % (label, sig))
    except Exception as e:
        log("%s __init__ sig ERR %s" % (label, e))
    try:
        Contact.create(path=path, **desired)
        log("%s Contact.create(%s, %s) OK" % (label, path, desired))
        STATE["sensor"] = path
        try:
            app_utils.update_app(steps=2)
        except Exception:
            pass
        return True
    except Exception:
        log("%s Contact.create FAILED" % label)
        traceback.print_exc()
        return False


def set_sensor_attr(label, path, match, value):
    prim = stage.GetPrimAtPath(path)
    if not prim or not prim.IsValid():
        log("%s %s MISSING" % (label, path))
        return False
    done = False
    for a in prim.GetAttributes():
        if match.lower() in a.GetName().lower():
            try:
                before = a.Get()
                a.Set(value)
                log("%s %s attr %s %s -> %s OK" % (label, path, a.GetName(), before, a.Get()))
                done = True
            except Exception as e:
                log("%s %s attr %s set ERR %s" % (label, path, a.GetName(), e))
    if not done:
        log("%s %s no attr matching '%s'" % (label, path, match))
    return done


# ================= P0b source dive =================
log("P0B ==== deep source dive ====")
for owner, oname in ((Contact, "Contact"), (ContactSensor, "ContactSensor"),
                     (contact_mod, "module")):
    if owner is None:
        continue
    for fn_name in ("__init__", "_check_sensor_prim_type", "get_sensor_reading",
                    "_acquire_interface", "_init_frame", "add_raw_contact_data_to_frame",
                    "reset", "on_timeline_stop", "authoring_object"):
        fn = getattr(owner, fn_name, None)
        if fn is None:
            continue
        try:
            src = inspect.getsource(fn)
            if len(src) > 2200:
                src = src[:2200] + "\n...<%d total>" % len(src)
            log("P0B ---- %s.%s ----\n%s" % (oname, fn_name, src))
        except Exception as e:
            log("P0B %s.%s getsource ERR %s" % (oname, fn_name, e))
# find _SensorStepManager
try:
    import isaacsim.sensors.experimental.physics.impl.contact_sensor as _csm
    log("P0B contact_sensor.py file=%s" % inspect.getfile(_csm))
    txt = inspect.getsource(_csm)
    i = txt.find("StepManager")
    log("P0B StepManager ctx=%s" % (txt[max(0, i - 600):i + 600] if i >= 0 else "NOT-FOUND"))
except Exception as e:
    log("P0B stepmanager ERR %s" % e)
# Scene solver dump: ALL attrs incl defaults
dump_attrs("P0B-SCENE", "/World/PhysicsScene", authored_only=False)
dump_attrs("P0B-SENSOR-ALL", STATE["sensor"], authored_only=False)
try:
    world = stage.GetPrimAtPath("/World")
    log("P0B-WORLD children=%s" % [str(c.GetPath()) for c in world.GetChildren()])
except Exception as e:
    log("P0B-WORLD ERR %s" % e)

# ================= P1 baseline =================
log("P1 ==== baseline ====")
sim_state("P1")
log("P1 cube schemas=%s ground schemas=%s" % (schemas(CUBE), schemas(GROUND)))
if not app_utils.is_playing():
    try:
        app_utils.play()
        app_utils.update_app(steps=10)
    except Exception as e:
        log("P1 play ERR %s" % e)
try:
    app_utils.update_app(steps=30)
except Exception as e:
    log("P1 step ERR %s" % e)
read_sensor("P1-live")

# ================= P2a1 cube threshold -> 0 =================
if not STATE["hit"]:
    log("P2A1 ==== cube report threshold 1.0 -> 0.0 (ground untouched) ====")
    stop_all("P2A1")
    apply_contact_report("P2A1", CUBE, 0.0)
    play_settle("P2A1", steps=90, drop_z=0.6)
    read_sensor("P2A1")
else:
    log("P2A1 SKIP success at %s" % STATE["where"])

# ================= P2a2 + ground report 0 =================
if not STATE["hit"]:
    log("P2A2 ==== + ground report threshold 0.0 (both bodies) ====")
    stop_all("P2A2")
    apply_contact_report("P2A2", GROUND, 0.0)
    apply_contact_report("P2A2", CUBE, 0.0)
    play_settle("P2A2", steps=90, drop_z=0.6)
    read_sensor("P2A2")
else:
    log("P2A2 SKIP success at %s" % STATE["where"])

# ================= P2b kinematic ground =================
if not STATE["hit"]:
    log("P2B ==== kinematic rigid ground + report ====")
    stop_all("P2B")
    try:
        g = stage.GetPrimAtPath(GROUND)
        UsdPhysics.RigidBodyAPI.Apply(g)
        UsdPhysics.RigidBodyAPI(g).CreateKinematicEnabledAttr(True)
        log("P2B ground RigidBodyAPI+kinematic OK schemas=%s" % schemas(GROUND))
    except Exception:
        log("P2B ground RigidBody FAILED")
        traceback.print_exc()
    apply_contact_report("P2B", GROUND, 0.0)
    play_settle("P2B", steps=90, drop_z=0.6)
    read_sensor("P2B")
else:
    log("P2B SKIP success at %s" % STATE["where"])

# ================= P4a recreate radius unset =================
if not STATE["hit"]:
    log("P4A ==== sensor recreate child-path, radius unset ====")
    stop_all("P4A")
    try:
        stage.RemovePrim(Sdf.Path(STATE["sensor"]))
        log("P4A removed sensor")
    except Exception as e:
        log("P4A remove ERR %s" % e)
    if create_sensor_filtered("P4A", "/World/S3Cube/contact",
                              min_threshold=0.0, max_threshold=1e6):
        dump_attrs("P4A", STATE["sensor"])
        play_settle("P4A", steps=90, drop_z=0.6)
        read_sensor("P4A")
else:
    log("P4A SKIP success at %s" % STATE["where"])

# ================= P4b sibling negative control =================
if not STATE["hit"]:
    log("P4B ==== sibling placement /World/S3Contact (expect invalid/zero) ====")
    stop_all("P4B")
    try:
        stage.RemovePrim(Sdf.Path(STATE["sensor"]))
        log("P4B removed sensor")
    except Exception as e:
        log("P4B remove ERR %s" % e)
    if create_sensor_filtered("P4B", "/World/S3Contact",
                              min_threshold=0.0, max_threshold=1e6):
        dump_attrs("P4B", STATE["sensor"])
        play_settle("P4B", steps=90, drop_z=0.6)
        read_sensor("P4B")
    # restore child sensor for later phases
    try:
        stage.RemovePrim(Sdf.Path(STATE["sensor"]))
        Contact.create(path="/World/S3Cube/contact", min_threshold=0.0, max_threshold=1e6)
        STATE["sensor"] = "/World/S3Cube/contact"
        log("P4B restored child sensor")
    except Exception as e:
        log("P4B restore ERR %s" % e)
else:
    log("P4B SKIP success at %s" % STATE["where"])

# ================= P3 sensorPeriod =================
if not STATE["hit"]:
    log("P3 ==== sensorPeriod 0.02 ====")
    stop_all("P3")
    set_sensor_attr("P3", STATE["sensor"], "eriod", 0.02)
    dump_attrs("P3", STATE["sensor"], filt=("eriod", "adius", "hreshold", "nabled"))
    play_settle("P3", steps=90, drop_z=0.6)
    read_sensor("P3")
else:
    log("P3 SKIP success at %s" % STATE["where"])

# ================= PN Newton dump + PhysX force =================
if not STATE["hit"]:
    log("PN ==== solver interrogation ====")
    stop_all("PN")
    dump_attrs("PN-SCENE", "/World/PhysicsScene", authored_only=False)
    try:
        import carb.settings as _cs
        log("PN carb.settings available")
    except Exception as e:
        log("PN carb.settings ERR %s" % e)
    # best effort: remove NewtonSceneAPI so PhysX owns the scene, re-parse
    try:
        sc = stage.GetPrimAtPath("/World/PhysicsScene")
        removed = sc.RemoveAPI("NewtonSceneAPI") if hasattr(sc, "RemoveAPI") else "no-RemoveAPI"
        log("PN RemoveAPI(NewtonSceneAPI) -> %s; schemas now=%s" % (removed, schemas("/World/PhysicsScene")))
    except Exception as e:
        log("PN RemoveAPI ERR %s" % e)
    play_settle("PN", steps=90, drop_z=0.6)
    read_sensor("PN")
else:
    log("PN SKIP success at %s" % STATE["where"])

log("FINAL SUCCESS=%s where=%s sensor=%s" % (STATE["hit"], STATE["where"], STATE["sensor"]))
if STATE["hit"] and app_utils.is_playing():
    try:
        app_utils.update_app(steps=60)
    except Exception as e:
        log("FINAL extra-settle ERR %s" % e)
    sim_state("FINAL-confirm")
    read_sensor("FINAL-confirm")
log("MEGA2-DONE")
