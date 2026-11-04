"""Verify V1 (runs LOCALLY): 5 kg / 5 m drop matches theory + rest 0.5."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/physics/core/evidence/"


def _load(path):
    for enc in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            with open(path, encoding=enc) as fh:
                return json.load(fh)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return json.load(open(path, encoding="utf-8"))


def main():
    run = _load(EVDIR + "v1_exam.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"V1-TRAJ ((?:[-\d.]+,?)+)", run.get("output", ""))
    if not m:
        print("FAIL: no trajectory. output=%r" % (run.get("output", "")[:300],))
        return 1
    zs = [float(v) for v in m.group(1).split(",")]
    print("traj=%s" % m.group(1))
    fails = []
    if len(zs) != 6:
        fails.append("want 6 samples, got %d" % len(zs))
    elif not 2.0 < zs[1] < 3.5:
        fails.append("z[1]=%.4f in flight, want ~2.82" % zs[1])
    for z in zs[2:]:
        if abs(z - 0.5) > 0.1:
            fails.append("rest sample %.4f, want 0.5" % z)
    if fails:
        print("V1-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("V1-PASS")
    return 0


sys.exit(main())
