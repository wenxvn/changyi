# H-20260910-010：抽取医生资源策略纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医生就诊资源策略、专家偏好修正和 H-TriageRank 资源错配惩罚移入 `backend/app/domain/recommendation/resource_policy.py`，legacy `enhanced_recommend_doctors` 保留候选和急症兜底职责。

## 证据

45 个 pytest、11 项 API 主 smoke 及 2 项 400/404 边界检查、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院/医生 candidate、explain、剩余资源组合和交通 feature；保留 legacy/v1 API 兼容，不把 `fairness` 包装成对外公平性承诺。
