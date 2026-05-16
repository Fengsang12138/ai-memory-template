# AI Memory Template

可直接复用的**项目长期记忆**模板，默认面向 Codex / OpenAI 系 coding agent；需要时可显式启用 Claude Code 协作入口。

当它位于 `ai-update/projects/ai-memory-template/` 时，这个目录是作者工作源；发布目标是独立仓库 `git@github.com:Fengsang12138/ai-memory-template.git`。被单独 clone 使用时，它本身就是完整模板仓库。

## Codex 默认 + 可选 Claude 协作

| 文件 | 给谁看 |
|---|---|
| `AGENTS.md` | 默认安装的 Codex / OpenAI 系 coding agent 入口 |
| `CLAUDE.md` | 可选的 Claude Code 入口（显式 `--agent both` 或 `--agent claude` 才安装） |
| `memory/AGENT_PROTOCOL.md` | **唯一权威读写规范**，Codex 默认使用；启用 Claude 后两边都指向它 |
| `memory.md` | 根级兼容入口（给只会扫描仓库根的旧工具） |

Codex-only 和 Codex + Claude 协作版都共用同一套 `memory/*`：`brief.md` / `handoff.md` / `activeContext.md` / `tasks.md` / `decisions.md` / `progress.md` / `glossary.md` / `archive/`。

`handoff.md` 是短交接层：当 Codex、人类或显式接入的 Claude Code 在同一个项目里切换时，用它记录当前目标、下一步、dirty files、do-not-touch 和开放问题。它是覆盖式当前状态，不是历史流水。

## 可选自动化：Claude 侧的 Stop hook

只有显式选择 `--agent both` 或 `--agent claude` 时，模板才会安装 `.claude/settings.json`。它自带 `Stop` hook，Claude 每次说完话后 harness 自动跑 `scripts/memory/brief-refresh`。**`brief.md` 无需手动维护**，它会尽量和 `handoff/activeContext/tasks/progress/decisions` 对齐。

progress.md 的实际内容写入仍由 agent 按协议判断价值后手动完成（避免噪声）。
handoff.md 也必须显式写入；Stop hook 不会替你猜下一步。

Codex 侧没有等价的 harness hook；Codex 按 `AGENTS.md` 的约定在 turn 结束时自律写回。同一份 `scripts/memory/*` 在 Codex-only 和 Codex + Claude 协作版里都可用。

## 这版模板比旧版多了什么

- 拆出 `memory/AGENT_PROTOCOL.md`：Codex 默认使用；启用 Claude 后两边共用一份读写规则，降低漂移。
- 新增 `memory/handoff.md` + `scripts/memory/handoff`：把即时交接从长期历史里分离出来，减少 GPT/Claude 切换时互相误判。
- 保留可选 `CLAUDE.md` + `.claude/settings.json`：Claude Code 的入口 + Stop hook 自动刷 brief。
- `install_memory_bank.py --agent both|codex|claude`：默认 `codex`；显式 `both` 才安装 Codex + Claude 协作版。
- `brief.md` 作为默认入口，避免每次全量读大文件。
- `brief-refresh` 自动从 `handoff/activeContext/tasks/progress/decisions` 生成摘要。
- `prune` 归档旧进展和旧决策，长期项目更省 token。
- `task` 支持按任务 id 更新 `todo / in-progress / done / blocked` 状态。
- `tasks.md` 的 `owner` 默认用 `shared`，模型/工具路由建议放到 `handoff.md`，不再当作长期任务所有权。
- `session-log` / `session-watch` / `session-merge`：本地会话先缓存到 `memory/.session-cache.md`，`--promote` 才进正式进展。
- 更适合 WSL 的换行规范，避免 bash 脚本 `^M`。

## 适用场景

- 会持续几个月以上的长期项目。
- 想先用 Codex 稳定维护项目记忆，并在需要时接入 Claude Code 或其它协作者。
- 不想把所有历史都塞进 prompt，而是让 agent 按需读取。

## 安装到现有项目

```bash
# 默认：Codex-only
python3 install_memory_bank.py /path/to/your-project

# Codex + Claude 协作版
python3 install_memory_bank.py /path/to/your-project --agent both

# 只装 Claude 侧
python3 install_memory_bank.py /path/to/your-project --agent claude

# 只装 Codex 侧（等同默认）
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
- 只有 `--agent both|claude` 会安装或合并 `.claude/settings.json`；合并时保留项目已有 hooks，只按"matcher + command"签名去重后追加
- 合并 `.vscode/tasks.json`
- 追加 `.gitignore` / `.gitattributes` 中必要规则
- 不覆盖你项目里已经存在的 Memory 内容
- `--upgrade-infra` 刷新模板管理的基础设施：`memory/AGENT_PROTOCOL.md`、`memory/README.md`、`scripts/memory/`、VS Code tasks、ignore 规则；不覆盖 `AGENTS.md`、`CLAUDE.md`、`memory.md` 或项目语义记忆（如 `brief.md` / `handoff.md` / `activeContext.md` / `tasks.md` / `progress.md` / `decisions.md`）
- `--dry-run` 只输出将执行的动作，不写文件

### `--agent` 默认值与升级安全

`--agent` 默认值是 `codex`，目的是让新项目和升级项目都先走 Codex-only，不意外塞入 Claude 配置：

| 场景 | `--agent` 默认 | 理由 |
|---|---|---|
| 首次安装（无 `--upgrade-infra`） | `codex` | 先安装 Codex-only 版本，避免默认创建 Claude 入口和 hook |
| 升级（带 `--upgrade-infra`） | `codex` | 刷新共享协议/脚本 + Codex 那侧，不碰 `.claude/settings.json` |

要安装 Claude + Codex 协作版，或给已有 Codex-only 项目接上 Claude，必须**显式传 `--agent`**：`--agent both` 或 `--agent claude`。

### 升级已有项目的安全姿势

对一个已经在用本模板的 Codex 项目，推荐按下列顺序推进，避免 Claude 运行配置悄悄上车：

```bash
# 1. 先 dry-run 看会改什么
python3 install_memory_bank.py /path/to/existing-project --upgrade-infra --dry-run

# 2. 确认 diff 可接受后，只升级共享协议与基础设施（不碰 Claude settings）
python3 install_memory_bank.py /path/to/existing-project --upgrade-infra

# 3. 想给这个项目接上 Claude 时，再单独显式跑一次；要双入口就用 --agent both
python3 install_memory_bank.py /path/to/existing-project --agent claude --dry-run
python3 install_memory_bank.py /path/to/existing-project --agent claude
```

升级永远是幂等的：`scripts/memory/brief-refresh` 在 `brief.md` 实质内容没变时不重写文件（避免 git status 噪声），`.gitignore` / `.gitattributes` / `.vscode/tasks.json` / `.claude/settings.json` 按签名去重合并，同一命令重复跑不会叠加。

## 手工复制

也可以把下面这些文件直接拷到你的项目根目录：

```text
AGENTS.md                 # 默认 Codex 入口
CLAUDE.md                 # 可选：若显式启用 Claude Code
.claude/settings.json     # 可选：若显式启用 Claude Code Stop hook
memory.md
memory/
scripts/memory/
.vscode/tasks.json
.gitignore
.gitattributes
```

## 初始化后的最小使用方式

1. 每次开始任务前，先读 `memory/brief.md`。
2. 接手别人/另一个 agent 的未完工作，或工作区有 dirty files 时，再读 `memory/handoff.md`。
3. 需要更多细节时，再读 `memory/activeContext.md` 和 `memory/tasks.md`。
4. 本 turn 有实质产出时，写 `memory/progress.md`（只"值得记的事"才写，空闲问答不写）。
5. 需要交给下一位协作者时，更新 `memory/handoff.md`。
6. 重要取舍写 `memory/decisions.md`。
7. Codex 侧：按约定手动跑 `scripts/memory/brief-refresh`。若显式启用 Claude 侧，Stop hook 会自动刷新 `brief.md`。

外部工具只扫描根级 `memory.md` 时，它会引导到真正的 `memory/` 记忆库。

## 常用命令

```bash
scripts/memory/focus "实现登录流程" -d "OAuth2 + 本地 session"
scripts/memory/task "补齐登录页错误提示" -p high
scripts/memory/task --id t20260424010101 --status in-progress
scripts/memory/progress "完成登录接口联调" --files "api/auth.py,web/login.tsx" --next "处理错误码映射"
scripts/memory/handoff --agent codex --next-agent claude-code --goal "完成登录联调" --next "验证错误码映射" --dirty "api/auth.py,web/login.tsx"
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

- 长期记忆放仓库内；原始大对话留在本机 `~/.codex/sessions/`，显式启用 Claude 时其 transcript 也只留在本机。
- `brief.md` 保持短小；`progress.md` / `decisions.md` 定期归档。
- `handoff.md` 保持短小且可覆盖；不要把它当历史。
- session-only 记录默认留在 `memory/.session-cache.md`，确认有正式价值后再提升为 `progress.md`。
- 模板仓库只维护通用能力，不混入具体业务历史。
- 模板升级优先更新基础设施层，不盲目覆盖项目自己的 memory 内容。
- `ai-update` 内这份子项目是作者工作源，独立模板仓库是发布目标；两者关系是单向同步，不是复杂 git 绑定。
