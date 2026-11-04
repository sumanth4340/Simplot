"""Co-validate (runs LOCALLY): sense must cover every physics scene.

Loads co_sense_pN.json snapshots and asserts the probe reports each
drill's bodies, physics flags, and (P3) joint anchors/sites exactly.
"""
import json
import sys

EVDIR = "action-reasoner/skills/workspace-sense/evidence/"
TOL = 1e-3


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def _snap(name):
    env = _load(EVDIR + name)
    if env.get("status") != "ok":
        raise RuntimeError("%s status=%r" % (name, env.get("status")))
    return json.loads(env["output"])


def _close(a, b):
    return abs(a - b) <= TOL


EXPECT = {
    "p1": {"body": ("/World/P1Cube", [0, 0, 2], 1.0),
           "static": "/World/P1Ground"},
    "p2": {"body": ("/World/P2Cube", [0, 0, 2], 1.0),
           "static": "/World/P2Ground"},
    "p4": {"bodies": [(("/World/P4A", [0, 0, 0.5], 1.0)),
                      ("/World/P4B", [0, 0, 2], 1.0)],
           "static": "/World/P4Ground"},
}


def _check_body(snap, path, pos, mass, fails, tag):
    recs = [p for p in snap["prims"] if p["path"] == path]
    if not recs:
        fails.append("%s: %s missing" % (tag, path))
        return
    r = recs[0]
    if r.get("pos") is None or any(not _close(g, w) for g, w in zip(r["pos"], pos)):
        fails.append("%s: %s pos=%r want %r" % (tag, path, r.get("pos"), pos))
    if r.get("rigid") is not True:
        fails.append("%s: %s rigid=%r" % (tag, path, r.get("rigid")))
    if r.get("mass") is None or not _close(r["mass"], mass):
        fails.append("%s: %s mass=%r" % (tag, path, r.get("mass")))
    if r.get("collision") is not True:
        fails.append("%s: %s collision=%r" % (tag, path, r.get("collision")))


def _check_static(snap, path, fails, tag):
    recs = [p for p in snap["prims"] if p["path"] == path]
    if not recs:
        fails.append("%s: %s missing" % (tag, path))
        return
    r = recs[0]
    if r.get("rigid") is not False or r.get("collision") is not True:
        fails.append("%s: %s rigid=%r collision=%r"
                     % (tag, path, r.get("rigid"), r.get("collision")))


def main():
    fails = []
    try:
        snaps = {k: _snap("co_sense_%s.json" % k) for k in ("p1", "p2", "p3", "p4")}
    except RuntimeError as exc:
        print("CO-FAIL\n  - %s" % exc)
        return 1
    for tag, s in snaps.items():
        if s.get("physics_scene") != "/World/PhysicsScene":
            fails.append("%s: physics_scene=%r" % (tag, s.get("physics_scene")))
        if s.get("errors"):
            fails.append("%s: probe errors=%r" % (tag, s["errors"][:2]))
    _check_body(snaps["p1"], *EXPECT["p1"]["body"], fails, "p1")
    _check_static(snaps["p1"], EXPECT["p1"]["static"], fails, "p1")
    _check_body(snaps["p2"], *EXPECT["p2"]["body"], fails, "p2")
    _check_static(snaps["p2"], EXPECT["p2"]["static"], fails, "p2")
    for path, pos, mass in EXPECT["p4"]["bodies"]:
        _check_body(snaps["p4"], path, pos, mass, fails, "p4")
    _check_static(snaps["p4"], EXPECT["p4"]["static"], fails, "p4")
    s3 = snaps["p3"]
    _check_body(s3, "/World/P3Arm", [0, 0, 1.5], 1.0, fails, "p3")
    _check_static(s3, "/World/P3Base", fails, "p3")
    js = [j for j in s3["joints"] if j["path"] == "/World/P3Hinge"]
    if not js:
        fails.append("p3: hinge joint missing")
    else:
        j = js[0]
        if j.get("type") != "PhysicsRevoluteJoint":
            fails.append("p3: hinge type=%r" % (j.get("type"),))
        if j.get("body0") != ["/World/P3Base"] or j.get("body1") != ["/World/P3Arm"]:
            fails.append("p3: hinge bodies=%r/%r" % (j.get("body0"), j.get("body1")))
        for k, want in (("anchor0_pos", [0, 0, 0.5]), ("anchor1_pos", [0, 0, -0.5])):
            got = j.get(k)
            if got is None or any(not _close(g, w) for g, w in zip(got, want)):
                fails.append("p3: %s=%r want %r" % (k, got, want))
        if str(j.get("axis", "")).lower() != "z":
            fails.append("p3: axis=%r" % (j.get("axis"),))
        if j.get("anchor0_site") != "midX+midY+maxZ":
            fails.append("p3: site0=%r" % (j.get("anchor0_site"),))
        if j.get("anchor1_site") != "midX+midY+minZ":
            fails.append("p3: site1=%r" % (j.get("anchor1_site"),))
    print("scenes sensed: p1=%d p2=%d p3=%d p4=%d prims"
          % tuple(len(snaps[k]["prims"]) for k in ("p1", "p2", "p3", "p4")))
    if fails:
        print("CO-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("CO-PASS")
    return 0


sys.exit(main())
