from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def utc_now_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


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


def parse_sections(text: str) -> tuple[str, list[str], dict[str, str]]:
    title = "# Active Context — 当前焦点"
    if text:
        for line in text.splitlines():
            if line.startswith("# "):
                title = line
                break

    order: list[str] = []
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip("\n")
                order.append(current_name)
            current_name = line[3:].strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip("\n")
        order.append(current_name)

    return title, order, sections


def unique_archive_path(archive_dir: Path) -> Path:
    base = archive_dir / f"activeContext_{utc_today()}_full.md"
    if not base.exists():
        return base
    stamp = datetime.now(timezone.utc).strftime("%H%M%S")
    return archive_dir / f"activeContext_{utc_today()}_{stamp}_full.md"


def build_output(
    *,
    title_line: str,
    now_ts: str,
    order: list[str],
    sections: dict[str, str],
) -> str:
    parts = [title_line, "", f"last_updated: {now_ts}", ""]
    for index, name in enumerate(order):
        parts.append(f"## {name}")
        body = sections.get(name, "").strip("\n")
        if body:
            parts.append(body)
        parts.append("")
        if index == len(order) - 1:
            continue
    return "\n".join(parts).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Update memory/activeContext.md while preserving existing sections.")
    parser.add_argument("--file", required=True, help="Path to activeContext.md")
    parser.add_argument("--title", required=True, help="Current focus title")
    parser.add_argument("--details", default="", help="Optional detail line")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    archive_dir = file_path.parent / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    existing = read_text(file_path)
    archive_ref = ""
    if existing.strip():
        archive_path = unique_archive_path(archive_dir)
        write_text(archive_path, existing)
        archive_ref = f"memory/archive/{archive_path.name}"

    title_line, order, sections = parse_sections(existing)
    if not order:
        order = ["Active Focus", "Scope", "Entry Points", "Archive"]

    if "Active Focus" not in order:
        order.insert(0, "Active Focus")
    for required in ("Scope", "Entry Points", "Archive"):
        if required not in order:
            order.append(required)

    active_focus = [f"- {args.title}"]
    if args.details:
        active_focus.append(f"  - {args.details}")
    sections["Active Focus"] = "\n".join(active_focus)

    if not sections.get("Scope", "").strip():
        sections["Scope"] = "- （TODO）列出本次涉及文件/模块：\n  - "
    if not sections.get("Entry Points", "").strip():
        sections["Entry Points"] = "- （TODO）补齐入口/命令/宏入口：\n  - "
    sections["Archive"] = f"- 上一次完整快照：`{archive_ref}`" if archive_ref else "- （无）"

    write_text(
        file_path,
        build_output(
            title_line=title_line,
            now_ts=utc_now_ts(),
            order=order,
            sections=sections,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
