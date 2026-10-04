# ROUND4 修正复评报告（2026-10-02）

本次为当前源码真实五seed重跑；旧2026-09-16文稿和结果保留在 `evaluation/core_exploration/legacy_evidence/`。完整新探索见 `docs/algorithm/CORE_EXPLORATION_REPORT.md`。

## 原版源码控制与证据纠正

直接执行Git HEAD原版函数seed42：Acc .624413，T .7。旧.737089/T .5及mean .742438无法从当前原源码复现。下面报告实际结果，不保留不可复现headline。

| 模型 | Acc mean | std | Macro-F1 | ECE raw |
|---|---:|---:|---:|---:|
| char_ngram_tfidf_lr | 0.608179 | 0.034233 | 0.404872 | 0.195829 |
| linear_svm_binary | 0.468807 | 0.024979 | 0.396978 | 0.249830 |
| logistic_regression_binary | 0.459129 | 0.024158 | 0.381607 | 0.207238 |
| multinomial_nb | 0.326695 | 0.026162 | 0.252202 | 0.097618 |
| tfidf_logistic_regression | 0.377989 | 0.027764 | 0.366143 | 0.258841 |
| three_state_lr | 0.459129 | 0.024158 | 0.381607 | 0.207238 |
| word_char_fusion_lr | 0.430939 | 0.054146 | 0.391450 | 0.174392 |

最佳模型：char_ngram_tfidf_lr；five seeds [42, 123, 2026, 3407, 7777]。

## 同一预测器的选择性拒答

cal/test/clean/perturbed复用模型权重、训练期特征和温度；model_id=f62c94a325c5f9636fac9d3653f06c259ed01d57ef40c93ace4df8a129509e6e

| cal目标coverage | 实际test coverage | retained Acc |
|---|---:|---:|
| 100% | 0.990610 | 0.625592 |
| 90% | 0.915493 | 0.646154 |
| 80% | 0.760563 | 0.740741 |
| 70% | 0.624413 | 0.81203 |
| 60% | 0.535211 | 0.850877 |
| 50% | 0.474178 | 0.881188 |

阈值0全覆盖Acc=0.624413。

## 安全与限制

Safety真实执行观察：{"case_count": 142, "red_flag_recall": 1.0, "under_triage_rate": 0.0, "over_triage_rate": 0.0, "emergency_false_negative": 0}

readiness=RESEARCH_ONLY

公开文本、有限类别/表达component覆盖，不是中文临床验证。症状变化压力不宣称医学语义不变。全部原始矩阵/曲线/混淆/学习曲线在results/。
