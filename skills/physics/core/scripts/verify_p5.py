"""Verify P5 (runs LOCALLY): two drop trajectories must match to 1e-4."""
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
    run = _load(EVDIR + "p5_run.json")
    if run.get("status") != "ok":
        print("FAIL: run status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    ts = re.findall(r"P5-TRAJ\d ((?:[-\d.]+,?)+)", run.get("output", ""))
    if len(ts) != 2:
        print("FAIL: want 2 trajectories. output=%r" % (run.get("output", "")[:300],))
        return 1
    t0 = [float(v) for v in ts[0].split(",")]
    t1 = [float(v) for v in ts[1].split(",")]
    diff = max(abs(a - b) for a, b in zip(t0, t1))
    print("traj0=%s" % ts[0])
    print("traj1=%s" % ts[1])
    print("maxdiff=%.6f" % diff)
    fails = []
    if len(t0) != len(t1) or not t0:
        fails.append("trajectory length mismatch")
    if t0[-1] >= t0[0]:
        fails.append("trial 0 did not fall")
    if diff > 1e-4:
        fails.append("maxdiff=%.6f > 1e-4" % diff)
    if fails:
        print("P5-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("P5-PASS")
    return 0


sys.exit(main())
