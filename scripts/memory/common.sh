#!/usr/bin/env sh
set -eu

# Resolve repo root based on this script location
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
MEM_DIR="$ROOT_DIR/memory"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' python3
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    printf '%s\n' python
    return 0
  fi
  echo "Python interpreter not found. Install python3 or python." >&2
  exit 1
}

ensure_files() {
  mkdir -p "$MEM_DIR"
  mkdir -p "$MEM_DIR/archive"
  for f in brief.md activeContext.md tasks.md decisions.md progress.md glossary.md; do
    if [ ! -f "$MEM_DIR/$f" ]; then
      touch "$MEM_DIR/$f"
    fi
  done
}
