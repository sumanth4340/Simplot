import isaacsim.core.experimental.utils.app as app_utils
import omni.isaac.dynamic_control as dc
app_utils.stop()
await app_utils.update_app_async(steps=5)
app_utils.play()
await app_utils.update_app_async(steps=60)
d = dc.acquire_dynamic_control_interface()
art = d.get_articulation("/World/R2Bot")
out = {"art": str(art)}
if art != dc.INVALID_ARTICULATION:
    out["ndof"] = d.get_articulation_dof_count(art)
    out["nbodies"] = d.get_articulation_body_count(art)
    dof = d.get_articulation_dof_states(art, dc.STATE_POS)
    out["pos"] = [float(x) for x in dof["pos"]] if dof is not None else None
app_utils.stop()
print("DCSTATE=" + str(out))
