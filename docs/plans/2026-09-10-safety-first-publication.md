# 计划：在 v1 输出层落实 Safety-first 发布边界

- 日期：2026-09-10
- 变更等级：L3
- 状态：已完成

## 目标

将已建立的 Safety Gate decision 接入 `/api/v1` triage 和 recommendations 的公共输出：当状态为 `EMERGENCY` 或 `INSUFFICIENT_INFORMATION` 时，隐藏疾病候选和疾病模型预测；急症同时隐藏普通追问，信息不足保留补充信息问题；两者都保留红旗标签、紧急/复核动作、科室方向、免责声明和资源推荐所需的安全事实，避免形成诊断锚定。

## 非目标

- 不修改 `analyze_medical_triage` 的红旗规则、否定语义、阈值、关键词或推荐权重。
- 不改变 legacy `/api/*` 响应，legacy 迁移在后续 API adapter/parity 切片单独处理。
- 不删除用户输入事实、红旗标签、照护等级、120/急诊提示或专业复核建议。
- 不把 `ABSTAIN` 当作疾病结论；它只表示 Safety Gate 优先级下不公开疾病候选。

## 方案与边界

- 复用 `evaluate_safety_gate` 和四态 `TriageStatus`，在 v1 adapter 的 publication boundary 做不可变浅拷贝和脱敏。
- `EMERGENCY`：疾病预测置为 `abstained`，候选列表和普通 follow-up 问题为空，保留红旗和紧急处置文案。
- `INSUFFICIENT_INFORMATION`：疾病预测置为 `abstained`，保留信息不足状态；不将当前 legacy 未命中该状态的 `不舒服` 误记为已修复。
- 推荐计算内部仍使用原始 triage，公共响应才进行脱敏，避免改变现有排序计算；只对 v1 recommendations 启用。

## 原子步骤

- [x] 建立 v1 Safety-first publication helper。
- [x] 在 v1 triage/recommendations 接入，保留 legacy 兼容路径。
- [x] 新增急症和信息不足公共输出测试，确认候选和 follow-up 不泄漏。
- [x] 更新 Safety Card、架构、风险、进度、历史和 review。
- [x] 运行 L3 验证：Safety Evaluation、API smoke、全量测试、快照和静态检查。

## 验收标准

- v1 急症响应不包含疾病候选名称/概率和普通追问问题，且红旗、急诊动作和免责声明仍存在。
- v1 信息不足响应不包含疾病预测候选，仍明确要求补充信息和专业复核。
- legacy API 快照不变；v1 常规推荐的字段和排序快照不变。
- Safety Evaluation 基线仍真实可重复，未把脱敏行为误报为规则召回修复。

## 验证命令与结果

实施结果：23 个 pytest 全部通过；Safety Evaluation 仍为 Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；v1 API smoke 11 项通过；急症公共响应的疾病预测已 abstain，红旗和紧急处置保留；characterization snapshot 哈希保持 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`；`py_compile`、Node check、数据质量和 `git diff --check` 通过。

## 回滚

回退本切片即可恢复 v1 原始疾病候选输出；不涉及规则、数据、模型或 legacy API。
