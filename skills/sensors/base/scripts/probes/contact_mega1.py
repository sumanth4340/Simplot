"""Contact drill mega-probe P1 (runs INSIDE Isaac Sim).

Phase 0: source-dive installed Contact sensor (imports, signatures, getsource).
Phase 1: baseline live read of existing /World/S3Cube/contact.
Phase 2a: suspect-1a ground contact-report opt-in (stop/author/play/drop/settle/read).
Phase 2b: suspect-1b ground RigidBody-kinematic + report (only if still zero).
Phase 4a: suspect-2a sensor recreate, radius unset (only if still zero).
Phase 4b: suspect-2b sensor placement variant per Contact.create signature (only if still zero).
Phase 3: suspect-3 sensorPeriod 0.02s (only if still zero).
Stops experimenting at first in_contact=True; ends with confirmation read.
Stacking: opt-ins are additive; sensor recreates replace sensor prim only.
"""
import traceback
import inspect

SUCCESS = {"hit": False, "where": None}
SENSOR_PATH = "/World/S3Cube/contact"
CUBE = "/World/S3Cube"
GROUND = "/World/S3Ground"


def log(m):
    print(m, flush=True)


# ---------------- imports ----------------
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
    log("IMP PhysxSchema OK members=%s" % [n for n in dir(PhysxSchema) if "ontact" in n or "eport" in n])
except Exception as e:
    PhysxSchema = None
    log("IMP PhysxSchema FAIL %s" % e)

import isaacsim.core.experimental.utils.app as app_utils
log("IMP app_utils OK")

try:
    from isaacsim.core.simulation_manager import SimulationManager as SM
    log("IMP SimulationManager OK dt=%s backend=%s" % (SM.get_physics_dt(), SM.get_backend()))
except Exception as e:
    SM = None
    log("IMP SimulationManager FAIL %s" % e)

# Contact API: brute-force import
Contact = None
ContactSensor = None
get_raw_contacts = None
contact_mod = None
for modname in ("isaacsim.sensors.experimental.physics",
                "isaacsim.sensors.experimental.contact",
                "isaacsim.sensors.physics",
                "isaacsim.sensors.experimental"):
    try:
        m = __import__(modname, fromlist=["*"])
        names = [n for n in dir(m) if "ontact" in n]
        log("IMP %s OK contactish=%s" % (modname, names))
        if contact_mod is None and any("ontact" in n for n in dir(m)):
            contact_mod = m
        if Contact is None and hasattr(m, "Contact"):
            Contact = m.Contact
            contact_mod = m
        if ContactSensor is None and hasattr(m, "ContactSensor"):
            ContactSensor = m.ContactSensor
        if get_raw_contacts is None and hasattr(m, "get_raw_contacts"):
            get_raw_contacts = m.get_raw_contacts
    except Exception as e:
        log("IMP %s FAIL %s" % (modname, e))
log("IMP Contact=%s ContactSensor=%s get_raw_contacts=%s mod=%s"
    % (Contact, ContactSensor, get_raw_contacts,
       getattr(contact_mod, "__name__", None)))
if contact_mod is not None:
    try:
        log("IMP modfile=%s" % inspect.getfile(contact_mod))
    except Exception as e:
        log("IMP modfile ERR %s" % e)
    try:
        log("IMP moddir=%s" % sorted([n for n in dir(contact_mod) if not n.startswith("_")])[:80])
    except Exception as e:
        log("IMP moddir ERR %s" % e)

stage = omni.usd.get_context().get_stage()


# ---------------- helpers ----------------
def schemas(p):
    prim = stage.GetPrimAtPath(p)
    if not prim or not prim.IsValid():
        return ["MISSING"]
    try:
        return sorted([str(a) for a in prim.GetAppliedSchemas()])
    except Exception as e:
        return ["ERR %s" % e]


def dump_attrs(label, p, filt=None):
    prim = stage.GetPrimAtPath(p)
    if not prim or not prim.IsValid():
        log("%s %s MISSING" % (label, p))
        return
    try:
        log("%s %s type=%s schemas=%s" % (label, p, prim.GetTypeName(), schemas(p)))
        for a in prim.GetAuthoredAttributes():
            n = a.GetName()
            if filt and not any(k in n for k in filt):
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


def cube_pose(label):
    try:
        prim = stage.GetPrimAtPath(CUBE)
        m = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
        tr = m.ExtractTranslation()
        log("%s cube USD-view pos=(%.4f,%.4f,%.4f)" % (label, tr[0], tr[1], tr[2]))
    except Exception as e:
        log("%s cube USD-view ERR %s" % (label, e))
    try:
        import omni.physx as _px
        px = _px.get_physx_interface()
        for fn in ("get_rigidbody_transformation", "get_rigidbody_linear_velocity"):
            try:
                log("%s cube physx.%s = %s" % (label, fn, getattr(px, fn)(CUBE)))
            except Exception as e2:
                log("%s cube physx.%s ERR %s" % (label, fn, e2))
    except Exception as e:
        log("%s cube physx-iface ERR %s" % (label, e))


def read_sensor(label):
    global SENSOR_PATH
    log("READ %s sensor=%s" % (label, SENSOR_PATH))
    prim = stage.GetPrimAtPath(SENSOR_PATH)
    log("READ %s valid=%s type=%s" % (
        label, bool(prim and prim.IsValid()), prim.GetTypeName() if prim else "?"))
    if prim and prim.IsValid():
        for a in prim.GetAuthoredAttributes():
            try:
                log("READ %s sattr %s = %s" % (label, a.GetName(), a.Get()))
            except Exception as e:
                log("READ %s sattr %s ERR %s" % (label, a.GetName(), e))
    if ContactSensor is None:
        log("READ %s SKIP no ContactSensor class" % label)
        return None
    try:
        s = ContactSensor(SENSOR_PATH)
    except Exception:
        log("READ %s ContactSensor() ctor FAILED" % label)
        traceback.print_exc()
        return None
    try:
        d = s.get_data()
    except Exception:
        log("READ %s get_data FAILED" % label)
        traceback.print_exc()
        return None
    try:
        if isinstance(d, dict):
            for k in sorted(d.keys()):
                v = d[k]
                sv = str(v)
                if len(sv) > 600:
                    sv = sv[:600] + "...<%d>" % len(sv)
                log("READ %s data[%s] = %s" % (label, k, sv))
            ic = d.get("in_contact", None)
            f = d.get("force", None)
            nc = d.get("number_of_contacts", None)
            log("READ %s SUMMARY in_contact=%s force=%s n=%s t=%s step=%s" % (
                label, ic, f, nc, d.get("time"), d.get("physics_step")))
            try:
                fmag = None
                import math as _m
                if isinstance(f, (list, tuple)) and len(f) == 3:
                    fmag = _m.sqrt(sum(x * x for x in f))
                elif isinstance(f, (int, float)):
                    fmag = abs(f)
                if ic is True and fmag is not None and 5.0 < fmag < 15.0 and not SUCCESS["hit"]:
                    SUCCESS["hit"] = True
                    SUCCESS["where"] = label
                    log("READ %s *** SUCCESS fmag=%.4f ***" % (label, fmag))
            except Exception as e:
                log("READ %s success-check ERR %s" % (label, e))
        else:
            log("READ %s get_data non-dict type=%s val=%s" % (label, type(d), str(d)[:500]))
    except Exception:
        traceback.print_exc()
    for meth in ("get_raw_data", "is_valid"):
        try:
            fn = getattr(s, meth, None)
            if fn is None:
                log("READ %s %s() absent" % (label, meth))
            else:
                r = fn() if meth != "get_raw_data" else fn()
                log("READ %s %s() = %s" % (label, meth, str(r)[:600]))
        except Exception as e:
            log("READ %s %s() ERR %s" % (label, meth, e))
    if get_raw_contacts is not None:
        for target in (CUBE, SENSOR_PATH):
            try:
                rc = get_raw_contacts(target)
                log("READ %s get_raw_contacts(%s) = %s" % (label, target, str(rc)[:800]))
            except Exception as e:
                log("READ %s get_raw_contacts(%s) ERR %s" % (label, target, e))
    else:
        log("READ %s SKIP get_raw_contacts (no such fn)" % label)
    return d


def stop_all(label):
    try:
        app_utils.stop()
        app_utils.update_app(steps=5)
    except Exception as e:
        log("%s stop ERR %s" % (label, e))
    sim_state(label + "-stopped")


def drop_cube(z=0.6):
    prim = stage.GetPrimAtPath(CUBE)
    try:
        UsdGeom.XformCommonAPI(prim).SetTranslate(Gf.Vec3d(0, 0, z))
        log("DROP cube z->%.2f via XformCommonAPI" % z)
    except Exception as e:
        log("DROP ERR %s" % e)


def play_settle(label, steps=90, drop_z=0.6):
    drop_cube(drop_z)
    try:
        app_utils.play()
        app_utils.update_app(steps=steps)
    except Exception as e:
        log("%s play/settle ERR %s" % (label, e))
    sim_state(label)
    cube_pose(label)


def apply_contact_report(label, prim_path, threshold=1.0):
    prim = stage.GetPrimAtPath(prim_path)
    ok = False
    if PhysxSchema is not None:
        for cls_name in ("PhysxContactReportAPI", "PhysxContactReporterAPI"):
            try:
                cls = getattr(PhysxSchema, cls_name, None)
                if cls is None:
                    continue
                cls.Apply(prim)
                log("%s %s %s.Apply OK" % (label, prim_path, cls_name))
                ok = True
                try:
                    api = cls(prim)
                    if hasattr(api, "CreateThresholdAttr"):
                        api.CreateThresholdAttr(threshold)
                        log("%s %s CreateThresholdAttr(%s) OK" % (label, prim_path, threshold))
                    elif hasattr(api, "CreateContactReportThresholdAttr"):
                        api.CreateContactReportThresholdAttr(threshold)
                        log("%s %s CreateContactReportThresholdAttr(%s) OK" % (label, prim_path, threshold))
                except Exception as e:
                    log("%s %s threshold-attr ERR %s" % (label, prim_path, e))
                break
            except Exception as e:
                log("%s %s %s ERR %s" % (label, prim_path, cls_name, e))
    if UsdPhysics is not None:
        for cls_name in ("ContactReportAPI", "PhysicsContactReportAPI"):
            try:
                cls = getattr(UsdPhysics, cls_name, None)
                if cls is None:
                    continue
                cls.Apply(prim)
                log("%s %s %s.Apply OK" % (label, prim_path, cls_name))
                ok = True
                break
            except Exception as e:
                log("%s %s %s ERR %s" % (label, prim_path, cls_name, e))
    # fallback: raw attr candidates
    for aname in ("physxContactReport:threshold", "physxContact:threshold",
                  "physxContactReport:contactThreshold", "physics:contactReportThreshold"):
        try:
            a = prim.GetAttribute(aname)
            if a and a.IsValid():
                a.Set(threshold)
                log("%s %s raw-attr %s=%.2f OK" % (label, prim_path, aname, threshold))
                ok = True
        except Exception as e:
            log("%s %s raw-attr %s ERR %s" % (label, prim_path, aname, e))
    dump_attrs(label + "-schema", prim_path, filt=("eport", "hreshold", "igid", "inematic", "ollision", "ass", "ensity"))
    return ok


def create_sensor_filtered(label, path, **desired):
    """Call Contact.create with only kwargs its signature accepts; report filtering."""
    global SENSOR_PATH
    if Contact is None:
        log("%s SKIP no Contact class" % label)
        return False
    try:
        sig = inspect.signature(Contact.create)
        params = set(sig.parameters.keys())
        log("%s Contact.create sig=%s" % (label, sig))
    except Exception as e:
        log("%s signature ERR %s" % (label, e))
        params = set()
    kwargs = {}
    for k, v in desired.items():
        if k in params or not params:
            kwargs[k] = v
        else:
            # try common aliases
            alias = {"sensor_period": ("sensorPeriod", "period", "dt"),
                     "min_threshold": ("minThreshold", "threshold_min"),
                     "max_threshold": ("maxThreshold", "threshold_max")}.get(k, ())
            used = None
            for a in alias:
                if a in params:
                    kwargs[a] = v
                    used = a
                    break
            log("%s kwarg %s %s" % (label, k, ("-> %s" % used) if used else "DROPPED (not in sig)"))
    try:
        if "path" in params:
            Contact.create(path=path, **kwargs)
        else:
            Contact.create(path, **kwargs)
        log("%s Contact.create(%s, %s) OK" % (label, path, kwargs))
        SENSOR_PATH = path
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
    for a in prim.GetAuthoredAttributes():
        if match in a.GetName():
            try:
                before = a.Get()
                a.Set(value)
                log("%s %s attr %s %s -> %s OK" % (label, path, a.GetName(), before, a.Get()))
                done = True
            except Exception as e:
                log("%s %s attr %s set ERR %s" % (label, path, a.GetName(), e))
    # also try well-known full names
    for full in ("sensorPeriod", "contact:sensorPeriod", "physxContact:sensorPeriod",
                 "radius", "contact:radius"):
        if match in full:
            try:
                a = prim.GetAttribute(full)
                if a and a.IsValid():
                    a.Set(value)
                    log("%s %s fullattr %s -> %s OK" % (label, path, full, a.Get()))
                    done = True
            except Exception as e:
                log("%s %s fullattr %s ERR %s" % (label, path, full, e))
    if not done:
        log("%s %s no attr matching '%s'" % (label, path, match))
    return done


# ================= P0 source dive =================
log("P0-SRC ==== Contact.create ====")
try:
    log("P0-SRC sig Contact.create = %s" % inspect.signature(Contact.create))
except Exception as e:
    log("P0-SRC sig ERR %s" % e)
for obj, name in ((Contact, "Contact"), (ContactSensor, "ContactSensor")):
    try:
        log("P0-SRC file %s = %s" % (name, inspect.getfile(obj)))
    except Exception as e:
        log("P0-SRC file %s ERR %s" % (name, e))
for fn_name in ("create", "_ensure_sensor", "on_physics_step", "get_raw_contacts",
                "get_data", "get_raw_data", "_on_physics_step", "initialize"):
    for owner, oname in ((Contact, "Contact"), (ContactSensor, "ContactSensor"),
                         (contact_mod, "module")):
        if owner is None:
            continue
        fn = getattr(owner, fn_name, None)
        if fn is None:
            continue
        try:
            src = inspect.getsource(fn)
            if len(src) > 2600:
                src = src[:2600] + "\n...<%d chars total>" % len(src)
            log("P0-SRC ---- %s.%s ----\n%s" % (oname, fn_name, src))
        except Exception as e:
            log("P0-SRC %s.%s getsource ERR %s" % (oname, fn_name, e))
try:
    log("P0-SRC ContactSensor methods=%s" % sorted([n for n in dir(ContactSensor) if not n.startswith("__")]))
except Exception as e:
    log("P0-SRC methods ERR %s" % e)

# ================= P1 baseline =================
log("P1-BASE ==== baseline ====")
sim_state("P1-BASE")
dump_attrs("P1-BASE", "/World/PhysicsScene")
dump_attrs("P1-BASE", CUBE)
dump_attrs("P1-BASE", GROUND)
dump_attrs("P1-BASE", SENSOR_PATH)
if not app_utils.is_playing():
    try:
        app_utils.play()
        app_utils.update_app(steps=10)
    except Exception as e:
        log("P1-BASE play ERR %s" % e)
try:
    app_utils.update_app(steps=30)
except Exception as e:
    log("P1-BASE step ERR %s" % e)
sim_state("P1-BASE-live")
cube_pose("P1-BASE-live")
read_sensor("P1-BASE-live")

# fresh drop + settle baseline (proves rest contact from motion, not spawn touch)
stop_all("P1-DROP")
play_settle("P1-DROP", steps=90, drop_z=0.6)
read_sensor("P1-DROP")

# ================= P2a ground report =================
if not SUCCESS["hit"]:
    log("P2A ==== ground contact-report opt-in ====")
    stop_all("P2A")
    apply_contact_report("P2A", GROUND, 1.0)
    apply_contact_report("P2A", CUBE, 1.0)
    log("P2A cube schemas=%s ground schemas=%s" % (schemas(CUBE), schemas(GROUND)))
    play_settle("P2A", steps=90, drop_z=0.6)
    read_sensor("P2A")
else:
    log("P2A SKIP (already success at %s)" % SUCCESS["where"])

# ================= P2b kinematic ground =================
if not SUCCESS["hit"]:
    log("P2B ==== kinematic rigid ground + report ====")
    stop_all("P2B")
    try:
        g = stage.GetPrimAtPath(GROUND)
        UsdPhysics.RigidBodyAPI.Apply(g)
        UsdPhysics.RigidBodyAPI(g).CreateKinematicEnabledAttr(True)
        log("P2B ground RigidBodyAPI+kinematic OK")
    except Exception:
        log("P2B ground RigidBody FAILED")
        traceback.print_exc()
    apply_contact_report("P2B", GROUND, 1.0)
    play_settle("P2B", steps=90, drop_z=0.6)
    read_sensor("P2B")
else:
    log("P2B SKIP (already success at %s)" % SUCCESS["where"])

# ================= P4a radius-unset recreate =================
if not SUCCESS["hit"]:
    log("P4A ==== sensor recreate, radius unset ====")
    stop_all("P4A")
    try:
        stage.RemovePrim(Sdf.Path(SENSOR_PATH))
        log("P4A removed %s" % SENSOR_PATH)
    except Exception as e:
        log("P4A remove ERR %s" % e)
    create_sensor_filtered("P4A", "/World/S3Cube/contact",
                           min_threshold=0.0, max_threshold=1e6)
    dump_attrs("P4A", SENSOR_PATH)
    play_settle("P4A", steps=90, drop_z=0.6)
    read_sensor("P4A")
else:
    log("P4A SKIP (already success at %s)" % SUCCESS["where"])

# ================= P4b placement variant =================
if not SUCCESS["hit"]:
    log("P4B ==== sensor placement variant ====")
    stop_all("P4B")
    try:
        stage.RemovePrim(Sdf.Path(SENSOR_PATH))
        log("P4B removed %s" % SENSOR_PATH)
    except Exception as e:
        log("P4B remove ERR %s" % e)
    # sibling-scope sensor at /World level (signature-driven kwargs)
    ok = create_sensor_filtered("P4B", "/World/S3Contact",
                                min_threshold=0.0, max_threshold=1e6)
    if ok:
        dump_attrs("P4B", SENSOR_PATH)
        play_settle("P4B", steps=90, drop_z=0.6)
        read_sensor("P4B")
else:
    log("P4B SKIP (already success at %s)" % SUCCESS["where"])

# ================= P3 sensorPeriod =================
if not SUCCESS["hit"]:
    log("P3 ==== sensorPeriod 0.02s ====")
    stop_all("P3")
    if SM is not None:
        try:
            log("P3 physics_dt=%s" % SM.get_physics_dt())
        except Exception as e:
            log("P3 dt ERR %s" % e)
    set_sensor_attr("P3", SENSOR_PATH, "eriod", 0.02)
    dump_attrs("P3", SENSOR_PATH, filt=("eriod", "adius", "hreshold"))
    play_settle("P3", steps=90, drop_z=0.6)
    read_sensor("P3")
else:
    log("P3 SKIP (already success at %s)" % SUCCESS["where"])

# ================= confirmation =================
log("FINAL SUCCESS=%s where=%s sensor=%s" % (SUCCESS["hit"], SUCCESS["where"], SENSOR_PATH))
if SUCCESS["hit"] and app_utils.is_playing():
    try:
        app_utils.update_app(steps=60)
    except Exception as e:
        log("FINAL extra-settle ERR %s" % e)
    sim_state("FINAL-confirm")
    cube_pose("FINAL-confirm")
    read_sensor("FINAL-confirm")
log("MEGA1-DONE")
