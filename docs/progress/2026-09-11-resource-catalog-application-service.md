# 2026-09-11 资源目录 Application Service 进度

## 本次完成

- 新增 `ResourceCatalogApplicationService`，集中处理 v1 医院/医生索引、医院筛选、详情查找、真实医生优先和兼容医生回退。
- `app.py` v1 资源 handlers 收敛为 service 调用、response envelope 和既有 404 适配；公开字段白名单与 provenance builder 未改变。
- 新增 service unit，覆盖 source marker、医院筛选、公开字段投影、医生回退和未知资源。

## 验证

- Python compile：通过。
- 资源目录 API smoke：7/7 通过，含索引、筛选、详情和医院/医生 404。
- 全量 pytest：95/95 通过。
- characterization snapshot：`legacy_snapshot.json` SHA-256 仍为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- Safety Evaluation：16 case 基线保持；本切片未修改医学逻辑。

## 未完成与下一步

完整 legacy route parity、逐字段 provenance、服务端分页/检索和正式附近急诊路径仍开放；医院目录继续保持 `migration_pending`。

## 回滚

恢复 `app.py` 原 v1 资源查找代码并删除 service、unit test 和本组文档即可。
