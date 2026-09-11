# Final Refactor Plan

日期：2026-09-11
状态：已完成
变更等级：L2（架构与入口收敛）；医学规则、模型、推荐权重和数据口径冻结

## 目标

把现有并行迁移收敛为一套正式运行基线：React/Vite 成为 Flask 的默认前端，v1 成为正式业务 API，后端组合边界清晰，删除无调用方的 legacy UI、路由、适配器、资源和重复过程文档，并用行为快照、Safety Evaluation 和核心 smoke 证明重构没有改变医学辅助语义。

## 非目标

- 不新增产品页面、API 能力、地图/导航、实时交通、账号、数据库或部署系统。
- 不修改红旗规则、分诊阈值、疾病模型、推荐候选、权重、排序、交通公式、医学文案或数据口径。
- 不修复当前已登记的 Safety Evaluation 缺口和数据质量异常；只验证它们在重构前后保持一致。

## 工作步骤

1. 盘点并收敛后端 runtime、application、domain、infrastructure 的所有权，令 `app.py` 只保留 Flask 启动、组合和 HTTP 适配职责。
2. 盘点全部旧路由和真实调用方；保留有明确兼容调用方的入口，删除被 v1 完全替代且无调用方的入口。
3. 将生产默认 `/` 和 SPA 刷新路径切换到已存在的 React build；新前端只调用 `/api/v1/*`。
4. 添加/运行核心 Routine、Insufficient、Emergency、资源、地图、Trust、Profile 和错误边界 smoke；保持推荐快照 SHA-256 与 Safety baseline。
5. 在切换验证通过后删除 legacy HTML/JS/CSS、无引用 Leaflet/备份/二进制和 dead wrapper；保留数据与脚本仍需要的静态资源。
6. 审计 Python/Node 依赖与维护脚本，不引入第二套实现或测试体系。
7. 将有长期价值的结果合并到 README、current status、architecture、risk/quality、changelog 和 backlog；删除重复的过程性 plan/progress/history/review。

## 验收标准

- `python app.py` 单一启动路径提供 React 首页及 `/triage`、`/resources`、`/map`、`/trust`、`/profile` 刷新。
- 正式前端只请求 `/api/v1/*`；保留的旧接口有明确兼容理由，dead route 和 dead asset 不再存在。
- `app.py` 不再拥有主要医学、推荐、交通、目录或模型实现；各边界有唯一 canonical owner。
- Python、pytest、Safety Evaluation、数据校验、前端 typecheck/test/build 和 API smoke 通过；行为基线无意外变化。
- 当前状态、架构、README、风险和回滚说明与代码事实一致；文档数量和内容明显收敛。

## 回滚

每个切片独立提交；若 cutover 或删除验证失败，恢复对应入口/文件的单个提交，不使用 reset、force push 或覆盖用户改动。医学/推荐快照异常时停止删除并回到上一个已验证边界。

## 记录动作

完成后更新 `docs/status/current.md`、`docs/architecture/current-state.md`、`README.md`、`docs/risks/register.md`、`memory.md`，生成简短 `docs/REFACTOR_CHANGELOG.md` 与 `docs/POST_REFACTOR_BACKLOG.md`，并保留最终 review 证据。
