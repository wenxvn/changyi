# H-20260910-021：抽取交通样本计算边界

- 日期：2026-09-10
- 类型：交通数据架构 / L2 行为保持重构
- 结果：完成

## 事件

将四类医院交通样本计算从 `app.py` 移入 `backend/app/domain/recommendation/traffic.py`，通过显式医院、样本和距离函数输入；加载、缓存、汇总和推荐使用策略保持在兼容层。

## 证据

78 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续治理交通 cache 生命周期并完成医院 candidate/API application service 剩余边界；不将脱敏样本宣传为实时交通或医疗事实。
