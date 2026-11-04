import json
import traceback
try:
    import omni.usd
    import omni.timeline
    from pxr import UsdGeom, UsdPhysics, Gf
    stage = omni.usd.get_context().get_stage()
    out = {"stage_valid": bool(stage), "stage_url": None, "tree": [], "counts": {}, "bots": [], "blocks": [], "grasp_joints": [], "hinges": [], "timeline": {}}
    if stage is not None:
        try:
            out["stage_url"] = str(stage.GetRootLayer().GetIdentifier())
        except Exception as e:
            out["stage_url"] = f"<err {e}>"
        # (1) recursive list /World depth 4
        def prim_type(p):
            try:
                return str(p.GetTypeName())
            except Exception:
                return "?"
        def walk(path_str, depth, max_depth, acc):
            prim = stage.GetPrimAtPath(path_str)
            if not prim or not prim.IsValid():
                acc.append({"path": path_str, "valid": False})
                return
            acc.append({"path": path_str, "type": prim_type(prim), "depth": depth, "valid": True})
            if depth >= max_depth:
                return
            for ch in prim.GetChildren():
                walk(str(ch.GetPath()), depth + 1, max_depth, acc)
        tree = []
        w = stage.GetPrimAtPath("/World")
        if w and w.IsValid():
            walk("/World", 0, 4, tree)
        else:
            tree.append({"path": "/World", "valid": False})
        out["tree"] = tree
        paths = [t["path"] for t in tree if t.get("valid")]
        # counts (substring match on path)
        out["counts"] = {
            "M4Bot": sum(1 for p in paths if "M4Bot" in p),
            "M4Block": sum(1 for p in paths if "M4Block" in p),
            "GraspJoint": sum(1 for p in paths if "GraspJoint" in p),
            "total_valid": len(paths),
        }
        # helper: world pose via USD (Default time, flag stale-vs-physics)
        xc = UsdGeom.XformCache()
        def world_pose(prim):
            try:
                m = xc.GetLocalToWorldTransform(prim)
                tr = m.ExtractTranslation()
                return [float(tr[0]), float(tr[1]), float(tr[2])]
            except Exception as e:
                return f"<err {e}>"
        def phys_apis(prim):
            apis = []
            try:
                apis = list(prim.GetAppliedSchemas())
            except Exception:
                pass
            flags = {}
            for name, cls in [("RigidBodyAPI", UsdPhysics.RigidBodyAPI), ("ArticulationRootAPI", UsdPhysics.ArticulationRootAPI), ("CollisionAPI", UsdPhysics.CollisionAPI), ("DriveAPI_angular", UsdPhysics.DriveAPI), ("RevoluteJoint", UsdPhysics.RevoluteJoint), ("FixedJoint", UsdPhysics.FixedJoint)]:
                try:
                    flags[name] = bool(prim.HasAPI(cls))
                except Exception as e:
                    flags[name] = f"<err {e}>"
            return {"applied": apis, "flags": flags}
        # (2) each M4Bot-path prim detail: report top-level bots (depth<=2 containing M4Bot) + full list
        bot_paths = [p for p in paths if "M4Bot" in p]
        # top-level bot roots: shortest paths (fewest '/'-separated elements) containing M4Bot
        roots = sorted(set(bot_paths), key=lambda p: (p.count("/"), p))
        # keep only those that are not nested under another bot path
        top = []
        for r in roots:
            if not any(r != t and r.startswith(t + "/") for t in top):
                top.append(r)
        for bp in top[:10]:
            prim = stage.GetPrimAtPath(bp)
            if not prim or not prim.IsValid():
                out["bots"].append({"path": bp, "valid": False})
                continue
            kids = [{"path": str(c.GetPath()), "name": str(c.GetName()), "type": prim_type(c)} for c in prim.GetChildren()]
            out["bots"].append({"path": bp, "type": prim_type(prim), "world_pos_usd_default": world_pose(prim), "physics": phys_apis(prim), "children": kids, "child_count": len(kids)})
        out["bot_path_all"] = bot_paths
        # (3a) M4Block poses
        for bp in [p for p in paths if "M4Block" in p][:10]:
            prim = stage.GetPrimAtPath(bp)
            if not prim or not prim.IsValid():
                out["blocks"].append({"path": bp, "valid": False})
                continue
            kids = [{"path": str(c.GetPath()), "type": prim_type(c)} for c in prim.GetChildren()]
            out["blocks"].append({"path": bp, "type": prim_type(prim), "world_pos_usd_default": world_pose(prim), "physics": phys_apis(prim), "children": kids})
        # (3b) Hinge targets: search Hinge1/2 under each top bot + /World-level fallbacks
        hinge_paths = [p for p in paths if "Hinge1" in p or "Hinge2" in p]
        for hp in hinge_paths[:10]:
            prim = stage.GetPrimAtPath(hp)
            d = {"path": hp, "valid": bool(prim and prim.IsValid()), "type": prim_type(prim) if prim else "?"}
            if prim and prim.IsValid():
                for attr in ["drive:angular:physics:targetPosition", "drive:angular:physics:targetVelocity", "drive:angular:physics:damping", "drive:angular:physics:stiffness", "drive:angular:physics:maxForce", "state:angular:physics:position", "state:angular:physics:velocity"]:
                    try:
                        a = prim.GetAttribute(attr)
                        d[attr] = a.Get() if a and a.IsValid() else None
                    except Exception as e:
                        d[attr] = f"<err {e}>"
                d["physics"] = phys_apis(prim)
            out["hinges"].append(d)
        # (3c) GraspJoint presence: tree matches + canonical path check
        for gp in [p for p in paths if "GraspJoint" in p][:10]:
            prim = stage.GetPrimAtPath(gp)
            out["grasp_joints"].append({"path": gp, "valid": bool(prim and prim.IsValid()), "type": prim_type(prim) if prim else "?", "physics": phys_apis(prim) if prim else {}})
        canon = stage.GetPrimAtPath("/World/M4GraspJoint")
        out["M4GraspJoint_canonical_valid"] = bool(canon and canon.IsValid())
        if canon and canon.IsValid():
            out["M4GraspJoint_canonical_type"] = prim_type(canon)
        # (4) timeline reads only
        try:
            tl = omni.timeline.get_timeline_interface()
            out["timeline"] = {"current_time": tl.get_current_time(), "is_playing": tl.is_playing(), "is_stopped": tl.is_stopped() if hasattr(tl, "is_stopped") else "n/a", "is_paused": tl.is_paused() if hasattr(tl, "is_paused") else "n/a"}
        except Exception as e:
            out["timeline"] = {"error": str(e)}
    print("PROBE_JSON:" + json.dumps(out, default=str))
except Exception:
    print("PROBE_JSON:" + json.dumps({"fatal": traceback.format_exc()}))
