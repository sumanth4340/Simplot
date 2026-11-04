import json, traceback
try:
    import omni.usd
    from pxr import UsdGeom
    stage = omni.usd.get_context().get_stage()
    out = {"v2": {}, "scan": [], "joint_rels": {}, "poses": {}}
    xc = UsdGeom.XformCache()
    def pose(p):
        try:
            t = xc.GetLocalToWorldTransform(p).ExtractTranslation()
            return [float(t[0]), float(t[1]), float(t[2])]
        except Exception as e:
            return f"<err {e}>"
    # deep walk /World to depth 6 collecting bot/m4-ish paths
    def walk(path, depth, acc):
        prim = stage.GetPrimAtPath(path)
        if not prim or not prim.IsValid():
            return
        acc.append((path, str(prim.GetTypeName()), depth))
        if depth >= 6:
            return
        for c in prim.GetChildren():
            walk(str(c.GetPath()), depth + 1, acc)
    allp = []
    walk("/World", 0, allp)
    out["scan"] = [{"path": p, "type": t, "depth": d} for (p, t, d) in allp if ("bot" in p.lower() or "/M4" in p or "Grasp" in p or "V5" in p or "v5" in p)]
    out["world_children"] = [{"path": p, "type": t} for (p, t, d) in allp if d == 1]
    # M4V2Bot full detail
    v2 = stage.GetPrimAtPath("/World/M4V2Bot")
    if v2 and v2.IsValid():
        sub = []
        walk("/World/M4V2Bot", 0, sub)
        det = {"path": "/World/M4V2Bot", "type": str(v2.GetTypeName()), "world_pos": pose(v2), "applied": list(v2.GetAppliedSchemas()), "subtree": [{"path": p, "type": t, "depth": d} for (p, t, d) in sub]}
        # J0 drive targets (read-only)
        j0 = stage.GetPrimAtPath("/World/M4V2Bot/J0")
        if j0 and j0.IsValid():
            jd = {"type": str(j0.GetTypeName()), "applied": list(j0.GetAppliedSchemas()), "world_pos": pose(j0)}
            for a in ["drive:angular:physics:targetPosition", "drive:angular:physics:targetVelocity", "physics:body0", "physics:body1"]:
                try:
                    attr = j0.GetAttribute(a)
                    jd[a] = attr.Get() if attr and attr.IsValid() else None
                except Exception as e:
                    jd[a] = f"<err {e}>"
            det["J0"] = jd
        l0 = stage.GetPrimAtPath("/World/M4V2Bot/Link0")
        if l0 and l0.IsValid():
            det["Link0"] = {"type": str(l0.GetTypeName()), "applied": list(l0.GetAppliedSchemas()), "world_pos": pose(l0)}
        out["v2"] = det
    else:
        out["v2"] = {"valid": False}
    # M4GraspJoint rel targets (read-only relationship reads)
    gj = stage.GetPrimAtPath("/World/M4GraspJoint")
    if gj and gj.IsValid():
        for r in ["physics:body0", "physics:body1"]:
            try:
                rel = gj.GetRelationship(r)
                out["joint_rels"][r] = [str(t) for t in rel.GetTargets()] if rel and rel.IsValid() else None
            except Exception as e:
                out["joint_rels"][r] = f"<err {e}>"
        try:
            excl = gj.GetAttribute("physics:excludeFromArticulation")
            out["joint_rels"]["excludeFromArticulation"] = excl.Get() if excl and excl.IsValid() else None
        except Exception as e:
            out["joint_rels"]["excludeFromArticulation"] = f"<err {e}>"
    # poses of key V5 prims
    for p in ["/World/M4Bot/Root", "/World/M4Bot/Link1", "/World/M4Bot/Link2", "/World/M4Bot/Link2/GraspSite", "/World/M4Block", "/World/M4ShelfA", "/World/M4ShelfB", "/World/M4Ground"]:
        prim = stage.GetPrimAtPath(p)
        out["poses"][p] = pose(prim) if (prim and prim.IsValid()) else "INVALID"
    print("PROBE_JSON:" + json.dumps(out, default=str))
except Exception:
    print("PROBE_JSON:" + json.dumps({"fatal": traceback.format_exc()}))
