"""R2 deep listener: publishers info, receipt wall-time, full precision."""
import json
import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

topic, count, timeout, out = (
    sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4])


class L(Node):
    def __init__(self):
        super().__init__("muse_probe2")
        self.got = []
        self.t0 = time.time()
        self.create_subscription(JointState, topic, self.cb, 10)

    def cb(self, msg):
        self.got.append({
            "wall": time.time() - self.t0,
            "t": msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            "pos": [repr(x) for x in msg.position],
            "vel": [repr(x) for x in msg.velocity]})


rclpy.init()
node = L()
pubs = node.get_publishers_info_by_topic(topic)
print("PUBS=%d" % len(pubs))
for p in pubs:
    try:
        print("PUB node=%s qos=%s" % (p.node_name, p.qos_profile.depth))
    except Exception as e:
        print("PUB info-err %s" % e)
t0 = time.time()
while len(node.got) < count and time.time() - t0 < timeout:
    rclpy.spin_once(node, timeout_sec=0.5)
node.destroy_node()
rclpy.shutdown()
json.dump({"count": len(node.got), "stamps": node.got}, open(out, "w"))
print("LISTEN-OK count=%d" % len(node.got))
