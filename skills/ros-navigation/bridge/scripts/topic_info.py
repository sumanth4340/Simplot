"""Topic+QoS inspector (runs OUTSIDE Isaac Sim, pixi env python).

Lists all topics, then publisher QoS for the requested topic.
Usage: python topic_info.py [/topic]
Sourced env required (setup.ps1 + Library/bin on PATH).
"""
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

rclpy.init()
node = Node("muse_topicinfo")
topics = []
for _ in range(25):
    topics = [t for t in node.get_topic_names_and_types()
              if t[0] not in ("/parameter_events", "/rosout")]
    if topics:
        break
    rclpy.spin_once(node, timeout_sec=1.0)
topics = sorted(topics, key=lambda t: t[0])
print("TOPICS %d" % len(topics))
for name, types in topics:
    print("  %s : %s" % (name, ",".join(types)))
want = sys.argv[1] if len(sys.argv) > 1 else None
if want:
    try:
        infos = node.get_publishers_info_by_topic(want)
    except Exception as e:
        print("PUB-INFO-ERR", repr(e)[:200])
        infos = []
    print("PUBS %s count=%d" % (want, len(infos)))
    for i in infos:
        q = i.qos_profile
        print("  reliability=%s durability=%s depth=%s "
              "lifespan=%s deadline=%s liveliness=%s" % (
                  q.reliability, q.durability, q.depth,
                  q.lifespan, q.deadline, q.liveliness))
node.destroy_node()
rclpy.shutdown()
print("TOPICINFO done")
