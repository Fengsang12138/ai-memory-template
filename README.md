# AI Memory Template

可直接复用的**项目长期记忆**模板，面向 Codex、Claude 与人类协作者共享的长期工作流。

当它位于 `ai-update/projects/ai-memory-template/` 时，这个目录是作者工作源；发布目标是独立仓库 `git@github.com:Fengsang12138/ai-memory-template.git`。被单独 clone 使用时，它本身就是完整模板仓库。

## 两个入口 + 一套协议

| 文件 | 给谁看 |
|---|---|
| `AGENTS.md` | Codex / OpenAI 系 coding agent 入口 |
| `CLAUDE.md` | Claude Code 入口 |
| `memory/AGENT_PROTOCOL.md` | **唯一权威读写规范**，上面两个入口都指向它 |
| `memory.md` | 根级兼容入口（给只会扫描仓库根的旧工具） |

两种 agent 共用同一套 `memory/*`：`brief.md` / `activeContext.md` / `tasks.md` / `decisions.md` / `progress.md` / `glossary.md` / `archive/`。

## 自动化：Claude 侧的 Stop hook

`.claude/settings.json` 自带 `Stop` hook，Claude 每次说完话后 harness 自动跑 `scripts/memory/brief-refresh`。**`brief.md` 无需手动维护**，它永远和 `activeContext/tasks/progress/decisions` 对齐。

progress.md 的实际内容写入仍由 agent 按协议判断价值后手动完成（避免噪声）。

Codex 侧没有等价的 harness hook；Codex 按 `AGENTS.md` 的约定在 turn 结束时自律写回，同一份 `scripts/memory/*` 两边都用。

## 这版模板比旧版多了什么

- 拆出 `memory/AGENT_PROTOCOL.md`：Codex 和 Claude 共用一份读写规则，降低漂移。
- 新增 `CLAUDE.md` + `.claude/settings.json`：Claude Code 的入口 + Stop hook 自动刷 brief。
- `install_memory_bank.py --agent both|codex|claude`：可选装单侧，默认两侧都装。
- `brief.md` 作为默认入口，避免每次全量读大文件。
- `brief-refresh` 自动从 `activeContext/tasks/progress/decisions` 生成摘要。
- `prune` 归档旧进展和旧决策，长期项目更省 token。
- `task` 支持按任务 id 更新 `todo / in-progress / done / blocked` 状态。
- `session-log` / `session-watch` / `session-merge`：本地会话先缓存到 `memory/.session-cache.md`，`--promote` 才进正式进展。
- 更适合 WSL 的换行规范，避免 bash 脚本 `^M`。

## 适用场景

- 会持续几个月以上的长期项目。
- 想在不同 AI 工具、不同机器、不同系统之间共享"项目记忆"。
- 不想把所有历史都塞进 prompt，而是让 agent 按需读取。

## 安装到现有项目

```bash
# 默认：两个 agent 都装
python3 install_memory_bank.py /path/to/your-project

# 只装 Claude 侧
python3 install_memory_bank.py /path/to/your-project --agent claude

# 只装 Codex 侧
python3 install_memory_bank.py /path/to/your-project --agent codex

# 预览
python3 install_memory_bank.py /path/to/your-project --dry-run

# 升级基础设施但不覆盖项目自己的 memory 内容
python3 install_memory_bank.py /path/to/your-project --upgrade-infra
```

如果省略路径，默认安装到当前工作目录。
如你的系统把 Python 3 注册为 `python`，也可以直接用 `python install_memory_bank.py`。

### 安装逻辑

- 复制缺失的 `memory/`、`scripts/memory/`、`memory.md`
- 按 `--agent` 复制 `AGENTS.md` / `CLAUDE.md` / `.claude/settings.json`
- `.claude/settings.json` 是**合并**而非覆盖：保留项目已有 hooks，只按"matcher + command"签名去重后追加
- 合并 `.vscode/tasks.json`
- 追加 `.gitignore` / `.gitattributes` 中必要规则
- 不覆盖你项目里已经存在的 Memory 内容
- `--upgrade-infra` 只刷新 `scripts/memory/`、VS Code tasks、ignore 规则，不覆盖 `AGENTS.md`、`CLAUDE.md`、`memory.md` 或 `memory/*.md`
- `--dry-run` 只输出将执行的动作，不写文件

## 手工复制

也可以把下面这些文件直接拷到你的项目根目录：

```text
AGENTS.md                 # 若用 Codex
CLAUDE.md                 # 若用 Claude Code
.claude/settings.json     # 若用 Claude Code
memory.md
memory/
scripts/memory/
.vscode/tasks.json
.gitignore
.gitattributes
```

## 初始化后的最小使用方式

1. 每次开始任务前，先读 `memory/brief.md`。
2. 需要更多细节时，再读 `memory/activeContext.md` 和 `memory/tasks.md`。
3. 本 turn 有实质产出时，写 `memory/progress.md`（只"值得记的事"才写，空闲问答不写）。
4. 重要取舍写 `memory/decisions.md`。
5. Claude 侧：Stop hook 自动刷新 `brief.md`。Codex 侧：按约定手动跑 `scripts/memory/brief-refresh`。

外部工具只扫描根级 `memory.md` 时，它会引导到真正的 `memory/` 记忆库。

## 常用命令

```bash
scripts/memory/focus "实现登录流程" -d "OAuth2 + 本地 session"
scripts/memory/task "补齐登录页错误提示" -p high
scripts/memory/task --id t20260424010101 --status in-progress
scripts/memory/progress "完成登录接口联调" --files "api/auth.py,web/login.tsx" --next "处理错误码映射"
scripts/memory/session-log "最近会话摘要" --session "/path/to/session.jsonl"
scripts/memory/session-merge --promote
scripts/memory/brief-refresh
scripts/memory/prune --keep-progress 30 --keep-decisions 20
```

## WSL 建议

- 在 WSL 内单独克隆这个模板仓库，再安装到 Linux 侧项目目录。
- 不要依赖 Windows 挂载盘上的 CRLF 脚本直接在 bash 执行。
- `~/.codex/sessions/` 在 Windows 与 WSL 往往不是同一套目录，属于正常现象。

## 维护原则

- 长期记忆放仓库内；原始大对话留在本机 `~/.codex/sessions/` 或 Claude Code transcript 目录。
- `brief.md` 保持短小；`progress.md` / `decisions.md` 定期归档。
- session-only 记录默认留在 `memory/.session-cache.md`，确认有正式价值后再提升为 `progress.md`。
- 模板仓库只维护通用能力，不混入具体业务历史。
- 模板升级优先更新基础设施层，不盲目覆盖项目自己的 memory 内容。
- `ai-update` 内这份子项目是作者工作源，独立模板仓库是发布目标；两者关系是单向同步，不是复杂 git 绑定。
