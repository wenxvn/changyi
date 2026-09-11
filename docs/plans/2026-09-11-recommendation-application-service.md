# 常医后端重构计划：Recommendation Application Service 边界

状态：已完成  
日期：2026-09-11  
变更等级：L3（推荐结果编排边界；仅行为保持，不修改权重、候选资格或医学策略）

## 目标

把 `_build_recommendation_data` 的结果编排从 `app.py` 移到独立 application service。保留 legacy/v1 的输入校验差异、位置解析和旧函数兼容，但让 service 接收已解析的 `RecommendationContext`，只负责调用既有 triage、resource policy、hospital/doctor recommenders、版本权重和 Safety-first publication。

## 非目标

- 不修改医院/医生候选生成、交通可达性、排序权重、场景映射、资源策略、Safety Gate 或医学文案。
- 不删除旧 `/api/recommend`、`/api/recommend/enhanced`、`/api/v1/recommendations`，不改变 URL、状态码、字段和排序快照。
- 不在 service 中重新实现模型、红旗判断、交通计算或数据加载。

## 安全与行为基线

- Emergency 推荐仍使用既有 `safety_first_publication`，医院候选可保持现有急症路径，但疾病候选/模型公开输出继续 abstain。
- 既有 16-case Safety Evaluation、推荐快照和 v1/legacy contract 作为反例与回归基线；本 slice 不修复已知 under-triage。
- 普通/urgent/complex/surgery/first_visit 的场景、专家偏好、位置解析和医生 top-n 必须保持现有调用参数。

## 实施步骤

1. 新增 `RecommendationContext` 和注入式 `RecommendationApplicationService`。
2. 让 `app.py` 负责 legacy/v1 输入解析、区域位置解析和兼容 response；把结果组装交给 service。
3. 增加 service unit tests，补 v1/legacy 正常、Emergency 和非法输入回归。
4. 更新 architecture、migration/status、progress、history、review、risk 和 memory。
5. 运行 Python compile、全量 pytest、Safety Evaluation、推荐快照/API smoke 和 diff 检查。

## 回滚

恢复 `app.py` 的 `_build_recommendation_data` 结果组装并移除 service、unit test 和对应文档即可；不影响旧 API、模型、数据和前端。
