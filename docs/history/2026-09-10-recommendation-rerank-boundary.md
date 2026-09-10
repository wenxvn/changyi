# H-20260910-007：抽取医院候选 rerank 纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医院候选的基础分排序、区域多样性约束和普通场景三甲数量约束移入 `backend/app/domain/recommendation/pipeline.py`，legacy `recommend` 通过区域回调接入；急症路径不应用普通场景约束。

## 证据

34 个 pytest、11 项 API smoke、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院/医生 candidate、score、explain 和交通 feature；保留 legacy/v1 API 兼容，不把 `fairness` 包装成对外公平性承诺。
