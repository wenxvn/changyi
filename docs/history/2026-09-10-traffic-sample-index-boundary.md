# H-20260910-016：抽取交通样本索引纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L2 数据边界行为保持重构
- 结果：完成

## 事件

将 station/taxi/bike 已计算样本行的按医院 ID 建索引逻辑移入 `backend/app/domain/recommendation/traffic.py`。缓存生命周期、样本计算、数据加载和交通展示/排序语义仍由 `app.py` 负责。

## 证据

61 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续评估医院 candidate 遍历和交通样本生成/cache 治理边界；交通样本仍是演示数据，不能表述为实时路况或到院保障。
