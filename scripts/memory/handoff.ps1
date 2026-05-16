param(
  [string]$Agent = "unassigned",
  [string]$NextAgent = "unassigned",
  [string]$Mode = "handoff",
  [Parameter(Mandatory = $true)]
  [string]$Goal,
  [Parameter(Mandatory = $true)]
  [string]$Next,
  [string]$Dirty = "",
  [string]$DoNotTouch = "",
  [string]$Questions = "",
  [string]$Notes = "",
  [ValidateSet("low", "med", "high")]
  [string]$Confidence = "med"
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

function Convert-ToBullets([string]$Text, [string]$Empty = "（无）") {
  if (-not $Text.Trim()) {
    return "- $Empty"
  }
  $parts = $Text -split "(?:`r`n|`n|;\s+)" | Where-Object { $_.Trim() }
  return (($parts | ForEach-Object { "- $($_.Trim())" }) -join "`n")
}

$file = Join-Path $MemDir "handoff.md"
$stamp = Get-Timestamp

$content = @"
# Handoff Snapshot — 当前交接快照

updated: $stamp
last_agent: $Agent
suggested_next_agent: $NextAgent
mode: $Mode
confidence: $Confidence

## Current Goal
$(Convert-ToBullets $Goal "（未填写）")

## Next Action
$(Convert-ToBullets $Next "（未填写）")

## Dirty Files
$(Convert-ToBullets $Dirty)

## Do Not Touch
$(Convert-ToBullets $DoNotTouch)

## Open Questions
$(Convert-ToBullets $Questions)

## Notes
$(Convert-ToBullets $Notes)
- 本文件是短交接层，不是历史记录；每次实质交接都可以整体覆盖。
- 长期事实进 `brief.md` / `activeContext.md`，历史进 `progress.md` / `decisions.md`。
"@

Set-Content -Path $file -Value $content -Encoding UTF8

try {
  & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
} catch {
  Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
}

Write-Host "Updated $file (+ refreshed brief.md)"
