# 模型卡

## 当前模型

- 模型：多项式朴素贝叶斯，症状标签到疾病类别的研究原型。
- 主模型：`data/symptom_disease_model/models/symptom_disease_41_nb.json`。
- 训练数据：41 类、304 行结构化数据；当前模型文件记录 230/74 的一次分层切分。
- 当前记录的指标：Top-1 `0.973`、Top-3 `1.000`。

## 不能这样解释

这些数字来自小型、弱标注/教育型数据和单次切分，不能宣传为临床准确率，也不能写成“疾病概率”或诊断结果。当前模型没有完成按 symptom-set fingerprint 分组的防泄漏切分，也没有完整 Macro F1、校准和独立安全集证据，因此默认只能用于研究与分诊辅助。

## 降级策略

模型文件缺失、损坏、未知症状过多、已知症状不足或置信度不足时，返回 `model_unavailable`/`abstain` 语义，仍可提供基础的安全提示、追问和就医导航；Safety Gate 不依赖模型。

## 后续证据

至少建立规则 baseline、当前 NB、线性 baseline 和完整流水线比较，输出 Top-1/3、Macro Precision/Recall/F1、Per-class Recall、Coverage、Abstention、Brier/ECE，并保存 split manifest、数据 hash、模型版本和 git commit。
