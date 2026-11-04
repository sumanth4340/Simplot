"""Verify X4 (runs LOCALLY): one snapshot proves all four masters."""
import json
import sys

EVDIR = "action-reasoner/skills/cross-val/evidence/"


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def main():
    fails = []
    run = _load(EVDIR + "x4_run.json")
    if run.get("status") != "ok":
        print("X4-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    snap = json.loads(_load(EVDIR + "x4_sense.json")["output"])
    got = {p["path"]: p for p in snap["prims"]}
    print("prims sensed: %d joints: %d" % (len(got), len(snap["joints"])))
    cube = got.get("/World/X4Cube")
    if cube is None or cube.get("rigid") is not True or cube.get("mass") != 1.0:
        fails.append("physics cube wrong: %r" % (cube,))
    hj = [j for j in snap["joints"] if j["path"] == "/World/X4Hinge"]
    if not hj:
        fails.append("hinge missing")
    else:
        j = hj[0]
        if (j.get("anchor0_site") != "midX+midY+maxZ"
                or j.get("anchor1_site") != "midX+midY+minZ"):
            fails.append("hinge sites %r/%r" % (j.get("anchor0_site"), j.get("anchor1_site")))
    if "/World/X4Bot/Geometry/base" not in got:
        fails.append("imported arm missing")
    if not any("shoulder" in p for p in got if "Joint" in got[p]["type"]):
        fails.append("imported shoulder missing")
    tri = got.get("/World/X4Tri")
    if tri is None or tri.get("size") != [1.0, 1.0, 0.0]:
        fails.append("mesh wrong: %r" % (tri,))
    if "/World/X4Looks/X4Red" not in got:
        fails.append("material missing")
    envs = [p for p in got if p.startswith("/World/x4envs/env_")]
    if len(envs) != 2:
        fails.append("clones=%d" % (len(envs),))
    if snap.get("physics_scene") != "/World/PhysicsScene":
        fails.append("physics scene missing")
    if fails:
        print("X4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("X4-PASS")
    return 0


sys.exit(main())
