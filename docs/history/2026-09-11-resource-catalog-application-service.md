# H-20260911-002：v1 资源目录 Application Service

- 日期：2026-09-11
- 类型：后端只读资源目录边界 / L2 行为保持重构
- 结果：完成首版

## 事件

将 v1 医院/医生索引与详情的目录查找和兼容回退从 `app.py` 移入 `ResourceCatalogApplicationService`。现有公开字段白名单、来源状态、provenance 和 HTTP envelope 保持不变。

## 证据

service unit、7/7 资源 API smoke、95/95 pytest、Safety Evaluation 和稳定 characterization snapshot 通过；未修改医疗规则、推荐权重、模型或旧入口。

## 后续

继续完整 legacy route parity、逐字段 provenance、交通新鲜度/刷新策略和正式附近急诊路径；本 service 不代表资源已通过正式发布审核。
