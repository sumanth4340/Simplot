# OmniGraph — Discovery Notes (live-verified, Isaac Sim 6.0.0)

## Controller.edit calling conventions
- Keys: CREATE_NODES [(name, type)], CONNECT [(src, dst)],
  SET_VALUES [(attr, value[, og.Type])], DISCONNECT [(src, dst)].
- Bare "Node.attr" names resolve via the per-call creation map:
  later edits MUST use full paths ("/World/G/Node.attr").
- Prefer ONE atomic edit (create+connect+values) over split edits:
  fewer ordering hazards, though atomicity does NOT fix R2.
- Probe installed signatures live (Skill 6 R3 rule): read
  Controller.edit docstring + node .ogn/.cpp + Kit log.

## Node inventory (probed, this install)
- omni.graph.action.OnPlaybackTick: outputs:tick (exec),
  outputs:time (double, seconds).
- omni.graph.nodes.Multiply: inputs:a/b, outputs:product.
- omni.graph.nodes.Add: inputs:a/b, outputs:sum (probed attr
  list: inputs:a, inputs:b, outputs:sum + node:type*).
- omni.graph.nodes.WritePrimAttribute: inputs:execIn, inputs:value
  (template), inputs:primPath, inputs:name, inputs:usePath.
- Introspection: og.ObjectLookup.attribute(path)
  .get_upstream_connections(); og.get_node_by_path(P).get_attribute(
  name).get(); og.get_graph_by_path(P).set_disabled()/is_disabled().

## Runtime semantics (earned the hard way)
- R1 prompt evaluation: build writes land pre-play (usdWriteBack).
- R5 data-flow firing: Write fires when upstream DATA changes.
- R6 stale instances: recreated graph prims shadow until a
  re-touch; fresh paths work immediately (t1=5.0 first try).
- R7 disable semantics: clock runs while off; resume jumps to
  live (catch-up = missed + new windows).
- R8 silent contention: N graphs x 1 target = no warning; last
  writer wins per tick in an unspecified mix.

## Session notes
- Sim crashed 4x this training arc (render/lidar/bridge-reset);
  recovery: relaunch windowed + bridge poll; scripts rebuild the
  stage anonymously; evidence on disk never lost.
- Numeric gates: numpy space-padded floats need tolerant regex;
  joint targets are DEGREES, get_dof_positions RADIANS.
