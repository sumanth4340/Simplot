"""WORKSPACE-SENSE v0.2 — full telemetry snapshot as JSON.

Runs INSIDE Isaac Sim via isaacsim_send.py. No repo imports, Kit/USD only.
Captures: every prim (pose, world bbox, size, physics flags) + every
PhysicsJoint (bodies, local anchors, axis, attachment site label).
v0.2: when playing, `live` maps each rigid body to SIMULATED pose +
velocities via RigidPrim tensors (USD reads are authored-state only).
v0.3: `live` also captured at rest after play (source="rest", clock>0);
source="tensor" while playing. Edit state (clock=0) reports live=null.
"""
import json


def _f(x, n=4):
    try:
        return round(float(x), n)
    except Exception:
        return None


def _site_of(stage, xcache, bcache, body_paths, anchor):
    """Label where a joint anchor sits on its body: maxX+midY+midZ etc.

    Local range is derived from the world bbox minus body translation:
    ComputeLocalBound returns world-frame bounds on this Kit build.
    Rotated bodies get a `rotated:` prefix (bbox inflated, label approximate).
    """
    try:
        if not body_paths or anchor is None:
            return "unknown"
        bprim = stage.GetPrimAtPath(body_paths[0])
        if not bprim or not bprim.IsValid():
            return "unknown"
        mat = xcache.GetLocalToWorldTransform(bprim)
        t = mat.ExtractTranslation()
        q = mat.ExtractRotation().GetQuaternion()
        qi = q.GetImaginary()
        ident = abs(q.GetReal() - 1.0) < 1e-3 and sum(abs(v) for v in qi) < 1e-3
        wrng = bcache.ComputeWorldBound(bprim).ComputeAlignedRange()
        mn, mx = wrng.GetMin(), wrng.GetMax()
        tags = []
        for i, ax in enumerate("XYZ"):
            lo = float(mn[i]) - float(t[i])
            hi = float(mx[i]) - float(t[i])
            a = float(anchor[i])
            span = hi - lo
            tol = max(1e-4, span * 1e-3)
            if abs(a - hi) <= tol:
                tags.append("max" + ax)
            elif abs(a - lo) <= tol:
                tags.append("min" + ax)
            elif abs(a - (lo + hi) / 2) <= tol:
                tags.append("mid" + ax)
            else:
                tags.append("in" + ax)
        label = "+".join(tags)
        return label if ident else "rotated:" + label
    except Exception as exc:
        return "unknown:%r" % (exc,)


def main():
    from pxr import UsdPhysics
    from pxr import Usd, UsdGeom
    import omni.usd
    import isaacsim.core.experimental.utils.app as app_utils

    out = {"prims": [], "joints": [], "timeline": {},
           "physics_scene": None, "errors": []}
    stage = omni.usd.get_context().get_stage()
    if stage is None or not stage:
        out["errors"].append("no stage open")
        print(json.dumps(out))
        return
    try:
        import omni.timeline
        tiface = omni.timeline.get_timeline_interface()
        out["timeline"] = {"playing": bool(app_utils.is_playing()),
                           "t": round(float(tiface.get_current_time()), 3)}
    except Exception as exc:
        out["timeline"] = {"playing": None, "t": None, "error": repr(exc)}
    try:
        tcode = Usd.TimeCode.Default()
        xcache = UsdGeom.XformCache(tcode)
        # "render"/"proxy" purposes are invisible to a ["default"] query;
        # include them (S3 caught this). "guide" stays excluded by design.
        bcache = UsdGeom.BBoxCache(tcode, [UsdGeom.Tokens.default_, "render", "proxy"])
    except Exception as exc:
        out["errors"].append("cache init: %r" % (exc,))
        print(json.dumps(out))
        return

    for prim in stage.Traverse():
        try:
            path = str(prim.GetPath())
            tname = prim.GetTypeName()
            rec = {"path": path, "type": tname}
            try:
                mat = xcache.GetLocalToWorldTransform(prim)
                t = mat.ExtractTranslation()
                q = mat.ExtractRotation().GetQuaternion()
                qi = q.GetImaginary()
                rec["pos"] = [_f(t[0]), _f(t[1]), _f(t[2])]
                rec["quat"] = [_f(q.GetReal()), _f(qi[0]), _f(qi[1]), _f(qi[2])]
            except Exception as exc:
                rec["pose_error"] = repr(exc)
            try:
                rng = bcache.ComputeWorldBound(prim).ComputeAlignedRange()
                mn, mx = rng.GetMin(), rng.GetMax()
                rec["bbox_min"] = [_f(mn[0]), _f(mn[1]), _f(mn[2])]
                rec["bbox_max"] = [_f(mx[0]), _f(mx[1]), _f(mx[2])]
                rec["size"] = [_f(mx[0] - mn[0]), _f(mx[1] - mn[1]), _f(mx[2] - mn[2])]
            except Exception as exc:
                rec["bbox_error"] = repr(exc)
            try:
                rec["rigid"] = bool(prim.HasAPI(UsdPhysics.RigidBodyAPI))
            except Exception:
                rec["rigid"] = None
            try:
                rec["collision"] = bool(prim.HasAPI(UsdPhysics.CollisionAPI))
            except Exception:
                rec["collision"] = None
            try:
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    rb = UsdPhysics.RigidBodyAPI(prim)
                    rec["kinematic"] = bool(rb.GetKinematicEnabledAttr().Get())
                else:
                    rec["kinematic"] = None
            except Exception:
                rec["kinematic"] = None
            try:
                if prim.HasAPI(UsdPhysics.MassAPI):
                    rec["mass"] = _f(UsdPhysics.MassAPI(prim).GetMassAttr().Get())
                else:
                    rec["mass"] = None
            except Exception:
                rec["mass"] = None
            try:
                if UsdPhysics.Scene(prim):
                    out["physics_scene"] = path
            except Exception:
                pass
            out["prims"].append(rec)
            try:
                if "Joint" in tname and tname.startswith("Physics"):
                    j = UsdPhysics.Joint(prim)
                    jrec = {"path": path, "type": tname}
                    try:
                        jrec["body0"] = [str(t) for t in j.GetBody0Rel().GetTargets()]
                    except Exception:
                        jrec["body0"] = []
                    try:
                        jrec["body1"] = [str(t) for t in j.GetBody1Rel().GetTargets()]
                    except Exception:
                        jrec["body1"] = []
                    a0 = a1 = None
                    try:
                        p0 = j.GetLocalPos0Attr().Get()
                        r0 = j.GetLocalRot0Attr().Get()
                        a0 = [float(p0[0]), float(p0[1]), float(p0[2])]
                        jrec["anchor0_pos"] = [_f(a0[0]), _f(a0[1]), _f(a0[2])]
                        i0 = r0.GetImaginary()
                        jrec["anchor0_quat"] = [_f(r0.GetReal()), _f(i0[0]), _f(i0[1]), _f(i0[2])]
                    except Exception as exc:
                        jrec["anchor0_error"] = repr(exc)
                    try:
                        p1 = j.GetLocalPos1Attr().Get()
                        r1 = j.GetLocalRot1Attr().Get()
                        a1 = [float(p1[0]), float(p1[1]), float(p1[2])]
                        jrec["anchor1_pos"] = [_f(a1[0]), _f(a1[1]), _f(a1[2])]
                        i1 = r1.GetImaginary()
                        jrec["anchor1_quat"] = [_f(r1.GetReal()), _f(i1[0]), _f(i1[1]), _f(i1[2])]
                    except Exception as exc:
                        jrec["anchor1_error"] = repr(exc)
                    if tname == "PhysicsRevoluteJoint":
                        try:
                            jrec["axis"] = str(
                                UsdPhysics.RevoluteJoint(prim).GetAxisAttr().Get())
                        except Exception:
                            pass
                    jrec["anchor0_site"] = _site_of(stage, xcache, bcache, jrec["body0"], a0)
                    jrec["anchor1_site"] = _site_of(stage, xcache, bcache, jrec["body1"], a1)
                    out["joints"].append(jrec)
            except Exception as exc:
                out["errors"].append("joint %s: %r" % (path, exc))
        except Exception as exc:
            out["errors"].append("prim skipped: %r" % (exc,))
    rigid_paths = [r["path"] for r in out["prims"] if r.get("rigid") is True]
    out["live"] = None
    playing = out["timeline"].get("playing") is True
    rested = (not playing) and (out["timeline"].get("t") or 0) > 0
    if (playing or rested) and rigid_paths:
        src = "tensor" if playing else "rest"
        try:
            from isaacsim.core.experimental.prims import RigidPrim
            rp = RigidPrim(paths=rigid_paths)
            pos, quat = rp.get_world_poses()
            pos = pos.numpy()
            quat = quat.numpy()
            try:
                lv, av = rp.get_velocities()
                lv, av = lv.numpy(), av.numpy()
            except Exception:
                lv = av = None
            live = {}
            for i, p in enumerate(rigid_paths):
                e = {"source": src,
                     "pos": [_f(pos[i][0]), _f(pos[i][1]), _f(pos[i][2])],
                     "quat": [_f(quat[i][0]), _f(quat[i][1]),
                             _f(quat[i][2]), _f(quat[i][3])]}
                e["linvel"] = ([_f(lv[i][0]), _f(lv[i][1]), _f(lv[i][2])]
                               if lv is not None else None)
                e["angvel"] = ([_f(av[i][0]), _f(av[i][1]), _f(av[i][2])]
                               if av is not None else None)
                live[p] = e
            out["live"] = live
        except Exception as exc:
            out["errors"].append("live: %r" % (exc,))
    print(json.dumps(out))


main()
