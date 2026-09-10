# 2026-09-10 Safety Gate 状态契约与评估集

## 目标

完成 P2-S2 的安全基础切片：统一四态对外分诊状态，建立不依赖 Flask/模型/资源排序的 Safety Gate domain 边界，并运行独立 Safety Evaluation Set 得到 legacy 基线。

## 已完成

- 新增 `TriageStatus`、`SafetyAction` 和不可变 `SafetyGateDecision`。
- `app.py` 的 v1 状态映射改为调用 `triage_status_from_legacy`，旧 `_v1_triage_status` 名称和 API 字段保留。
- 新增 16 个安全 case，覆盖心血管急症、卒中、呼吸困难、急腹症、严重外伤、意识异常、过敏、孕产急症、儿童危重、眼科急症、心理危机、否定、口语和信息不足。
- CI 增加 Safety Evaluation baseline 步骤；评估缺口不被伪装为通过。

## 基线结果

- Red Flag Recall：`0.9231`
- Under-triage Rate：`0.0769`
- Over-triage Rate：`0.0`
- Emergency False Negative：`1`
- `colloquial-breathlessness`（`喘不上来`）和 `vague-discomfort`（`不舒服`）继续标记为 `review_required`。

## 验证

- 全量 pytest：21/21 通过。
- Safety Evaluation：16 case 成功运行并输出上述真实指标。
- API smoke：11/11 通过，v1 急症状态仍为 `EMERGENCY`，旧入口可访问。
- `py_compile`、`node --check`、数据质量扫描、稳定 snapshot 和 `git diff --check` 通过。

## 未完成与下一步

本切片只统一状态契约和评估入口，没有修复红旗规则。下一步应拆分 recommendation pipeline；涉及 alias under-triage 或信息不足降级的修复必须另立 L3 计划、Safety Case 和医学审核记录。

## 回滚

回退本切片改动即可恢复 `app.py` 内的状态映射并移除评估边界；不涉及原始数据、模型和推荐权重。
