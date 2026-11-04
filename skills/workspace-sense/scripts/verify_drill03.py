"""Verify Drill 03 (runs LOCALLY): live sensing tracks the fall exactly."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/workspace-sense/evidence/"


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


def _truth(name):
    env = _load(EVDIR + name)
    m = re.search(r"LIVE-TRUTH z=([-\d.]+) vz=([-\dnan.]+) via=(\S+)",
                  env.get("output", ""))
    if not m:
        raise RuntimeError("%s has no truth: %r" % (name, env.get("output", "")[:200]))
    vz = m.group(2)
    return float(m.group(1)), (float("nan") if vz == "nan" else float(vz)), m.group(3)


def main():
    fails = []
    try:
        a = _snap("drill_03_senseA.json")
        b = _snap("drill_03_senseB.json")
        c = _snap("drill_03_senseC.json")
        zb, vzb, via1 = _truth("drill_03_step20.json")
        zc, vzc, via2 = _truth("drill_03_step120.json")
    except RuntimeError as exc:
        print("DRILL03-FAIL\n  - %s" % exc)
        return 1
    print("stepping: 20 via=%s, +100 via=%s" % (via1, via2))
    la = (a.get("live") or {}).get("/World/LiveCube")
    lb = (b.get("live") or {}).get("/World/LiveCube")
    lc = (c.get("live") or {}).get("/World/LiveCube")
    if la is None or lb is None or lc is None:
        print("DRILL03-FAIL\n  - live block missing: A=%s B=%s C=%s"
              % (la is not None, lb is not None, lc is not None))
        return 1
    za, zbp, zcp = la["pos"][2], lb["pos"][2], lc["pos"][2]
    print("sense-live z: A=%.4f B=%.4f C=%.4f | truth: B=%.4f C=%.4f"
          % (za, zbp, zcp, zb, zc))
    print("sense-live vz: B=%r C=%r | truth vz: B=%.4f C=%.4f"
          % (lb.get("linvel"), lc.get("linvel"), vzb, vzc))
    if abs(za - 2.0) > 0.05:
        fails.append("A.z=%.4f, want 2.0 (just played)" % za)
    if not zbp < za - 0.1:
        fails.append("B.z=%.4f did not fall below A.z=%.4f" % (zbp, za))
    if abs(zbp - zb) > 1e-3:
        fails.append("B.z sense=%.4f vs truth=%.4f" % (zbp, zb))
    if lb.get("linvel") is None or not lb["linvel"][2] < -1.0:
        fails.append("B.vz=%r, want < -1 (in flight)" % (lb.get("linvel"),))
    if abs(zcp - 0.5) > 0.1:
        fails.append("C.z=%.4f, want 0.5 (rested)" % zcp)
    if abs(zcp - zc) > 1e-3:
        fails.append("C.z sense=%.4f vs truth=%.4f" % (zcp, zc))
    if lc.get("linvel") is None or abs(lc["linvel"][2]) > 0.3:
        fails.append("C.vz=%r, want ~0 (rested)" % (lc.get("linvel"),))
    if fails:
        print("DRILL03-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("DRILL03-PASS")
    return 0


sys.exit(main())
