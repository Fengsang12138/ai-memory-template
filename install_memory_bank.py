from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parent

MEMORY_SRC = TEMPLATE_ROOT / "memory"
SCRIPTS_SRC = TEMPLATE_ROOT / "scripts" / "memory"
TASKS_SRC = TEMPLATE_ROOT / ".vscode" / "tasks.json"
AGENTS_SRC = TEMPLATE_ROOT / "AGENTS.md"
CLAUDE_SRC = TEMPLATE_ROOT / "CLAUDE.md"
CLAUDE_SETTINGS_SRC = TEMPLATE_ROOT / ".claude" / "settings.json"
MEMORY_ENTRY_SRC = TEMPLATE_ROOT / "memory.md"
PROTOCOL_SRC = MEMORY_SRC / "AGENT_PROTOCOL.md"
MEMORY_README_SRC = MEMORY_SRC / "README.md"
GITIGNORE_SRC = TEMPLATE_ROOT / ".gitignore"
GITATTRIBUTES_SRC = TEMPLATE_ROOT / ".gitattributes"
SKIP_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".swp"}

AGENT_CHOICES = ("both", "codex", "claude")


@dataclass
class InstallReport:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add(self, bucket: str, path: Path, root: Path) -> None:
        relative = path.relative_to(root).as_posix()
        getattr(self, bucket).append(relative)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def should_skip_source(path: Path) -> bool:
    if any(part in SKIP_NAMES for part in path.parts):
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    return False


def copy_tree(
    src: Path,
    dest: Path,
    *,
    overwrite: bool,
    dry_run: bool,
    report: InstallReport,
    root: Path,
    skip_relative_paths: set[str] | None = None,
) -> None:
    if not src.exists():
        return
    skip_relative_paths = skip_relative_paths or set()
    for item in src.rglob("*"):
        if should_skip_source(item.relative_to(src)):
            continue
        rel = item.relative_to(src)
        if rel.as_posix() in skip_relative_paths:
            continue
        target = dest / rel
        if item.is_dir():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue
        existed = target.exists()
        if target.exists() and not overwrite:
            report.add("unchanged", target, root)
            continue
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
        report.add("updated" if existed else "created", target, root)


def copy_file(
    src: Path,
    dest: Path,
    *,
    overwrite: bool,
    dry_run: bool,
    report: InstallReport,
    root: Path,
) -> None:
    if not src.exists():
        return
    if dest.exists() and not overwrite:
        report.add("unchanged", dest, root)
        return
    existed = dest.exists()
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    report.add("updated" if existed else "created", dest, root)


def append_missing_lines(dest: Path, src: Path, *, dry_run: bool, report: InstallReport, root: Path) -> None:
    incoming_lines = src.read_text(encoding="utf-8").splitlines()
    existing_text = dest.read_text(encoding="utf-8", errors="ignore") if dest.exists() else ""
    existing_lines = existing_text.splitlines()
    updated = False
    for line in incoming_lines:
        if line not in existing_lines:
            existing_lines.append(line)
            updated = True
    if not dest.exists() or updated:
        if not dry_run:
            dest.write_text("\n".join(existing_lines).rstrip() + "\n", encoding="utf-8")
        report.add("merged", dest, root)
    else:
        report.add("unchanged", dest, root)


def merge_tasks(existing_path: Path, incoming_path: Path, *, dry_run: bool, report: InstallReport, root: Path) -> None:
    incoming = json.loads(incoming_path.read_text(encoding="utf-8"))

    if not existing_path.exists():
        if not dry_run:
            ensure_dir(existing_path.parent)
            existing_path.write_text(json.dumps(incoming, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.add("created", existing_path, root)
        return

    try:
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fallback = existing_path.with_suffix(existing_path.suffix + ".ai-memory-template")
        if not dry_run:
            fallback.write_text(json.dumps(incoming, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.warnings.append(
            f"{existing_path.relative_to(root).as_posix()} contains invalid JSON; wrote template copy to {fallback.relative_to(root).as_posix()}"
        )
        return

    existing_inputs = {item.get("id") for item in existing.get("inputs", [])}
    incoming_inputs = [item for item in incoming.get("inputs", []) if item.get("id") not in existing_inputs]

    existing_tasks = {item.get("label") for item in existing.get("tasks", [])}
    incoming_tasks = [item for item in incoming.get("tasks", []) if item.get("label") not in existing_tasks]

    changed = False
    if incoming_inputs:
        existing.setdefault("inputs", []).extend(incoming_inputs)
        changed = True
    if incoming_tasks:
        existing.setdefault("tasks", []).extend(incoming_tasks)
        changed = True
    if "version" not in existing and "version" in incoming:
        existing["version"] = incoming["version"]
        changed = True

    if changed:
        if not dry_run:
            existing_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.add("merged", existing_path, root)
    else:
        report.add("unchanged", existing_path, root)


def merge_claude_settings(
    existing_path: Path,
    incoming_path: Path,
    *,
    dry_run: bool,
    report: InstallReport,
    root: Path,
) -> None:
    """Merge .claude/settings.json, preserving any project-specific hooks the user already defined."""
    incoming = json.loads(incoming_path.read_text(encoding="utf-8"))

    if not existing_path.exists():
        if not dry_run:
            ensure_dir(existing_path.parent)
            existing_path.write_text(json.dumps(incoming, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.add("created", existing_path, root)
        return

    try:
        existing = json.loads(existing_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fallback = existing_path.with_suffix(existing_path.suffix + ".ai-memory-template")
        if not dry_run:
            fallback.write_text(json.dumps(incoming, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.warnings.append(
            f"{existing_path.relative_to(root).as_posix()} contains invalid JSON; wrote template copy to {fallback.relative_to(root).as_posix()}"
        )
        return

    changed = False
    incoming_hooks = incoming.get("hooks", {})
    existing_hooks = existing.setdefault("hooks", {})
    for event, entries in incoming_hooks.items():
        existing_entries = existing_hooks.setdefault(event, [])
        # Deduplicate by matcher+command signature so re-running install is idempotent.
        existing_sig = {
            (e.get("matcher", ""), tuple((h.get("type"), h.get("command")) for h in e.get("hooks", [])))
            for e in existing_entries
        }
        for entry in entries:
            sig = (
                entry.get("matcher", ""),
                tuple((h.get("type"), h.get("command")) for h in entry.get("hooks", [])),
            )
            if sig not in existing_sig:
                existing_entries.append(entry)
                existing_sig.add(sig)
                changed = True

    if changed:
        if not dry_run:
            existing_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.add("merged", existing_path, root)
    else:
        report.add("unchanged", existing_path, root)


def install(
    dest_root: Path,
    *,
    upgrade_infra: bool,
    dry_run: bool,
    agent: str,
) -> InstallReport:
    report = InstallReport()
    install_codex = agent in ("both", "codex")
    install_claude = agent in ("both", "claude")

    copy_tree(
        MEMORY_SRC,
        dest_root / "memory",
        overwrite=False,
        dry_run=dry_run,
        report=report,
        root=dest_root,
        skip_relative_paths={"AGENT_PROTOCOL.md", "README.md"} if upgrade_infra else None,
    )
    if upgrade_infra:
        # Protocol docs are template-managed infrastructure. Project-specific
        # memory state such as brief/handoff/activeContext/tasks/progress stays
        # protected by the non-overwriting copy_tree call above.
        copy_file(
            PROTOCOL_SRC,
            dest_root / "memory" / "AGENT_PROTOCOL.md",
            overwrite=True,
            dry_run=dry_run,
            report=report,
            root=dest_root,
        )
        copy_file(
            MEMORY_README_SRC,
            dest_root / "memory" / "README.md",
            overwrite=True,
            dry_run=dry_run,
            report=report,
            root=dest_root,
        )
    copy_tree(
        SCRIPTS_SRC,
        dest_root / "scripts" / "memory",
        overwrite=upgrade_infra,
        dry_run=dry_run,
        report=report,
        root=dest_root,
    )

    # memory.md is agent-neutral; always install (compatibility entry for tools that scan repo root).
    copy_file(
        MEMORY_ENTRY_SRC,
        dest_root / "memory.md",
        overwrite=False,
        dry_run=dry_run,
        report=report,
        root=dest_root,
    )

    if install_codex:
        copy_file(
            AGENTS_SRC,
            dest_root / "AGENTS.md",
            overwrite=False,
            dry_run=dry_run,
            report=report,
            root=dest_root,
        )

    if install_claude:
        copy_file(
            CLAUDE_SRC,
            dest_root / "CLAUDE.md",
            overwrite=False,
            dry_run=dry_run,
            report=report,
            root=dest_root,
        )
        merge_claude_settings(
            dest_root / ".claude" / "settings.json",
            CLAUDE_SETTINGS_SRC,
            dry_run=dry_run,
            report=report,
            root=dest_root,
        )

    merge_tasks(
        dest_root / ".vscode" / "tasks.json",
        TASKS_SRC,
        dry_run=dry_run,
        report=report,
        root=dest_root,
    )
    append_missing_lines(
        dest_root / ".gitignore",
        GITIGNORE_SRC,
        dry_run=dry_run,
        report=report,
        root=dest_root,
    )
    append_missing_lines(
        dest_root / ".gitattributes",
        GITATTRIBUTES_SRC,
        dry_run=dry_run,
        report=report,
        root=dest_root,
    )
    return report


def print_report(report: InstallReport) -> None:
    for label, values in [
        ("Created", report.created),
        ("Updated", report.updated),
        ("Merged", report.merged),
        ("Unchanged", report.unchanged),
    ]:
        if not values:
            continue
        print(f"{label}:")
        for value in values:
            print(f"- {value}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install a shared project memory bank template into an existing project."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target project root. Defaults to current directory.",
    )
    parser.add_argument(
        "--upgrade-infra",
        action="store_true",
        help=(
            "Refresh template-managed infrastructure files (memory/AGENT_PROTOCOL.md, memory/README.md, "
            "scripts/memory/, VS Code tasks, ignore rules) without overwriting AGENTS.md, CLAUDE.md, "
            "memory.md, or project-specific memory content."
        ),
    )
    parser.add_argument(
        "--agent",
        choices=AGENT_CHOICES,
        default=None,
        help=(
            "Which agent entry to install. "
            "'both' installs AGENTS.md + CLAUDE.md + .claude/settings.json; "
            "'codex' installs only AGENTS.md; "
            "'claude' installs only CLAUDE.md + .claude/settings.json. "
            "Default is 'codex' for both fresh installs and --upgrade-infra. "
            "Pass --agent both explicitly for the Codex + Claude collaboration setup, "
            "or --agent claude to add only the Claude entry and Stop hook. "
            "memory/ and scripts/memory/ are always installed because they are agent-neutral."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files.",
    )
    args = parser.parse_args()

    # Codex-only is the conservative default for both fresh installs and
    # upgrades. Claude support stays available through an explicit --agent.
    if args.agent is None:
        resolved_agent = "codex"
        default_note = " (default for --upgrade-infra)" if args.upgrade_infra else " (default for fresh install)"
    else:
        resolved_agent = args.agent
        default_note = " (explicit)"

    dest_root = Path(args.target).resolve()
    if not args.dry_run:
        ensure_dir(dest_root)
    report = install(
        dest_root,
        upgrade_infra=args.upgrade_infra,
        dry_run=args.dry_run,
        agent=resolved_agent,
    )
    print_report(report)
    action = "Would install" if args.dry_run else "Installed"
    print(f"{action} memory bank template into: {dest_root} (agent={resolved_agent}{default_note})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
