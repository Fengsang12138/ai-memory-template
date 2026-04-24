param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Summary,
  [string]$SessionPath = "",
  [string]$Next = "",
  [string]$CachePath = "",
  [switch]$Promote
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

$sessionRoot = if ($env:CODEX_SESSION_DIR) { $env:CODEX_SESSION_DIR } else { Join-Path $HOME ".codex/sessions" }

function Get-LatestSessionFile($root) {
  if (-not (Test-Path $root)) { return $null }
  Get-ChildItem -Path $root -Recurse -Filter "*.jsonl" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}

if (-not $SessionPath) {
  $latest = Get-LatestSessionFile $sessionRoot
  if (-not $latest) {
    Write-Error "未找到会话文件（*.jsonl）于 $sessionRoot"
    exit 1
  }
  $SessionPath = $latest.FullName
}

$stamp = Get-Timestamp
$file = if ($Promote) {
  Join-Path $MemDir "progress.md"
} elseif ($CachePath) {
  $CachePath
} else {
  Join-Path $MemDir ".session-cache.md"
}

$parent = Split-Path -Parent $file
if ($parent -and -not (Test-Path $parent)) {
  New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$lines = @(
  "- 时间：$stamp",
  "  - 摘要：$Summary",
  "  - Codex 会话：$SessionPath"
)

if ($Next) {
  $lines += "  - 下一步建议：$Next"
}

Add-Content -Path $file -Value ($lines -join "`n") -Encoding UTF8
if ($Promote) {
  try {
    & (Join-Path $ScriptDir "brief-refresh.ps1") | Out-Null
  } catch {
    Write-Host "Warn: failed to refresh brief.md ($($_.Exception.Message))"
  }
  Write-Host "Promoted session log to $file (+ refreshed brief.md)"
} else {
  Write-Host "Cached session log to $file (not promoted to progress.md)"
}
