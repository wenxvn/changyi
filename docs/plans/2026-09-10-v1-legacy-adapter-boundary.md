# v1 legacy adapter 边界计划

状态：已完成

## 目标

把 `/api/v1` 蓝图调用 legacy 组合函数的延迟适配逻辑移入独立 adapter 模块，并补齐 v1 请求校验、错误 envelope、查询过滤和 legacy 兼容的契约回归。

## 非目标

- 不改变任何 v1/legacy URL、HTTP 状态、响应字段、状态枚举或业务结果。
- 不在 adapter 中复制 triage、recommendation、模型或数据访问逻辑。
- 不进行认证、CORS、生产部署或真实数据接入改造。

## 步骤

- [x] 新增独立的延迟 legacy adapter，路由只通过 adapter 调用既有函数。
- [x] 增加 v1 非 JSON、未声明字段、坐标和 region 边界契约测试。
- [x] 验证 v1/legacy 主流程和 response envelope parity。
- [x] 更新进度、历史、复核、状态、架构、质量和风险记录。

## 验收与回滚

- v1 路由仍能延迟加载 legacy 实现，避免导入循环。
- 400 错误包含稳定 `data/meta/error` envelope；合法请求和 legacy 入口保持可用。
- 全量 pytest、API 烟雾、Safety Eval、数据校验、编译检查和快照检查通过。
- 回滚方式：恢复 `routes.py` 内联 lazy handler 并移除 adapter/契约测试/记录。

## 验证记录

- 目标回归：v1 API contract、Safety 和 adapter 相关测试 13/13 通过。
- 全量验证结果已记录在 `docs/progress/2026-09-10-v1-legacy-adapter-boundary.md`。

## 风险

该切片只整理 API 适配边界，不解决 legacy 业务组合；完整 route parity、认证与生产安全仍需后续独立评审。
