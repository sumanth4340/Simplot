"""verify_a1 (runs LOCALLY): KITTI dataset valid.

4 images + 4 label files (image_02/label_02), 2 rows each,
classes kboxa/kboxb, boxes in-range with height>=25, rgb
non-black, semantic map has 3 ids (bg + 2 classes). Pixel stats
via isaacsim python (PIL lives there only).
"""
import glob
import os
import subprocess
import sys

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


EVD = "action-reasoner/skills/sdg/adv/evidence/a1_out/"
imgs = sorted(glob.glob(EVD + "Camera/image_02/*.png"))
labs = sorted(glob.glob(EVD + "Camera/label_02/*.txt"))
sems = sorted(glob.glob(EVD + "Camera/semantic/*.png"))
srgbs = sorted(glob.glob(EVD + "Camera/semantic_rgb/*.png"))
check("4 images", len(imgs) == 4)
check("4 label files", len(labs) == 4)
rows_ok, cls_ok, box_ok = True, True, True
for p in labs:
    rows = [ln.split() for ln in open(p).read().splitlines()
            if ln.strip()]
    if len(rows) != 2:
        rows_ok = False
    cls = sorted(r[0].strip("'\"") for r in rows)
    if cls != ["kboxa", "kboxb"]:
        cls_ok = False
    for r in rows:
        x0, y0, x1, y1 = (float(v) for v in r[4:8])
        if not (0 <= x0 < x1 <= 320 and 0 <= y0 < y1 <= 240
                and y1 - y0 >= 25):
            box_ok = False
check("2 rows each", rows_ok)
check("classes kboxa/kboxb", cls_ok)
check("boxes in-range h>=25", box_ok)

pngs = ([imgs[0], sems[0], srgbs[0]]
        if (imgs and sems and srgbs) else [])
p = subprocess.run(
    ["C:/isaacsim/python.bat",
     "action-reasoner/skills/sdg/adv/scripts/pngstats.py"] + pngs
    if pngs else ["cmd", "/c", "exit 1"],
    capture_output=True, text=True, timeout=240)
import re as _re
stats = {}
for ln in p.stdout.splitlines():
    for cand in pngs:
        if ln.startswith(cand):
            mm = _re.search(r"mean=([\d.]+)", ln)
            nn = _re.search(r"nunique=(\d+)", ln)
            if mm and nn:
                stats[cand] = {"mean": float(mm.group(1)),
                               "nunique": int(nn.group(1))}
rgb = stats.get(imgs[0], {}) if imgs else {}
sem = stats.get(sems[0], {}) if sems else {}
srg = stats.get(srgbs[0], {}) if srgbs else {}
check("rgb non-black", rgb.get("mean", 0) > 30)
# KITTI sem ids are 0-based class indices with background folded
# into 0 (bg+kboxa=0, kboxb=1). Colorized map carries the mapping
# colors (bg + red + green).
check("semantic 2 ids", sem.get("nunique", 0) == 2)
check("semrgb 3 colors", srg.get("nunique", 0) == 3)
print("A1-" + ("PASS" if not fails else "FAIL " + ",".join(fails)))
sys.exit(1 if fails else 0)
