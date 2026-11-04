"""Verify X1 (runs LOCALLY): physics scene survives save/open, drops."""
import json
import os
import re
import sys

EVDIR = "action-reasoner/skills/cross-val/evidence/"
USD = "action-reasoner/skills/cross-val/stages/x1.usd"


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
    run = _load(EVDIR + "x1_run.json")
    if run.get("status") != "ok":
        print("X1-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"X1-REPORT z0=([-\d.]+) z1=([-\d.]+) t0=([-\d.]+) t1=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("X1-FAIL\n  - no report")
        return 1
    z0, z1, t0, t1 = (float(m.group(i)) for i in range(1, 5))
    print("motion: z0=%.4f z1=%.4f dt=%.3f" % (z0, z1, t1 - t0))
    if abs(z0 - 2.0) > 0.05:
        fails.append("z0=%.4f" % z0)
    if abs(z1 - 0.5) > 0.1:
        fails.append("z1=%.4f" % z1)
    if not t1 > t0:
        fails.append("no time advance")
    if not os.path.exists(USD) or os.path.getsize(USD) == 0:
        fails.append("x1.usd missing/empty")
    snap = json.loads(_load(EVDIR + "x1_sense.json")["output"])
    recs = [p for p in snap["prims"] if p["path"] == "/World/X1Cube"]
    if not recs or recs[0].get("rigid") is not True:
        fails.append("XCUBE not rigid post-open")
    if fails:
        print("X1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("X1-PASS")
    return 0


sys.exit(main())
