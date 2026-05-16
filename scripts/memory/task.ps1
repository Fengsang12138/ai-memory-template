param(
  [Parameter(Position = 0)]
  [string]$Title = "",
  [string]$Priority = "med",
  [string]$Owner = "shared",
  [string]$Id = "",
  [ValidateSet("todo", "in-progress", "done", "blocked")]
  [string]$Status = ""
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

$file = Join-Path $MemDir "tasks.md"
$pythonCmd = Get-PythonCommand
$taskScript = Join-Path $ScriptDir "task_update.py"

if ($Id -or $Status) {
  if (-not $Id -or -not $Status) {
    Write-Error "Use -Id TASK_ID and -Status todo|in-progress|done|blocked together."
    exit 1
  }
  & $pythonCmd $taskScript --file $file update --id $Id --status $Status
} else {
  if (-not $Title) {
    Write-Error "Task title is required, or use -Id with -Status to update an existing task."
    exit 1
  }
  & $pythonCmd $taskScript --file $file add --title $Title --priority $Priority --owner $Owner
}

try {
  & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
} catch {
  Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
}

Write-Host "Updated $file (+ refreshed brief.md)"
