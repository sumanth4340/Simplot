# Detail the parent RTX sensor command + try creating a lidar.
import omni.kit.commands as kc
import omni.usd

print("=== IsaacSensorCreateRtxSensor ===")
try:
    for p in kc.get_command_parameters("IsaacSensorCreateRtxSensor"):
        print("  ", p.name, "| default=", repr(p.default)[:100])
except Exception as e:
    print("  ERR", repr(e)[:200])
try:
    print("  DOC:", (kc.get_command_doc("IsaacSensorCreateRtxSensor")
                     or "")[:800])
except Exception as e:
    print("  DOC-ERR", repr(e)[:120])

st = omni.usd.get_context().get_stage()
if st.GetPrimAtPath("/N2LidarProbe").IsValid():
    st.RemovePrim("/N2LidarProbe")
ok, sensor = kc.execute("IsaacSensorCreateRtxLidar",
                        path="/N2LidarProbe")
print("CREATE", ok, sensor)
p = st.GetPrimAtPath("/N2LidarProbe")
print("VALID", p.IsValid(),
      "TYPE", p.GetTypeName() if p.IsValid() else None)
if p.IsValid():
    for c in p.GetChildren():
        print("  CHILD", c.GetPath(), c.GetTypeName())
    st.RemovePrim("/N2LidarProbe")
print("SIG3 done")
