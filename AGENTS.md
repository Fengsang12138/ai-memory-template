# AGENTS.md — Codex 入口

本文件是 Codex / OpenAI coding agent 在本仓库的入口。**读写规范以 [`memory/AGENT_PROTOCOL.md`](./memory/AGENT_PROTOCOL.md) 为准**（Codex、Claude、人类协作者共用）；本文件只保留 Codex 特有的补充。

更新时间：2026-04-24（UTC）

## 作用与范围
- 作用：为 Codex 提供稳定的共享上下文入口与写回规范；在每次任务开始前"读"，在任务结束后按价值"写回"。
- 范围：此文件位于仓库根目录，对整个仓库生效。若子目录存在更靠近的 `AGENTS.md`，则就近优先生效；显式用户/对话指令优先级最高。
- Claude Code 入口在 [`CLAUDE.md`](./CLAUDE.md)，两边共用同一份 `memory/AGENT_PROTOCOL.md` 和 `memory/*`。

## 最小动作清单

读写的完整清单见 `memory/AGENT_PROTOCOL.md`。下面是 Codex 侧的 quick 版：

- 动手前：读 `memory/brief.md`；需要细节再读 `memory/activeContext.md` / `memory/tasks.md`。
- 动手后（本 turn 有实质产出时）：写 `memory/progress.md`、必要时写 `decisions.md` / `activeContext.md` / `tasks.md`，**最后手动跑 `scripts/memory/brief-refresh`**（Codex 没有等价的 harness hook，brief 刷新要自己触发）。
- 原始会话不要默认写进 `progress.md`；`session-log` 默认只缓存到 `memory/.session-cache.md`，用 `--promote` 才提升为正式进展。

## 工作流原则
- 小步提交，小改动：避免大规模重排/重命名，保持可审阅性。
- 可追溯：所有写回均附 UTC 时间戳，便于定位与回滚。
- 事实优先：当 Memory 与源码/测试冲突时，以源码/测试为准，同时在 `decisions.md` 记录冲突与处置。
- 少读多检索：默认只读 `brief.md`，历史内容优先用关键词检索，不整文件通读。

## Codex 会话指引（Codex 专属）

- 会话位置默认是 `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`。
- 如在 WSL 与 Windows 双环境切换，二者通常各有独立的 `~/.codex/sessions/`。
- 如需自定义会话目录，可设置环境变量 `CODEX_SESSION_DIR`。
- 推荐把"会话原文"留在本机 `~/.codex/sessions/`，只把摘要、决策与下一步写回仓库 Memory。
- 会话缓存默认是草稿材料，不等于正式进展；不要让自动捕获污染 `progress.md`。

## 脚本与 VS Code 集成

脚本索引见 `memory/AGENT_PROTOCOL.md` 第 5 节。VS Code 用户可从命令面板 `Tasks: Run Task` → `Memory: *` 触发（bash / PowerShell 双通）。

## 质量与风格
- 语言：中文为主，必要时可双语补充；代码注释遵循所在语言常用风格。
- 文档格式：Markdown；时间使用 UTC，格式 `YYYY-MM-DDTHH:MM:SSZ`。
- 不要泄露密钥/令牌；如需演示，使用占位符或本地 `.env.example`。

—— End of AGENTS.md
