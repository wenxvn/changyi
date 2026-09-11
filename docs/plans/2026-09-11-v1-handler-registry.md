# 常医后端重构计划：v1 Handler Registry 兼容接缝

状态：已完成  
日期：2026-09-11  
变更等级：L2（应用工厂/路由适配解耦；保持接口行为）

## 目标

让 v1 blueprint 优先从当前 Flask application 的显式 handler registry 解析兼容 handler，避免每次请求都反向导入根级 `app` 模块，同时保留旧 lazy import 作为外部调用兼容回退。

## 非目标

- 不改变 v1/legacy URL、方法、状态码、response envelope、医学规则、推荐排序或数据。
- 不在本切片重写 factory 组合、删除 `legacy_adapter`、实现结构化 follow-up 或切换默认前端。
- 不新增认证、跨进程注册、远程服务或生产部署行为。

## 验收

- `app.py` 在 composition 完成后注册全部 v1 兼容 handler；有 Flask context 时 adapter 优先使用 registry。
- 无 context 或未注册时仍可通过既有 lazy import 解析，保证历史调用方兼容。
- registry unit/contract、全量 pytest、v1 API smoke、快照、Safety Evaluation 和 diff 检查通过。

## 回滚

移除 registry 注册与解析优先级，恢复 adapter 直接 lazy import 即可；不影响 route URL 和数据。

## 实施结果

- 新增 `register_legacy_handlers` 和 application extension registry；v1 route 请求不再依赖每次反向 import `app`。
- 保留旧 import fallback，并新增 registry contract test；全量 pytest 为 `109/109`。
- v1 API、快照和 Safety Evaluation 基线保持。
