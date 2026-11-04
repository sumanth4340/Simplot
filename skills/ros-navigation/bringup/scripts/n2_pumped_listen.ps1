$ErrorActionPreference = "Stop"
# Pumped listen for /scan (N1 pumped-leg pattern, scan flavor).
$SEND = "Downloads/IsaacSim-release-6.3/IsaacSim-release-6.3/skills/isaac-sim-remote/scripts/isaacsim_send.py"
$WS = "C:\Users\sruja_ob3di74"
$job = Start-Job -ScriptBlock {
  param($send, $ws)
  Set-Location $ws
  $o = @()
  for ($i = 0; $i -lt 6; $i++) {
    $r = python $send --raw --timeout 300 --file action-reasoner/skills/ros-navigation/bringup/scripts/n1_pump40.py 2>&1 | Out-String
    $o += $r
  }
  $o -join "`n"
} -ArgumentList $SEND, $WS
& powershell -NoProfile -ExecutionPolicy Bypass -File action-reasoner/skills/ros-navigation/bridge/scripts/listen.ps1 /scan scan 5 120 action-reasoner/skills/ros-navigation/bringup/evidence/n2_scan.json
Write-Output "LISTEN-DONE"
$pump = Receive-Job -Job $job -Wait | Out-String
Write-Output ("PUMP-LOG: " + $pump)
Remove-Job -Job $job
