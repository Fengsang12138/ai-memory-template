param(
  [int]$IntervalSeconds = 300,
  [string]$Summary = "",
  [string]$SessionDir = "",
  [string]$CachePath = "",
  [string]$StatePath = "",
  [switch]$Once
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
$stateFile = if ($StatePath) { $StatePath } else { Join-Path $MemDir ".session-watch.state" }

function Get-LatestSessionFile($root) {
  if (-not (Test-Path $root)) { return $null }
  Get-ChildItem -Path $root -Recurse -Filter "*.jsonl" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
}

while ($true) {
  $latest = Get-LatestSessionFile $sessionRoot
  if ($latest) {
    $latestPath = $latest.FullName
    $lastPath = ""
    if (Test-Path $stateFile) {
      $lastPath = (Get-Content -Path $stateFile -Raw).Trim()
    }
    if ($latestPath -ne $lastPath) {
      & (Join-Path $ScriptDir "session-cache.ps1") -Summary $Summary -SessionPath $latestPath -CachePath $cacheFile
      Set-Content -Path $stateFile -Value $latestPath -Encoding UTF8
    }
  }

  if ($Once) { break }
  Start-Sleep -Seconds $IntervalSeconds
}
