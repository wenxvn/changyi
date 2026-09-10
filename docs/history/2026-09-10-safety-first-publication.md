# H-20260910-004：v1 输出落实 Safety-first abstain

- 日期：2026-09-10
- 类型：医学安全发布边界 / L3
- 结果：完成，legacy parity 待后续

## 事件

在 `/api/v1` triage 和 recommendations 的公共输出层接入 Safety Gate：`EMERGENCY` 或 `INSUFFICIENT_INFORMATION` 时隐藏疾病候选和疾病模型预测；急症不公开普通 follow-up。红旗标签、急诊动作、免责声明和资源方向继续返回。legacy `/api/*` 不变。

## 证据

23 个 pytest 通过，急症公共输出测试通过，稳定快照未变化；Safety Evaluation 的 legacy 基线仍为 Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。

## 后续

完成 recommendation/API adapter parity 后，再决定是否把同一发布边界迁移到 legacy；任何红旗召回或信息不足规则修改必须独立走 L3 安全审核。
