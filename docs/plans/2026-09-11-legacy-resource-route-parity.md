# 常医后端重构计划：旧资源路由收敛到目录 Application Service

状态：已完成  
日期：2026-09-11  
变更等级：L2（只读资源目录编排；保持接口行为）

## 目标

将旧 `/api/*` 医院/医生索引、详情和医院-医生关系路由也接入已经建立的 `ResourceCatalogApplicationService`，缩小 `app.py` 的目录查找职责，并为后续 v1/legacy route parity 提供同一组可测试的目录选择规则。

## 非目标

- 不改变旧路由 URL、方法、响应 envelope、字段、source 文案、404 状态码或真实/兼容数据选择口径。
- 不修改公开字段白名单、医院/医生 provenance、推荐、分诊、地图、反馈和统计接口。
- 不激活医院目录、引入数据库/分页、修复医学规则或改变急诊路径。

## 实施步骤

1. 在资源 application service 增加旧目录 payload、医院详情、医生筛选、医院-医生关系和增强医生详情的编排方法。
2. 将旧资源路由收敛为参数读取、service 调用和原有 HTTP 适配。
3. 增加 service 与 Flask route smoke，运行编译、全量测试和 characterization snapshot。

## 验收

- 旧索引、详情、关系和增强详情的响应形状与现有数据选择规则保持一致。
- `app.py` 不再直接遍历旧资源集合处理上述路由。
- service unit、legacy route smoke、全量 pytest、快照和 diff 检查通过。

## 回滚

恢复旧资源路由中的查找实现并移除本切片新增测试和记录即可；不修改数据、模型或 URL。

## 实施结果

- `ResourceCatalogApplicationService` 已承载六类旧资源读模型编排；`app.py` 只保留 query 参数、JSON envelope 和原有 404 适配。
- 新增 3 个 legacy route tests；全量 pytest 为 `99/99`。
- 既有 characterization snapshot SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
