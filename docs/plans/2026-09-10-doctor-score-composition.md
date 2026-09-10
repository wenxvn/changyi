# 计划：抽取医生综合 score 组合边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

完成 P2-S3 医生推荐的下一小步：将医生基础 feature 的权重组合、可用性/连续照护/历史 `fairness` 加权、风险惩罚和专长加成抽取为纯函数，缩小 `enhanced_recommend_doctors` 的 score 组合职责。

## 非目标

- 不改变医生/医院数据、医生过滤、候选召回、推荐权重、资源错配惩罚或专家偏好策略。
- 不迁移急症兜底召回、解释文案、交通/距离计算、API route 或 Safety Gate。
- 不把内部 `fairness` 字段改名为对外公平性指标。

## 当前基线

- `enhanced_recommend_doctors` 已有共享 scoring/医院 feature 兼容调用，但医生 base/extra score 公式仍在 `app.py`。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 在 `backend/app/domain/recommendation/scoring.py` 增加 `score_doctor_candidate`，只接受显式 feature、权重和风险惩罚。
- `app.py` 继续负责候选过滤、医院查找、交通/距离和专家资源策略；仅委托 score 组合。
- 通过医生 score 正/负例、全量测试、API smoke 和 characterization snapshot 验证行为保持。

## 原子步骤

- [x] 建立医生综合 score 纯函数并接入 legacy `enhanced_recommend_doctors`。
- [x] 新增基础权重、额外 feature、风险惩罚和专长加成测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- score helper 不依赖 Web、数据加载、模型或全局数据。
- 资源错配惩罚、专家偏好和急症兜底路径保持原位置与语义。

## 回滚

回退本切片即可恢复医生 score 在 `app.py` 内联计算，不涉及数据、模型、规则或 API。

## 验证结果

- `uv run --no-project --with-requirements requirements-dev.txt python -m pytest`：40/40 通过。
- API 主 smoke：11/11 通过；另加 legacy 空推荐 400 和未知 v1 路径 404 边界检查 2/2 通过。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot、数据质量和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 资源错配惩罚、专家偏好、急症兜底召回和解释文案未迁移或改写。
