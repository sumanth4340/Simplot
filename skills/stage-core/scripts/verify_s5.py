"""Verify S5 (runs LOCALLY): ref + variant + payload cycle exact."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/stage-core/evidence/"
ASSET = "action-reasoner/skills/stage-core/stages/s5_widget.usda"


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
    run = _load(EVDIR + "s5_run.json")
    if run.get("status") != "ok":
        print("S5-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"S5-REPORT small=([-\d.]+) large=([-\d.]+) loaded=(\w+) "
                  r"gone=(\w+) back=(\w+)", run.get("output", ""))
    if not m:
        print("S5-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    small, large = float(m.group(1)), float(m.group(2))
    loaded, gone, back = (m.group(3) == "True", m.group(4) == "True",
                          m.group(5) == "True")
    print("report: small=%.1f large=%.1f loaded=%s gone=%s back=%s"
          % (small, large, loaded, gone, back))
    if small != 1.0:
        fails.append("small=%r" % (small,))
    if large != 4.0:
        fails.append("variant switch failed: %r" % (large,))
    if not (loaded and gone and back):
        fails.append("payload cycle: %s/%s/%s" % (loaded, gone, back))
    try:
        text = open(ASSET, encoding="utf-8").read()
    except OSError as exc:
        fails.append("asset: %r" % (exc,))
    else:
        if "variantSet" not in text or "defaultPrim" not in text:
            fails.append("asset content wrong")
    if fails:
        print("S5-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("S5-PASS")
    return 0


sys.exit(main())
