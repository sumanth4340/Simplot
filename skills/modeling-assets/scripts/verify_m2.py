"""Verify M2 (runs LOCALLY): URDF arm imported with links + joint."""
import glob
import json
import re
import sys

EVDIR = "action-reasoner/skills/modeling-assets/evidence/"
OUTDIR = "action-reasoner/skills/modeling-assets/assets/m2_out"


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
    run = _load(EVDIR + "m2_run.json")
    if run.get("status") != "ok":
        print("M2-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"M2-REPORT out=(\S+) root=(\w+) joints=(\S*) base=(\w+) arm=(\w+)",
                  run.get("output", ""))
    if not m:
        print("M2-FAIL\n  - no report: %r" % (run.get("output", "")[:400],))
        return 1
    out, root, joints, base, arm = (m.group(1), m.group(2) == "True",
                                    m.group(3), m.group(4) == "True",
                                    m.group(5) == "True")
    print("report: out=%s root=%s joints=%s base=%s arm=%s"
          % (out, root, joints, base, arm))
    if not root:
        fails.append("root /m2_bot invalid")
    if "shoulder" not in joints:
        fails.append("shoulder missing from joints=%r" % (joints,))
    if not base or not arm:
        fails.append("links base=%s arm=%s" % (base, arm))
    usds = glob.glob(OUTDIR + "/**/*.usd*", recursive=True)
    print("usd outputs: %d files" % len(usds))
    if not usds:
        fails.append("no .usd output under %s" % OUTDIR)
    snap = json.loads(_load(EVDIR + "m2_sense.json")["output"])
    got = {p["path"]: p for p in snap["prims"]}
    jr = [p for p in got if "shoulder" in p and "Joint" in got[p]["type"]]
    print("sense joints: %r" % (jr,))
    if not jr:
        fails.append("shoulder joint missing from sense")
    elif got[jr[0]]["type"] != "PhysicsRevoluteJoint":
        fails.append("shoulder type=%r" % (got[jr[0]]["type"],))
    for link in ("/World/M2Bot/Geometry/base", "/World/M2Bot/Geometry/base/arm"):
        if link not in got:
            fails.append("%s missing from sense" % link)
    if fails:
        print("M2-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M2-PASS")
    return 0


sys.exit(main())
