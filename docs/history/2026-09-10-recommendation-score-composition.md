# H-20260910-008：抽取医院综合 score 组合纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医院已计算 feature 的权重组合、风险惩罚和 feature snapshot 组装移入 `backend/app/domain/recommendation/scoring.py`，legacy `recommend` 保留候选生成和输入准备职责。

## 证据

37 个 pytest、11 项 API smoke、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院/医生 candidate、explain、医生 score 和交通 feature；保留 legacy/v1 API 兼容，不把 `fairness` 包装成对外公平性承诺。
