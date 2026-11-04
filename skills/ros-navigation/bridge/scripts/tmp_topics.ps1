$ErrorActionPreference = "Stop"
. C:\dev\lyrical\setup.ps1
$env:PATH = "C:\dev\lyrical\.pixi\envs\default\Library\bin;C:\dev\lyrical\.pixi\envs\default\bin;" + $env:PATH
$py = "C:\dev\lyrical\.pixi\envs\default\python.exe"
& $py -c "import rclpy; from rclpy.node import Node; rclpy.init(); n=Node('t'); import time; time.sleep(3); print('TOPICS=' + str(sorted([t for t,_ in n.get_topic_names_and_types()]))); n.destroy_node(); rclpy.shutdown()"
