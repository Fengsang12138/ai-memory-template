from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


VALID_STATUSES = {"todo", "in-progress", "done", "blocked"}
TASK_RE = re.compile(r"^(?P<prefix>\s*-\s+\[)(?P<check>[ xX])(?P<suffix>\]\s+\()(?P<meta>[^)]*)(?P<tail>\).*)$")
TASK_ID_RE = re.compile(r"(?:^|,\s*)id:\s*([^,\s)]+)")


def utc_id() -> str:
    return "t" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def find_active_insert(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Active\s*$", line.strip()):
            return i + 1
    return None


def add_task(path: Path, title: str, priority: str, owner: str) -> None:
    lines = read_lines(path)
    task_id = utc_id()
    entry = f"- [ ] (id: {task_id}, p: {priority}, status: todo, owner: {owner}) {title}"
    insert_at = find_active_insert(lines)

    if insert_at is None:
        if lines and lines[-1].strip():
            lines.extend(["", "## Active", entry])
        else:
            lines.extend(["## Active", entry])
    else:
        lines.insert(insert_at, entry)

    write_lines(path, lines)
    print(f"Added task {task_id}")


def task_id_from_meta(meta: str) -> str | None:
    match = TASK_ID_RE.search(meta)
    if not match:
        return None
    return match.group(1)


def set_metadata_value(meta: str, key: str, value: str) -> str:
    fields = [field.strip() for field in meta.split(",") if field.strip()]
    replaced = False
    for i, field in enumerate(fields):
        if field.startswith(f"{key}:"):
            fields[i] = f"{key}: {value}"
            replaced = True
            break
    if not replaced:
        insert_at = 1
        for i, field in enumerate(fields):
            if field.startswith("p:"):
                insert_at = i + 1
                break
        fields.insert(insert_at, f"{key}: {value}")
    return ", ".join(fields)


def update_status(path: Path, task_id: str, status: str) -> None:
    if status not in VALID_STATUSES:
        raise SystemExit(f"Invalid status: {status}. Use one of: {', '.join(sorted(VALID_STATUSES))}")

    lines = read_lines(path)
    found = False
    for i, line in enumerate(lines):
        match = TASK_RE.match(line)
        if not match:
            continue
        if task_id_from_meta(match.group("meta")) != task_id:
            continue
        check = "x" if status == "done" else " "
        meta = set_metadata_value(match.group("meta"), "status", status)
        lines[i] = f"{match.group('prefix')}{check}{match.group('suffix')}{meta}{match.group('tail')}"
        found = True
        break

    if not found:
        raise SystemExit(f"Task id not found: {task_id}")

    write_lines(path, lines)
    print(f"Updated task {task_id} -> {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a task or update a task status in memory/tasks.md.")
    parser.add_argument("--file", required=True, help="Path to memory/tasks.md.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task.")
    add_parser.add_argument("title", nargs="?", help="Task title.")
    add_parser.add_argument("--title", dest="title_option", help="Task title.")
    add_parser.add_argument("--priority", default="med", help="Task priority.")
    add_parser.add_argument("--owner", default="unassigned", help="Task owner.")

    update_parser = subparsers.add_parser("update", help="Update a task status by id.")
    update_parser.add_argument("task_id", nargs="?", help="Task id.")
    update_parser.add_argument("--id", dest="task_id_option", help="Task id.")
    update_parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES), help="New task status.")

    args = parser.parse_args()
    path = Path(args.file)

    if args.command == "add":
        title = args.title_option or args.title
        if not title:
            raise SystemExit("Task title is required.")
        add_task(path, title=title, priority=args.priority, owner=args.owner)
        return 0

    if args.command == "update":
        task_id = args.task_id_option or args.task_id
        if not task_id:
            raise SystemExit("Task id is required.")
        update_status(path, task_id=task_id, status=args.status)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
