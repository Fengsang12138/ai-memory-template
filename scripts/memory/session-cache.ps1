param(
  [string]$Summary = "",
  [string]$SessionPath = "",
  [string]$CachePath = "",
  [string]$SessionDir = ""
)

Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptDir "common.ps1")
Ensure-Files

if (-not $Summary) {
  $Summary = "自动捕获（未摘要）"
}

$sessionRoot = if ($SessionDir) { $SessionDir } elseif ($env:CODEX_SESSION_DIR) { $env:CODEX_SESSION_DIR } else { Join-Path $HOME ".codex/sessions" }
$cacheFile = if ($CachePath) { $CachePath } else { Join-Path $MemDir ".session-cache.md" }

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
$lines = @(
  "- 时间：$stamp",
  "  - 摘要：$Summary",
  "  - Codex 会话：$SessionPath"
)

Add-Content -Path $cacheFile -Value ($lines -join "`n") -Encoding UTF8
Write-Host "Cached session log to $cacheFile"
