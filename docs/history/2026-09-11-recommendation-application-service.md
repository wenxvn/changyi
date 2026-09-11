# 2026-09-11：抽取 Recommendation Application Service

## 背景

推荐 domain 已有 candidate、feature、score、rerank 和 traffic seam，但最终结果编排仍集中在 `app.py`，legacy/v1 迁移容易误改顺序、版本字段或 Safety-first 发布。

## 处理

- 新增 `RecommendationContext` 与注入式 `RecommendationApplicationService`。
- 将 triage、resource strategy、医院/医生 recommenders、位置 context、权重/版本字段和 Safety-first publication 组装移出 `_build_recommendation_data`。
- 保留 legacy/v1 解析与兼容 wrapper，使用 service unit、全量 pytest、快照和 Emergency smoke 验证行为。

## 结果

93/93 pytest 通过，推荐快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；未改变医学规则、推荐权重或旧入口。
