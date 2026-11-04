"""Verify S4 (runs LOCALLY): sublayer wins, then reverts; file on disk."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
SUB = "action-reasoner/skills/stage-core/stages/s4_override.usda"


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
    run = _load(EVDIR + "s4_run.json")
    if run.get("status") != "ok":
        print("S4-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"S4-REPORT base=([-\d.]+) over=([-\d.]+) stack0=(\S+) "
                  r"reverted=([-\d.]+) stack1=(\S+)", run.get("output", ""))
    if not m:
        print("S4-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    base, over, stack0, rev, stack1 = (float(m.group(1)), float(m.group(2)),
                                       m.group(3), float(m.group(4)), m.group(5))
    print("report: base=%.1f over=%.1f stack0=%s reverted=%.1f stack1=%s"
          % (base, over, stack0, rev, stack1))
    if base != 1.0:
        fails.append("base=%r" % (base,))
    if over != 3.0:
        fails.append("override did not win: %r" % (over,))
    if "s4_override" not in stack0:
        fails.append("stack top=%r, want s4_override layer" % (stack0,))
    if rev != 1.0:
        fails.append("revert=%r" % (rev,))
    if "s4_base" not in stack1:
        fails.append("revert top=%r, want s4_base layer" % (stack1,))
    for name, wants in (("s4_override.usda", ("S4Cube", "3", "over")),
                        ("s4_base.usda", ("S4Cube", "def Cube"))):
        try:
            text = open("action-reasoner/skills/stage-core/stages/" + name,
                        encoding="utf-8").read()
        except OSError as exc:
            fails.append("%s: %r" % (name, exc))
        else:
            if any(w not in text for w in wants):
                fails.append("%s content wrong" % (name,))
    if fails:
        print("S4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("S4-PASS")
    return 0


sys.exit(main())
