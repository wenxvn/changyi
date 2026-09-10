# H-20260910-003：建立 Safety Gate 状态契约与安全评估基线

- 日期：2026-09-10
- 类型：医学安全边界 / L3
- 结果：完成，规则缺口保持开放

## 事件

新增四态 `TriageStatus` 和 `SafetyGateDecision`，将 `/api/v1` 的 legacy 状态映射收敛到 domain；新增 16-case Safety Evaluation Set 及真实指标脚本。该切片不改红旗规则、否定语义、分诊阈值或推荐逻辑。

## 结果

基线 Red Flag Recall 为 `0.9231`，Under-triage Rate 为 `0.0769`，Over-triage Rate 为 `0.0`，Emergency False Negative 为 `1`。`喘不上来` alias under-triage 和 `不舒服` 信息不足未降级继续公开记录，不作为通过结论。

## 后续

P2-S3 处理推荐流水线边界；医学规则修复需单独 L3 计划、反例、ADR 和审核记录。
