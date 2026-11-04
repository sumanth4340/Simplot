import omni.graph.core as og
g = og.get_graph_by_path("/World/O4GraphB")
print("GRAPH=" + ",".join(sorted(n for n in dir(g) if not n.startswith("_"))))
print("EVALMODES=" + ",".join(sorted(n for n in dir(og.GraphEvaluationMode) if not n.startswith("_"))))
print("EXECST=" + ",".join(sorted(n for n in dir(og.ExecutionAttributeState) if not n.startswith("_"))))
print("NODECTRL=" + ",".join(sorted(n for n in dir(og.NodeController) if not n.startswith("_"))))
n = og.get_node_by_path("/World/O4GraphB/Write")
print("NODE=" + ",".join(sorted(x for x in dir(n) if not x.startswith("_"))))
