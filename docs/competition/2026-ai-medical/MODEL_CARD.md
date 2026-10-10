# 模型卡（2026-10-10 冻结基线）

## 当前模型

- 模型：多项式朴素贝叶斯，症状标签到疾病类别的研究原型，线上仅作次要证据（分数封顶，不单独决定科室路径，Safety Gate 不依赖模型）。
- 主模型：`data/symptom_disease_model/models/symptom_disease_41_nb.json`。
- 训练数据：41 类、304 行结构化数据（`disease_symptom_structured_41diseases_long.csv`，见 `evaluation/model/grouped_split_report.json` 的 dataset 记录）。
- random 切分记录：test 74 行，Top-1 `0.973`、Top-3 `1.000`（宽松参考，可能受近重复样本影响）。
- strict 近重复同标签隔离：test 24 行，Top-1 `0.208`、Top-3 `0.333`（仅覆盖部分类别，不能与随机切分横向比较）。
- 另有 exact fingerprint 分组与 5-fold Grouped Near-Duplicate CV（跨 split 近重复 0），见同一报告与 `docs/algorithm/CORE_EXPLORATION_REPORT.md`。

## 不能这样解释

这些数字来自小型、弱标注/教育型数据；random 高分不能宣传为临床准确率，也不能写成“疾病概率”或诊断结果。防泄漏分组（fingerprint / near-duplicate）已经建立，结果更贴近泛化风险但仍是离线原型证据；模型默认只能用于研究与分诊辅助。

## 降级策略

模型文件缺失、损坏、未知症状过多、已知症状不足或置信度不足时，返回 `model_unavailable`/`abstain` 语义，仍可提供基础的安全提示、追问和就医导航；Safety Gate 不依赖模型。

## 后续证据

至少建立规则 baseline、当前 NB、线性 baseline 和完整流水线比较，输出 Top-1/3、Macro Precision/Recall/F1、Per-class Recall、Coverage、Abstention、Brier/ECE，并保存 split manifest、数据 hash、模型版本和 git commit。
