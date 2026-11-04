"""Verify S1 (runs LOCALLY): stage round-trip exact, .usd on disk."""
import json
import os
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
USD = "action-reasoner/skills/stage-core/stages/s1.usd"


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
        sa = _snap("s1_senseA.json")
        sb = _snap("s1_senseB.json")
        sc = _snap("s1_senseC.json")
        sv = _load(EVDIR + "s1_save.json")
        so = _load(EVDIR + "s1_open.json")
    except RuntimeError as exc:
        print("S1-FAIL\n  - %s" % exc)
        return 1
    na, nb, nc = (len(s["prims"]) for s in (sa, sb, sc))
    print("counts: freshA=%d freshB=%d reopened=%d" % (na, nb, nc))
    if sv.get("status") != "ok":
        fails.append("save failed: %r" % (sv.get("evalue"),))
    if so.get("status") != "ok":
        fails.append("open failed: %r" % (so.get("evalue"),))
    if not os.path.exists(USD) or os.path.getsize(USD) == 0:
        fails.append("usd missing/empty: %s" % USD)
    for tag, s in (("A", sa), ("B", sb)):
        if any(p["path"] == "/World/S1Cube" for p in s["prims"]):
            fails.append("fresh %s contains S1Cube" % tag)
    recs = [p for p in sc["prims"] if p["path"] == "/World/S1Cube"]
    if not recs:
        fails.append("reopened stage missing S1Cube")
    else:
        r = recs[0]
        if r.get("pos") != [1.0, 2.0, 0.5] or r.get("size") != [1.0, 1.0, 1.0]:
            fails.append("S1Cube wrong: pos=%r size=%r" % (r.get("pos"), r.get("size")))
    pathsB = {p["path"] for p in sb["prims"]}
    pathsC = {p["path"] for p in sc["prims"]}
    if not pathsB <= pathsC:
        fails.append("reopened lost prims: %r" % (pathsB - pathsC,))
    extra = sorted(pathsC - pathsB - {"/World/S1Cube"})
    print("auto-added on open: %r" % (extra,))
    if extra and not all(e.startswith("/OmniKit_Viewport_LightRig") for e in extra):
        fails.append("unexpected extra prims: %r" % (extra,))
    if fails:
        print("S1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("S1-PASS")
    return 0


sys.exit(main())
