$ErrorActionPreference = "Stop"
. C:\dev\lyrical\setup.ps1
$env:PATH = "C:\dev\lyrical\.pixi\envs\default\Library\bin;C:\dev\lyrical\.pixi\envs\default\bin;" + $env:PATH
$py = "C:\dev\lyrical\.pixi\envs\default\python.exe"
& $py -c "import ctypes; ctypes.CDLL('rmw_fastrtps_cpp.dll'); print('LOAD-OK')"
& $py -c "import rclpy; rclpy.init(); print('INIT-OK'); rclpy.shutdown()"
