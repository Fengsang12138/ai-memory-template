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

### 2.1 量化写入规则（防 bloat）

为避免每轮对话都堆长条目导致记忆库半年后无法阅读，写回时**必须**遵守以下硬约束：

- **progress.md 单条 ≤ 4 行**：只保留"时间 / 摘要 / 涉及文件 / 下一步"。摘要 ≤ 160 字。
  - **禁止**在 progress 条目里塞"主要产物"编号清单、成就总结、长段叙述——那是 `brief.md` 的职责。
  - 摘要写"做了什么 + 结果"，不写"怎么做到的"。
- **decisions.md 分轻重两档**：
  - **轻量（次级偏好、记个备忘、非取舍类）**：用单行 `- YYYY-MM-DDTHH:MM:SSZ：一句话`。对应脚本 `scripts/memory/note "msg"`（不带 `--decision`）。
  - **完整五段式（真·取舍）**：当且仅当有 ≥2 个被认真考虑过又被否掉的备选方案时才用。对应脚本 `scripts/memory/note "msg" --decision`。
  - 判断口诀：写不出两条以上"备选"就不配进五段式，直接走轻量。
- **合并同会话决策**：一次对话里推导出的多个相关决策，合并为**一个**时间戳块（五段式里的"决策"字段可以用分项），不要拆成 N 个时间戳完全相同的条目。
- **废弃任务直接归档**：`tasks.md` 里不保留"已废弃"墓碑段。需要保留历史时剪到 `memory/archive/tasks-archive.md`，主文件只列活任务。
- **决策字段别和 progress 重复**：若某条信息已经在 progress 的"下一步建议"里写过，就别再开一条 decision 说"决定下一步做 X"。

### 2.2 什么是"值得记的事"

写之前先问自己：**半年后的我 / 另一个 agent 读到这一条会不会受益？** 如果答案是"大概不会"，就不要写。

**值得记**：架构取舍、范围变化、术语引入、跨会话才能接上的上下文、用户明确要求保留的偏好。

**不值得记**：
- 总结"我刚才做了什么"（progress 的摘要一行足够，别展开）
- "下一步打算做 X"而 X 已经在 tasks.md 里
- 次级视觉/文案偏好（密度、颜色、命名风格）——除非反复冲突过，否则走轻量 note
- 本轮对话内的中间思路（那是 session cache 的职责）

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
