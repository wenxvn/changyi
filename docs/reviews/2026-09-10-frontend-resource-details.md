# Review：Frontend Resource Details

日期：2026-09-10  
范围：`backend/app/application/resources.py`、v1 resource detail routes、`frontend/src/api/resources.ts`、resource schemas、`ResourcesPage` 和对应契约  
计划：[2026-09-10-frontend-resource-details.md](../plans/2026-09-10-frontend-resource-details.md)

## 1. 计划对齐

结论：通过，首版范围已完成。

- 医院/医生详情使用版本化只读 endpoint，前端按用户选择加载。
- 公开字段白名单、provenance、404 和错误重试边界已实现。
- 没有修改旧详情接口、医学规则、推荐排序或 legacy 默认入口。

## 2. 系统完整性

结论：通过。

- application builder 不读取 Flask/request，也不把内部评分、床位或原始医生抓取链接带入新详情。
- 前端详情通过共享 client 和 runtime parser 读取；索引、详情和来源状态是不同状态边界。
- pytest 覆盖成功、404 和字段不扩散；前端边界测试覆盖新 API 调用和 provenance 文案。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，但当前切片没有新的 P1 阻断。

- [P1] 医院/医生逐字段来源、许可证、更新时间和正式发布范围仍未登记，详情保持 provisional/migration pending。
- [P1] 正式附近急诊路径、完整 route parity、Playwright/E2E、视觉 baseline、keyboard/contrast 和远端 CI 首次运行仍待完成。
- [P2] 医生索引仍可能一次返回 2,100 条资料；服务端分页/检索可作为后续性能切片。

## 总结

资源详情首版可以用于本地并行前端演示和继续迁移，但不应被解释为已完成 provenance 审核，也不能作为 competition-ready 或默认入口切换依据。
