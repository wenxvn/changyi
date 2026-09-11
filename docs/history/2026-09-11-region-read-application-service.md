# 历史记录：Region Read Application Service

日期：2026-09-11

## 事件

将 `/api/v1/ready` 与 `/api/v1/regions` 的区域 registry 读取从 blueprint 内联逻辑移到 `RegionReadApplicationService`，并由 `create_app` 通过 extension 注册。

## 结果

- 新增 readiness、active-only summaries 的 service tests。
- 全量 pytest 达到 `116/116`，既有 v1 envelope、状态码和 Region Pack 行为保持。
- 未引入跨城市、远程数据或生产安全行为。
