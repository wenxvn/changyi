# 2026-09-10 医生资源策略边界

## 目标

抽取医生推荐中的就诊资源策略、专家偏好修正和资源错配惩罚，保持原有推荐行为和安全优先路径。

## 已完成

- 新增 `backend/app/domain/recommendation/resource_policy.py`。
- `app.py` 通过兼容导入调用 `resource_strategy`、`apply_resource_fit` 和 `doctor_resource_mismatch_penalty`。
- 候选过滤、医院查询、交通/距离、急症兜底和 API 输出仍由 legacy 负责。
- 新增急症、较重、普通、专家偏好、资源错配和惩罚上限测试。

## 验证

- 全量 pytest：45/45 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院/医生 candidate、explain、剩余资源组合和交通 feature 仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。下一步继续拆 candidate/explain 组合，不修改医学规则或推荐权重。

## 回滚

回退本切片即可恢复资源策略在 `app.py` 内联计算，不涉及数据、模型、规则或 API。
