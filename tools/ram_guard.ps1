# Kill a long compute if the machine is about to run out of memory.
#
# This box has frozen twice from over-subscription. The n=12 frontier DP has an
# unbounded state dictionary, so it must not be left to run unattended without a
# floor under free RAM. Losing the run costs hours; freezing the box costs more.
#
#   powershell -NoProfile -File tools\ram_guard.ps1 -TargetPid 17812 -FloorGB 1.2

param(
    [Parameter(Mandatory = $true)][int]$TargetPid,
    [double]$FloorGB = 1.2,
    [int]$IntervalSec = 20,
    [string]$LogPath = "bench\out\ram_guard.log"
)

$dir = Split-Path -Parent $LogPath
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

function Write-Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $LogPath -Value $line
}

Write-Log "guard started: pid=$TargetPid floor=${FloorGB}GB interval=${IntervalSec}s"

while ($true) {
    $proc = Get-Process -Id $TargetPid -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Log "target pid $TargetPid has exited; guard stopping"
        break
    }

    $os = Get-CimInstance Win32_OperatingSystem
    $freeGB = $os.FreePhysicalMemory / 1MB
    $procGB = $proc.WorkingSet64 / 1GB

    if ($freeGB -lt $FloorGB) {
        Write-Log ("free RAM {0:N2}GB below floor {1:N2}GB; target holding {2:N2}GB - KILLING pid {3}" -f $freeGB, $FloorGB, $procGB, $TargetPid)
        Stop-Process -Id $TargetPid -Force
        Write-Log "killed. Terms already written to the log remain valid; rerun with a lower --limit."
        break
    }
    Start-Sleep -Seconds $IntervalSec
}
