"""Verify Drill 01 (runs LOCALLY): sense output must match the known cube."""
import json
import sys

EVID = "action-reasoner/skills/workspace-sense/evidence/drill_01_sense.json"
EXPECT = {"pos": [2.0, -1.0, 0.5], "size": [1.0, 1.0, 1.0], "rigid": False}
TOL = 1e-3


def close(a, b):
    return abs(a - b) <= TOL


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
        print("FAIL: send status=%r result=%r" % (env.get("status"), env.get("evalue")))
        return 1
    snap = json.loads(env["output"])
    recs = [p for p in snap["prims"] if p["path"] == "/World/SenseCube"]
    if not recs:
        print("FAIL: /World/SenseCube missing from snapshot")
        return 1
    rec = recs[0]
    fails = []
    for k in ("pos", "size"):
        got, want = rec.get(k), EXPECT[k]
        if got is None or any(not close(g, w) for g, w in zip(got, want)):
            fails.append("%s: got %r want %r" % (k, got, want))
    if rec.get("rigid") is not EXPECT["rigid"]:
        fails.append("rigid: got %r want %r" % (rec.get("rigid"), EXPECT["rigid"]))
    print("prims sensed: %d joints: %d errors: %r"
          % (len(snap["prims"]), len(snap["joints"]), snap["errors"][:3]))
    print("SenseCube: %s" % json.dumps(rec, indent=None))
    if fails:
        print("DRILL01-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("DRILL01-PASS")
    return 0


sys.exit(main())
