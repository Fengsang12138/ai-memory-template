from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def ensure_memory_files(mem_dir: Path) -> None:
    mem_dir.mkdir(parents=True, exist_ok=True)
    (mem_dir / "archive").mkdir(parents=True, exist_ok=True)
    for name in [
        "brief.md",
        "activeContext.md",
        "tasks.md",
        "decisions.md",
        "progress.md",
        "glossary.md",
    ]:
        path = mem_dir / name
        if not path.exists():
            write_text(path, "")


def extract_heading_body(markdown: str, heading: str) -> str | None:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.M)
    m = pattern.search(markdown)
    if not m:
        return None
    start = m.end()
    rest = markdown[start:]
    m2 = re.search(r"^##\s+", rest, re.M)
    body = rest[: m2.start()] if m2 else rest
    return body.strip("\n")


def extract_bullets(markdown: str, heading: str, max_items: int) -> list[str]:
    body = extract_heading_body(markdown, heading)
    if not body:
        return []
    out: list[str] = []
    for line in body.splitlines():
        line = line.rstrip()
        if line.startswith("- "):
            out.append(line)
        if len(out) >= max_items:
            break
    return out


def limit_section(markdown: str, heading: str, max_items: int, max_chars: int) -> str | None:
    body = extract_heading_body(markdown, heading)
    if not body:
        return None
    candidates = [line.rstrip() for line in body.splitlines() if line.strip()]
    bullets = [line for line in candidates if line.startswith("- ")]
    lines = bullets if bullets else candidates
    if not lines:
        return None
    limited = [_truncate(line, max_chars) for line in lines[:max_items]]
    return "\n".join(limited)


def extract_tasks(tasks_md: str, max_items: int) -> list[str]:
    body = extract_heading_body(tasks_md, "Active")
    if not body:
        return []
    out: list[str] = []
    for line in body.splitlines():
        line = line.rstrip()
        if line.startswith("- [ ]"):
            out.append(line)
        if len(out) >= max_items:
            break
    return out


@dataclass(frozen=True)
class Entry:
    ts: str
    summary: str


_TIME_START_RE = re.compile(
    r"^- 时间：(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$"
)
_NOTE_START_RE = re.compile(
    r"^- (?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)：(?P<msg>.*)$"
)
_SUMMARY_RE = re.compile(r"^\s+- 摘要：\s*(?P<val>.*)\s*$")
_DECISION_RE = re.compile(r"^\s+- 决策：\s*(?P<val>.*)\s*$")
_SESSION_MARKERS = ("Codex 会话：", "Claude 会话：", "会话文件：", "Session:")


def _truncate(text: str, max_len: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def collect_progress(progress_md: str, max_items: int) -> list[Entry]:
    lines = progress_md.splitlines()
    out: list[Entry] = []
    i = 0
    while i < len(lines):
        m = _TIME_START_RE.match(lines[i].rstrip())
        if not m:
            i += 1
            continue
        ts = m.group("ts")
        j = i + 1
        entry_lines = [lines[i]]
        summary = ""
        while j < len(lines) and not _TIME_START_RE.match(lines[j].rstrip()):
            entry_lines.append(lines[j])
            if not summary:
                sm = _SUMMARY_RE.match(lines[j])
                if sm:
                    summary = sm.group("val").strip()
            j += 1
        entry_text = "\n".join(entry_lines)
        session_only = any(marker in entry_text for marker in _SESSION_MARKERS)
        if summary and "自动捕获" not in summary and not session_only:
            out.append(Entry(ts=ts, summary=_truncate(summary, 160)))
        i = j

    out.sort(key=lambda e: e.ts, reverse=True)
    deduped: list[Entry] = []
    seen = set()
    for e in out:
        key = (e.ts, e.summary)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
        if len(deduped) >= max_items:
            break
    return deduped


def collect_decisions(decisions_md: str, max_items: int) -> list[Entry]:
    lines = decisions_md.splitlines()
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
        decision = ""

        if m_note:
            decision = m_note.group("msg").strip()
            out.append(Entry(ts=ts, summary=_truncate(decision, 160)))
            i += 1
            continue

        j = i + 1
        while j < len(lines) and not _TIME_START_RE.match(lines[j].rstrip()):
            dm = _DECISION_RE.match(lines[j])
            if dm and not decision:
                decision = dm.group("val").strip()
            j += 1
        if decision:
            out.append(Entry(ts=ts, summary=_truncate(decision, 160)))
        i = j

    out.sort(key=lambda e: e.ts, reverse=True)
    deduped: list[Entry] = []
    seen = set()
    for e in out:
        key = (e.ts, e.summary)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
        if len(deduped) >= max_items:
            break
    return deduped


def extract_manual_focus(brief_md: str, max_items: int) -> str | None:
    return limit_section(brief_md, "当前焦点（TL;DR）", max_items=max_items, max_chars=180)


def build_brief(
    now_ts: str,
    manual_focus: str | None,
    entry_points: list[str],
    scope_lines: list[str],
    tasks: list[str],
    progress: list[Entry],
    decisions: list[Entry],
    tasks_limit: int,
    progress_limit: int,
    decisions_limit: int,
) -> str:
    parts: list[str] = []
    parts.append("# Memory Brief — 快速上下文（低 token）")
    parts.append("")
    parts.append(f"last_updated: {now_ts}")
    parts.append("")
    parts.append(
        "> 默认只加载本文件 + `memory/activeContext.md` + `memory/tasks.md`。\n"
        "> 需要历史细节时，优先 `rg` 在 `memory/decisions.md` / `memory/progress.md` / `memory/archive/` 内检索，避免整文件全读。"
    )
    parts.append("")

    parts.append("## 当前焦点（TL;DR）")
    if manual_focus and manual_focus.strip():
        parts.append(manual_focus.rstrip())
    else:
        parts.append("- （手工维护）一句话说明当前目标/约束/范围。")
    parts.append("")

    parts.append("## 常用入口")
    if entry_points:
        parts.extend(entry_points)
    else:
        parts.append("- （缺失）请在 `memory/activeContext.md` 的 `## Entry Points` 补齐。")
    parts.append("")

    parts.append("## 关键范围（Scope）")
    if scope_lines:
        parts.extend(scope_lines)
    else:
        parts.append("- （缺失）请在 `memory/activeContext.md` 的 `## Scope` 补齐。")
    parts.append("")

    parts.append(f"## 近期待办（Top {tasks_limit}）")
    if tasks:
        parts.extend(tasks)
    else:
        parts.append("- （无）")
    parts.append("")

    parts.append(f"## 最近进展（Last {progress_limit}）")
    if progress:
        for e in progress:
            parts.append(f"- {e.ts}：{e.summary}")
    else:
        parts.append("- （无）")
    parts.append("")

    parts.append(f"## 近期关键决策（Last {decisions_limit}）")
    if decisions:
        for e in decisions:
            parts.append(f"- {e.ts}：{e.summary}")
    else:
        parts.append("- （无）")
    parts.append("")

    parts.append("## 维护约定（省 token）")
    parts.append("- 本文件只保留短摘要；长历史入口在 `memory/progress.md` / `memory/decisions.md` / `memory/archive/`。")
    parts.append("- 每次任务结束：正式产出写 `progress.md`；重要取舍写 `decisions.md`；然后刷新 `brief.md`。")
    parts.append("- 原始或 session-only 会话记录默认留在本地或 `memory/.session-cache.md`，不要自动塞进正式进展。")
    parts.append("- 脚本：`scripts/memory/brief-refresh`（刷新本文件）、`scripts/memory/prune`（归档旧记录）。")
    parts.append("")

    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh memory/brief.md (low-token summary).")
    parser.add_argument("--focus", type=int, default=3, help="Max current focus lines to keep.")
    parser.add_argument("--tasks", type=int, default=5, help="Max active tasks to list.")
    parser.add_argument("--progress", type=int, default=3, help="Max progress entries to list.")
    parser.add_argument("--decisions", type=int, default=3, help="Max decision entries to list.")
    args = parser.parse_args()

    root = repo_root_from_script(Path(__file__))
    mem_dir = root / "memory"
    ensure_memory_files(mem_dir)

    brief_path = mem_dir / "brief.md"
    active_context_path = mem_dir / "activeContext.md"
    tasks_path = mem_dir / "tasks.md"
    decisions_path = mem_dir / "decisions.md"
    progress_path = mem_dir / "progress.md"

    now_ts = utc_now_ts()

    brief_existing = read_text(brief_path)
    focus_limit = max(args.focus, 0)
    tasks_limit = max(args.tasks, 0)
    progress_limit = max(args.progress, 0)
    decisions_limit = max(args.decisions, 0)
    manual_focus = extract_manual_focus(brief_existing, max_items=focus_limit)

    active_context = read_text(active_context_path)
    entry_points = extract_bullets(active_context, "Entry Points", max_items=8)
    scope_lines = extract_bullets(active_context, "Scope", max_items=8)

    tasks_md = read_text(tasks_path)
    active_tasks = extract_tasks(tasks_md, max_items=tasks_limit)

    progress_md = read_text(progress_path)
    recent_progress = collect_progress(progress_md, max_items=progress_limit)

    decisions_md = read_text(decisions_path)
    recent_decisions = collect_decisions(decisions_md, max_items=decisions_limit)

    brief = build_brief(
        now_ts=now_ts,
        manual_focus=manual_focus,
        entry_points=entry_points,
        scope_lines=scope_lines,
        tasks=active_tasks,
        progress=recent_progress,
        decisions=recent_decisions,
        tasks_limit=tasks_limit,
        progress_limit=progress_limit,
        decisions_limit=decisions_limit,
    )
    write_text(brief_path, brief)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
