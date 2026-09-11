# 常医后端重构计划：目录索引与统计 Read Model

状态：已完成  
日期：2026-09-11  
变更等级：L2（只读目录索引/统计编排；保持接口行为）

## 目标

将旧 `/api/departments`、`/api/districts` 和 `/api/stats` 的集合派生与统计组装纳入 `ResourceCatalogApplicationService`，完成资源目录 read-model 的又一小步收敛。

## 非目标

- 不改变医院/医生数据、统计字段、固定 top departments、区域顺序、来源/许可状态或 URL。
- 不修改推荐、分诊、交通、地图、模型、医学规则或数据质量口径。
- 不引入数据库、缓存、分页、实时统计或生产认证。

## 验收

- service 不依赖 Flask；索引与统计仍从注入 suppliers 派生。
- 三个旧路由的 response shape、数据数量、排序和统计值保持；service unit、route smoke、全量 pytest、快照和 diff 通过。

## 回滚

恢复旧 route 内部集合/统计代码并移除新增 service 方法、测试和记录即可；不修改数据文件。

## 实施结果

- `ResourceCatalogApplicationService` 已承载科室索引、区域索引和系统统计 read model；旧 routes 只保留 JSON envelope。
- 新增 service 覆盖；全量 pytest 为 `106/106`。
- characterization snapshot 和 Safety Evaluation 基线保持。
