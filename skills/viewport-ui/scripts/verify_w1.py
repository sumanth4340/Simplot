"""verify_w1 (runs LOCALLY): viewport PNG exists, sized, non-degenerate."""
import json, os

EV = json.load(open("action-reasoner/skills/viewport-ui/evidence/w1_shot.json"))
PNG = "action-reasoner/skills/viewport-ui/evidence/w1_viewport.png"

checks = {}
checks["send ok"] = EV.get("status") == "ok"
checks["saved message"] = "Saved viewport screenshot" in EV.get("output", "")
checks["png exists >50KB"] = os.path.exists(PNG) and os.path.getsize(PNG) > 50000
try:
    import sys
    sys.path.insert(0, "action-reasoner/skills/viewport-ui/scripts")
    from pngstats import png_stats
    st = png_stats(PNG)
    checks["min size 640x480"] = st["w"] >= 640 and st["h"] >= 480
    checks["mean 10..245"] = 10.0 < st["mean"] < 245.0
    checks["non-uniform"] = st["std"] > 1.0
    print("INFO size=%dx%d mean=%.1f std=%.1f" % (
        st["w"], st["h"], st["mean"], st["std"]))
except Exception as e:
    checks["png read"] = False
    print("INFO png read failed: %r" % e)

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("W1-" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
