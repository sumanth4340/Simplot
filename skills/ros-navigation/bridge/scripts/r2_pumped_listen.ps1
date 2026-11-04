$ErrorActionPreference = "Stop"
# Pumped listen: force sim frames (background pump job) while the
# system-ROS listener collects (foreground). Frames stop between
# bridge calls, freezing physics/OG reads, so an unpumped listen
# sees static values with advancing stamps.
$SEND = "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/skills/isaac-sim-remote/scripts/isaacsim_send.py"
$WS = "C:\Users\sruja_ob3di74"
$job = Start-Job -ScriptBlock {
  param($send, $ws)
  Set-Location $ws
  $o = @()
  for ($i = 0; $i -lt 6; $i++) {
    $r = python $send --raw --timeout 300 --file action-reasoner/skills/ros-navigation/bridge/scripts/r2_pump40.py 2>&1 | Out-String
    $o += $r
  }
  $o -join "`n"
} -ArgumentList $SEND, $WS
& powershell -NoProfile -ExecutionPolicy Bypass -File action-reasoner/skills/ros-navigation/bridge/scripts/listen.ps1 /joint_states jointstate 8 120 action-reasoner/skills/ros-navigation/bridge/evidence/r2_js.json
Write-Output "LISTEN-DONE"
$pump = Receive-Job -Job $job -Wait | Out-String
Write-Output ("PUMP-LOG: " + $pump)
Remove-Job -Job $job
