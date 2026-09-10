# H-20260910-011：抽取医生结果解释与组装纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将普通医生候选的解释生成、分数快照和结果对象组装移入 `backend/app/domain/recommendation/candidate.py`，legacy `enhanced_recommend_doctors` 保留候选过滤、资源策略和急症兜底职责。

## 证据

49 个 pytest、11 项 API 主 smoke 及 2 项 400/404 边界检查、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院/医生 candidate 过滤、交通组合、急症兜底 explain 和剩余资源组合；保留 legacy/v1 API 兼容，不把 `fairness` 包装成对外公平性承诺。
