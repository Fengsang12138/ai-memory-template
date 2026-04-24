param(
  [int]$KeepProgress = 30,
  [int]$KeepDecisions = 20,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$argsList = @(
  "--keep-progress", $KeepProgress,
  "--keep-decisions", $KeepDecisions
)
if ($DryRun) {
  $argsList += "--dry-run"
}

python (Join-Path $ScriptDir "prune_memory.py") @argsList

