import omni.usd
import omni.graph.core as og
import isaacsim.core.experimental.utils.app as app_utils
stage = omni.usd.get_context().get_stage()
app_utils.stop()
await app_utils.update_app_async(steps=5)
keys = og.Controller.Keys
og.Controller.edit("/World/O4GraphB", {
    keys.CREATE_NODES: [
        ("OnPB", "omni.graph.action.OnPlaybackTick"),
        ("Mul", "omni.graph.nodes.Multiply"),
        ("Write", "omni.graph.nodes.WritePrimAttribute"),
    ],
    keys.CONNECT: [
        ("OnPB.outputs:tick", "Write.inputs:execIn"),
        ("OnPB.outputs:time", "Mul.inputs:a"),
        ("Mul.outputs:product", "Write.inputs:value"),
    ],
    keys.SET_VALUES: [
        ("Mul.inputs:b", 10.0, og.Type(og.BaseDataType.DOUBLE)),
        ("Write.inputs:primPath", "/World/O4Bot/Hinge1"),
        ("Write.inputs:name", "drive:angular:physics:targetPosition"),
        ("Write.inputs:usePath", True),
    ],
})
app_utils.play(commit=True)
await app_utils.update_app_async(steps=30)
t = float(stage.GetPrimAtPath("/World/O4Bot/Hinge1").GetAttribute(
    "drive:angular:physics:targetPosition").Get())
print("FRESHPATH t1=%.3f" % t)
