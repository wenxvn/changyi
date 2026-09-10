# H-20260910-006：抽取医院推荐 feature 纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医院能力、等级、可用性、质量、连续照护、特殊人群适配、风险惩罚和解释生成移入 `backend/app/domain/recommendation/features.py`，保留 legacy 兼容导入。

## 证据

27 个 pytest、11 项 API smoke 和推荐稳定快照通过；快照哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。未修改推荐权重、数据或 API 字段。

## 后续

继续拆分 candidate/score/rerank/explain 和交通可达性边界；在语义审查前不把 `fairness` 作为公平性承诺。
