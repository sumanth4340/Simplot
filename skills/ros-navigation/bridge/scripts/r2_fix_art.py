"""R2 articulation fix (runs INSIDE Isaac Sim via bridge).

Repairs /World/R2Bot built by r2_build.py so PhysX recognizes it as a
2-DOF articulation. Root cause: the base link was kinematic
(physics:kinematicEnabled=true). PhysX excludes kinematic bodies from
articulations, so with J1 rooted at the kinematic base the backend
found zero joints / zero links and the prims Articulation wrapper
returned None for link/joint names.

Repair (in place, idempotent):
  1. base -> dynamic (kinematicEnabled=false)
  2. world-anchored FixedJoint /World/R2Bot/FixedBase -> base, so the
     now-dynamic base stays fixed instead of falling (contributes 0 DOFs)
  3. J1 localPos1 -> (0,-0.2,0) so both joint frames coincide at y=0.5
     (was 0.2 m apart, causing a snap/pop on play)
  4. MassAPI mass=1kg on base/link1/link2 (was unset)
  5. PhysxArticulationAPI on /World/R2Bot (standard overlay)

Run after r2_build.py, before timeline play:
  python isaacsim_send.py --file r2_build.py
  python isaacsim_send.py --file r2_fix_art.py
"""
import omni.usd
from pxr import UsdPhysics, PhysxSchema, Gf

ROOT = "/World/R2Bot"

st = omni.usd.get_context().get_stage()
rp = st.GetPrimAtPath(ROOT)
if not rp.IsValid():
    print("R2-FIX-NO-ROOT (run r2_build.py first)")
else:
    # 5. PhysX articulation overlay on root
    PhysxSchema.PhysxArticulationAPI.Apply(rp)

    # 1+4. dynamic base + masses
    base = st.GetPrimAtPath(ROOT + "/base")
    UsdPhysics.RigidBodyAPI.Get(st, base.GetPath()
                                ).GetKinematicEnabledAttr().Set(False)
    for link in ("base", "link1", "link2"):
        p = st.GetPrimAtPath(ROOT + "/" + link)
        mass = UsdPhysics.MassAPI.Apply(p)
        if mass.GetMassAttr().Get() in (None, 0):
            mass.CreateMassAttr().Set(1.0)

    # 3. coincident J1 frames at y=0.5 (base top / link1 bottom)
    j1 = UsdPhysics.RevoluteJoint.Get(st, ROOT + "/J1")
    j1.GetLocalPos0Attr().Set(Gf.Vec3f(0, 0.25, 0))
    j1.GetLocalPos1Attr().Set(Gf.Vec3f(0, -0.2, 0))

    # 2. world anchor (body0 unset == world frame)
    fb_path = ROOT + "/FixedBase"
    if not st.GetPrimAtPath(fb_path).IsValid():
        fb = UsdPhysics.FixedJoint.Define(st, fb_path)
        fb.GetBody1Rel().SetTargets([base.GetPath()])
        fb.GetLocalPos1Attr().Set(Gf.Vec3f(0, 0, 0))

    kin = base.GetAttribute("physics:kinematicEnabled").Get()
    fb_ok = st.GetPrimAtPath(fb_path).IsValid()
    print("R2-FIX-OK kinematic=%s fixedbase=%s j1pos1=%s" % (
        kin, fb_ok, j1.GetLocalPos1Attr().Get()))
