# 2026-09-11 旧分诊路由收敛进度

## 本次完成

- `/api/triage`、`/api/followup` 和 `/api/assistant/process` 已通过 `TriageApplicationService` 编排。
- 保留旧接口的历史 response shape、原始模型字段、assistant 答案拼接、空输入 400 和 JSON envelope。
- v1 仍使用独立的 Safety-first publication，旧接口未被静默改成 v1 语义。

## 验证

- Python compile：通过。
- 全量 pytest：`100/100` 通过。
- characterization snapshot：预期保持既有 SHA-256 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- Safety Evaluation：16 case 基线保持；本切片未修改医学规则。

## 未完成与下一步

完整 legacy parity 还包括疾病预测、推荐、交通、统计和其他助手交互；结构化 follow-up answer API、正式急诊路径、逐字段 provenance 与医学审核仍开放。

## 回滚

恢复旧分诊 handlers 的局部编排并移除本切片 service 方法、测试和记录即可。
