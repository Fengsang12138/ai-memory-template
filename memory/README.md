# Memory Bank（记忆库）

此目录用于在长期项目中持久化共享的"上下文、决策与当前焦点"。Codex 通过根目录 `AGENTS.md` 默认使用；如显式安装 Claude Code 支持，Claude 也通过 `CLAUDE.md` 使用同一份 [`AGENT_PROTOCOL.md`](./AGENT_PROTOCOL.md)。

如外部工具只会先寻找仓库根目录的 `memory.md`，请把它当成兼容入口，再继续进入本目录。

如这个模板正在 `ai-update/projects/ai-memory-template/` 中被维护，则本目录是作者工作源的一部分；对外发布时仍只发布模板本身。

## 结构
- `brief.md`：低 token 快速上下文，默认优先加载。
- `handoff.md`：短交接快照，跨 agent/跨会话接手未完工作时优先读取；覆盖式维护，不当历史。
- `activeContext.md`：当前焦点（目标/范围/入口/约束）。
- `tasks.md`：任务清单（优先级/状态/负责人）。
- `decisions.md`：关键决策日志（背景/决策/备选/理由/影响）。
- `progress.md`：工作流水账（变更摘要/涉及文件/下一步）。
- `glossary.md`：名词表与约定。
- `archive/`：历史归档，用于长期项目降 token。
- `memory/.session-cache.md`：会话缓存（默认忽略）；由 `session-log` / `session-cache` / `session-watch` 写入，待确认后用显式 promote 合并入 `progress.md`。

## Token 优化策略
- 默认只加载：`brief.md`；跨 agent 接手时加读 `handoff.md`；需要 active 细节时再读 `activeContext.md` + `tasks.md`。
- 历史细节优先用关键词检索：`rg "关键词" memory/decisions.md memory/progress.md memory/archive/`。
- `progress.md` / `decisions.md` 只保留最近 N 条，旧内容归档到 `memory/archive/`。

## 快速开始
- 前提：系统可用 `python3` 或 `python`。
- 在 VS Code 命令面板运行：`Tasks: Run Task` -> 选择 `Memory: *` 任务。
- 或直接运行脚本（bash）：
  - `scripts/memory/note "关于 API 版本的决定"`
  - `scripts/memory/focus "实现用户登录" -d "OAuth2 + 本地会话，先后端对接"`
  - `scripts/memory/task "实现登录页" -p high`
  - `scripts/memory/task --id t00000000000000 --status done`
  - `scripts/memory/progress "完成登录接口联调，待处理错误码映射"`
  - `scripts/memory/handoff --agent codex --next-agent reviewer --goal "完成登录联调" --next "验证错误码映射" --dirty "api/auth.py,web/login.tsx"`
  - `scripts/memory/session-log "最近会话摘要" --session "/path/to/session.jsonl"`
  - `scripts/memory/session-cache --summary "自动捕获摘要"`
  - `scripts/memory/session-watch --interval 300`
  - `scripts/memory/session-merge --promote`
  - `scripts/memory/brief-refresh`
  - `scripts/memory/prune --keep-progress 30 --keep-decisions 20`
- Windows PowerShell：
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/note.ps1 "关于 API 版本的决定"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/focus.ps1 "实现用户登录" -Details "OAuth2 + 本地会话，先后端对接"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/task.ps1 "实现登录页" -Priority high`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/task.ps1 -Id t00000000000000 -Status done`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/progress.ps1 "完成登录接口联调，待处理错误码映射" -Files "a,b,c" -Next "修正错误码"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/handoff.ps1 -Agent codex -NextAgent reviewer -Goal "完成登录联调" -Next "验证错误码映射" -Dirty "api/auth.py,web/login.tsx"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/session-log.ps1 "最近一次 Codex 对话摘要"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/session-cache.ps1 -Summary "自动捕获摘要"`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/session-watch.ps1 -IntervalSeconds 300`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/session-merge.ps1 -Promote`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/brief-refresh.ps1`
  - `powershell -ExecutionPolicy Bypass -File scripts/memory/prune.ps1 -KeepProgress 30 -KeepDecisions 20`

## 使用约定
- 每次任务开始前先读 `brief.md`。
- 接手他人/其他 agent 的未完工作，或工作区有 dirty files 时，再读 `handoff.md`。
- 对采用本模板写回规则的代理，只在本 turn 有实质产出时写 `progress.md`；纯问答不写。
- 需要交给下一位协作者时更新 `handoff.md`，不要把即时交接塞进 `progress.md`。
- 有重要取舍时写 `decisions.md`。
- 焦点变化时更新 `activeContext.md`。
- 最后刷新 `brief.md`。
- session-only 记录默认留在 `memory/.session-cache.md`，不要和正式项目进展混在一起。
- Claude 支持是可选入口；若启用，Claude auto memory 与仓库里的 `memory/` 仍是两套机制，是否让 Claude 写回由用户或 Claude 工作流明确决定。
- `tasks.md` 的 `owner` 记录人类/团队责任或 `shared`；模型路由建议放进 `handoff.md`。

> 所有条目会带 UTC 时间戳，便于追踪。
