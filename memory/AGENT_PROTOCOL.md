# Agent Protocol — 共享 Memory Bank 读写规范

本文件是 Codex、Claude 与其它 coding agent 的**共用协议源**。
- `../AGENTS.md` 是 Codex / OpenAI 系 agent 的入口，指向本文件。
- `../CLAUDE.md` 是 Claude Code 的入口，指向本文件。
- 两个入口只保留各自工具链特有的补充（会话路径、harness hook、工具约定），**读写规范以本文件为准**。

更新时间：2026-04-24（UTC）

## 1. 读（每次任务开始前）

默认按下列顺序，**按需递进**、不要整文件通读：

1. `memory/brief.md`——低 token 默认入口，只读它也应能继续工作。
2. `memory/activeContext.md`——当前焦点/目标/范围/约束；需要细节时读。
3. `memory/tasks.md`——任务清单与状态；需要待办细节时读。
4. `memory/decisions.md`——按关键词检索，不通读。
5. `memory/progress.md`——按关键词或时间窗检索，不通读。
6. `memory/glossary.md`——遇到术语歧义时再读。
7. `memory.md`（仓库根）——只是兼容入口，别停留在这里。

## 2. 写（每次任务结束前）

**不是每个 turn 都写**。只在本 turn 产生"值得记的事"时写回：

| 触发条件 | 写入文件 |
|---|---|
| 改了代码、完成了可交付产出、有下一步动作 | `memory/progress.md` |
| 发生关键取舍（技术/产品/架构） | `memory/decisions.md` |
| 焦点或范围变化 | `memory/activeContext.md` |
| 新增、拆分、完结任务 | `memory/tasks.md` |
| 出现新术语/缩写/约定 | `memory/glossary.md` |

**收尾动作**：如上述任一文件被更新，最后必须刷新 `memory/brief.md`（可跑 `scripts/memory/brief-refresh`）。

**空闲/纯问答 turn 不写**。避免污染流水账。

## 3. 原则

- **事实优先**：Memory 与源码/测试冲突时以源码/测试为准；冲突本身写进 `decisions.md`。
- **少读多检索**：`rg "关键词" memory/decisions.md memory/progress.md memory/archive/`。
- **时间戳**：写回都用 UTC `YYYY-MM-DDTHH:MM:SSZ`。
- **小步**：一次写回只对应一次有意义产出，别攒一大块。
- **会话原文不入库**：Codex `~/.codex/sessions/`、Claude Code transcript 都留在本机；只把"摘要+决策+下一步"写进仓库 memory。
- **session-only 草稿**：`session-log`/`session-watch` 默认写 `memory/.session-cache.md`，确认有价值时再 `--promote` 进 `progress.md`。

## 4. 归档与 bloat 控制

长期项目必跑：

```bash
scripts/memory/prune --keep-progress 30 --keep-decisions 20
```

把超出阈值的旧条目推到 `memory/archive/`。`brief.md` 由 `brief-refresh` 自动重算，不用手动维护长度。

## 5. 脚本索引（两 agent 通用）

```
scripts/memory/focus <目标> [-d <细节>]        # 更新 activeContext.md
scripts/memory/task <标题> [-p high|med|low]   # 追加任务
scripts/memory/task --id <id> --status <状态>  # 更新任务状态
scripts/memory/progress <摘要> [--files ...] [--next ...]
scripts/memory/note <备注>                     # 快速写 decisions.md
scripts/memory/brief-refresh                   # 刷新 brief.md
scripts/memory/prune [--keep-progress N] [--keep-decisions N]
scripts/memory/session-log / session-cache / session-watch / session-merge
```

所有脚本都有 `.ps1` 对应版本。VS Code 用户可从命令面板 `Tasks: Run Task` → `Memory: *` 触发。

## 6. 承诺

- 动手改代码前先读 `memory/brief.md`；其余文件按需加载。
- 工具只识别根级 `memory.md` 时，继续进入 `memory/brief.md`，别停留。
- 约束不明确时，先在 `decisions.md` 留下取舍理由再实现。
- 结束 turn 前按本协议第 2 节写回。

—— End of AGENT_PROTOCOL.md
