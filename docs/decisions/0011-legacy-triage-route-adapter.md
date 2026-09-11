# ADR-0011：旧分诊路由复用 Triage Application Service

状态：已接受  
日期：2026-09-11  
范围：旧 `/api/triage`、`/api/followup`、`/api/assistant/process`

## 背景

v1 分诊已经有独立 application service，但旧路由仍在 `app.py` 自行组合 triage、模型和 htriage 字段。两条路径重复编排，容易在后续 parity 工作中产生不易发现的差异。

## 决定

- 将旧路由的原始 payload 组装放到同一个 `TriageApplicationService`，但不复用 v1 的 Safety-first publication，以保持历史接口行为。
- service 只负责编排注入依赖和 assistant 答案拼接；Flask request 读取、空输入 400 和 JSON envelope 仍在 `app.py`。
- 不修改医学规则和任何安全策略；Safety Evaluation 的已知缺口继续登记为 review required。

## 影响

正向影响：旧分诊路径和 v1 路径有清晰的可测试 application 边界，`app.py` 的业务组装减少。

代价：旧接口继续暴露历史模型/分诊字段，不能将其视为安全发布接口；完整 route parity、结构化 follow-up 和医学审核仍未完成。

## 回滚

恢复旧 handlers 的原始组装即可；不涉及数据、模型或数据库。
