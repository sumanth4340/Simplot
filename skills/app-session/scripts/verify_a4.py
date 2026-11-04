"""verify_a4 (runs LOCALLY): inspection gates."""
import re

T = open("action-reasoner/skills/app-session/evidence/a4_report.txt",
       encoding="utf-8").read()

checks = {}
checks["tree shows marker"] = "A2Marker" in T.split("$ send")[1]
checks["cube filter lists it"] = "/World/A2Marker" in T.split("$ send")[2]
checks["prim detail path"] = "Path: /World/A2Marker" in T.split("$ send")[3]
checks["no errors"] = "ERROR" not in T

ok = all(checks.values())
for k, v in checks.items():
    print(("PASS " if v else "FAIL ") + k)
print("A4-" + ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)
