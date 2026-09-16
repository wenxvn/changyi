# ROUND4 报告：Safety-Constrained Selective Care Routing

更新时间：2026-09-16
复现：`.venv/bin/python -m evaluation.care_routing.run_round4 --write`
（快速刷新 selective：`run_round4_refresh`）
产物：`results/round4_*.json` / `round4_risk_coverage.csv` / `round4_data_gap_map.csv`

**安全边界未变**：Safety Gate / 红旗 / Safety Evaluation / 生产 API / 前端均未修改。
数据仍为 expanded_41 公开文本集（1289 行），**不是临床病例**。

主算法骨架：

```text
Safety Gate → Direct Department → Selective Abstention → Care Routing
```

---

## 1. 最佳 Direct Department 轻量模型

**`char_ngram_tfidf_lr`（字符 2–4 gram TF-IDF + Logistic Regression）**

5 seeds，honest quota split（Jaccard 0.8）：

| 模型 | Dept Acc | Macro-F1 | Top-2 | ECE | Wrong-conf |
| --- | --- | --- | --- | --- | --- |
| **char n-gram + LR** | **0.742±0.013** | 0.642 | 0.876 | 0.259 | 0.003 |
| Linear SVM (binary) | 0.469±0.025 | 0.397 | 0.619 | 0.250 | 0.008 |
| LR (binary) | 0.459±0.024 | 0.382 | 0.623 | 0.207 | 0.046 |
| TF-IDF word + LR | 0.378±0.028 | 0.366 | 0.627 | 0.259 | 0.060 |
| word+char fusion + LR | 0.378±0.028 | 0.366 | 0.627 | 0.257 | 0.059 |
| Multinomial NB | 0.327±0.026 | 0.252 | 0.588 | 0.098 | 0.026 |

## 2. 相比 Round3 Direct Department ≈0.45

**+29.2pp（0.450 → 0.742）**，且多 seed std 仅 0.013。
提升主要来自**文本表示**（char n-gram），不是单纯换线性分类器。

## 3. Risk–Coverage（max-probability，阈值只来自 calibration）

| 目标 coverage | 实际 test coverage | Retained Acc | Abstention | Wrong-conf |
| --- | --- | --- | --- | --- |
| 100% | 0.995 | 0.627 | 0.005 | 0.005 |
| 90% | 0.878 | 0.663 | 0.122 | 0.005 |
| **80%** | **0.657** | **0.807** | 0.343 | **0.007** |
| **70%** | **0.549** | **0.838** | 0.451 | 0.009 |
| **60%** | **0.479** | **0.873** | 0.521 | 0.010 |
| 50% | 0.376 | 0.938 | 0.624 | 0.013 |

说明：calibration 分位阈值迁移到 test 后，实际 coverage 低于目标——**分布仍有偏移**，但 retained accuracy 随拒答明显上升，wrong-but-confident 保持极低。

## 4. 80% / 70% / 60% coverage 下 Accuracy

- 目标 80% → 实际 coverage 65.7%，**Acc 0.807**
- 目标 70% → 实际 coverage 54.9%，**Acc 0.838**
- 目标 60% → 实际 coverage 47.9%，**Acc 0.873**

**核心答案**：只对最可信的约一半输入自动给科室时，准确率可到 **~0.84–0.87**。

## 5. 最难区分的科室对

统计混淆（seed=42, char 模型）：

1. **呼吸内科 → 皮肤科**（14）
2. 泌尿外科 → 皮肤科（11）
3. 内分泌代谢科 → 皮肤科（9）
4. 消化内科 → 感染性疾病科（9）
5. 神经内科 → 皮肤科（9）

多数为单向混淆（非 A↔B 对称）。train 统计显示共享症状特征很弱（top shared 仅 `i_have_red`），更像是**皮肤科样本主导 / 其他科室表达不足**导致的偏置，而非经典医学易混对。

## 6. 下一轮最应补哪些科室数据

Data Gap Map（**模型数据优先级，不是医疗重要性排名**）：

| 优先级 | 科室 | 原因摘要 |
| --- | --- | --- |
| 1 | **呼吸内科** | recall=0，被皮肤科大量吞掉 |
| 2 | **泌尿外科** | recall 低，混淆→皮肤科 |
| 3 | **内分泌代谢科** | recall 低 |
| 4 | **神经内科** | recall 低 |
| 5 | **消化内科** | 混淆→感染性疾病科 |

完整表：`round4_data_gap_map.csv`。

## 7. 表示消融：symptom / word / char / fusion / three-state

固定 LR：

| 表示 | Acc |
| --- | --- |
| **char n-gram TF-IDF** | **0.742** |
| symptom binary | 0.459 |
| three-state present | 0.459 |
| word TF-IDF | 0.378 |
| word+char fusion | 0.378 |

**结论：提升主要来自字符 n-gram 文本表示**，不是分类器本身。fusion 未超过 char-only（实现上简单拼接，且 word 部分拖累）。
注：当前 char n-gram 作用在**症状码拼接文本**，不是原始中文口语全文。

## 8. Shadow Mode

## **`RESEARCH_ONLY`**

| 条件 | 结果 |
| --- | --- |
| 优于 Round3 Direct | ✅ +29pp |
| 多 seed 稳定 | ✅ std≈0.013 |
| Risk-Coverage retained acc | ✅ 80% 目标下 0.81 |
| wrong-but-confident | ✅ ≤1% |
| Calibration (ECE) | ❌ **0.26**（>0.15） |
| Safety regression | ✅ 未改生产路径 |
| 科室覆盖 | ✅ test 11 科室 |

**不够进 Shadow Mode**：绝对表现与选择性拒答已明显改善，但 **ECE 过高**，概率不能直接当置信度用。下一步优先做温度/校准修复与更均衡的科室数据。

---

## 鲁棒性 + Selective（clean vs perturbed）

Clean retained acc（目标 80%）≈0.81。meaning-preserving 扰动后 coverage 与 retained acc 大体保持或略升，wrong-conf 仍低。标注 `robustness_simulation`。

## Safety 边界

离线契约检查 `all_pass=True`：

- Emergency 不因 Direct Department 进入普通路由（架构约束）
- Direct Department 不覆盖 Safety
- Abstention 不降低红旗优先级
- Safety Evaluation **142** cases 指标未变

## 学习曲线（Direct Dept）

char n-gram：20%→100% train **0.44 → 0.74**，趋势 **still_rising**。补数据仍有效。

---

## 暂缓（按任务书）

IG 产品化、RL、Hybrid Safety、GNN、LLM 微调、LTR——继续暂缓。

## 下一轮

1. **校准修复**（温度/Platt on char LR），目标 ECE≤0.15 后再谈 Shadow。
2. 按 Data Gap Map 补呼吸/泌尿/内分泌等科室独立表达。
3. 融合表示重做（避免 word 部分拖累）；考虑原始中文口语 char n-gram。
4. 保持 Safety-first：任何产品化仍需 L3。
