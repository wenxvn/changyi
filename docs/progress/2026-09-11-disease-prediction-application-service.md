# 2026-09-11 疾病预测 Application Service 进度

## 本次完成

- 新增 `DiseasePredictionApplicationService` 和 `DiseasePredictionResult`。
- `/api/predict-disease` 保留原输入字段选择、400/503/200 状态码、详情标签和 response shape，仅将模型结果编排移出 route。
- 对 unavailable、空结果和可用详情 enrichment 增加单测。

## 验证

- Python compile：通过。
- 全量 pytest：`102/102` 通过。
- 模型 smoke、Safety Evaluation 和 characterization snapshot：基线保持。

## 未完成与下一步

模型低置信度/分布外评估、完整 legacy route parity、逐字段 provenance、正式附近急诊路径和远端 CI 仍开放；本切片不扩大为医学规则修复。

## 回滚

恢复旧 prediction handler 的模型调用与标签 enrichment，并移除本切片 service、测试和记录即可。
