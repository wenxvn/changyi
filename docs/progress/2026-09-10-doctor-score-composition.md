# 2026-09-10 医生综合 score 组合边界

## 目标

完成 P2-S3 医生推荐的下一小步：抽取医生基础 feature 的权重组合、可用性/连续照护/历史 `fairness` 加权、风险惩罚和专长加成，保持推荐行为不变。

## 已完成

- 在 `backend/app/domain/recommendation/scoring.py` 新增 `score_doctor_candidate` 纯函数。
- `app.py` 保留医生候选过滤、医院查找、交通/距离和资源策略，改为通过兼容导入调用 score helper。
- 新增基础权重、额外 feature、风险惩罚、专长加成和边界裁剪测试。

## 验证

- 全量 pytest：40/40 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。
- Python compile、Node check、数据校验、推荐快照和 `git diff --check` 通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 未完成与下一步

医院/医生 candidate、explain、资源错配/专家偏好策略和交通 feature 仍未完全拆出；`fairness` 对外语义和逐字段 provenance 仍需审查。下一步继续拆 candidate/explain 组合，不修改医学规则或推荐权重。

## 回滚

回退本切片即可恢复医生 score 在 `app.py` 内联计算，不涉及数据、模型、规则或 API。
