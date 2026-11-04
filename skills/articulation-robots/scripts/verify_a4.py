"""Verify A4 (runs LOCALLY): schema overlay complete and valid."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/articulation-robots/evidence/"
WANT_LINKS = {"/World/A4Bot/Base", "/World/A4Bot/Link1", "/World/A4Bot/Link2"}
WANT_JOINTS = {"/World/A4Bot/Hinge1", "/World/A4Bot/Hinge2"}


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
    run = _load(EVDIR + "a4_run.json")
    if run.get("status") != "ok":
        print("A4-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"A4-REPORT robot=(\w+) type=(\w+) links=(\S+) joints=(\S+) "
                  r"bad=(\d+) rootlink=(\S+)", run.get("output", ""))
    if not m:
        print("A4-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    robot, rtype = m.group(1) == "True", m.group(2)
    links = set(m.group(3).split("|"))
    joints = set(m.group(4).split("|"))
    bad, rootlink = int(m.group(5)), m.group(6)
    print("report: robot=%s type=%s links=%d joints=%d bad=%d rootlink=%s"
          % (robot, rtype, len(links), len(joints), bad, rootlink))
    print("  links=%s" % sorted(links))
    print("  joints=%s" % sorted(joints))
    if not robot:
        fails.append("robot API missing")
    if rtype != "Manipulator":
        fails.append("type=%r" % (rtype,))
    if not WANT_LINKS <= links:
        fails.append("links missing %r" % (WANT_LINKS - links,))
    if not WANT_JOINTS <= joints:
        fails.append("joints missing %r" % (WANT_JOINTS - joints,))
    if bad != 0:
        fails.append("invalid relations: %d" % bad)
    if rootlink != "/World/A4Bot/Base":
        fails.append("rootlink=%r" % (rootlink,))
    if fails:
        print("A4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("A4-PASS")
    return 0


sys.exit(main())
