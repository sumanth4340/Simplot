"""Verify S2 (runs LOCALLY): 6 typed prims created exact, deleted clean."""
import json
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
TOL = 1e-3
EXPECT = {
    "/World/S2_Cube": ("Cube", [1.0, 1.0, 1.0]),
    "/World/S2_Sphere": ("Sphere", [1.0, 1.0, 1.0]),
    "/World/S2_Cyl": ("Cylinder", [0.5, 0.5, 2.0]),
    "/World/S2_Cone": ("Cone", [1.0, 1.0, 1.0]),
    "/World/S2_Plane": ("Plane", [4.0, 2.0, 0.0]),
    "/World/S2_Mesh": ("Mesh", [1.0, 1.0, 0.0]),
}


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


def main():
    fails = []
    try:
        sa = _snap("s2_senseA.json")
        sb = _snap("s2_senseB.json")
        sc = _snap("s2_senseC.json")
    except RuntimeError as exc:
        print("S2-FAIL\n  - %s" % exc)
        return 1
    na, nb, nc = (len(s["prims"]) for s in (sa, sb, sc))
    print("counts: base=%d created=%d deleted=%d" % (na, nb, nc))
    if nb != na + 6:
        fails.append("created=%d, want base+6=%d" % (nb, na + 6))
    if nc != na:
        fails.append("after delete=%d, want base=%d" % (nc, na))
    got = {p["path"]: p for p in sb["prims"]}
    for path, (want_type, want_size) in EXPECT.items():
        r = got.get(path)
        if r is None:
            fails.append("%s missing" % path)
            continue
        if r.get("type") != want_type:
            fails.append("%s type=%r" % (path, r.get("type")))
        size = r.get("size")
        if size is None or any(abs(g - w) > TOL for g, w in zip(size, want_size)):
            fails.append("%s size=%r want %r" % (path, size, want_size))
    left = [p for p in sc["prims"] if p["path"] in EXPECT]
    if left:
        fails.append("leftovers: %r" % ([p["path"] for p in left],))
    if fails:
        print("S2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("S2-PASS")
    return 0


sys.exit(main())
