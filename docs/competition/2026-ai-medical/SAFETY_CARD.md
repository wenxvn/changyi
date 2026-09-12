# 安全卡

## 安全边界

系统是演示型就医决策辅助，不替代医生、急救人员或线下评估。所有医学输出都必须带辅助性质和不确定性提示。

## Safety Gate

输入清理、症状标准化和否定识别之后，先执行红旗规则，再决定是否可以进入疾病候选、追问和资源推荐。胸痛伴呼吸困难、意识异常、卒中强信号、大量出血、严重过敏、孕产急症、儿童危重、心理危机等场景必须优先急诊/急救评估。

## 急症 UI 规则

第一屏只突出风险结论、下一步、附近急诊和 120 入口；不突出普通医生排行榜、论文数量或匹配分。急症场景的医院排序优先距离、急诊能力和医疗能力，公交/骑行不能把用户引向更远资源。

## 低置信度与信息不足

描述过短、缺失关键时间/严重程度/伴随症状或模型不可用时，使用 `INSUFFICIENT_INFORMATION` 或 `ABSTAIN` 语义，追问有限信息并建议专业复核，不强行生成诊断锚定。

## 必测安全指标

建立独立 Safety Evaluation Set，报告 Red Flag Recall、Under-triage Rate、Over-triage Rate、Emergency False Negative。指标必须由运行结果产生，不手工填写目标数字。

## 当前 characterization 发现

本轮将 `喘不上来`、`喘不过气`、`上不来气` 等口语呼吸困难，以及压榨样胸痛伴冷汗的组合纳入安全回归；“不舒服”“很不舒服”“身体不适”等过于笼统的输入进入信息不足路径。规则仍是演示系统的固定样例回归，不代表医学覆盖完整，新增或修改红旗规则仍需专业复核。

## P2-S1 输入边界记录

`backend/app/domain/medical_input.py` 承载口语归一化和否定窗口纯函数；测试覆盖呼吸困难口语、压榨样胸痛、冷汗、否定表达和转折后的再次阳性。安全规则匹配保留原始表达，避免把否定短语追加的标准别名误判为阳性；统一 `INSUFFICIENT_INFORMATION` 的安全语义已接入笼统输入路径。

## P2-S2 状态契约与基线评估

`backend/app/domain/triage/safety_gate.py` 提供 `EMERGENCY`、`URGENT`、`ROUTINE`、`INSUFFICIENT_INFORMATION` 四态枚举，以及“紧急评估”“补充信息并复核”“继续辅助流程”三类非诊断交接动作。它只消费既有 triage 结果，不重新实现医学规则；急症要求人工/专业复核，信息不足要求补充信息并复核。

`evaluation/safety/safety_cases.json` 共 135 个 case，脚本运行结果为：Red Flag Recall `1.0`、Under-triage Rate `0.0`、Over-triage Rate `0.0312`、Emergency False Negative `0`；信息不足样例全部命中。数字只反映当前固定样例和规则回归，不是发布目标或医学审核结论。

## P2-S2 Safety-first 发布

`/api/v1` 在 `EMERGENCY` 或 `INSUFFICIENT_INFORMATION` 状态下对疾病候选和疾病模型预测执行 abstain；急症同时不公开普通 follow-up，保留红旗标签、急诊动作、免责声明和必要的资源方向。该保护由 `backend/app/domain/triage/publication.py` 承载，发生在公共输出边界，不改变冻结的规则或内部推荐计算；急症医生兜底评分已抽取为可测试纯函数，但仍只是辅助候选排序，不构成临床优先级。正式 v1 handler 由 `backend/app/composition.py` 直接注册，不再经过已删除的 lazy adapter。
