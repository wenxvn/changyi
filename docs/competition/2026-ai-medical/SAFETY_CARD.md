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

`tests/characterization/legacy_snapshot.json` 显示，`喘不上来` 经归一化产生“呼吸困难”标签，但 legacy `common` 场景仍返回 `routine`；`不舒服` 也仍返回普通倾向。两者是待医学审核的 under-triage/信息不足反例，不在本轮直接改规则；在 L3 Safety Gate 完成前不得宣称统一安全枚举已实现。
