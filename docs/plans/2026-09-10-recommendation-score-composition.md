# 计划：抽取医院综合 score 组合边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成
- 关联 ADR：`docs/decisions/0004-recommendation-domain-boundaries.md`

## 目标

完成 P2-S3 下一小步：将医院已计算 feature 的权重组合、风险惩罚和对内 feature snapshot 组装移入可独立测试的纯函数，继续缩小 legacy `recommend` 的职责。

## 非目标

- 不改变医院/医生数据、交通样本、推荐权重、风险阈值、排序顺序或 API 字段。
- 不迁移候选生成、距离/交通计算、解释文案、医生排序、API route 或 Safety Gate。
- 不把内部 `fairness` 字段改名为对外公平性指标。

## 当前基线

- `recommend` 已将 feature 计算和 rerank 分别委托给 domain，但医院综合 score 公式和 feature snapshot 仍在 `app.py`。
- 稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 在 `backend/app/domain/recommendation/scoring.py` 增加只接受显式数值、权重和交通展示字典的 `score_hospital_candidate`。
- `app.py` 保留候选循环和输入准备，使用兼容导入调用 score helper；保持原始浮点、四位 feature 精度和百分制 composite 行为。
- 通过 score 正/负例、全量测试、API smoke 和 characterization snapshot 验证无行为漂移。

## 原子步骤

- [x] 建立医院综合 score 纯函数并接入 legacy `recommend`。
- [x] 新增权重、风险惩罚和边界裁剪测试。
- [x] 运行全量测试、API smoke、快照、静态检查和数据质量检查。
- [x] 更新架构、评分卡、风险、进度、历史和 review。

## 验收标准

- 推荐稳定快照哈希不变，legacy/v1 字段和排序不变。
- score helper 不依赖 Web、数据加载、模型或全局数据。
- 风险惩罚仍进入同一公式，未引入新的医学承诺。

## 回滚

回退本切片即可恢复 `recommend` 内联 score 组合，不涉及数据、模型、规则或 API。

## 验证结果

- `uv run --no-project --with-requirements requirements-dev.txt python -m pytest`：37/37 通过。
- API smoke：11/11 通过；legacy/v1 路径的状态码和关键流程保持可用。
- Safety Evaluation Set：16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；既有 `review_required` 缺口保持不变。
- Python compile、Node check、characterization snapshot、数据质量和 `git diff --check` 通过；快照 SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- score helper 仅依赖显式 feature、权重和交通展示字典；未改动推荐权重、风险惩罚语义或对外字段。
