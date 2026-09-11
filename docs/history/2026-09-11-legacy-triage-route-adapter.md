# 历史记录：旧分诊路由收敛

日期：2026-09-11

将旧 `/api/triage`、`/api/followup` 和 `/api/assistant/process` 的结果编排移入 `TriageApplicationService`，保留历史接口输出、答案拼接和错误行为；v1 继续独立使用 Safety-first publication。新增 service 覆盖后全量测试为 100/100，未修改医学规则、模型、推荐或原始数据。Safety Evaluation 已知缺口和结构化 follow-up/正式急诊路径继续开放。
