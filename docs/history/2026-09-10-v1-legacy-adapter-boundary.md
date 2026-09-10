# H-20260910-020：抽取 v1 legacy 延迟适配器

- 日期：2026-09-10
- 类型：API 架构 / L2 行为保持重构
- 结果：完成

## 事件

将 `/api/v1` blueprint 到 `app.py` legacy handler 的延迟解析逻辑移入 `backend/app/api/v1/legacy_adapter.py`，路由保持复用既有实现，并补充 v1 contract 边界测试。

## 证据

74 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分交通样本生成/cache 和完整 route adapter parity；当前 v1 仍是兼容外壳，不宣称生产级认证或完整应用服务化。
