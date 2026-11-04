$ErrorActionPreference = "Stop"
. C:\dev\lyrical\setup.ps1
$env:PATH = "C:\dev\lyrical\.pixi\envs\default\Library\bin;C:\dev\lyrical\.pixi\envs\default\bin;" + $env:PATH
$py = "C:\dev\lyrical\.pixi\envs\default\python.exe"
& $py action-reasoner\skills\ros\scripts\r2_pubcount.py $args[0] $args[1] $args[2]
