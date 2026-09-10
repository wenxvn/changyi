# H-20260910-019：抽取 Safety-first 公共发布边界

- 日期：2026-09-10
- 类型：安全架构 / L3 行为保持重构
- 结果：完成

## 事件

将 Safety Gate 之后的疾病候选、模型预测和急症 follow-up 降级逻辑移入 `backend/app/domain/triage/publication.py`。红旗规则、状态判定、legacy 输出和 API 路由路径保持不变。

## 证据

68 个 pytest、13 项 API smoke（含 400/404 边界）、Safety Evaluation、Python/Node 静态检查、数据质量检查和推荐稳定快照通过。快照 SHA-256 保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 后续

继续处理 API adapter parity 和医院/交通剩余 legacy 组合；Safety Evaluation 的已知缺口仍需医学审核，publication 脱敏不等于规则召回修复。
