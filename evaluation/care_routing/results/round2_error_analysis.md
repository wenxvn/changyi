# Round2 误差分析：near-dup Accuracy≈0.188 根因

协议：near_duplicate_same_label triple split (honest)；seed=42

## 一句话结论

0.188 是「表达簇外推 + 样本规模」与「NB 模型假设/容量」叠加的结果：同一诚实切分下 LR/SVM 可到 1.0，说明 NB 不是无辜的；但 33/41 疾病仅单 component、test 100% unseen combination，数据结构仍是产品化主动追问的硬瓶颈。

## Component 结构

- 单 component 疾病：**33/41**
- 多 component 疾病：**8/41**
- component 数分布：`{1: 33, 5: 8}`
- 诚实切分规模：train=280 / cal=8 / test=16
- test 覆盖病种数：8

## 指标

- Top-1 Accuracy: **0.1875**
- Top-2 / Top-3: 0.25 / 0.25
- Department Accuracy: 0.1875
- Macro-F1: 0.104167
- Mean confidence / entropy / top3 set: 0.208421 / 4.197981 / 3.0
- Wrong-but-confident (conf≥0.7): 0.0625
- Unseen combination ratio: 1.0
- Unseen symptom token ratio: 0.28

## 主要错误贡献类别

- Acne: 2 errors
- Allergy: 2 errors
- Fungal infection: 2 errors
- Gastroenteritis: 2 errors
- Heart attack: 2 errors
- Paralysis (brain hemorrhage): 2 errors
- Urinary tract infection: 1 errors

## 证据

- 33/41 疾病只有 1 个近重复 component，无法诚实拆分。
- 诚实 test 仅 16 行，覆盖 8 个病种。
- test 中 unseen combination ratio = 1.0，unseen symptom token ratio = 0.28。
- Top-1=0.1875 但 Top-3=0.25，说明标签空间仍部分可达但排序错误。
- mean confidence=0.208421 vs accuracy=0.1875，高置信错误存在。
- model_baselines：同一 near-dup split 上 LR/LinearSVM accuracy=1.0 vs NB=0.1875，NB 容量是重要共因。

## 不是主因

- 不是单纯“304 条太少”——random split 在同样 304 条上能到 0.97。
- 不是可以通过放宽切分“修好”的指标问题——改切分会重新引入泄漏。
- 也不能只怪数据：线性模型在相同 test 上可达 1.0，NB 的独立性假设/平滑在稀疏组合上明显吃亏。

> 完整 confusion / per-class / component-size 表见 `results/round2_error_analysis.json`。
