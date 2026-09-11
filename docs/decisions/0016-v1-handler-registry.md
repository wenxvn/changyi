# ADR-0016：v1 Blueprint 使用显式 Handler Registry

状态：已接受  
日期：2026-09-11  
范围：`backend/app/api/v1/legacy_adapter.py` 与根级 Flask composition

## 背景

v1 blueprint 为了兼容渐进迁移，通过 `legacy_adapter` 在请求时导入 `app` 并查找 handler。该桥接可用，但让 application factory 与 legacy composition 隐式耦合，也不利于验证实际使用的 handler 来源。

## 决定

- 根级 `app.py` 在所有 v1 handler 定义后向 Flask application extension 注册显式映射。
- `legacy_adapter` 在有 Flask context 且 registry 存在时优先返回注册 handler；没有 registry/context 时保留原 lazy import fallback。
- registry 只解决 handler 解析，不承载请求、医学规则、推荐策略或数据加载。

## 影响

正向影响：请求期的 v1/legacy 接缝可观察、可测试，减少隐式模块反向依赖；旧外部调用方仍可用 fallback。

代价：完整独立 factory 仍需要后续将 handler composition 从 `app.py` 进一步移出；当前 registry 不是生产依赖注入容器。

## 回滚

删除 registry 优先分支与注册调用即可，保留原 `importlib` lazy bridge。
