# Review：疾病预测 Application Service

日期：2026-09-11  
范围：`backend/app/application/prediction.py`、prediction route、相关测试  
计划：[2026-09-11-disease-prediction-application-service.md](../plans/2026-09-11-disease-prediction-application-service.md)  
决策：[0012-disease-prediction-application-service.md](../decisions/0012-disease-prediction-application-service.md)

## 1. 计划对齐

结论：通过。prediction route 的模型结果编排已移入 service，HTTP 字段和状态码保持。

## 2. 系统完整性

结论：通过。service 不依赖 Flask、不加载文件、不实现推理或医学规则；unavailable/empty/detail 分支有 unit 覆盖。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 模型低置信度、分布外和医学审核仍未完成；模型输出继续只能作为辅助信息。
- [P1] 完整 legacy route parity、正式急诊路径、逐字段 provenance 和远端 CI 首次运行仍开放。
- [P2] 模型 adapter 的文件加载和版本化仍在 composition root，可作为后续 infrastructure slice。

## 总结

本切片完成了 prediction endpoint 的应用层边界，不代表模型质量或临床安全得到验证。
