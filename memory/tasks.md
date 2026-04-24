# Tasks — 任务清单

> 状态：`todo` | `in-progress` | `done` | `blocked`
> 历史（已完成/旧清单）：`memory/archive/`

## Active
- [ ] (id: t00000000000000, p: med, status: todo, owner: unassigned) 示例任务：初始化项目目标、入口命令与首批待办

## Backlog
- [ ] (id: t00000000000001, p: low, status: todo, owner: unassigned) 示例任务：定期执行 `scripts/memory/prune`，归档旧进展与旧决策

## 说明
- 新任务使用脚本追加：`scripts/memory/task "任务标题" -p high|med|low`
- 更新状态使用任务 id：`scripts/memory/task --id t00000000000000 --status done`
- 可在条目后补充链接，如 PR、Issue、设计文档等。
