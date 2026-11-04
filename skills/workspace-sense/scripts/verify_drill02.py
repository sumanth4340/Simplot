"""Verify Drill 02 (runs LOCALLY): joint anchors + sites must match truth."""
import json
import sys

EVID = "action-reasoner/skills/workspace-sense/evidence/drill_02_sense.json"
TOL = 1e-3


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def main():
    env = _load(EVID)
    if env.get("status") != "ok":
        print("FAIL: send status=%r" % (env.get("status"),))
        return 1
    snap = json.loads(env["output"])
    fails = []
    joints = [j for j in snap["joints"] if j["path"] == "/World/JointCube_Cyl"]
    if not joints:
        print("FAIL: joint missing; joints=%r errors=%r"
              % ([j["path"] for j in snap["joints"]], snap["errors"][:3]))
        return 1
    j = joints[0]
    print("Joint: %s" % json.dumps(j))
    if j.get("type") != "PhysicsRevoluteJoint":
        fails.append("type: %r" % (j.get("type"),))
    if j.get("body0") != ["/World/JointCube"]:
        fails.append("body0: %r" % (j.get("body0"),))
    if j.get("body1") != ["/World/JointCyl"]:
        fails.append("body1: %r" % (j.get("body1"),))
    for k, want in (("anchor0_pos", [0.5, 0, 0]), ("anchor1_pos", [-0.5, 0, 0])):
        got = j.get(k)
        if got is None or any(abs(g - w) > TOL for g, w in zip(got, want)):
            fails.append("%s: got %r want %r" % (k, got, want))
    if str(j.get("axis", "")).lower() != "x":
        fails.append("axis: %r" % (j.get("axis"),))
    if j.get("anchor0_site") != "maxX+midY+midZ":
        fails.append("anchor0_site: %r" % (j.get("anchor0_site"),))
    if j.get("anchor1_site") != "minX+midY+midZ":
        fails.append("anchor1_site: %r" % (j.get("anchor1_site"),))
    prims = {p["path"]: p for p in snap["prims"]}
    cube = prims.get("/World/JointCube", {})
    if cube.get("rigid") is not True or abs((cube.get("mass") or 0) - 2.0) > TOL:
        fails.append("cube physics: rigid=%r mass=%r" % (cube.get("rigid"), cube.get("mass")))
    if fails:
        print("DRILL02-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("DRILL02-PASS")
    return 0


sys.exit(main())
