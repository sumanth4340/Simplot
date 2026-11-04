"""verify_x5 (runs LOCALLY): V5-final scene passes every graduated skill's lens."""
import json, re

EV = json.load(open("action-reasoner/skills/cross-val/evidence/x5_run.json"))["output"]

def f(pat, i=1):
    m = re.search(pat, EV)
    return float(m.group(i)) if m else float("nan")

def b(pat):
    m = re.search(pat, EV)
    return m and m.group(1) == "True"

checks = {}
checks["stage: all 7 prims valid"]    = b(r"valid=(\w+)")
checks["art: root present"]           = b(r"root=(\w+)")
checks["model: Link2 size 0.20"]      = abs(f(r"link=([\d.]+)") - 0.20) < 1e-6
checks["model: shelf top 0.30"]       = abs(f(r"stop=([\d.]+)") - 0.30) < 1e-6
checks["art: q within limits"]        = b(r"klim=(\w+)")
checks["art: place branch (q1>0)"]    = f(r"q=\[([-\d.]+)") > 0.0
checks["sense+phys: block at A"]      = abs(f(r"bx=([-\d.]+)") - 0.55) < 0.02
checks["sense+phys: block on top"]    = abs(f(r"bz=([-\d.]+)") - 0.36) < 0.02
checks["phys: still settled"]         = f(r"spd=([\d.]+)") < 0.2
checks["phys: block rigid+coll"]      = b(r"rigid=(\w+)") and b(r"coll=(\w+)")

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("X5-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
