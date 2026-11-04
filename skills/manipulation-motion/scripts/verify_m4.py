"""Verify M4 (runs LOCALLY): all grasp/lift/place gates green."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/manipulation-motion/evidence/"


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
    a = _load(EVDIR + "m4a_run.json")
    b = _load(EVDIR + "m4b_run.json")
    for name, run in (("m4a", a), ("m4b", b)):
        if run.get("status") != "ok":
            print("M4-FAIL\n  - %s status=%r err=%r"
                  % (name, run.get("status"), run.get("evalue")))
            return 1
    m = re.search(r"M4A-REPORT err_pd=([-\d.]+) err_a=([-\d.]+) "
                  r"err_t=([-\d.]+) err_g=([-\d.]+) g0=([-\d.]+) "
                  r"g0b=([-\d.]+) attached=(\w+)", a.get("output", ""))
    if not m:
        print("M4-FAIL\n  - m4a no report")
        return 1
    pd, ea, et, eg, g0, g0b = (float(m.group(i)) for i in range(1, 7))
    att = m.group(7) == "True"
    print("m4a: err_pd=%.4f err_a=%.4f err_t=%.4f err_g=%.4f g0=%.4f "
          "g0b=%.4f attached=%s" % (pd, ea, et, eg, g0, g0b, att))
    for n, v in (("err_pd", pd), ("err_a", ea), ("err_t", et),
                 ("err_g", eg)):
        if v >= 0.02:
            fails.append("%s=%.4f" % (n, v))
    if g0b >= 0.02:
        fails.append("grasp g0b=%.4f" % (g0b,))
    if not att:
        fails.append("not attached")
    m = re.search(r"M4B-REPORT zmax=([-\d.]+) err_p=([-\d.]+) "
                  r"pxy=([-\d.]+) pz=([-\d.]+) spd=([-\d.]+) "
                  r"released=(\w+)", b.get("output", ""))
    if not m:
        print("M4-FAIL\n  - m4b no report")
        return 1
    zmax, err_p, pxy, pz, spd = (float(m.group(i)) for i in range(1, 6))
    rel = m.group(6) == "True"
    print("m4b: zmax=%.4f err_p=%.4f pxy=%.4f pz=%.4f spd=%.4f "
          "released=%s" % (zmax, err_p, pxy, pz, spd, rel))
    if zmax <= 1.0:
        fails.append("lift zmax=%.4f" % (zmax,))
    if err_p >= 0.02:
        fails.append("err_p=%.4f" % (err_p,))
    if pxy >= 0.05:
        fails.append("place pxy=%.4f" % (pxy,))
    if pz >= 0.03:
        fails.append("place pz=%.4f" % (pz,))
    if spd >= 0.05:
        fails.append("place spd=%.4f" % (spd,))
    if not rel:
        fails.append("not released")
    if fails:
        print("M4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M4-PASS")
    return 0


sys.exit(main())
