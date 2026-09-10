# 计划：建立 Safety Gate 状态契约与评估集

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

完成 P2-S2 的安全基础切片：把对外分诊状态统一为 `EMERGENCY`、`URGENT`、`ROUTINE`、`INSUFFICIENT_INFORMATION`，建立独立的 Safety Gate 纯函数边界和可运行的 Safety Evaluation Set。先记录现有规则的真实表现，再决定是否修改医学规则。

## 非目标

- 不在本切片改变红旗关键词、否定窗口、严重程度阈值、分诊规则优先级或推荐权重。
- 不把 `VisitScenario`（`common`、`complex`、`surgery`、`first_visit`）当作分诊状态；本切片只统一输出状态契约。
- 不把模型候选疾病作为诊断，不新增疾病概率宣传或临床承诺。
- 不在没有医学审核记录的情况下修复 alias under-triage、模糊输入降级或任何红旗召回缺口。

## 当前基线

- legacy `analyze_medical_triage` 已有急症、较重、普通和信息不足分支，但 `/api/v1` 的状态映射仍定义在 `app.py`。
- characterization 已发现 `喘不上来` 归一化后仍可能未进入急症路径，`不舒服` 在 `common` 场景仍可能返回普通倾向；两者作为待审核反例保留。
- 当前稳定快照哈希为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。

## 方案与边界

- 新增 `backend/app/domain/triage/safety_gate.py`，只接受 legacy triage 结果，提供 `TriageStatus`、`SafetyAction` 和不可变 `SafetyGateDecision`；不导入 Flask、模型、数据仓库或路由。
- `app.py` 通过兼容导入调用状态映射，继续保留 `_v1_triage_status` 的旧名称和返回字符串。
- Safety Evaluation Set 放在 `evaluation/safety/`，区分明确红旗正例、否定表达、口语表达和信息不足反例；评估脚本输出真实 Recall、Under-triage、Over-triage、Emergency False Negative，不手工填写指标。
- 评估集中的已知缺口标记为 `review_required`，不伪装成通过，也不让本切片绕过既有回归门禁。

## 原子步骤

- [x] 建立状态枚举、Safety Gate decision 和 legacy 适配函数。
- [x] 迁移 v1 状态映射并新增 domain 单元测试，确认旧 API 字段不变。
- [x] 建立 Safety Evaluation Set 和可重复评估脚本，输出真实基线指标。
- [x] 更新 Safety Card、评分卡、风险、进度、历史和 review。
- [x] 运行 L3 验证：红旗正例、否定/口语/模糊反例、API smoke、全量测试、快照和静态检查。

## 验收标准

- 四个对外状态有单一枚举来源，`/api/v1/triage` 仍返回相同状态字符串和 envelope。
- Safety Gate 对急症要求优先紧急评估，对信息不足要求补充信息/专业复核；这些是安全输出语义，不替代医学规则审核。
- 评估脚本能从 JSON case set 计算指标，并明确列出 `review_required` 缺口。
- 稳定快照不变；旧 `/api/*`、`/api/v1/*` 和模型不可用降级保持可用。

## 验证命令与结果

实施结果：21 个 pytest 全部通过；Safety Evaluation Set 共 16 个 case，Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；API smoke 11 项通过；`py_compile`、Node check、数据质量扫描、稳定快照和 `git diff --check` 通过。上述指标是 legacy 规则的真实基线，不是发布目标或医学审核结论。

## 风险、回滚和记录动作

- 风险：状态映射抽取改变 `信息不足` 判断或把场景误作等级；用旧快照和映射单测阻断。
- 风险：评估集标签被误读为医学真值；每个 case 记录来源类型、审核状态和 notes，`review_required` 不计为通过。
- 回滚：回退本切片即可恢复 `app.py` 的状态映射和删除评估脚本，不涉及数据/模型文件。
- 完成后更新 `docs/status/current.md`、`docs/progress/`、`docs/history/`、`docs/reviews/` 和 `docs/risks/register.md`。
