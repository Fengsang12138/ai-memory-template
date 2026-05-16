Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..\\..")
$MemDir = Join-Path $RootDir "memory"

function Get-Timestamp {
  (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Get-PythonCommand {
  foreach ($cmd in @("python3", "python")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
      return $cmd
    }
  }
  throw "Python interpreter not found. Install python3 or python."
}

function Ensure-Files {
  if (-not (Test-Path $MemDir)) {
    New-Item -ItemType Directory -Path $MemDir -Force | Out-Null
  }

  $archiveDir = Join-Path $MemDir "archive"
  if (-not (Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
  }

  foreach ($name in @("brief.md", "handoff.md", "activeContext.md", "tasks.md", "decisions.md", "progress.md", "glossary.md")) {
    $path = Join-Path $MemDir $name
    if (-not (Test-Path $path)) {
      New-Item -ItemType File -Path $path -Force | Out-Null
    }
  }
}
