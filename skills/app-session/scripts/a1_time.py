"""A1 time snippet (runs INSIDE Isaac Sim): set/get round-trip.

set_current_time applies on the next frame pump: set -> pump 2
steps -> get. Without the pump the get reads the stale time.
"""
import omni.timeline
import isaacsim.core.experimental.utils.app as app_utils
tl = omni.timeline.get_timeline_interface()
tl.set_current_time(2.5)
await app_utils.update_app_async(steps=2)
print("TIME-SET-GET %.3f" % tl.get_current_time())
