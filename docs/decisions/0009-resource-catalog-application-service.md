# ADR-0009：以 Application Service 编排 v1 资源目录

状态：已接受  
日期：2026-09-11  
范围：`backend/app/application/resources.py` 与 v1 医院/医生目录适配器

## 背景

资源详情的公开字段 builder 已经独立，但 v1 路由仍在 `app.py` 直接查找医院、真实医生和兼容医生，并决定详情关系。这样会让 HTTP adapter 同时承担目录编排和公开投影选择。

## 决定

- 新增 `ResourceCatalogApplicationService`，通过显式 supplier 注入医院、真实医生和兼容医生集合。
- service 负责索引列表、医院筛选、真实医生优先、兼容医生回退和调用现有公开字段 builder；不负责 Flask、envelope 或 HTTP 状态码。
- `app.py` 只把 query 参数传给 service，并将 `None` 映射为已有 `RESOURCE_NOT_FOUND` envelope。
- 医院目录由 `HospitalRepository` 从 active Region Pack 加载；目录状态为 `provisional`，公开事实、派生能力和未支持字段分别投影。医生详情仍使用公开字段白名单。为避免破坏既有 v1 客户端，列表/详情的旧 source/status 字段暂保留兼容值，但不得作为已核验事实展示。

## 影响

正向影响：v1 资源目录可无 Flask 单测，医院目录不再依赖组合根常量，后续完整 route parity 有清晰的 read-only 接缝。代价：完整 provenance、分页和旧路由收敛仍未完成。

## 回滚

回退 service 接入并恢复 `app.py` 原查找逻辑即可；不需要回滚数据或模型。
