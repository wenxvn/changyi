# H-20260910-005：抽取推荐排序共享纯函数

- 日期：2026-09-10
- 类型：推荐架构 / L3 行为保持重构
- 结果：完成

## 事件

将推荐排序中无 Web、数据读取和模型依赖的 clamp、文本、科室关系、医生职称和内部资源分层逻辑移入 `backend/app/domain/recommendation/scoring.py`，legacy 入口保留兼容别名。

## 证据

27 个 pytest 通过，推荐稳定快照和 API smoke 保持不变。未修改推荐权重、交通数据、医院/医生数据或医学规则。

## 后续

继续拆分 candidate/feature/score/rerank/explain；`fairness` 仍是内部历史字段，未被包装为对外公平性承诺。
