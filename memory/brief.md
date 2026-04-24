# Memory Brief — 快速上下文（低 token）

last_updated: 2026-03-10T00:00:00Z

> 默认只加载本文件 + `memory/activeContext.md` + `memory/tasks.md`。
> 需要历史细节时，优先 `rg` 在 `memory/decisions.md` / `memory/progress.md` / `memory/archive/` 内检索，避免整文件全读。

## 当前焦点（TL;DR）
- （手工维护）一句话说明当前项目目标、关键约束与交付边界。

## 常用入口
- （缺失）请在 `memory/activeContext.md` 的 `## Entry Points` 补齐。

## 关键范围（Scope）
- （缺失）请在 `memory/activeContext.md` 的 `## Scope` 补齐。

## 近期待办（Top 5）
- [ ] (id: t00000000000000, p: med, status: todo, owner: unassigned) 示例任务：初始化项目目标、入口命令与首批待办

## 最近进展（Last 3）
- （无）

## 近期关键决策（Last 3）
- （无）

## 维护约定（省 token）
- 本文件只保留短摘要；长历史入口在 `memory/progress.md` / `memory/decisions.md` / `memory/archive/`。
- 每次任务结束：正式产出写 `progress.md`；重要取舍写 `decisions.md`；然后刷新 `brief.md`。
- 原始或 session-only 会话记录默认留在本地或 `memory/.session-cache.md`，不要自动塞进正式进展。
- 脚本：`scripts/memory/brief-refresh`（刷新本文件）、`scripts/memory/prune`（归档旧记录）。
