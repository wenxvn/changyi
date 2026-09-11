# Review：症状疾病模型 Adapter

日期：2026-09-11  
范围：`backend/app/infrastructure/models/symptom_disease.py`、`app.py` wrapper、model/prediction tests  
计划：[2026-09-11-symptom-disease-model-adapter.md](../plans/2026-09-11-symptom-disease-model-adapter.md)  
决策：[0017-symptom-disease-model-adapter.md](../decisions/0017-symptom-disease-model-adapter.md)

## 1. 计划对齐

结论：通过。模型加载和推理参数已离开 Flask root，legacy wrapper 和输出契约保持。

## 2. 系统完整性

结论：通过。adapter 不依赖 Flask，不新增推理或医学规则；runtime injected test、真实模型 smoke 和缺失文件降级均覆盖。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 现有模型质量、低置信度、分布外和训练泄漏风险仍开放，输出继续只能作为辅助信息。
- [P1] 完整 route parity、正式急诊路径、逐字段 provenance、E2E/视觉/无障碍门禁和远端 CI 首次运行仍未完成。
- [P2] runtime 仍由 legacy composition root 注入路径和 normalizer，后续再处理模型版本/Region 配置治理。

## 总结

本切片完成模型 infrastructure 边界，不宣称模型质量或临床安全得到验证。
