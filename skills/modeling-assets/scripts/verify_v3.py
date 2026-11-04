"""Verify V3 (runs LOCALLY): ref + bind + clones survive round-trip."""
import json
import os
import re
import sys

EVDIR = "action-reasoner/skills/modeling-assets/evidence/"
USD = "action-reasoner/skills/modeling-assets/stages/v3.usd"


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
    return {p["path"] for p in json.loads(env["output"])["prims"]}


def main():
    fails = []
    try:
        pa = _snap("v3_senseA.json")
        pb = _snap("v3_senseB.json")
        build = _load(EVDIR + "v3_build.json")
        check = _load(EVDIR + "v3_check.json")
    except RuntimeError as exc:
        print("V3-FAIL\n  - %s" % exc)
        return 1
    if build.get("status") != "ok" or check.get("status") != "ok":
        print("V3-FAIL\n  - build/check error")
        return 1
    m = re.search(r"V3-REPORT bound=(\S+) clones=(\d+)", build.get("output", ""))
    c = re.search(r"V3-CHECK base=(\S+) clone=(\S+)", check.get("output", ""))
    if not m or not c:
        print("V3-FAIL\n  - missing reports")
        return 1
    print("build: bound=%s clones=%s | check: base=%s clone=%s"
          % (m.group(1), m.group(2), c.group(1), c.group(2)))
    if m.group(1) != "/World/V3Looks/V3Red" or m.group(2) != "4":
        fails.append("build report wrong")
    if c.group(1) != "/World/V3Looks/V3Red" or c.group(2) != "/World/V3Looks/V3Red":
        fails.append("bindings did not persist/inherit")
    if not os.path.exists(USD) or os.path.getsize(USD) == 0:
        fails.append("v3.usd missing/empty")
    want = {"/World/V3Bot/Geometry/base", "/World/V3Bot/Geometry/base/arm",
            "/World/V3Bot/Physics/shoulder", "/World/V3Looks/V3Red"}
    want |= {"/World/venvs/env_%d/Geometry/base" % i for i in range(4)}
    for tag, paths in (("built", pa), ("reopened", pb)):
        if not want <= paths:
            fails.append("%s missing %r" % (tag, sorted(want - paths)))
    if fails:
        print("V3-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("V3-PASS")
    return 0


sys.exit(main())
