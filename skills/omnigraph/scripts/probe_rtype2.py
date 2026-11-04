import omni.graph.core as og
for spec in ("Write.inputs:value", "Mul.outputs:product", "Vec.inputs:x",
             "Mul.inputs:a", "Mul.inputs:b", "Vec.inputs:y", "Vec.inputs:z"):
    try:
        att = og.ObjectLookup.attribute("/World/O3Graph/" + spec)
        print(spec + " resolved=" + str(att.get_resolved_type()))
    except Exception as e:
        print(spec + " ERR " + repr(e)[:100])
