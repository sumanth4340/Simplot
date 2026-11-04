"""verify_a2 (runs LOCALLY): same seed identical, diff seed
different, all boxes in-range."""
import sys

import numpy as np

EVD = "action-reasoner/skills/sdg/adv/evidence/"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


L = [np.load(EVD + "a2_layouts_%d.npy" % i) for i in range(3)]
check("shapes", all(a.shape == (6, 3, 4) for a in L))
check("same-seed identical", bool((L[0] == L[1]).all()))
check("diff-seed differs", bool((L[0] != L[2]).any()))
ok = True
for a in L:
    x0, y0, x1, y1 = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    if not bool((((0 <= x0) & (x0 < x1) & (x1 <= 320)
                   & (0 <= y0) & (y0 < y1) & (y1 <= 240)).all())):
        ok = False
check("boxes in-range", ok)
print("A2-" + ("PASS" if not fails else "FAIL " + ",".join(fails)))
sys.exit(1 if fails else 0)
