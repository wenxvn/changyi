# H-20260910-015：抽取急症医生兜底结果组装纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 安全相关行为保持重构
- 结果：完成

## 事件

将“无普通候选时”的急症医生结果字典组装移入 `backend/app/domain/recommendation/candidate.py`。候选是否进入兜底、分数计算、急症优先级和排序仍由 legacy 兼容层负责。

## 证据

59 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续处理交通样本 map/cache 和医院 candidate 遍历；急症规则仍需医学审核，兜底结果只表示辅助推荐候选，不构成诊断或急救指令。
