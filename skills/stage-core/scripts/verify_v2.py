"""Verify V2 (runs LOCALLY): composed scene exact before + after save."""
import json
import os
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
USD = "action-reasoner/skills/stage-core/stages/v2.usd"
TOL = 1e-3
EXPECT = {
    "/World/VBase": ("Cube", [0.0, 0.0, 0.5], [2.5, 2.5, 2.5]),
    "/World/V2Direct": ("Sphere", [3.0, 0.0, 0.5], [1.0, 1.0, 1.0]),
    "/World/V2Widget/Box": ("Cube", None, [4.0, 4.0, 4.0]),
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


def _check(snap, tag, fails):
    got = {p["path"]: p for p in snap["prims"]}
    for path, (want_type, want_pos, want_size) in EXPECT.items():
        r = got.get(path)
        if r is None:
            fails.append("%s: %s missing" % (tag, path))
            continue
        if r.get("type") != want_type:
            fails.append("%s: %s type=%r" % (tag, path, r.get("type")))
        if want_pos is not None and r.get("pos") != want_pos:
            fails.append("%s: %s pos=%r" % (tag, path, r.get("pos")))
        size = r.get("size")
        if size is None or any(abs(g - w) > TOL for g, w in zip(size, want_size)):
            fails.append("%s: %s size=%r want %r" % (tag, path, size, want_size))


def main():
    fails = []
    try:
        sa = _snap("v2_senseA.json")
        sb = _snap("v2_senseB.json")
        sv = _load(EVDIR + "v2_save.json")
        so = _load(EVDIR + "v2_open.json")
    except RuntimeError as exc:
        print("V2-FAIL\n  - %s" % exc)
        return 1
    if sv.get("status") != "ok":
        fails.append("save failed")
    if so.get("status") != "ok":
        fails.append("open failed")
    if not os.path.exists(USD) or os.path.getsize(USD) == 0:
        fails.append("v2.usd missing/empty")
    _check(sa, "built", fails)
    _check(sb, "reopened", fails)
    if fails:
        print("V2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("V2-PASS")
    return 0


sys.exit(main())
