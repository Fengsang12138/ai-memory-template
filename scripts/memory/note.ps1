param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Message,
  [switch]$Decision
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

$stamp = Get-Timestamp
$file = Join-Path $MemDir "decisions.md"

if ($Decision) {
  $lines = @(
    "- 时间：$stamp",
    "  - 背景：",
    "  - 决策：$Message",
    "  - 备选：",
    "  - 理由：",
    "  - 影响："
  )
  $entry = ($lines -join "`n").TrimEnd()
} else {
  $entry = "- $stamp：$Message"
}

$contentLines = @()
if (Test-Path $file) {
  $contentLines = Get-Content -Path $file -Encoding UTF8
}

$insertAt = -1
for ($i = 0; $i -lt $contentLines.Count; $i++) {
  if ($contentLines[$i] -match '^##\s+记录') {
    $insertAt = $i + 1
    break
  }
}

if ($insertAt -lt 0) {
  Add-Content -Path $file -Value ($entry + "`n") -Encoding UTF8
} else {
  $newLines = @()
  if ($insertAt -gt 0) {
    $newLines += $contentLines[0..($insertAt - 1)]
  }
  $newLines += ""
  $newLines += ($entry -split "`n")
  $newLines += ""
  if ($insertAt -lt $contentLines.Count) {
    $newLines += $contentLines[$insertAt..($contentLines.Count - 1)]
  }
  Set-Content -Path $file -Value ($newLines -join "`n") -Encoding UTF8
}

try {
  & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
} catch {
  Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
}

Write-Host "Updated $file (+ refreshed brief.md)"
