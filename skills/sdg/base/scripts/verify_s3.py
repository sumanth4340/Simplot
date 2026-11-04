"""verify_s3 (runs LOCALLY): writer output gates.

3 direct_rgb .npy (240,320,4 uint8, mean>30) + 3 bbox .npy
non-empty with the S2 box + labels JSON naming s2cube.
"""
import glob
import json
import sys
import numpy as np

R = json.load(open("action-reasoner/skills/sdg/base/evidence/s3_run.json"))["output"]
OUT = "action-reasoner/skills/sdg/base/evidence/s3_out"
rgbs = sorted(glob.glob(OUT + "/direct_rgb_*.npy"))
bboxes = sorted(glob.glob(OUT + "/bounding_box_2d_tight_*.npy"))
labs = sorted(glob.glob(OUT + "/bounding_box_2d_tight_labels_*.json"))
arrs = [np.load(p) for p in rgbs]
bb0 = np.load(bboxes[0], allow_pickle=True) if bboxes else []

checks = {}
checks["3 rgb npy"] = len(rgbs) == 3
checks["report rgb"] = "rgb_files=3" in R
checks["rgb shape"] = all(a.shape == (240, 320, 4) for a in arrs)
checks["rgb uint8"] = all(a.dtype == np.uint8 for a in arrs)
checks["rgb non-black"] = all(a.mean() > 30.0 for a in arrs)
checks["3 bbox npy"] = len(bboxes) == 3
checks["report bbox"] = "bbox_files=3" in R
checks["bbox has box"] = len(bb0) == 1 and (bb0[0][3] - bb0[0][1]) > 0
checks["labels name s2cube"] = all(
    "s2cube" in open(p).read() for p in labs) and len(labs) == 3

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("S3-" + ("PASS" if ok else "FAIL"))
raise SystemExit(0 if ok else 1)
import sys
sys.exit(0 if ok else 1)
