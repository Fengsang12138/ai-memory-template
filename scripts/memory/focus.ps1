param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Title,
  [string]$Details = ""
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

$file = Join-Path $MemDir "activeContext.md"
$python = Get-PythonCommand
$argsList = @((Join-Path $ScriptDir "update_active_context.py"), "--file", $file, "--title", $Title)
if ($Details) {
  $argsList += @("--details", $Details)
}
& $python @argsList
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

try {
  & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
} catch {
  Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
}

Write-Host "Updated $file (+ refreshed brief.md)"
