"""verify_v12 (runs LOCALLY): exam gates."""
import glob
import json
import re
import numpy as np

B = json.load(open("action-reasoner/skills/sdg/base/evidence/v12_build.json"))["output"]
R = json.load(open("action-reasoner/skills/sdg/base/evidence/v12_run.json"))["output"]
OUT = "action-reasoner/skills/sdg/base/evidence/v12_out"

frames = {}
for m in re.finditer(r"f(\d):nbox=(\d+),cls=([\w+]+),pxa=(\d+),pxb=(\d+),mean=([\d.]+)", R):
    frames[int(m.group(1))] = {
        "nbox": int(m.group(2)), "cls": m.group(3),
        "pxa": int(m.group(4)), "pxb": int(m.group(5)),
        "mean": float(m.group(6))}
rgbs = sorted(glob.glob(OUT + "/rgb_*.npy"))
sems = sorted(glob.glob(OUT + "/sem_*.npy"))
bbs = sorted(glob.glob(OUT + "/bounding_box_2d_tight_*.npy"))
arrs = [np.load(p) for p in rgbs]

checks = {}
checks["props valid"] = "valid=True" in B
checks["labels applied"] = "v12a" in B and "v12b" in B
checks["3 frames"] = len(frames) == 3
checks["2 boxes/frame"] = all(frames[i]["nbox"] == 2 for i in range(3))
checks["classes a+b"] = all(frames[i]["cls"] == "v12a+v12b" for i in range(3))
checks["pixels a>100"] = all(frames[i]["pxa"] > 100 for i in range(3))
checks["pixels b>100"] = all(frames[i]["pxb"] > 100 for i in range(3))
checks["rgb non-black"] = all(frames[i]["mean"] > 30.0 for i in range(3))
checks["3 rgb files"] = len(rgbs) == 3
checks["rgb shape"] = all(a.shape == (240, 320, 4) for a in arrs)
checks["3 sem files"] = len(sems) == 3
checks["3 bbox files"] = len(bbs) == 3
checks["views differ"] = len({frames[i]["pxa"] for i in range(3)}) == 3

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("V12-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
