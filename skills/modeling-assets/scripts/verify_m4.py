"""Verify M4 (runs LOCALLY): 9 clones sensed at distinct grid spots."""
import json
import re
import sys

EVDIR = "action-reasoner/skills/modeling-assets/evidence/"


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
    run = _load(EVDIR + "m4_run.json")
    if run.get("status") != "ok":
        print("M4-FAIL\n  - status=%r err=%r" % (run.get("status"), run.get("evalue")))
        return 1
    m = re.search(r"M4-REPORT clones=(\d+)", run.get("output", ""))
    if not m:
        print("M4-FAIL\n  - no report: %r" % (run.get("output", "")[:300],))
        return 1
    n = int(m.group(1))
    print("report: clones=%d" % n)
    if n != 9:
        fails.append("clones=%d" % (n,))
    snap = json.loads(_load(EVDIR + "m4_sense.json")["output"])
    envs = [p for p in snap["prims"] if p["path"].startswith("/World/envs/env_")]
    print("sensed env prims: %d" % len(envs))
    if len(envs) != 9:
        fails.append("envs=%d, want 9" % (len(envs),))
    cubes = [p for p in envs if p.get("type") == "Cube"]
    if len(cubes) != 9:
        fails.append("env cubes=%d, want 9" % (len(cubes),))
    pos = {tuple(p["pos"]) for p in cubes if p.get("pos")}
    if len(pos) != 9:
        fails.append("distinct positions=%d, want 9" % (len(pos),))
    if not any(p["path"] == "/World/M4Src" for p in snap["prims"]):
        fails.append("source M4Src missing")
    if fails:
        print("M4-FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("M4-PASS")
    return 0


sys.exit(main())
