# ADR-0019：v1 区域读取使用显式 Application Service

状态：已接受  
日期：2026-09-11  
范围：`/api/v1/ready`、`/api/v1/regions`

## 背景

版本化 blueprint 已能通过 handler registry 复用 legacy 业务，但 ready/regions 仍在路由模块直接创建 `RegionRegistry`。这让 API 层知道 infrastructure 路径，也不利于对区域状态和公开摘要做独立契约测试。

## 决定

- 新增 `RegionReadApplicationService`，只负责活动区域判断和公开摘要读取。
- `create_app` 将 service 注册到 Flask extension；supplier 根据当前 `REGION_ROOT` 配置动态创建 registry，保持测试和配置覆盖行为。
- blueprint 只负责读取配置、组装 v1 success/failure envelope 和返回 HTTP 状态。

## 影响

正向影响：区域读取边界可独立测试，blueprint 不再直接依赖 infrastructure registry。

限制：service 仍由当前 Flask factory 组合；跨城市切换、远程区域数据和正式发布审核不在本 ADR 范围。

## 回滚

删除 extension 注册和 service 调用，恢复 routes.py 的原 registry 读取即可。
