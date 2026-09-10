# H-20260910-013：抽取交通 feature 与可达性 score 纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将医院交通 payload、普通/初诊交通融合和急症/较重距离优先 score 移入 `backend/app/domain/recommendation/traffic.py`；保留交通样本 map/cache 在 legacy。

## 证据

56 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院 candidate 组装、交通样本加载/map/cache 和急症兜底 explain；保留“骑行仅展示、不参与医疗推荐排序”的声明。
