# CLAUDE.md — Claude Code 入口

本文件是 Claude Code 在本仓库的入口。读写规范以 [`memory/AGENT_PROTOCOL.md`](./memory/AGENT_PROTOCOL.md) 为准（Codex、Claude、人类协作者共用）。

更新时间：2026-05-01（UTC）

## 最小动作清单

- 动手前：读 [`memory/brief.md`](./memory/brief.md)；接手他人/其他 agent 的未完工作时再读 `memory/handoff.md`，需要细节再读 `activeContext.md` / `tasks.md`。
- 动手后（本 turn 有实质产出时）：按协议第 2 节写 `progress.md` / `decisions.md` / `activeContext.md` / `tasks.md`；若需要交给下一位协作者，更新 `memory/handoff.md`；最后跑 `scripts/memory/brief-refresh`。
- 纯问答、查询类 turn **不写回**，避免污染流水账。
- **写之前先看协议 §2.1「量化写入规则」**：progress 单条 ≤4 行；决策先判断轻/重档，轻决策走 `scripts/memory/note`（单行），重决策才用五段式；多决策合并一个时间戳块；废弃任务进 archive，不留墓碑。
- 前端改完后默认不主动截图验证；除非用户显式要求截图/浏览器验收/发图，否则只做非截图检查，详见协议 §2.4。

## Claude Code 特有约定

- **工具映射**：用 `Read` 看 memory 文件，用 `Edit` 做增量写回（比 `Write` 安全），用 `Bash` 跑 `scripts/memory/*`。
- **TodoWrite**：多步任务用 TodoWrite 跟踪，turn 结束时把"已完成"的项同步到 `memory/tasks.md`（`scripts/memory/task --id … --status done`）。
- **Skill 调用**：触发 skill 前后若焦点变化，更新 `activeContext.md`。
- **会话存档**：Claude Code 的 transcript 在本机，不要把原文写进仓库 memory；只写摘要/决策/下一步。
- **模型路由**：建议下一位 agent 或工具时写进 `memory/handoff.md`，不要把 `tasks.md` 的 `owner` 改成模型名来表达路由。

## 自动化：Stop hook

本模板自带 `.claude/settings.json`，配置了 `Stop` hook：Claude 每次说完话后，harness 自动跑 `scripts/memory/brief-refresh`，保证 `brief.md` 尽量和 `handoff/activeContext/tasks/progress/decisions` 对齐。

- hook 只刷新 brief.md，**不**自动写 progress.md——内容写入仍由 Claude 在 turn 内判断价值后手动完成。
- hook 不更新 `handoff.md`；交接内容仍需 Claude 在 turn 内显式写入，避免把空闲问答误记成正式状态。
- 如不需要该 hook，删除 `.claude/settings.json` 里对应条目即可。
- 想进一步自动归档，可加一条 Stop hook 跑 `scripts/memory/prune`（默认未开启，避免新手项目被过早归档干扰）。

## 与 AGENTS.md 的关系

- `CLAUDE.md`（本文件）=  Claude 入口 + Claude 特有约定
- `AGENTS.md` = Codex 入口 + Codex 特有约定（会话 JSONL、WSL 提示）
- `memory/AGENT_PROTOCOL.md` = 两者共用的读写规范（唯一权威源）

读写规则有歧义时以 `AGENT_PROTOCOL.md` 为准。

—— End of CLAUDE.md
