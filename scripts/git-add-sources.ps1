param(
  [string]$BaseDir = "."
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

function Resolve-BaseDir {
  param(
    [string]$Path
  )

  if ([System.IO.Path]::IsPathRooted($Path)) {
    return $Path
  }
  return Join-Path $RepoRoot $Path
}

function Add-ExistingPaths {
  param (
    [string[]]$Paths
  )

  foreach ($path in $Paths) {
    if (Test-Path $path) {
      # Use -C to ensure git runs in repo root regardless of current working directory.
      git -C $RepoRoot add -- $path
    }
  }
}

# Template extension point: add future files by pattern if needed.
function Add-ByPattern {
  param (
    [string]$Root,
    [string[]]$Include
  )

  if (-not (Test-Path $Root)) {
    return
  }

  $files = Get-ChildItem -Path $Root -Recurse -File -Include $Include -ErrorAction SilentlyContinue
  if ($files.Count -gt 0) {
    git -C $RepoRoot add -- ($files | ForEach-Object { $_.FullName })
  }
}

$resolvedBase = Resolve-BaseDir $BaseDir

Add-ExistingPaths @(
  (Join-Path $resolvedBase "README.md"),
  (Join-Path $resolvedBase "environment.yml"),
  (Join-Path $resolvedBase ".gitignore"),
  (Join-Path $resolvedBase "AGENTS.md"),
  (Join-Path $resolvedBase "README.MD"),
  (Join-Path $resolvedBase ".vscode"),
  (Join-Path $resolvedBase "memory"),
  (Join-Path $resolvedBase "scripts")
)

Write-Host "已添加主要源码及配置文件，请运行 git status 进一步确认。"
