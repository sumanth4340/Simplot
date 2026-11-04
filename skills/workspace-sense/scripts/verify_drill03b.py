"""Verify Drill 03 v2 (runs LOCALLY): live + rest sensing, rigorous.

Phase 1 (hot): mid-play tensor snapshot present, sane, error-free.
Phase 2 (paused): two-body flight/rest positions exact (P5 cross-check).
Phase 3 (in-sim): in-flight velocity + cross-instance agreement.
"""
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


def main():
    fails = []
    try:
        hot = _snap("d3_hot.json")
        s0 = _snap("d3_sense0.json")
        sb = _snap("d3_senseB.json")
        sc = _snap("d3_senseC.json")
        vel = _load(EVDIR + "d3_vel.json")
    except RuntimeError as exc:
        print("DRILL03-FAIL\n  - %s" % exc)
        return 1
    if vel.get("status") != "ok":
        print("DRILL03-FAIL\n  - vel status=%r" % (vel.get("status"),))
        return 1
    # Phase 1: hot tensor snapshot
    hl = (hot.get("live") or {}).get("/World/LiveCube")
    print("hot: live=%s source=%s errors=%r"
          % (hl is not None, (hl or {}).get("source"), hot.get("errors")))
    if hl is None or hl.get("source") != "tensor" or hot.get("errors"):
        fails.append("hot tensor snapshot invalid")
    elif not 0.4 <= hl["pos"][2] <= 2.05:
        fails.append("hot z=%.4f out of [0.4,2.05]" % hl["pos"][2])
    # Phase 2: edit + paused precision
    if s0.get("live") is not None:
        fails.append("sense0 live should be null in edit state")
    lb1 = (sb.get("live") or {}).get("/World/LiveCube")
    lb2 = (sb.get("live") or {}).get("/World/LiveCube2")
    lc1 = (sc.get("live") or {}).get("/World/LiveCube")
    lc2 = (sc.get("live") or {}).get("/World/LiveCube2")
    if None in (lb1, lb2, lc1, lc2):
        fails.append("paused live missing: B1=%s B2=%s C1=%s C2=%s"
                     % tuple(v is not None for v in (lb1, lb2, lc1, lc2)))
    else:
        print("B: cube1 z=%.4f cube2 z=%.4f gap=%.6f"
              % (lb1["pos"][2], lb2["pos"][2], lb2["pos"][2] - lb1["pos"][2]))
        print("C: cube1 z=%.4f cube2 z=%.4f (want 0.5)"
              % (lc1["pos"][2], lc2["pos"][2]))
        if lb1.get("source") != "rest" or lb2.get("source") != "rest":
            fails.append("B source should be rest")
        if not 1.15 < lb1["pos"][2] < 1.6:
            fails.append("B cube1 z=%.4f, want 18-24 steps of fall" % lb1["pos"][2])
        if not 3.15 < lb2["pos"][2] < 3.6:
            fails.append("B cube2 z=%.4f, want 18-24 steps of fall" % lb2["pos"][2])
        if abs((lb2["pos"][2] - lb1["pos"][2]) - 2.0) > 1e-6:
            fails.append("B gap=%.6f, want exactly 2.0 (same fall, both bodies)"
                         % (lb2["pos"][2] - lb1["pos"][2]))
        if abs(lc1["pos"][2] - 0.5) > 0.05 or abs(lc2["pos"][2] - 0.5) > 0.05:
            fails.append("C not rested: %.4f/%.4f" % (lc1["pos"][2], lc2["pos"][2]))
    # Phase 3: velocity proof
    m = re.search(r"VEL-REPORT z=([-\d.]+) vz=([-\d.]+) instdiff=([-\d.]+)",
                  vel.get("output", ""))
    if not m:
        fails.append("no VEL-REPORT: %r" % (vel.get("output", "")[:200],))
    else:
        z, vz, d = float(m.group(1)), float(m.group(2)), float(m.group(3))
        print("vel: z=%.4f vz=%.4f instdiff=%.6f" % (z, vz, d))
        if not 1.15 < z < 1.6:
            fails.append("vel-phase z=%.4f, want 18-24 steps of fall" % z)
        if not -4.0 < vz < -3.1:
            fails.append("vz=%.4f, want 20-24 steps of gravity" % vz)
        if d > 1e-6:
            fails.append("instance diff=%.6f" % d)
    if fails:
        print("DRILL03-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("DRILL03-PASS")
    return 0


sys.exit(main())
