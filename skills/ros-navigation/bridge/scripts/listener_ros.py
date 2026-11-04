"""System-ROS listener (runs OUTSIDE Isaac Sim, system python).

Sourced env required (setup.ps1). Subscribes to a topic, collects
up to COUNT messages or TIMEOUT s, writes JSON {count, stamps}.
Usage: python listener_ros.py <topic> <msgtype> <count> <timeout> <out>
msgtype: clock | jointstate | tf | odom | scan.
"""
import json
import sys
import time

import rclpy
from rclpy.node import Node

topic, msgtype, count, timeout, out = (
    sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]),
    sys.argv[5])
if msgtype == "clock":
    from rosgraph_msgs.msg import Clock
    TYPE = Clock
elif msgtype == "jointstate":
    from sensor_msgs.msg import JointState
    TYPE = JointState
elif msgtype == "tf":
    from tf2_msgs.msg import TFMessage
    TYPE = TFMessage
elif msgtype == "odom":
    from nav_msgs.msg import Odometry
    TYPE = Odometry
elif msgtype == "scan":
    from sensor_msgs.msg import LaserScan
    TYPE = LaserScan
else:
    raise SystemExit("unknown msgtype " + msgtype)


class L(Node):
    def __init__(self):
        super().__init__("muse_probe")
        self.got = []
        self.create_subscription(TYPE, topic, self.cb, 10)

    def cb(self, msg):
        if msgtype == "clock":
            self.got.append(msg.clock.sec + msg.clock.nanosec * 1e-9)
        elif msgtype == "jointstate":
            self.got.append({"names": list(msg.name),
                             "pos": list(msg.position),
                             "t": (msg.header.stamp.sec
                                   + msg.header.stamp.nanosec * 1e-9)})
        elif msgtype == "tf":
            self.got.append([{
                "child": t.child_frame_id,
                "parent": t.header.frame_id,
                "xyz": [t.transform.translation.x,
                        t.transform.translation.y,
                        t.transform.translation.z],
                "t": (t.header.stamp.sec
                      + t.header.stamp.nanosec * 1e-9)}
                for t in msg.transforms])
        elif msgtype == "odom":
            self.got.append({
                "frame": msg.header.frame_id, "child": msg.child_frame_id,
                "xyz": [msg.pose.pose.position.x,
                        msg.pose.pose.position.y,
                        msg.pose.pose.position.z],
                "vxyz": [msg.twist.twist.linear.x,
                         msg.twist.twist.linear.y,
                         msg.twist.twist.linear.z],
                "wxyz": [msg.twist.twist.angular.x,
                         msg.twist.twist.angular.y,
                         msg.twist.twist.angular.z],
                "t": (msg.header.stamp.sec
                      + msg.header.stamp.nanosec * 1e-9)})
        else:
            pos = [r for r in msg.ranges if r > 0]
            self.got.append({
                "frame": msg.header.frame_id,
                "n": len(msg.ranges),
                "rmin": float(min(msg.ranges)) if msg.ranges else None,
                "rmax": float(max(msg.ranges)) if msg.ranges else None,
                "rmin_valid": (float(min(pos)) if pos else None),
                "t": (msg.header.stamp.sec
                      + msg.header.stamp.nanosec * 1e-9)})


rclpy.init()
node = L()
t0 = time.time()
while (len(node.got) < count and time.time() - t0 < timeout):
    rclpy.spin_once(node, timeout_sec=0.5)
node.destroy_node()
rclpy.shutdown()
json.dump({"count": len(node.got), "stamps": node.got},
          open(out, "w"))
print("LISTEN-OK count=%d" % len(node.got))
