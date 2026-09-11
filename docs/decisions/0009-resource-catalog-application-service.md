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
- 所有 source/provenance 字段继续保持现状；医院仍为 `migration_pending`，医生详情仍使用公开字段白名单。

## 影响

正向影响：v1 资源目录可无 Flask 单测，后续完整 route parity 有清晰的 read-only 接缝。代价：医院目录仍是兼容常量，完整 provenance、分页和旧路由收敛仍未完成。

## 回滚

回退 service 接入并恢复 `app.py` 原查找逻辑即可；不需要回滚数据或模型。
