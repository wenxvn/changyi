# 计划：抽取医院候选 rerank 边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

完成 P2-S3 第三小步：把医院候选结果的基础排序、区域多样性约束和普通场景三甲数量约束移入 `backend/app/domain/recommendation/pipeline.py`，由 legacy `recommend` 注入区域解析函数继续使用，建立可独立测试的 rerank 边界。

## 非目标

- 不改变医院候选生成、feature 计算、推荐权重、风险惩罚、交通数据或解释文案。
- 不调整“普通/较重/急症”约束阈值，不引入新的公平性指标。
- 不迁移医生推荐、API route 或 Safety Gate。

## 当前基线

- `recommend` 在 `app.py` 内完成综合分排序后，内联执行区域多样性和三甲数量 rerank。
- 推荐稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新 pipeline helper 只接受已评分候选列表、triage level、top_n 和显式 `district_fn` 回调，不读取医院列表、Region 或 Flask。
- 保留当前调整量和排序顺序，`app.py` 只负责生成候选和 feature，domain 负责选择结果。
- 通过候选排序单测、推荐快照和 API smoke 验证行为保持。

## 原子步骤

- [x] 建立医院 rerank domain helper 并接入 legacy `recommend`。
- [x] 新增区域/三甲约束正例和急症旁路测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- rerank 模块不依赖 Web、数据加载、模型或全局数据。
- 急症不应用普通场景的区域/三甲多样性约束。

## 回滚

回退本切片即可恢复 `recommend` 内联 rerank，不涉及数据、模型、规则或 API。

## 验证结果

- `uv run --no-project --with-requirements requirements-dev.txt python -m pytest`：34/34 通过。
- API smoke：11/11 通过，覆盖 v1 health/ready/regions、triage/followups/recommendations、医院/医生读取和 legacy triage/recommend。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot 和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- rerank 模块只依赖标准库和 `recommendation.scoring.clamp`，急症不应用区域/三甲多样性约束。
