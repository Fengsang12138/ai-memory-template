# Memory Entry

This root file is a compatibility entry for tools or agents that look for `memory.md` at the repository root.

The canonical memory bank lives in [`memory/`](./memory/):

1. Read [`memory/brief.md`](./memory/brief.md) first.
2. Then read [`memory/activeContext.md`](./memory/activeContext.md) and [`memory/tasks.md`](./memory/tasks.md) if you need active detail.
3. Only read [`memory/decisions.md`](./memory/decisions.md), [`memory/progress.md`](./memory/progress.md), or [`memory/glossary.md`](./memory/glossary.md) when you need deeper history or terminology.

## Purpose

- Keep long-term project memory inside the repository, not only inside chat history.
- Make cross-session recovery cheaper by separating brief context, active focus, tasks, decisions, and progress.
- Let the repository remain the durable source of truth while local session logs stay outside the repo by default.
- Treat Claude/Codex runtime memory as separate from this repository memory bank unless a workflow explicitly syncs a summary back.

## Write-Back Reminder

- Update [`memory/progress.md`](./memory/progress.md) after meaningful work.
- Record important tradeoffs in [`memory/decisions.md`](./memory/decisions.md).
- Refresh [`memory/activeContext.md`](./memory/activeContext.md) and [`memory/tasks.md`](./memory/tasks.md) when focus or next steps change.
- Keep [`memory/brief.md`](./memory/brief.md) short enough to stay a low-token default entry point.
- Keep session-only logs in local runtime storage or `memory/.session-cache.md` until they are explicitly promoted.
