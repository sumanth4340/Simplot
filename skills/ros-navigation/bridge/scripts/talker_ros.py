"""System-ROS joint talker (runs OUTSIDE Isaac Sim, env python).

Publishes sensor_msgs/JointState at 10 Hz for DURATION s.
Usage: python talker_ros.py <topic> <v1> <v2> <duration>
Names fixed: [J1, J2] (matches R3Bot DOFs).
"""
import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

topic, v1, v2, dur = (
    sys.argv[1], float(sys.argv[2]), float(sys.argv[3]),
    float(sys.argv[4]))

rclpy.init()
node = Node("muse_talker")
pub = node.create_publisher(JointState, topic, 10)
msg = JointState()
msg.name = ["J1", "J2"]
msg.velocity = [v1, v2]
n = 0
t0 = time.time()
while time.time() - t0 < dur:
    msg.header.stamp = node.get_clock().now().to_msg()
    pub.publish(msg)
    n += 1
    time.sleep(0.1)
node.destroy_node()
rclpy.shutdown()
print("TALK-OK n=%d" % n)
