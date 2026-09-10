# H-20260910-014：抽取医院 candidate 结果组装纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医院候选的稳定结果对象组装移入 `backend/app/domain/recommendation/candidate.py`，legacy `recommend` 保留医院遍历、交通样本、feature/score 和 rerank 职责。

## 证据

58 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院 candidate 遍历、交通 map/cache 和急症兜底 explain；保留 legacy/v1 API 兼容，不把候选分数包装成医院官方承诺。
