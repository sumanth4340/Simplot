$ErrorActionPreference = "SilentlyContinue"
. C:\dev\lyrical\setup.ps1
Write-Output ("DISTRO=" + $env:ROS_DISTRO)
Write-Output ("DOMAIN=" + $env:ROS_DOMAIN_ID)
Write-Output ("RMW=" + $env:RMW_IMPLEMENTATION)
$pkgs = ros2 pkg list
Write-Output ("PKGS=" + $pkgs.Count)
Write-Output ("NAV2=" + ($pkgs | Where-Object { $_ -match "^nav2" }).Count)
Write-Output ("NAV2SAMPLE=" + (($pkgs | Where-Object { $_ -match "^nav2" } | Select-Object -First 5) -join ","))
