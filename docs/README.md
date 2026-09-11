# 项目文档入口

文档描述协作约束、当前事实、长期架构决策、质量门禁和风险；代码是运行事实，二者冲突时先暂停并记录决策。

## 日常阅读顺序

1. `AGENTS.md`
2. `README.md`
3. `docs/status/current.md`
4. `docs/architecture/current-state.md`
5. `docs/risks/register.md`、`docs/quality/quality-gates.md`
6. 与当前任务直接相关的 ADR 或 `docs/POST_REFACTOR_BACKLOG.md`

## 目录

- `architecture/`：当前系统边界。
- `decisions/`：仍影响未来实现的 ADR。
- `plans/`：高层路线图和当前重构收口计划；不为每个小步骤创建新文件。
- `quality/`：验证命令和质量门禁。
- `risks/`：开放风险登记。
- `competition/`：比赛产品、数据、安全和演示材料；迁移过程文档不再作为日常入口。
- `REFACTOR_CHANGELOG.md`：已完成重构里程碑。
- `POST_REFACTOR_BACKLOG.md`：暂不实现的后续任务。

日期使用 `YYYY-MM-DD`，项目时区为 Asia/Shanghai。不得把秘密、真实患者信息、Cookie、令牌或敏感日志写入任何文档。
