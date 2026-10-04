# 网站分数口径（W31）

正式中文临床概率校准仍未完成。以下两类量不能相互比较，也不能当作患病概率。

| API量 | 来源与含义 | 新语义字段 |
| --- | --- | --- |
| htriage disease_candidates旧probability | 候选score除本次top候选最大score，乘82再截断8..92的相对支持度；最高项常82，非概率分布、不能跨输入比较 | relative_support_score保同值，score_kind=relative_support_score；candidate_score_semantics.calibrated=false、clinical_probability=false |
| disease_prediction predictions概率 | 原型NB在其训练标签集合内计算的模型posterior；尚无独立中文临床校准证据 | probability_semantics.kind=uncalibrated_model_posterior，calibrated=false、clinical_probability=false |

旧候选probability只为API兼容保留，新消费者使用relative_support_score并读取语义；不得格式化成患病百分比，不将规则相对分与NB posterior相加或视为同一置信度。候选notice同步解释相对分。

W31未改变数值、排序、医学权重、模型文件、阈值或Safety。急症/信息不足仍隐藏疾病候选；辅助拒答原因和Safety优先说明保持原逻辑。新增语义字段描述的是分数性质，不能说明模型可用或存在候选。

固定6项合成发布协议只验证字段与原相对分兼容，不提供准确率、ECE、Brier、临床风险或校准改进。before/after独立版本结果在versioned-challenges/w31-score-before与w31-score-after，分别6失败与0失败，原失败不覆盖。
