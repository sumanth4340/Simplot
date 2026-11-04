"""Verify M3 (runs LOCALLY): material bound with exact values."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/modeling-assets/evidence/"


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
    run = _load(EVDIR + "m3_run.json")
    if run.get("status") != "ok":
        print("M3-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"M3-REPORT bound=(\S+) diffuse=([-\d.,]+) rough=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("M3-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    bound, dif, rgh = (m.group(1), [float(v) for v in m.group(2).split(",")],
                       float(m.group(3)))
    print("report: bound=%s diffuse=%s rough=%s" % (bound, dif, rgh))
    if bound != "/World/Looks/M3Red":
        fails.append("bound=%r" % (bound,))
    if dif != [1.0, 0.0, 0.0]:
        fails.append("diffuse=%r" % (dif,))
    if rgh != 0.4:
        fails.append("rough=%r" % (rgh,))
    snap = json.loads(_load(EVDIR + "m3_sense.json")["output"])
    paths = {p["path"] for p in snap["prims"]}
    for want in ("/World/M3Cube", "/World/Looks/M3Red",
                 "/World/Looks/M3Red/PBRShader"):
        if want not in paths:
            fails.append("%s missing" % want)
    if fails:
        print("M3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M3-PASS")
    return 0


sys.exit(main())
