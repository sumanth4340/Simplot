"""Verify A2 (runs LOCALLY): 2 DOFs named, connected, rest ~0."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/articulation-robots/evidence/"


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
    run = _load(EVDIR + "a2_run.json")
    if run.get("status") != "ok":
        print("A2-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"A2-REPORT roots=(\S+) ndof=(\d+) names=(\S+) "
                  r"q0=\[([-\d., eE+]+)\] q1=\[([-\d., eE+]+)\] dt=([-\d.]+)",
                  run.get("output", ""))
    if not m:
        print("A2-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    roots, ndof, names = m.group(1), int(m.group(2)), m.group(3).split(",")
    q0 = [float(v) for v in m.group(4).split(",")]
    q1 = [float(v) for v in m.group(5).split(",")]
    dt = float(m.group(6))
    print("report: roots=%s ndof=%d names=%s q0=%s q1=%s dt=%.3f"
          % (roots, ndof, names, q0, q1, dt))
    if roots != "/World/A2Bot/Base":
        fails.append("roots=%r" % (roots,))
    if ndof != 2:
        fails.append("ndof=%d" % (ndof,))
    if set(names) != {"Hinge1", "Hinge2"}:
        fails.append("names=%r" % (names,))
    if any(abs(v) > 0.05 for v in q0 + q1):
        fails.append("DOFs moved at rest")
    if not dt > 0:
        fails.append("no time advance")
    snap = json.loads(_load(EVDIR + "a2_sense.json")["output"])
    js = {j["path"]: j for j in snap["joints"]}
    for hp, b0, b1 in (("/World/A2Bot/Hinge1", "/World/A2Bot/Base", "/World/A2Bot/Link1"),
                       ("/World/A2Bot/Hinge2", "/World/A2Bot/Link1", "/World/A2Bot/Link2")):
        j = js.get(hp)
        if j is None:
            fails.append("%s missing" % hp)
        elif j.get("body0") != [b0] or j.get("body1") != [b1]:
            fails.append("%s bodies %r/%r" % (hp, j.get("body0"), j.get("body1")))
    if fails:
        print("A2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("A2-PASS")
    return 0


sys.exit(main())
