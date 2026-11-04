"""verify_va (runs LOCALLY): 12-frame re-sweep exam valid.

12 images + 12 labels; every label exactly 2 abox rows, boxes
in-range h>=25; frame 0/5/11 rgb non-black.
"""
import glob
import re as _re
import subprocess
import sys

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


EVD = "action-reasoner/skills/sdg/adv/evidence/va_out/"
imgs = sorted(glob.glob(EVD + "Camera/image_02/*.png"))
labs = sorted(glob.glob(EVD + "Camera/label_02/*.txt"))
check("12 images", len(imgs) == 12)
check("12 label files", len(labs) == 12)
rows_ok, cls_ok, box_ok = True, True, True
n_checked = 0
for p in labs:
    rows = [ln.split() for ln in open(p).read().splitlines()
            if ln.strip()]
    n_checked += 1
    if len(rows) != 2:
        rows_ok = False
        continue
    if sorted(r[0].strip("'\"") for r in rows) != ["abox", "abox"]:
        cls_ok = False
    for r in rows:
        x0, y0, x1, y1 = (float(v) for v in r[4:8])
        if not (0 <= x0 < x1 <= 320 and 0 <= y0 < y1 <= 240
                and y1 - y0 >= 25):
            box_ok = False
check("12 labels read", n_checked == 12)
check("2 abox rows each", rows_ok)
check("classes abox", cls_ok)
check("boxes in-range h>=25", box_ok)

sample = [imgs[i] for i in (0, 5, 11)] if len(imgs) == 12 else []
p = subprocess.run(
    ["C:/isaacsim/python.bat",
     "action-reasoner/skills/sdg/adv/scripts/pngstats.py"] + sample
    if sample else ["cmd", "/c", "exit 1"],
    capture_output=True, text=True, timeout=240)
means = []
for ln in p.stdout.splitlines():
    for cand in sample:
        if ln.startswith(cand):
            mm = _re.search(r"mean=([\d.]+)", ln)
            if mm:
                means.append(float(mm.group(1)))
check("sampled rgb non-black",
      len(means) == 3 and all(v > 30 for v in means))
print("VA-" + ("PASS" if not fails else "FAIL " + ",".join(fails)))
sys.exit(1 if fails else 0)
