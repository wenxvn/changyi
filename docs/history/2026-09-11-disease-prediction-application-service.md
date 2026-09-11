# 历史记录：疾病预测 Application Service

日期：2026-09-11

将旧 `/api/predict-disease` 的模型输出判定和详情症状标签 enrichment 移入注入式 `DiseasePredictionApplicationService`，保留原输入、200/400/503 状态码和 response shape。新增 unit 后全量测试为 102/102；模型 smoke、Safety Evaluation 与稳定快照未变化。本次不修改模型、训练数据、医学规则或分诊策略。
