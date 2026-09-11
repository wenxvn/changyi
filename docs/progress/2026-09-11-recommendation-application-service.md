# 2026-09-11 Recommendation Application Service

状态：首版完成，保持推荐行为与快照  
变更等级：L3（行为保持的推荐编排重构）  
计划：[2026-09-11-recommendation-application-service.md](../plans/2026-09-11-recommendation-application-service.md)  
决策：[0008-recommendation-application-service-boundary.md](../decisions/0008-recommendation-application-service-boundary.md)

## 已完成

- 新增 `backend/app/application/recommendation.py`，定义 `RecommendationContext` 和注入式 `RecommendationApplicationService`。
- `app.py` 保留 legacy/v1 的输入校验差异、区域位置解析、响应 envelope 和兼容入口；结果编排统一委托 service。
- service 继续调用既有 triage、resource policy、医院/医生推荐、版本权重、htriage projection 和 Safety-first publication。
- 不修改候选生成、交通计算、排序权重、专家偏好、场景映射、医学规则或 API 字段。

## 验证

- `tests/test_recommendation_application_service.py`：2 个 service unit 通过，覆盖 legacy/v1 doctor path、location context、版本字段和 Safety-first publication。
- `./.venv/bin/pytest -q`：93 passed。
- Safety Evaluation Set：16 case，指标仍为 Red Flag Recall `0.9231`、Under-triage `0.0769`、Emergency False Negative `1`。
- 推荐表征快照连续两次 SHA-256：`f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- v1 Emergency curl smoke 保留 `triage_status=EMERGENCY`、疾病候选/普通追问 abstain 和急诊文案。

## 未完成与边界

- 完整 legacy route parity、交通数据刷新/一致性、急症整体排序、结构化 follow-up answer API 和逐字段 provenance 仍未完成。
- service 只保证本次抽取的既有编排行为；任何医学或推荐策略调整必须另立 L3 计划、样例/反例和领域审核。

## 回滚

恢复 `app.py` 的 `_build_recommendation_data` 结果组装并移除 service、unit test 和对应文档即可；不影响 API、模型、数据和前端。
