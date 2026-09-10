# 计划：抽取医生资源策略边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

将医生推荐中的就诊资源策略、专家偏好修正和资源错配惩罚移入无 Web/数据读取依赖的纯函数模块，继续缩小 `enhanced_recommend_doctors` 的业务组合范围。

## 非目标

- 不改变医生候选过滤、医院查询、交通/距离计算、推荐权重、医学规则或 API 字段。
- 不改变急症兜底召回、解释文案、模型调用或 Safety Gate。
- 不把内部资源层级或 `fairness` 字段包装成对外医疗/公平性承诺。

## 实施与回滚

- 新增 `backend/app/domain/recommendation/resource_policy.py`，由 `app.py` 兼容导入 `resource_strategy`、`apply_resource_fit` 和 `doctor_resource_mismatch_penalty`。
- 纯函数只接收显式 triage、专家偏好、资源层级、feature 和医院能力输入；数据访问与候选循环保留在 legacy。
- 回退本切片即可恢复 `app.py` 内联资源策略，不涉及数据、模型或 API。

## 验证结果

- 全量 pytest：45/45 通过。
- API 主 smoke：11/11 通过；另加空输入 400 与未知路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot、数据质量和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
