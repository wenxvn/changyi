# 2026-10-03 词典语义审计（W10）

范围：现有98个alias/name/model的结构覆盖与合成真实caller探针，不导入病历，不训练或修改字典。证据在 `evaluation/core_exploration/results/alias-semantic-v1/`，before/after包含相同SHA256。

## 确认的问题与处置

- `抽搐 → muscle_pain → 肌肉疼痛`实际发布模型标准标签，单词输入还产生“甲型肝炎”预测，混合咳嗽产生“普通感冒”。这是旧模型探针结果，不是疾病事实。
- 查阅[NINDS Myoclonus](https://www.ninds.nih.gov/health-information/disorders/myoclonus)与[MedlinePlus Muscle aches](https://medlineplus.gov/ency/article/003178.htm)（2026-10-03访问）：前者描述不自主抽动/痉挛的运动现象，后者描述肌肉疼痛。**据此推断**原关联不能作为已核验的同义映射；资料不支持从“抽搐”直接诊断癫痫，也不提供本项目可训练替代码。
- `excessive_thirst`、`high_blood_pressure`、`spotting_ urination`不在正式模型词汇表，最后一项还缺name；保留原记录，不自动修拼写或新增疾病权重。
- 通用fever的粗粒度语义已有parser契约，但正式NB没有该特征；不能静默丢弃后仅用剩余症状发布疾病。明确高/低热对应既有特征保留。

adapter v2.4隔离待核验别名，未被否认的可疑/不支持输入拒绝整条辅助模型疾病与标准标签；`mapping_review.required/issues`记录原因。明确否认“抽搐”不阻挡独立肌肉痛，原字典/模型哈希完全未变。研究词典挑战仍是旧标签契约回归，不代表医学语义认证；其他关联（如胸闷与呼吸困难）仍未完成逐项医学核验。

## 未解决的最高P0

**2026-10-03 W11更新**：下述原始风险已在代码路径缓解：未确认抽搐进入独立Safety复核门禁且不排行，确认危险条件进入急症出口；明确否认危险条件仍需尽快专业评估。当前他人持续抽搐按已有急症规则处理，不再被历史过滤。原before/after保留当时ROUTINE的真实证据；临床有效性和更广语境覆盖仍开放，见WEBSITE_CONTINUATION的W11记录。

合成探针“抽搐”的独立Safety分支仍返回ROUTINE。**辅助模型隔离没有解决这一点**。下一轮先登记L3，固化当前错误/危险信号确认与资源门禁预期，设计独立于模型的保守复核路径；明确急症必须在先。固定142例通过不能覆盖此新发现，也不能作为安全完成声明。相关概念背景：[MedlinePlus Seizures](https://medlineplus.gov/ency/article/003200.htm)。不凭单词推断具体病因或擅自降低急症处理。
