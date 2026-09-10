# H-20260910-018：抽取医院单 candidate 组合边界

- 日期：2026-09-10
- 类型：推荐架构 / L2-L3 行为保持重构
- 结果：完成

## 事件

将医院单候选的 feature 组合、风险惩罚、综合 score、解释和结果对象组装移入 `backend/app/domain/recommendation/candidate.py`。候选遍历、位置/交通数据准备、缓存、整体 rerank 和医学策略仍在 legacy 兼容层。

## 证据

66 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院候选遍历和 API adapter parity；内部 feature/score 不是医院官方评级或临床诊断。
