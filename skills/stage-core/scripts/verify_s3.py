"""Verify S3 (runs LOCALLY): property matrix exact + transformed bbox."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
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
    run = _load(EVDIR + "s3_run.json")
    if run.get("status") != "ok":
        print("S3-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"S3-REPORT tr=([-\d.,]+) rot=([-\d.,]+) sc=([-\d.,]+) "
                  r"size=([-\d.]+) color=([-\d.,]+) vis1=(\w+) vis2=(\w+) "
                  r"pur1=(\w+) pur2=(\w+) op=([-\d.]+) tag=(\w+)",
                  run.get("output", ""))
    if not m:
        print("S3-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    tr = [float(v) for v in m.group(1).split(",")]
    ro = [float(v) for v in m.group(2).split(",")]
    sc = [float(v) for v in m.group(3).split(",")]
    size, color = float(m.group(4)), [float(v) for v in m.group(5).split(",")]
    vis1, vis2, pur1, pur2, op, tag = (m.group(i) for i in range(6, 12))
    print("report: tr=%s rot=%s sc=%s size=%s color=%s %s/%s %s/%s op=%s tag=%s"
          % (tr, ro, sc, size, color, vis1, vis2, pur1, pur2, op, tag))
    if tr != [1.0, 2.0, 3.0]:
        fails.append("translate %r" % (tr,))
    if ro != [0.0, 0.0, 90.0]:
        fails.append("rotXYZ %r" % (ro,))
    if sc != [2.0, 1.0, 0.5]:
        fails.append("scale %r" % (sc,))
    if size != 2.0:
        fails.append("size %r" % (size,))
    if color != [1.0, 0.0, 0.0]:
        fails.append("color %r" % (color,))
    if (vis1, vis2) != ("invisible", "inherited"):
        fails.append("visibility %s/%s" % (vis1, vis2))
    if (pur1, pur2) != ("guide", "render"):
        fails.append("purpose %s/%s" % (pur1, pur2))
    if float(op) != 0.5:
        fails.append("opacity %r" % (op,))
    if tag != "s3":
        fails.append("custom tag %r" % (tag,))
    snap = json.loads(_load(EVDIR + "s3_sense.json")["output"])
    recs = [p for p in snap["prims"] if p["path"] == "/World/S3Cube"]
    if not recs:
        fails.append("S3Cube missing from sense")
    else:
        r = recs[0]
        print("sense: pos=%r bbox=%r/%r" % (r.get("pos"), r.get("bbox_min"), r.get("bbox_max")))
        if r.get("pos") != [1.0, 2.0, 3.0]:
            fails.append("sense pos=%r" % (r.get("pos"),))
        for k, want in (("bbox_min", [0.0, 0.0, 2.5]), ("bbox_max", [2.0, 4.0, 3.5])):
            got = r.get(k)
            if got is None or any(abs(g - w) > TOL for g, w in zip(got, want)):
                fails.append("sense %s=%r want %r" % (k, got, want))
    if fails:
        print("S3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("S3-PASS")
    return 0


sys.exit(main())
