import inspect
import omni.graph.core as og
print("create_graph" + str(inspect.signature(og.Controller.create_graph)))
print("create_node" + str(inspect.signature(og.Controller.create_node)))
print("connect" + str(inspect.signature(og.Controller.connect)))
cands = [n for n in dir(og) if "egistr" in n or "NodeType" in n]
print("REG-CANDS=" + str(cands))
