# 常医后端重构计划：Region Read Application Service

状态：已完成  
日期：2026-09-11  
变更等级：L2（版本化只读区域接口拆分；保持接口行为）

## 目标

将 `/api/v1/ready` 与 `/api/v1/regions` 的 Region Pack 读取、活动区域判断和公开摘要组合移入 application service，使 blueprint 不直接实例化 infrastructure registry。

## 非目标

- 不改变 Region Pack 文件、active 状态、区域代码、HTTP 状态码或 v1 response envelope。
- 不新增区域、不改变医学规则、推荐策略、数据口径、认证或部署行为。
- 不在本切片实现跨城市切换、远程区域服务或正式数据发布。

## 验收

- `create_app` 注册显式 Region Read service；service 动态读取当前 `REGION_ROOT` 配置。
- `/api/v1/ready` 和 `/api/v1/regions` 保留原成功/失败 payload；health 不受影响。
- service unit、v1 contract、全量 pytest、API smoke 和 diff 检查通过。

## 回滚

移除 extension service 并恢复 routes.py 内的 `RegionRegistry.from_root` 调用即可；不改变 API URL 或 Region Pack 数据。

## 实施结果

- 新增 `RegionReadApplicationService`，承载活动区域 readiness 和 active-only public summaries。
- `create_app` 通过 Flask extension 注册 service，supplier 动态读取当前 `REGION_ROOT`；v1 blueprint 不再直接实例化 `RegionRegistry`。
- 新增 2 个 service unit tests；全量 pytest 为 `116/116`，Python 语法检查、v1 API smoke 和 `git diff --check` 通过。
