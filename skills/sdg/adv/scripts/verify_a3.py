"""verify_a3 (runs LOCALLY): 50-frame KITTI sweep valid.

50 images + 50 labels; every label exactly 2 abox rows, boxes
in-range h>=25; frame 0/24/49 rgb non-black. Pixel stats via
isaacsim python (PIL lives there only).
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


EVD = "action-reasoner/skills/sdg/adv/evidence/a3_out/"
imgs = sorted(glob.glob(EVD + "Camera/image_02/*.png"))
labs = sorted(glob.glob(EVD + "Camera/label_02/*.txt"))
check("50 images", len(imgs) == 50)
check("50 label files", len(labs) == 50)
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
check("50 labels read", n_checked == 50)
check("2 abox rows each", rows_ok)
check("classes abox", cls_ok)
check("boxes in-range h>=25", box_ok)

sample = [imgs[i] for i in (0, 24, 49)] if len(imgs) == 50 else []
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
print("A3-" + ("PASS" if not fails else "FAIL " + ",".join(fails)))
sys.exit(1 if fails else 0)
