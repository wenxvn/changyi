# Review：资源目录 Application Service

日期：2026-09-11  
范围：`backend/app/application/resources.py`、v1 资源 handlers、资源 service tests  
计划：[2026-09-11-resource-catalog-application-service.md](../plans/2026-09-11-resource-catalog-application-service.md)  
决策：[0009-resource-catalog-application-service.md](../decisions/0009-resource-catalog-application-service.md)

## 1. 计划对齐

结论：通过。索引/筛选/详情/回退编排已移入 service，`app.py` 仍保留 HTTP 参数、envelope 和 404 适配。

## 2. 系统完整性

结论：通过。service 不读取 Flask request，不加载文件，不实现医学判断；公开字段 builder、source marker、provenance 和 legacy 资源集合保持原边界。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 医院/医生逐字段来源、许可证、更新时间、完整 legacy route parity 和正式发布审核仍开放。
- [P1] 正式附近急诊路径、Playwright/E2E、视觉/无障碍矩阵和远端 CI 首次运行仍未完成。
- [P2] 资源列表仍一次返回当前公开索引，分页/检索可作为后续性能切片，但不在本次改变响应契约。

## 总结

本切片为 v1 资源目录建立了可测试的 application boundary，可以继续逐步收敛旧路由；不能宣称资源 provenance 或发布审核已完成。
