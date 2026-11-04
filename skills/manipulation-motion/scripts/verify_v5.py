"""V5 exam verifier: MIRROR pick-and-place (pick B -> place A), six gates + exam rule.

Mirror of verify_m4.py with sides flipped:
  block0.x must be NEGATIVE (picked from pedestal B at x=-0.55)
  block1.x must be POSITIVE (placed at pedestal A at x=+0.55)
  q_grasp[0] must be NEGATIVE (mirrored branch, Rule: (q1,q2)->(-q1,-q2))
  q_place/q_end[0] must be POSITIVE (mirror of m4b q_place)
"""
import json, re

VA = json.load(open("action-reasoner/skills/manipulation-motion/evidence/v5a_run.json"))["output"]
VB = json.load(open("action-reasoner/skills/manipulation-motion/evidence/v5b_run.json"))["output"]

def f(pat, s, i=1):
    m = re.search(pat, s)
    return float(m.group(i)) if m else float("nan")

def b(pat, s):
    m = re.search(pat, s)
    return m and m.group(1) == "True"

checks = {}
checks["GATE1 pre-descend<0.02"]      = f(r"err_pd=([\d.eE+-]+)", VA) < 0.02
checks["GATE2 approach<0.02"]         = f(r"err_a=([\d.eE+-]+)", VA) < 0.02
checks["GATE3 touch<0.01"]            = f(r"err_t=([\d.eE+-]+)", VA) < 0.01
checks["GATE3b gap<0.02 closed"]      = f(r"g0=([\d.eE+-]+)", VA) < 0.02
checks["GATE4 attached"]              = b(r"attached=(\w+)", VA)
checks["GATE5 zmax>1.5"]              = f(r"zmax=([\d.eE+-]+)", VB) > 1.5
checks["GATE5b err_p<0.05"]           = f(r"err_p=([\d.eE+-]+)", VB) < 0.05
checks["GATE5c pxy<0.02"]             = f(r"pxy=([\d.eE+-]+)", VB) < 0.02
checks["GATE6 released+settled"]      = b(r"released=(\w+)", VB) and f(r"spd=([\d.eE+-]+)", VB) < 0.2
# exam rule: mirrored sides
checks["EXAM picked-from-B(x<0)"]     = f(r"block0=\[([-\d.eE+]+)", VA) < 0.0
checks["EXAM placed-at-A(x>0)"]       = f(r"block1=\[([-\d.eE+]+)", VB) > 0.0
checks["EXAM grasp-branch<0"]         = f(r"q_grasp=\[([-\d.eE+]+)", VA) < 0.0
checks["EXAM place-branch>0"]         = f(r"q_end=\[([-\d.eE+]+)", VB) > 0.0
checks["EXAM b-fin+conv"]             = f(r"pz=([\d.eE+-]+)", VB) <= 0.001 and b(r"conv=(\w+)", VB)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V5-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
