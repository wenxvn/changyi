# H-20260910-012：抽取医生 candidate 过滤纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医生查询词构建、科室关系过滤和无科室关键词召回移入 `backend/app/domain/recommendation/candidates.py`，legacy 入口保留数据和模型组合职责。

## 证据

52 个 pytest 和推荐稳定快照通过；快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。未修改医学规则、医生数据、排序或 API 字段。

## 后续

继续拆分医院 candidate 组装、交通组合和急症兜底 explain；不把关键词命中解释为诊断或医生官方专长。
