param(
  [int]$Focus = 3,
  [int]$Tasks = 5,
  [int]$Progress = 3,
  [int]$Decisions = 3
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
$pythonCmd = Get-PythonCommand

$argsList = @(
  "--focus", $Focus,
  "--tasks", $Tasks,
  "--progress", $Progress,
  "--decisions", $Decisions
)

& $pythonCmd (Join-Path $ScriptDir "brief_refresh.py") @argsList
