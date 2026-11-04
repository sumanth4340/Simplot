"""verify_w3 (runs LOCALLY): selection round-trip + app shot valid."""
import json, os, sys

sys.path.insert(0, "action-reasoner/skills/viewport-ui/scripts")
from pngstats import png_stats

SET = json.load(open("action-reasoner/skills/viewport-ui/evidence/w3_set.json"))["output"]
GET = json.load(open("action-reasoner/skills/viewport-ui/evidence/w3_get.json"))["output"]
SHOT = json.load(open("action-reasoner/skills/viewport-ui/evidence/w3_shot.json"))
PNG = "action-reasoner/skills/viewport-ui/evidence/w3_app.png"

checks = {}
checks["set ack"] = "Selected 1 prim(s)" in SET
checks["get shows cube"] = "/World/W1Cube" in GET
checks["shot ok"] = SHOT.get("status") == "ok" and "Saved app screenshot" in SHOT.get("output", "")
checks["png exists >50KB"] = os.path.exists(PNG) and os.path.getsize(PNG) > 50000
st = png_stats(PNG)
print("INFO size=%dx%d mean=%.1f std=%.1f" % (st["w"], st["h"], st["mean"], st["std"]))
checks["min size 640x480"] = st["w"] >= 640 and st["h"] >= 480
checks["mean 5..250"] = 5.0 < st["mean"] < 250.0
checks["non-uniform"] = st["std"] > 1.0

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("W3-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
