"""Contact drill mega-probe P3 (runs INSIDE Isaac Sim). No globals (STATE dict only).

E0: engine/solver interrogation (get_active_physics_engine etc) live.
T1: transient test as-is: drop 0.6, reads at steps 5/12/30/90 (does ANY contact ever fire?).
R: revert to clean stacked state: ground static again, sensorPeriod->default 0.0025.
G1: suspect-GPU: physxScene:enableGPUDynamics False -> drop/settle/read.
S1: + suspect-sleep: physxScene:disableSleeping True (only if still zero).
E1: suspect-engine: switch_physics_engine to PhysX entry (only if still zero).
Q: scene-query sanity: raycast/overlap at contact patch (only if still zero).
X: capture sibling-Contact.create failure reason (cheap, diagnostic).
Stops at first in_contact=True + force in (5,15); ends with confirm read.
"""
import traceback
import inspect

STATE = {"sensor": "/World/S3Cube/contact", "hit": False, "where": None}
CUBE = "/World/S3Cube"
GROUND = "/World/S3Ground"


def log(m):
    print(m, flush=True)


def xcp(label):
    log("%s TRACEBACK:\n%s" % (label, traceback.format_exc()))


import omni.usd
from pxr import Usd, UsdGeom, Gf, Sdf

try:
    from pxr import UsdPhysics
except Exception:
    UsdPhysics = None
try:
    from pxr import PhysxSchema
except Exception:
    PhysxSchema = None

import isaacsim.core.experimental.utils.app as app_utils

try:
    from isaacsim.core.simulation_manager import SimulationManager as SM
    log("IMP SM OK")
except Exception as e:
    SM = None
    log("IMP SM FAIL %s" % e)

Contact = None
ContactSensor = None
get_iface_fn = None
try:
    import isaacsim.sensors.experimental.physics as _pm
    Contact = getattr(_pm, "Contact", None)
    ContactSensor = getattr(_pm, "ContactSensor", None)
    get_iface_fn = getattr(_pm, "get_contact_sensor_interface", None)
    log("IMP physics-mod OK")
except Exception as e:
    log("IMP physics-mod FAIL %s" % e)

IFACE = {"obj": None}
if get_iface_fn is not None:
    try:
        IFACE["obj"] = get_iface_fn()
        log("IMP iface OK")
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


def sim_state(label):
    try:
        log("%s playing=%s stopped=%s" % (label, app_utils.is_playing(), app_utils.is_stopped()))
    except Exception as e:
        log("%s state ERR %s" % (label, e))
    if SM is not None:
        try:
            log("%s t=%.4f steps=%s dt=%s simulating=%s" % (
                label, SM.get_simulation_time(), SM.get_num_physics_steps(),
                SM.get_physics_dt(), SM.is_simulating()))
        except Exception as e:
            log("%s SM ERR %s" % (label, e))


def cube_z(label):
    try:
        import omni.physx as _px
        r = _px.get_physx_interface().get_rigidbody_transformation(CUBE)
        log("%s cube physx pos=%s" % (label, r.get("position") if isinstance(r, dict) else r))
    except Exception as e:
        log("%s cube physx ERR %s" % (label, e))


def read_sensor(label):
    sp = STATE["sensor"]
    try:
        s = ContactSensor(sp)
        d = s.get_data()
        raw = s.get_raw_data()
        log("READ %s in_contact=%s force=%s n=%s t=%s step=%s rawlen=%d" % (
            label, d.get("in_contact"), d.get("force"), d.get("number_of_contacts"),
            d.get("time"), d.get("physics_step"), len(raw)))
        if raw:
            log("READ %s raw[0]=%s" % (label, str(raw[0])[:600]))
        try:
            import math as _m
            f = d.get("force")
            fmag = abs(f) if isinstance(f, (int, float)) else None
            if d.get("in_contact") is True and fmag is not None and 5.0 < fmag < 15.0 \
                    and not STATE["hit"]:
                STATE["hit"] = True
                STATE["where"] = label
                log("READ %s *** SUCCESS fmag=%.4f ***" % (label, fmag))
        except Exception as e:
            log("READ %s success-check ERR %s" % (label, e))
        return d
    except Exception as e:
        log("READ %s FAILED %s" % (label, e))
        xcp("READ %s" % label)
        return None


def stop_all(label):
    try:
        app_utils.stop()
        app_utils.update_app(steps=5)
    except Exception as e:
        log("%s stop ERR %s" % (label, e))


def drop_play(label, drop_z=0.6):
    try:
        UsdGeom.XformCommonAPI(stage.GetPrimAtPath(CUBE)).SetTranslate(Gf.Vec3d(0, 0, drop_z))
    except Exception as e:
        log("%s drop ERR %s" % (label, e))
    try:
        app_utils.play()
    except Exception as e:
        log("%s play ERR %s" % (label, e))


def steps(n, label):
    try:
        app_utils.update_app(steps=n)
    except Exception as e:
        log("%s steps ERR %s" % (label, e))
    sim_state(label)
    cube_z(label)


def set_scene_attr(label, name, value):
    try:
        prim = stage.GetPrimAtPath("/World/PhysicsScene")
        a = prim.GetAttribute(name)
        if a and a.IsValid():
            before = a.Get()
            a.Set(value)
            log("%s scene %s %s -> %s OK" % (label, name, before, a.Get()))
            return True
        log("%s scene %s INVALID attr" % (label, name))
        return False
    except Exception as e:
        log("%s scene %s ERR %s" % (label, name, e))
        xcp(label)
        return False


# ================= E0 engine interrogation =================
log("E0 ==== engine/solver interrogation ====")
sim_state("E0")
if not app_utils.is_playing():
    try:
        app_utils.play()
        app_utils.update_app(steps=5)
    except Exception as e:
        log("E0 play ERR %s" % e)
if SM is not None:
    for fn in ("get_active_physics_engine", "get_available_physics_engines",
               "get_default_engine", "get_solver_type", "get_broadphase_type",
               "is_gpu_dynamics_enabled", "get_physics_scenes", "get_default_physics_scene"):
        try:
            log("E0 SM.%s() = %s" % (fn, getattr(SM, fn)()))
        except Exception as e:
            log("E0 SM.%s() ERR %s" % (fn, e))
    for fn in ("switch_physics_engine", "set_solver_type", "set_broadphase_type",
               "enable_gpu_dynamics", "setup_simulation"):
        try:
            log("E0 sig SM.%s = %s" % (fn, inspect.signature(getattr(SM, fn))))
        except Exception as e:
            log("E0 sig SM.%s ERR %s" % (fn, e))
log("E0 cube schemas=%s" % schemas(CUBE))
log("E0 ground schemas=%s" % schemas(GROUND))
log("E0 scene schemas=%s" % schemas("/World/PhysicsScene"))

# ================= T1 transient test =================
log("T1 ==== transient: does ANY contact ever fire? ====")
stop_all("T1")
drop_play("T1", 0.6)
steps(5, "T1-s5")
read_sensor("T1-s5")
steps(7, "T1-s12-impact?")
read_sensor("T1-s12")
steps(18, "T1-s30")
read_sensor("T1-s30")
steps(60, "T1-s90-rest")
read_sensor("T1-s90")

# ================= X sibling-create failure reason =================
log("X ==== sibling Contact.create failure reason ====")
stop_all("X")
try:
    Contact.create(path="/World/S3Contact", min_threshold=0.0, max_threshold=1e6)
    log("X sibling create unexpectedly OK; removing")
    try:
        stage.RemovePrim(Sdf.Path("/World/S3Contact"))
    except Exception as e:
        log("X cleanup ERR %s" % e)
except Exception as e:
    log("X sibling create FAILED as before: %s: %s" % (type(e).__name__, e))
    xcp("X")

# ================= R revert to clean stacked state =================
log("R ==== revert: ground static, sensorPeriod default ====")
try:
    g = stage.GetPrimAtPath(GROUND)
    r = g.RemoveAPI("PhysicsRigidBodyAPI")
    log("R ground RemoveAPI(PhysicsRigidBodyAPI) -> %s; schemas=%s" % (r, schemas(GROUND)))
except Exception as e:
    log("R ground revert ERR %s" % e)
    xcp("R")
try:
    sp = stage.GetPrimAtPath(STATE["sensor"])
    a = sp.GetAttribute("sensorPeriod")
    if a and a.IsValid():
        a.Set(0.0025)
        log("R sensorPeriod -> %s" % a.Get())
    log("R sensor radius=%s threshold=%s" % (
        sp.GetAttribute("radius").Get(), sp.GetAttribute("threshold").Get()))
except Exception as e:
    log("R sensor revert ERR %s" % e)
try:
    c = stage.GetPrimAtPath(CUBE)
    log("R cube report threshold=%s" % c.GetAttribute("physxContactReport:threshold").Get())
    gr = stage.GetPrimAtPath(GROUND)
    log("R ground report threshold=%s" % gr.GetAttribute("physxContactReport:threshold").Get())
except Exception as e:
    log("R threshold-read ERR %s" % e)
log("R scene schemas=%s (Newton NOT restored)" % schemas("/World/PhysicsScene"))

# ================= G1 GPU dynamics OFF =================
if not STATE["hit"]:
    log("G1 ==== enableGPUDynamics False ====")
    stop_all("G1")
    set_scene_attr("G1", "physxScene:enableGPUDynamics", False)
    drop_play("G1", 0.6)
    steps(12, "G1-s12-impact?")
    read_sensor("G1-s12")
    steps(78, "G1-s90-rest")
    read_sensor("G1-s90")
else:
    log("G1 SKIP success at %s" % STATE["where"])

# ================= S1 + disable sleeping =================
if not STATE["hit"]:
    log("S1 ==== + disableSleeping True ====")
    stop_all("S1")
    set_scene_attr("S1", "physxScene:disableSleeping", True)
    drop_play("S1", 0.6)
    steps(12, "S1-s12-impact?")
    read_sensor("S1-s12")
    steps(78, "S1-s90-rest")
    read_sensor("S1-s90")
else:
    log("S1 SKIP success at %s" % STATE["where"])

# ================= E1 engine switch =================
if not STATE["hit"]:
    log("E1 ==== switch physics engine ====")
    stop_all("E1")
    if SM is not None:
        try:
            avail = SM.get_available_physics_engines()
            log("E1 available=%s active=%s default=%s" % (
                avail, SM.get_active_physics_engine(), SM.get_default_engine()))
            target = None
            for cand in avail:
                if "physx" in str(cand).lower():
                    target = cand
                    break
            if target is not None and str(SM.get_active_physics_engine()).lower() != str(target).lower():
                log("E1 switching to %s" % target)
                try:
                    SM.switch_physics_engine(target)
                    log("E1 switch OK active now=%s" % SM.get_active_physics_engine())
                except Exception as e:
                    log("E1 switch FAILED %s" % e)
                    xcp("E1")
            else:
                log("E1 no switch (already PhysX or no PhysX entry)")
        except Exception as e:
            log("E1 interrogation ERR %s" % e)
            xcp("E1")
    drop_play("E1", 0.6)
    steps(12, "E1-s12-impact?")
    read_sensor("E1-s12")
    steps(78, "E1-s90-rest")
    read_sensor("E1-s90")
else:
    log("E1 SKIP success at %s" % STATE["where"])

# ================= Q scene-query sanity =================
if not STATE["hit"]:
    log("Q ==== scene-query sanity at contact patch ====")
    try:
        import omni.physx as _px
        q = _px.get_physx_scene_query_interface()
        log("Q query-iface=%s" % q)
        log("Q query dir=%s" % sorted([n for n in dir(q) if not n.startswith("_")])[:40])
        # raycast down through the cube: expect hit at z~0 (ground top) from z=2
        try:
            hit = q.raycast_closest((0, 0, 2.0), (0, 0, -1), 10.0)
            log("Q raycast down = %s" % str(hit)[:600])
        except Exception as e:
            log("Q raycast ERR %s" % e)
            xcp("Q")
        # overlap box straddling the contact plane z=0
        try:
            ov = q.overlap_box((0.25, 0.25, 0.25), (0, 0, 0.05), (0, 0, 0, 1))
            log("Q overlap_box = %s" % str(ov)[:600])
        except Exception as e:
            log("Q overlap ERR %s" % e)
            xcp("Q")
    except Exception as e:
        log("Q iface ERR %s" % e)
        xcp("Q")
else:
    log("Q SKIP success at %s" % STATE["where"])

log("FINAL SUCCESS=%s where=%s sensor=%s" % (STATE["hit"], STATE["where"], STATE["sensor"]))
if STATE["hit"] and app_utils.is_playing():
    try:
        app_utils.update_app(steps=60)
    except Exception as e:
        log("FINAL extra-settle ERR %s" % (label, e))
    sim_state("FINAL-confirm")
    read_sensor("FINAL-confirm")
log("MEGA3-DONE")
