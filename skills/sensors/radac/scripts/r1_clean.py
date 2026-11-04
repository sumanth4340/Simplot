# R1 clean (INSIDE Isaac Sim): remove scratch radar prims.
import omni.usd

st = omni.usd.get_context().get_stage()
for p in ("/World/R1Birth", "/World/R1RadarSecond"):
    if st.GetPrimAtPath(p).IsValid():
        st.RemovePrim(p)
    print("CLEAN %s gone=%s" % (
        p, not st.GetPrimAtPath(p).IsValid()))
print("R1-CLEAN done")
