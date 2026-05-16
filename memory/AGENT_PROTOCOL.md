# Agent Protocol — 共享 Memory Bank 读写规范

本文件是项目级 Memory Bank 的**共用协议源**。
- `../AGENTS.md` 是默认安装的 Codex / OpenAI 系 agent 入口，指向本文件。
- `../CLAUDE.md` 是可选安装的 Claude Code 入口，启用后也指向本文件。
- 各 agent 入口只保留各自工具链特有的补充（会话路径、harness hook、工具约定），**读写规范以本文件为准**。

更新时间：2026-05-01（UTC）

## 1. 读（每次任务开始前）

默认按下列顺序，**按需递进**、不要整文件通读：

1. `memory/brief.md`——低 token 默认入口，只读它也应能继续工作。
2. `memory/handoff.md`——短交接快照；接手未完工作、跨 agent 切换、工作区有 dirty files 时必读。
3. `memory/activeContext.md`——当前焦点/目标/范围/约束；需要细节时读。
4. `memory/tasks.md`——任务清单与状态；需要待办细节时读。
5. `memory/decisions.md`——按关键词检索，不通读。
6. `memory/progress.md`——按关键词或时间窗检索，不通读。
7. `memory/glossary.md`——遇到术语歧义时再读。
8. `memory.md`（仓库根）——只是兼容入口，别停留在这里。

## 2. 写（每次任务结束前）

**不是每个 turn 都写**。只在本 turn 产生"值得记的事"时写回：

| 触发条件 | 写入文件 |
|---|---|
| 改了代码、完成了可交付产出、有下一步动作 | `memory/progress.md` |
| 发生关键取舍（技术/产品/架构） | `memory/decisions.md` |
| 焦点或范围变化 | `memory/activeContext.md` |
| 新增、拆分、完结任务 | `memory/tasks.md` |
| 出现新术语/缩写/约定 | `memory/glossary.md` |
| 需要另一位协作者或另一个 agent 接手当前未完状态 | `memory/handoff.md` |

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
- **任务 owner 不当模型路由**：`tasks.md` 的 `owner` 表示人类/团队责任或 `shared`；若只是建议 Codex、Claude、某个模型或工具接手，写入 `memory/handoff.md` 的 `suggested_next_agent` 或 Notes。

### 2.2 Handoff 写入规则（接手丝滑度）

`memory/handoff.md` 是**覆盖式当前状态**，不是历史。它回答"下一位协作者现在该怎么接"：

- `last_agent`：刚刚工作的 agent / 人类 / 工具。
- `suggested_next_agent`：建议下一位接手者；没有明确建议就写 `unassigned`。
- `mode`：如 `planning` / `implementation` / `verification` / `handoff`。
- `Current Goal`：本轮未完成或刚完成的具体目标。
- `Next Action`：下一位接手后最应该做的一步。
- `Dirty Files`：已知未提交、未合并、需要小心审阅的文件。
- `Do Not Touch`：本轮不要自动重排、覆盖、清理或迁移的文件/数据。
- `Open Questions`：继续前必须问用户或验证的问题。

当只是完成了干净、封闭的小任务且没有交接风险，可以不更新 handoff。跨 agent 切换、工作区有 dirty files、用户明确要求"下次接着做"时，必须更新。

### 2.3 什么是"值得记的事"

写之前先问自己：**半年后的我 / 另一个 agent 读到这一条会不会受益？** 如果答案是"大概不会"，就不要写。

**值得记**：架构取舍、范围变化、术语引入、跨会话才能接上的上下文、用户明确要求保留的偏好。

**不值得记**：
- 总结"我刚才做了什么"（progress 的摘要一行足够，别展开）
- "下一步打算做 X"而 X 已经在 tasks.md 里
- 次级视觉/文案偏好（密度、颜色、命名风格）——除非反复冲突过，否则走轻量 note
- 本轮对话内的中间思路（那是 session cache 的职责）
- 另一个 agent 的表达风格、工具习惯或文档格式偏好，除非它违反共享协议或阻塞工作。

### 2.4 前端截图验证限制

为避免 Codex / Claude 对话被浏览器截图、批注图、base64 图像结果撑大，前端修改后的默认验证方式改为**非截图优先**：

- **默认不主动截图验证**：改完前端后，不要自行调用浏览器截图、Computer Use 截图、Playwright screenshot、`view_image` 或任何会把页面图片塞进对话的工具。
- **必须有用户显式要求才截图**：只有当用户明确说"截图验证"、"打开浏览器看"、"发图给我看"、"用浏览器验收"等同义指令时，才进行截图或视觉验收。
- **常规验证替代方案**：优先使用代码检查、构建、lint、静态文本/DOM/CSS inspection、浏览器 URL/服务状态检查；必要时在最终回复说明"未截图验证，因为当前规则要求显式触发"。
- **用户已打开浏览器不等于授权截图**：除非用户这轮明确要求看图或验收视觉，否则不要因为浏览器已打开就自动截图。
- **若必须截图，先收窄范围**：优先单张、裁剪、小 viewport、低频率；截图后只做必要判断并尽快收口。

## 3. 原则

- **事实优先**：Memory 与源码/测试冲突时以源码/测试为准；冲突本身写进 `decisions.md`。
- **少读多检索**：`rg "关键词" memory/decisions.md memory/progress.md memory/archive/`。
- **时间戳**：写回都用 UTC `YYYY-MM-DDTHH:MM:SSZ`。
- **小步**：一次写回只对应一次有意义产出，别攒一大块。
- **会话原文不入库**：Codex `~/.codex/sessions/`、Claude Code transcript 都留在本机；只把"摘要+决策+下一步"写进仓库 memory。
- **session-only 草稿**：`session-log`/`session-watch` 默认写 `memory/.session-cache.md`，确认有价值时再 `--promote` 进 `progress.md`。
- **风格差异不是 bug**：只有违反共享协议、破坏测试/数据、阻塞下一步时才修另一个 agent 的产物；纯风格差异不作为问题处理。

## 4. 归档与 bloat 控制

长期项目必跑：

```bash
scripts/memory/prune --keep-progress 30 --keep-decisions 20
```

把超出阈值的旧条目推到 `memory/archive/`。`brief.md` 由 `brief-refresh` 自动重算，不用手动维护长度。

## 5. 脚本索引（Codex 默认，Claude 可选共用）

```
scripts/memory/focus <目标> [-d <细节>]        # 更新 activeContext.md
scripts/memory/task <标题> [-p high|med|low]   # 追加任务
scripts/memory/task --id <id> --status <状态>  # 更新任务状态
scripts/memory/progress <摘要> [--files ...] [--next ...]
scripts/memory/note <备注>                     # 快速写 decisions.md
scripts/memory/handoff --goal <目标> --next <下一步> [--agent ...] [--dirty ...]
scripts/memory/brief-refresh                   # 刷新 brief.md
scripts/memory/prune [--keep-progress N] [--keep-decisions N]
scripts/memory/session-log / session-cache / session-watch / session-merge
```

所有脚本都有 `.ps1` 对应版本。VS Code 用户可从命令面板 `Tasks: Run Task` → `Memory: *` 触发。

## 6. 承诺

- 动手改代码前先读 `memory/brief.md`；其余文件按需加载。
- 接手未完工作或切换 agent 时读 `memory/handoff.md`。
- 工具只识别根级 `memory.md` 时，继续进入 `memory/brief.md`，别停留。
- 约束不明确时，先在 `decisions.md` 留下取舍理由再实现。
- 结束 turn 前按本协议第 2 节写回；有交接风险时更新 `handoff.md`。

—— End of AGENT_PROTOCOL.md
