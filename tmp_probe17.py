"""Probe 17 (runs INSIDE Isaac Sim): backend + simstate mode inspect."""
import isaacsim.core.experimental.utils.backend as backend_utils

print("CURRENT=", backend_utils.get_current_backend(["tensor", "usd"]))
print("BACKEND-SET=", backend_utils.is_backend_set())
try:
    print("SIMSTATE=", backend_utils.get_simstate_mode())
except Exception as e:
    print("SIMSTATE-ERR=", repr(e)[:300])
try:
    print("RAISE-ON-FALLBACK=", backend_utils.should_raise_on_fallback())
except Exception as e:
    print("RAISE-ERR=", repr(e)[:200])
