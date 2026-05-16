from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def repo_root_from_script(script_path: Path) -> Path:
    return script_path.resolve().parents[2]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class Entry:
    ts: str
    raw: str


_TIME_START_RE = re.compile(
    r"^- 时间：(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$"
)
_NOTE_START_RE = re.compile(
    r"^- (?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)：(?P<msg>.*)$"
)


def split_preamble_and_entries(markdown: str) -> tuple[list[str], list[str]]:
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^##\s+记录", line.strip()):
            return lines[: i + 1], lines[i + 1 :]
    return lines, []


def parse_entries(lines: list[str]) -> list[Entry]:
    out: list[Entry] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m_time = _TIME_START_RE.match(line)
        m_note = _NOTE_START_RE.match(line)
        if not m_time and not m_note:
            i += 1
            continue

        ts = (m_time.group("ts") if m_time else m_note.group("ts")).strip()
        start = i
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if _TIME_START_RE.match(nxt) or _NOTE_START_RE.match(nxt):
                break
            i += 1
        raw = "\n".join(lines[start:i]).strip("\n").rstrip()
        if raw:
            out.append(Entry(ts=ts, raw=raw))
    return out


def update_full_history_pointer(preamble_lines: list[str], new_archive_ref: str) -> list[str]:
    out: list[str] = []
    replaced = False
    for line in preamble_lines:
        if re.match(r"^>\s*完整历史记录：`.*`", line.strip()):
            out.append(f"> 完整历史记录：`{new_archive_ref}`")
            replaced = True
        else:
            out.append(line)
    if replaced:
        return out

    # Best-effort insert near top.
    if out:
        out.insert(1, f"> 完整历史记录：`{new_archive_ref}`")
        out.insert(2, "")
    else:
        out.append(f"> 完整历史记录：`{new_archive_ref}`")
    return out


def unique_archive_path(archive_dir: Path, base_name: str) -> Path:
    today = utc_today()
    candidate = archive_dir / f"{base_name}_{today}_full.md"
    if not candidate.exists():
        return candidate
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")
    return archive_dir / f"{base_name}_{today}_{stamp}_full.md"


def prune_markdown(
    *,
    src_path: Path,
    archive_dir: Path,
    keep: int,
    dry_run: bool,
) -> tuple[int, int, Path | None]:
    original = read_text(src_path)
    if not original.strip():
        return 0, 0, None

    preamble_lines, entry_lines = split_preamble_and_entries(original)
    entries = parse_entries(entry_lines)
    entries.sort(key=lambda e: e.ts, reverse=True)

    keep_count = max(keep, 0)
    kept = entries[:keep_count]

    if not entries or len(entries) <= keep_count:
        return len(entries), len(kept), None

    if dry_run:
        archive_path = unique_archive_path(archive_dir, src_path.stem)
        return len(entries), len(kept), archive_path

    archive_path = unique_archive_path(archive_dir, src_path.stem)
    write_text(archive_path, original)

    archive_ref = f"memory/archive/{archive_path.name}"
    preamble_lines = update_full_history_pointer(preamble_lines, archive_ref)

    out_lines: list[str] = []
    out_lines.extend(preamble_lines)
    out_lines.append("")

    if kept:
        for idx, e in enumerate(kept):
            out_lines.append(e.raw.rstrip())
            if idx != len(kept) - 1:
                out_lines.append("")
    else:
        out_lines.append("- （无）")

    out_lines.append("")
    write_text(src_path, "\n".join(out_lines))
    return len(entries), len(kept), archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune memory/progress.md and memory/decisions.md into memory/archive/.")
    parser.add_argument("--keep-progress", type=int, default=30, help="Entries to keep in memory/progress.md.")
    parser.add_argument("--keep-decisions", type=int, default=20, help="Entries to keep in memory/decisions.md.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files; just report.")
    args = parser.parse_args()

    root = repo_root_from_script(Path(__file__))
    mem_dir = root / "memory"
    archive_dir = mem_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for path, keep in [
        (mem_dir / "progress.md", args.keep_progress),
        (mem_dir / "decisions.md", args.keep_decisions),
    ]:
        total, kept, archive_path = prune_markdown(
            src_path=path,
            archive_dir=archive_dir,
            keep=keep,
            dry_run=args.dry_run,
        )
        if not path.exists():
            continue
        if args.dry_run:
            archive_display = archive_path if archive_path else "(none)"
            print(f"[dry-run] {path}: entries={total}, keep={kept}, archive={archive_display}")
        else:
            ts = utc_now_ts()
            if archive_path is None:
                print(f"{ts} no pruning needed for {path.name}: entries={total}, keep={kept}")
            else:
                print(f"{ts} pruned {path.name}: entries={total} -> keep={kept}; archived to {archive_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
