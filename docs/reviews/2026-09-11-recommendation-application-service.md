# Review：Recommendation Application Service

日期：2026-09-11  
范围：`backend/app/application/recommendation.py`、`app.py` recommendation adapter 和 service tests  
计划：[2026-09-11-recommendation-application-service.md](../plans/2026-09-11-recommendation-application-service.md)  
决策：[0008-recommendation-application-service-boundary.md](../decisions/0008-recommendation-application-service-boundary.md)

## 1. 计划对齐

结论：通过。

- `RecommendationContext` 与 service 已承接结果编排；legacy/v1 输入差异和兼容 response 仍留在 `app.py`。
- 医院/医生调用参数、权重/版本字段、Safety-first publication 和旧入口均保留。

## 2. 系统完整性

结论：通过。

- service 不读取 Flask request，不加载数据，不实现医学规则、交通计算、候选资格或排序算法。
- 既有 domain/application 依赖通过注入组装，避免 service 反向 import legacy module。
- unit、API contract、Emergency publication 和快照共同覆盖输出边界。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 完整 legacy route parity、交通新鲜度/刷新、急症整体排序、资源 provenance 和 Safety Evaluation 已知缺口仍开放。
- [P1] 推荐排序、候选资格或医学规则变更仍需单独 L3 评审；本切片仅是行为保持抽取。
- [P2] `app.py` 仍是 composition root，后续需逐步收敛而不形成新的全局 service locator。

## 总结

Recommendation Application Service 首版达到行为保持的编排边界目标，可继续进行 v1 route parity 和交通生命周期拆分；不能单独宣称推荐质量或医学安全已完成。
