"""Verify X2 (runs LOCALLY): imported asset simulates stably."""
import json
import re
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
    run = _load(EVDIR + "x2_run.json")
    if run.get("status") != "ok":
        print("X2-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"X2-REPORT z0=([-\d.]+) z1=([-\d.]+) t0=([-\d.]+) "
                  r"t1=([-\d.]+) rigid=(\w+) joint=(\w+)", run.get("output", ""))
    if not m:
        print("X2-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    z0, z1, t0, t1 = (float(m.group(i)) for i in range(1, 5))
    rigid, joint = m.group(5) == "True", m.group(6) == "True"
    print("report: z0=%.4f z1=%.4f dt=%.3f rigid=%s joint=%s"
          % (z0, z1, t1 - t0, rigid, joint))
    if not t1 > t0:
        fails.append("no time advance")
    if abs(z1 - z0) > 0.2:
        fails.append("base moved %.4f -> %.4f" % (z0, z1))
    if not rigid:
        fails.append("imported base not rigid")
    if not joint:
        fails.append("shoulder joint invalid")
    snap = json.loads(_load(EVDIR + "x2_sense.json")["output"])
    js = [j for j in snap["joints"] if j["path"].endswith("/shoulder")]
    if not js:
        fails.append("shoulder not sensed")
    else:
        j = js[0]
        print("shoulder: type=%s bodies=%s/%s axis=%s sites=%s/%s" % (
            j.get("type"), j.get("body0"), j.get("body1"), j.get("axis"),
            j.get("anchor0_site"), j.get("anchor1_site")))
        if j.get("type") != "PhysicsRevoluteJoint":
            fails.append("shoulder type=%r" % (j.get("type"),))
        if not j.get("body0") or not j.get("body1"):
            fails.append("shoulder bodies missing")
    if fails:
        print("X2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("X2-PASS")
    return 0


sys.exit(main())
