# Review：Frontend Resources

日期：2026-09-10  
范围：`frontend/src/api/resources.ts`、资源 schema、`frontend/src/pages/ResourcesPage.tsx`、相关样式与契约  
计划：[2026-09-10-frontend-resources.md](../plans/2026-09-10-frontend-resources.md)

## 1. 计划对齐

结论：通过，首版范围已完成。

- 医院首屏索引、医生按 tab 加载、关键词筛选、资料预览和来源状态已实现。
- 地图保持建设中入口，未被当前资源索引伪装完成。
- v1 资源列表契约沿用现有接口，未改变 legacy 行为。

## 2. 系统完整性

结论：通过。

- 页面不直接调用 `fetch`，请求统一经共享 client；运行时 schema 校验医院/医生列表结构。
- 搜索只做展示层字段筛选，不生成医学状态、排序分或官方承诺。
- 医生索引按需加载，且只渲染前 48 条匹配资料，避免资源页无界渲染。
- 来源状态和缺失字段保持显式，详情预览不把索引资料包装成临床结论。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，但当前并行切片没有新的 P1 阻断。

- [P1] 真实医院/医生详情、字段 provenance、地图同步和附近急诊资源尚未具备发布契约。
- [P1] 尚无 Playwright 核心流程、截图 baseline、keyboard/contrast 矩阵和 CI frontend job。
- [P2] 当前医生接口一次返回完整公开资料，后续应补服务端分页/检索，降低大列表传输成本。

## 总结

本切片可用于本地资源浏览演示和继续并行开发；在资源详情、地图、Trust 与质量门禁完成前，不应切换为默认入口或标记 competition-ready。
