"""Count publishers/nodes on /joint_states after discovery settles."""
import sys
import time

import rclpy
from rclpy.node import Node

topic, wait, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
rclpy.init()
node = Node("muse_probe3")
time.sleep(wait)
pubs = node.get_publishers_info_by_topic(topic)
lines = ["PUBS=%d" % len(pubs)]
for p in pubs:
    try:
        lines.append("PUB node=%s ns=%s" % (p.node_name, p.node_namespace))
    except Exception as e:
        lines.append("PUB info-err %s" % e)
try:
    lines.append("NODES=" + str(sorted(node.get_node_names_and_namespaces())))
except Exception as e:
    lines.append("NODES-err %s" % e)
node.destroy_node()
rclpy.shutdown()
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
