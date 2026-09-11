# 常医后端重构计划：资源目录 Application Service

状态：已完成  
日期：2026-09-11  
变更等级：L2（只读资源目录编排；不改变医疗策略）

## 目标

把 `/api/v1` 医院/医生索引与详情的目录查找、兼容医生回退和公开 read model 编排移入独立 application service，使 `app.py` 只保留请求参数、v1 envelope 和 HTTP 404 适配。

## 非目标

- 不修改医院常量、医生 JSON、字段白名单、provenance 文案或来源状态。
- 不改变旧 `/api/*` 路由、推荐、分诊、地图和 Trust 行为。
- 不激活医院目录，不把 pending provenance 升级为正式发布，也不引入分页或数据库。

## 验收

- v1 医院/医生索引、`hospital_id` 筛选、详情公开投影、真实医生优先和兼容回退保持原响应。
- application service 不依赖 Flask request、response envelope 或全局 `app` 模块。
- service unit、v1 成功/404 smoke、全量 pytest、快照和 diff 检查通过。

## 回滚

恢复 `app.py` 中原 v1 目录查找实现并移除 service/unit test/记录即可；不影响旧数据、模型和 API 路径。
