"""Verify M1 (runs LOCALLY): mesh exact bounds + color + point count."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/modeling-assets/evidence/"
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
    fails = []
    run = _load(EVDIR + "m1_run.json")
    if run.get("status") != "ok":
        print("M1-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"M1-REPORT npoints=(\d+) color=([-\d.,]+)", run.get("output", ""))
    if not m:
        print("M1-FAIL\n  - no report: %r" % (run.get("output", "")[:200],))
        return 1
    npoints, color = int(m.group(1)), [float(v) for v in m.group(2).split(",")]
    print("report: npoints=%d color=%s" % (npoints, color))
    if npoints != 8:
        fails.append("npoints=%d" % (npoints,))
    if color != [1.0, 0.0, 0.0]:
        fails.append("color=%r" % (color,))
    snap = json.loads(_load(EVDIR + "m1_sense.json")["output"])
    recs = [p for p in snap["prims"] if p["path"] == "/World/M1Mesh"]
    if not recs:
        fails.append("M1Mesh missing from sense")
    else:
        r = recs[0]
        print("sense: pos=%r size=%r" % (r.get("pos"), r.get("size")))
        if r.get("type") != "Mesh":
            fails.append("type=%r" % (r.get("type"),))
        if r.get("pos") != [0.0, 0.0, 0.25]:
            fails.append("pos=%r" % (r.get("pos"),))
        size = r.get("size")
        if size is None or any(abs(g - w) > TOL for g, w in zip(size, [2.0, 1.0, 0.5])):
            fails.append("size=%r" % (size,))
        mn, mx = r.get("bbox_min"), r.get("bbox_max")
        if mn != [-1.0, -0.5, 0.0] or mx != [1.0, 0.5, 0.5]:
            fails.append("bbox=%r/%r" % (mn, mx))
    if fails:
        print("M1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M1-PASS")
    return 0


sys.exit(main())
