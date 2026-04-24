param(
  [string]$CachePath = "",
  [switch]$Keep,
  [switch]$Promote
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

$cacheFile = if ($CachePath) { $CachePath } else { Join-Path $MemDir ".session-cache.md" }
$progressFile = Join-Path $MemDir "progress.md"

if (-not $Promote) {
  Write-Host "Session cache is not promoted by default. Re-run with -Promote to append it to $progressFile."
  exit 0
}

if (-not (Test-Path $cacheFile) -or (Get-Item $cacheFile).Length -eq 0) {
  Write-Host "No cached session logs to merge."
  exit 0
}

Get-Content -Path $cacheFile | Add-Content -Path $progressFile -Encoding UTF8

if (-not $Keep) {
  Set-Content -Path $cacheFile -Value "" -Encoding UTF8
}

try {
  & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
} catch {
  Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
}

Write-Host "Merged session cache into $progressFile (+ refreshed brief.md)"
