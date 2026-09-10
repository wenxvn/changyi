# H-20260910-017：抽取医院 candidate 科室命中边界

- 日期：2026-09-10
- 类型：推荐架构 / L2 行为保持重构
- 结果：完成

## 事件

将医院候选目标科室的精确强项、已列出科室、相关科室和无命中回退判断移入 `backend/app/domain/recommendation/candidates.py`。医院候选全集、交通/feature/score、排序和解释保持由兼容层组合。

## 证据

64 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续拆分医院 candidate 遍历与 API adapter parity；`strength_score` 是系统内部排序输入，不是医院官方评级。
