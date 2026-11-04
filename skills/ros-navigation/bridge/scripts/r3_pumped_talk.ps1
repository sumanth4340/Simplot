$ErrorActionPreference = "Stop"
# Pumped talk: force sim frames (background pump job) while the
# system-ROS talker publishes commands (foreground).
$SEND = "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/skills/isaac-sim-remote/scripts/isaacsim_send.py"
$WS = "C:\Users\sruja_ob3di74"
. C:\dev\lyrical\setup.ps1
$env:PATH = "C:\dev\lyrical\.pixi\envs\default\Library\bin;C:\dev\lyrical\.pixi\envs\default\bin;" + $env:PATH
$py = "C:\dev\lyrical\.pixi\envs\default\python.exe"
Write-Output "PRE-TALK (match building):"
& $py action-reasoner\skills\ros\scripts\talker_ros.py /r3_cmd 0.8 -0.5 6
$job = Start-Job -ScriptBlock {
  param($send, $ws)
  Set-Location $ws
  $o = @()
  for ($i = 0; $i -lt 4; $i++) {
    $r = python $send --raw --timeout 300 --file action-reasoner/skills/ros-navigation/bridge/scripts/r3_pump40.py 2>&1 | Out-String
    $o += $r
  }
  $o -join "`n"
} -ArgumentList $SEND, $WS
& $py action-reasoner\skills\ros\scripts\talker_ros.py /r3_cmd 0.8 -0.5 25
Write-Output "TALK-DONE"
$pump = Receive-Job -Job $job -Wait | Out-String
Write-Output ("PUMP-LOG: " + $pump)
Remove-Job -Job $job
