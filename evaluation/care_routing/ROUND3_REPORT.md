# ROUND3 报告：扩大诚实评测与 Triage 分类器升级验证

更新时间：2026-09-16  
复现：`.venv/bin/python -m evaluation.care_routing.run_round3 --write`  
产物：`results/round3_*.json` / `round3_learning_curve.csv`

**安全边界未变**：Safety Gate / 红旗 / Safety Evaluation / 生产 API / 前端均未修改。  
expanded 集是仓库公开文本数据（structured 304 + training_long 同 41 病种去重 extras），**不是临床病例**。

---

## 数据与诚实评测上限

| 集合 | 行数 | 病种 | 说明 |
| --- | --- | --- | --- |
| structured_41 | 304 | 41 | Round1/2 主协议 |
| **expanded_41** | **1289** | 41 | +985 unique extras，来源可追溯 |
| 诚实 quota split (thr=0.8, seed=42) | train 840 / cal 236 / **test 213** | test 覆盖 **25** 病种 | 16 病种因 component 不足排除出 test |

- Component 定义：同标签症状集合 Jaccard 连通块（主阈值 **0.8**，非仅 exact fingerprint）。
- 0.7/0.8/0.85/0.9 阈值审计见 `round3_split_audit.json`。
- Cross-split 泄漏审计（Jaccard≥0.75）：**8 对，全部同标签**，max Jaccard=0.75（边界近义，非跨病泄漏）。
- **structured_304 诚实 test 上限仍是 ~8 病种**；不得为覆盖 41 类拆散 component。
- 外部专家集：仅 schema（`data_schema/external_eval_schema.json`），**无结果**。

---

## 七个必答问题

### 1. LR/SVM 在扩大诚实评测上是否仍明显优于 NB？

**是，但幅度从「1.0 vs 0.19」收缩为「~0.27 vs ~0.17」。**

5 seeds（42/123/2026/3407/7777），expanded quota 0.8：

| 模型 | Disease Acc | Macro-F1 | Top-3 | Dept Acc | ECE | Wrong-conf |
| --- | --- | --- | --- | --- | --- | --- |
| Multinomial NB | 0.173±0.022 | — | — | 0.315±0.025 | — | — |
| **Linear SVM** | **0.267±0.015** | — | — | **0.401±0.041** | raw 0.20→temp 0.08 | — |
| Logistic Regression | 0.265±0.021 | — | — | 0.300±0.032 | raw 0.043 | — |
| TF-IDF + LR | 0.252±0.028 | — | — | — | — | — |

### 2. LR/SVM 的 1.0 是否只是 n=16 偶然？

**主要是小样本偶然；但 LR>SNB 的方向仍成立。**

- Round2：test=16 时 LR/SVM=1.0（过拟合到可分小样本）。
- Round3：test=213/25 病种时 LR≈0.265、SVM≈0.267，**不再是 1.0**。
- 多 seed 上 LR/SVM 始终高于 NB（+9~9.4pp），**不是单 seed 偶然**，但绝对水平仍低。

### 3. Learning Curve 是否表明继续补数据仍有明显收益？

**是。20%→100% train 仍有 9~13pp 提升，未平台。**

| fraction | NB Acc | LR Acc | SVM Acc |
| --- | --- | --- | --- |
| 0.2 | 0.092±0.032 | 0.147±0.019 | 0.142±0.017 |
| 0.4 | 0.124±0.016 | 0.187±0.018 | 0.189±0.011 |
| 0.6 | 0.161±0.003 | 0.235±0.024 | 0.227±0.025 |
| 0.8 | 0.187±0.014 | 0.257±0.023 | 0.257±0.023 |
| 1.0 | 0.179±0.024 | 0.262±0.032 | 0.268±0.019 |

CSV：`results/round3_learning_curve.csv`。

### 4. 哪个模型对文本扰动最稳健？

**LR（mean drop 0.015）。**

| 扰动 | NB drop | LR drop | SVM drop |
| --- | --- | --- | --- |
| order_shuffle（bag 不变） | 0 | 0 | 0 |
| synonym_swap | — | 0.014 | — |
| drop_noncritical | — | **0.047** | — |
| add_filler | — | 0.005 | — |
| colloquial_noise | — | 0.009 | — |
| **mean / max** | 0.032 / 0.085 | **0.015 / 0.047** | 0.027 / 0.052 |

标注：`robustness_simulation`，未回训扰动集，未改红旗语义。

### 5. Direct Department vs Disease-first？

**Direct Department 明显更稳，更贴合 Care Routing。**

| 路径 | 科室 Acc (mean±std) |
| --- | --- |
| **Symptoms → Department (LR)** | **0.450±0.026** |
| Symptoms → Disease → Department (LR) | 0.291±0.026 |
| Symptoms → Disease → Department (NB) | 疾病 0.173 / 科室 0.315 |

疾病分类不是产品终点；粗标签聚合后科室路由更可靠。UI 不得把 disease 当诊断展示。

### 6. 主要错误是 same-department 还是 cross-department？

**以 cross-department 为主**（seed=42, LR disease-first）：

- correct 56 / same-dept 0 / **cross-dept 157** / safety-relevant 8
- 说明很多「病种错」直接变成「科室错」；Direct Department 路径更值得优化
- severity 仅研究用；safety_relevant 复用固定原型病种 allowlist，不新造临床分级

### 7. 是否具备 Shadow Mode 证据？

## **`RESEARCH_ONLY`**

| 条件 | 结果 |
| --- | --- |
| 更大诚实评测 | ✅ test≈213 / 25 病种 |
| LR/SVM 多 seed 稳定优于 NB | ⚠️ 方向是，但 Δ≈0.09 < 0.10 门槛 |
| Department 指标可靠 | ❌ 病种路由科室 Acc 仅 ~0.30–0.40 |
| Calibration 可接受 | ✅ LR ECE≈0.04 |
| Safety 不受影响 | ✅ 生产路径未改 |

**结论：不够进 Shadow Mode。** 绝对准确率仍低；继续补数据 + 以 Direct Department 为主线。

---

## 工程备注

- 纯 Python LR 拟合 ~1.3s / 模型序列化偏大（稀疏 dict JSON）；生产化需换向量化实现。
- NB 推理极快、模型小，但泛化弱。
- SVM decision score **不是概率**；温度校准后 ECE 0.20→0.08，仍研究用。

---

## 暂停方向（按任务书）

IG 策略优化、RL、Conformal 产品化、Hybrid Safety 产品化、GNN、LLM 微调、LTR——**继续暂停**。

---

## 下一轮

1. 继续扩多 component 真实/可核验症状描述（16 病种仍无法进诚实 test）。  
2. 以 **Direct Department** 为主模型做更大评测与校准。  
3. Shadow 前需：绝对科室 Acc 显著抬升 + Safety 回归 + L3。
