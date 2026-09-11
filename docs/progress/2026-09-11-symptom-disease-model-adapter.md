# 2026-09-11 症状疾病模型 Adapter 进度

## 本次完成

- 本地模型路径检查、lazy load、runtime 错误缓存、inference 参数和详情/非详情投影已移入 `SymptomDiseaseModelAdapter`。
- `app.py:predict_disease_name` 继续保留兼容入口，仅代理 adapter；prediction endpoint contract 未变。
- 增加 injected runtime、top-k/normalization 和缺失文件降级测试。

## 验证

- Python compile：通过。
- 全量 pytest：`110/110` 通过。
- 模型 smoke、prediction API smoke、Safety Evaluation、characterization snapshot：基线保持。

## 未完成与下一步

模型低置信度/分布外/泄漏评估、完整 legacy parity、正式急诊路径、逐字段 provenance、E2E/视觉矩阵和远端 CI 仍开放。

## 回滚

恢复旧 model loader/predictor 代码并移除 adapter、测试和记录即可。
