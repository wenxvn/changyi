# ADR-0010：旧资源路由复用 Resource Catalog Application Service

状态：已接受  
日期：2026-09-11  
范围：旧 `/api/hospitals*`、`/api/doctors*` 路由与 `backend/app/application/resources.py`

## 背景

v1 资源目录已经通过 application service 统一了医院/医生查找和公开详情投影，但旧接口仍在 `app.py` 直接遍历医院、真实医生和兼容医生集合。继续保留两套目录编排会让 route parity 难以验证，也会使后续数据源迁移重复修改。

## 决定

- 旧医院/医生索引、医院详情、医生详情、医院-医生关系和增强医生详情统一调用 `ResourceCatalogApplicationService`。
- service 只返回目录 payload，不依赖 Flask request、response 或状态码；旧路由继续负责既有 HTTP envelope 和 404 文案。
- 保留旧接口有意存在的差异：普通医生详情只查兼容目录，增强详情真实医生优先，`real=0` 的 source marker 仍为 `mock`。

## 影响

正向影响：旧资源路由和 v1 资源路由共享可测试的目录选择规则，`app.py` 的直接资源遍历减少，回滚边界清晰。

代价：旧接口的历史字段和 source 语义继续保留，医院目录 provenance、完整 route parity 和正式资源发布仍未完成。

## 回滚

只需恢复旧 route handler 内的查找代码并撤销对应测试；不涉及数据迁移或数据库变更。
