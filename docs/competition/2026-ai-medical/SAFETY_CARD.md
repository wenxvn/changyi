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

`tests/characterization/canonical_snapshot.json` 显示，`喘不上来` 经归一化产生“呼吸困难”标签，但现有 `common` 场景仍返回 `routine`；`不舒服` 也仍返回普通倾向。收口 smoke 还观察到压榨样胸痛伴喘不过气和冷汗的自然语言组合仍返回 `routine`。这些都是待医学审核的 under-triage/信息不足反例，不在本轮直接改规则；Safety Gate 的状态契约已建立，但红旗规则本身仍未完成独立迁移。

## P2-S1 输入边界记录

`backend/app/domain/medical_input.py` 现在只承载原有口语归一化和否定窗口纯函数，不改变红旗规则。测试覆盖 `喘不上来 -> 呼吸困难`、`没有胸痛，但出现呼吸困难`、硬边界后的再次阳性和 `否认呼吸困难`。输入层迁移通过快照回归；统一 `INSUFFICIENT_INFORMATION` 的安全语义已在 Safety Gate contract 中定义，但 alias under-triage 和模糊输入降级仍未修复。

## P2-S2 状态契约与基线评估

`backend/app/domain/triage/safety_gate.py` 提供 `EMERGENCY`、`URGENT`、`ROUTINE`、`INSUFFICIENT_INFORMATION` 四态枚举，以及“紧急评估”“补充信息并复核”“继续辅助流程”三类非诊断交接动作。它只消费既有 triage 结果，不重新实现医学规则；急症要求人工/专业复核，信息不足要求补充信息并复核。

`evaluation/safety/safety_cases.json` 共 16 个 case，脚本运行结果为：Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`。唯一红旗漏检是已记录的 `喘不上来` 口语 alias；`不舒服` 的信息不足期望也未命中。两者以及待领域确认的否定/普通样例均列为 `review_required`，这些数字是当前基线，不是发布目标或医学审核结论。

## P2-S2 Safety-first 发布

`/api/v1` 在 `EMERGENCY` 或 `INSUFFICIENT_INFORMATION` 状态下对疾病候选和疾病模型预测执行 abstain；急症同时不公开普通 follow-up，保留红旗标签、急诊动作、免责声明和必要的资源方向。该保护由 `backend/app/domain/triage/publication.py` 承载，发生在公共输出边界，不改变冻结的规则或内部推荐计算；急症医生兜底评分已抽取为可测试纯函数，但仍只是辅助候选排序，不构成临床优先级。正式 v1 handler 由 `backend/app/composition.py` 直接注册，不再经过已删除的 lazy adapter。
