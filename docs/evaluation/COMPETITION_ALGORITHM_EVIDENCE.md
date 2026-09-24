# COMPETITION_ALGORITHM_EVIDENCE

更新时间：2026-09-16（任务 03：竞赛级算法评测、消融与系统集成验收）
机器可读索引：`evaluation/competition/evidence_index.json`（权威数字以该文件与 `eval_matrix.json` 为准）
定位：**离线研究证据**，不是临床验证，不可宣传为诊断准确率或临床有效。

---

## 0. 权威证据索引（写材料只引用这里）

| 事实 | 权威值 | 来源 | 采信 |
| --- | --- | --- | --- |
| 算法骨架 | Safety Gate → Direct Department → Selective Abstention → Care Routing（Adaptive Inquiry = RESEARCH_ONLY） | `evaluation/care_routing/ROUND4_REPORT.md` | 是 |
| 数据 | expanded_41 **1289** 行（structured 304 + training_long extras），公开文本集 | `round4_report.json` dataset | 是 |
| 诚实划分 seed=42 | train 840 / cal 236 / test **213** 行 / **25** 病种，Jaccard 0.8 | `round4_report.json` split_meta | 是 |
| disease-first 科室 | **0.291 ± 0.026** | `round3_hierarchical.json` | 是 |
| Direct Dept Round3 binary LR | **0.450 ± 0.026** | 同上 | 是 |
| Direct Dept 最佳 | **char n-gram TF-IDF + LR = 0.742 ± 0.013**（5 seeds） | `round4_report.json` | 是 |
| ECE（未校准 headline） | **0.259 ± 0.017** | 同上 | 是 |
| ECE（温度校准后，seed42） | **0.061**（T=0.5，准确率不变） | `round4_direct_department_matrix.json` | 是，但 readiness 仍看未校准门槛 |
| Selective 目标 80% | 实际 coverage **0.657**，retained Acc **0.807**，wrong-conf **0.007** | `round4_selective_routing.json` | 是 |
| Selective 目标 70% / 60% | Acc **0.838** / **0.873**（coverage 0.549 / 0.479） | 同上 | 是 |
| Adaptive Inquiry | 诚实近重复：IG−Random = **−0.0625**；random split ΔAcc +0.108 **有泄漏不可用** | `round2_inquiry.json` | 是 |
| Safety Evaluation | **142** cases，Recall **1.0**，Under/Over **0.0**，Emergency FN **0** | `evaluate_safety` 实测 | 是 |
| pytest | **215 passed**（206 基线 + 9 竞赛验收） | 本轮实测 | 是 |
| frontend boundary | **17** | `npm run test` | 是 |
| 数据质量 | scanned **31** / issues **186**（全部 `bus_routes.json`） | `data_quality_report.json` | 是 |
| Shadow / 产品化 | **`RESEARCH_ONLY`**（ECE 门槛 0.15 未过 headline） | `run_round4.readiness_decision` | 是 |

**文档漂移（禁止再抄旧数）**：`README.md` 仍写 Safety 135 cases / Over-triage 0.0312；`SCORECARD.md` 冻结在 2026-09-11（38-case、108 pytest、187 issues）；`MODEL_CARD.md` 仍只写 NB random-split Top-1 0.973 且声称“未做防泄漏切分”（实际上 `evaluation/model/grouped_split_report.json` 已有）。对照见 `evaluation/competition/number_drift.json`。

---

## 1. 当前算法架构

```text
Safety Gate  →  Direct Department  →  Calibration  →  Selective Abstention
     ↓                  ↓                                    ↓
 红旗/急症短路      char n-gram + LR                      拒答/追问
     ↓                  ↓                                    ↓
 Emergency          assistive routing score            Care Routing
 出口/120           （not_medical_confidence）     （多目标加权医院/医生）
```

- Safety Gate 为既有规则层，**永远优先**于任何学习模型；冲突时学习输出被 `safety_first_*` 投影清空。
- Direct Department / Selective / Adaptive Inquiry 仍在 `evaluation/` 研究侧（`RESEARCH_ONLY`）；并行 Agent 正在产品化 `backend/app/domain/triage/scsr.py` 边界，**未改 Safety 规则**。
- Care Routing 为正式 `/api/v1/recommendations` 的多目标加权排序（临床匹配、可及性、连续照护、公平性、availability、急症能力），缺失字段降权，学术指标权重 0。

## 2. 数据与划分

| 项 | 值 |
| --- | --- |
| 主数据 | `disease_symptom_structured_41diseases_long.csv`（304）+ `disease_symptom_training_long.csv` 扩展，**1289** 行 / 41 病 |
| 来源 | HF `shanover/disease_symptoms_prec_full`（MIT）、`fhai50032/Symptoms_to_disease_7k`（Apache-2.0） |
| 性质 | 公开文本集，**不是常州真实就诊分布，不是临床病例** |
| 主切分 | same-label 近重复组件 quota 切分，Jaccard **0.8**，seed 42/123/2026/3407/7777 |
| train/cal/test | 840 / 236 / 213（test 25 病种 / 11 科室） |
| 泄漏 | exact fingerprint train∩test = **0**，cal∩test = **0**；跨 split 近重复对 = **0**（Round3 审计） |
| 阈值 | Selective / 温度 **只来自 calibration**，test 从不调阈值 |

## 3. Baseline 矩阵

| Track | 指标 | 值 | 划分 / seeds | 来源 |
| --- | --- | --- | --- | --- |
| legacy disease-first → 科室 | Acc | **0.291 ± 0.026** | honest quota，3 seeds | `round3_hierarchical.json` |
| legacy disease-first → 疾病 | Acc | 0.265 ± 0.026 | 同上 | 同上 |
| Direct Dept binary LR（Round3） | Acc | **0.450 ± 0.026** | 同上 | 同上 |
| Direct Dept char n-gram + LR（Round4） | Acc | **0.742 ± 0.013** | 5 seeds | `round4_report.json` |
| NB / word / fusion | Acc | 0.328 / 0.378 / 0.378 | 5 seeds | representation ablation |
| 生产 NB 疾病模型（对照） | Top-1 | random 0.973 / **near-dup 0.208** / grouped CV 0.084 | 见 grouped 报告 | `grouped_split_report.json` |

**为什么 Direct Department 优于 disease-first**：产品要的是就医方向（科室）而不是疾病名；disease-first 在错误疾病上会把科室也带错（0.291），Direct Dept 在同一诚实切分上 0.450（Round3）→ 0.742（Round4 表示升级），且与临床决策粒度一致（挂哪科，而非诊断何病）。

**char n-gram 提升来自哪里**：固定 LR 的表示消融显示 char n-gram 0.742 ≫ binary 0.459 ≈ three-state 0.459 > word 0.378 ≈ fusion 0.378。提升来自**字符 2–4 gram 文本表示**（对症状码拼接文本的子串模式敏感），不是换分类器，也不是 fusion。Limitation：当前 char 作用在症状码拼接，不是原始中文口语全文。

## 4. 核心指标（honest quota，5 seeds）

| 模型 | Acc | Macro-F1 | Top-2 | ECE | Wrong-conf |
| --- | --- | --- | --- | --- | --- |
| **char n-gram + LR** | **0.742±0.013** | 0.642 | 0.876 | 0.259 | 0.003 |
| Linear SVM (binary) | 0.469±0.025 | 0.397 | 0.619 | 0.250 | 0.008 |
| LR (binary) / three-state | 0.459±0.024 | 0.382 | 0.623 | 0.207 | 0.046 |
| TF-IDF word / fusion | 0.378±0.028 | 0.366 | 0.627 | 0.259 | 0.060 |
| Multinomial NB | 0.327±0.026 | 0.252 | 0.588 | 0.098 | 0.026 |

per-department recall（seed42 char）：皮肤科/呼吸与危重症 1.0，感染 0.93，骨科 0.85，消化 0.78，心血管 0.73，普外 0.6，内分泌/神经 0.3，泌尿 0.18，**呼吸内科 0.0**。Accuracy 被高频科室抬高，**低召回科室不可被掩盖**。

## 5. Calibration / Risk–Coverage

**何时拒答**：max-probability（温度校准后）低于 **calibration 分位阈值**时 abstain；阈值按目标 coverage（100/90/80/70/60/50%）在 **cal** 上取分位，**test 只评估**。

| 目标 coverage | 实际 test coverage | Retained Acc | Wrong-conf |
| --- | --- | --- | --- |
| 100% | 0.995 | 0.627 | 0.005 |
| 90% | 0.878 | 0.663 | 0.005 |
| **80%** | **0.657** | **0.807** | **0.007** |
| 70% | 0.549 | 0.838 | 0.009 |
| 60% | 0.479 | 0.873 | 0.010 |

- Temperature scaling（cal 上拟合）：seed42 char ECE **0.269 → 0.061**（T=0.5），准确率不变。
- 但迁到 test 后 coverage 明显低于目标（80%→66%）→ **分布偏移仍在**。
- readiness 判定仍用未校准 ECE≈0.26 > 0.15 → **`RESEARCH_ONLY`**。Calibration 有改善，但未稳定过产品门槛，且概率仍**不得**解释为医学置信度。

## 6. 消融

1. **表示**（固定 LR）：char 0.742 > binary/three-state 0.459 > word/fusion 0.378。
2. **task 形态**：Direct Dept 0.742 ≫ disease-first 科室 0.291。
3. **Selective**：coverage↓ → retained Acc↑（0.63→0.87），wrong-conf 始终 ≤1%。
4. **学习曲线**：char 20%→100% train 0.44→0.74，`still_rising` → 补数据有收益。
5. **鲁棒性**：meaning-preserving synthetic 扰动下 selective 大体保持；标注 `robustness_simulation`，**不是临床鲁棒性**。

## 7. Care Routing 验证（规则/特征一致性，非临床有效）

复现：`.venv/bin/python -m evaluation.competition.care_routing_ablation --write`
结果：`evaluation/competition/care_routing_ablation.json`

| 验证项 | 结果 | 含义 |
| --- | --- | --- |
| feature/weight leave-one-out | 去掉 clinical 权重后分数 76.6→67.7 | 权重真实参与合成 |
| 缺失位置重平衡 | accessibility 置 0，其余归一化和为 1.0 | 缺失特征不参与排序 |
| 距离优先 vs 专科优先 | 近而弱 72.0 > 远而强 49.8；专科档反转为 67.8 > 58.5 | 偏好改变会改变排序 |
| Emergency 绕过 rerank | emergency 调整全 0；routine 第三名 −3.5 | 急症不被常规多样性惩罚 |
| Emergency 风险 | 无急诊字段 penalty 0.45 > 有字段 0.10 | 急症能力显式降风险 |
| 连续照护 | 「慢病复诊」0.82 > 「首次不适」0.55；收藏加权需 `continuity_preference` + favorite ids | 只在授权/语境下影响 |
| 缺失/不可信字段 | beds/daily 缺失时 availability=0；academic 权重 0；provisional 能力分不进排序 | 不完整证据不当高质量证据 |

**表述边界**：以上只证明「符合规则定义」，**不能**写成「临床有效 / 提升治愈率」。

## 8. Safety 回归

- 实测：`python -m evaluation.safety.evaluate_safety` → **142 cases，Red Flag Recall 1.0，Under-triage 0.0，Over-triage 0.0，Emergency FN 0**。
- 契约：`round4_safety_check.json` `all_pass=true`（Emergency 不被科室模型改道；拒答不降红旗优先级）。
- 黄金测试 `test_safety_gate_precedes_learning_model_on_conflict`：模糊主诉 + `red_flag_check=present` → **EMERGENCY** 且疾病 abstain。
- 未改任何 Safety 规则 / 红旗 / 生产门禁。

## 9. 三个 E2E 黄金案例

自动验收：`tests/test_competition_golden_e2e.py`（4 tests）+ 采集 `evaluation/competition/golden_e2e.py --write`。
边界固定行为，不固定脆弱分数。

| 案例 | 观测 | 通过 |
| --- | --- | --- |
| 普通明确路径 | `咳嗽三天…` → ROUTINE，呼吸内科，5 医院 / 8 医生，`routine_outpatient` | ✅ |
| 模糊 → 追问 → 再路由 | `不舒服` → INSUFFICIENT_INFORMATION，abstain，8 个结构化追问；答案不污染 `condition`/`original_condition` | ✅ |
| Emergency short-circuit | `持续胸痛喘不上气` → EMERGENCY，abstain，`emergency_fast_track`，map 急诊字段列表，专家偏好关闭 | ✅ |

## 10. 数据 / 评测限制

**数据 provenance 分级**（`data_validation`：31 datasets / 186 issues）：

| 级别 | 内容 | 动作 |
| --- | --- | --- |
| 影响算法评测 | **无**（症状-疾病集独立于 transit 目录） | — |
| 影响推荐可信度 | 医生/医院来源仍 `public_source_mixed` / `provisional`（R-002） | 保持 provisional 标注，不升格为官方事实 |
| 只影响展示 | `bus_routes.json` 180×`PLACEHOLDER_TIMESTAMP` + 6×`TIME_ORDER` | 已隔离：交通 `quality=PROVISIONAL rankable=False` |
| 已知可接受 | 上述 186 条只读登记 | 本轮不修，不静默改数 |

其他限制：
1. expanded_41 是公开文本，不是常州就诊分布；类别不均衡（感染/皮肤科主导），呼吸内科 recall=0。
2. char n-gram 作用在症状码拼接，不是原始口语中文。
3. 温度校准在 cal 上有效，迁 test 后 coverage 偏移；conformal 仅研究可用。
4. Adaptive Inquiry 为 three-state **simulation**，IG 未稳定优于 Random。
5. Robustness 为 synthetic perturbation，不是临床鲁棒性。
6. Safety 142 固定样例 ≠ 临床覆盖（R-001）。

## 11. 比赛可宣传 / 禁止宣传

**可以写**：
- 离线研究显示 Direct Department 在诚实近重复切分上优于 disease-first 科室映射（0.742 vs 0.291）。
- Selective abstention 在 calibration 阈值下可把 retained accuracy 提到 0.81–0.87，wrong-but-confident ≤1%。
- 表示消融表明提升主要来自 char n-gram。
- Safety Gate 永远优先；142-case 固定样例 Red Flag Recall 1.0 / Emergency FN 0（工程回归）。
- Care Routing 对特征/偏好/缺失字段按可解释规则响应（可复现消融）。
- 模型不可用或低可信时 abstain + 追问 + 安全出口；位置缺失时距离权重归零。

**禁止宣传**：
- ❌ 临床准确率 / 诊断能力 / 处方或急救指令。
- ❌ 用 random-split NB 0.973 或 random-split IG +0.11 冒充诚实结果。
- ❌ 把 ECE 0.06（单 seed 温度）写成“已临床校准的置信度”。
- ❌ 把 synthetic robustness 写成真实临床鲁棒性。
- ❌ 把 Data Gap Map 写成医疗重要性排名。
- ❌ 把 Care Routing 消融写成“临床有效”。
- ❌ 把目录急诊字段写成实时可接诊。
- ❌ 当前结论一律标注 **离线研究证据，非临床验证**。

## 12. 复现命令（材料引用勿手抄）

```bash
# 算法矩阵 / 消融 / 黄金案例 / 安全 / 模型防泄漏 / 数据
.venv/bin/python -m evaluation.care_routing.run_round4 --write
.venv/bin/python -m evaluation.care_routing.run_round3 --write
.venv/bin/python -m evaluation.care_routing.run_round2 --write
.venv/bin/python -m evaluation.care_routing.run_experiments --write
.venv/bin/python -m evaluation.competition.care_routing_ablation --write
.venv/bin/python -m evaluation.competition.run_matrix --write
.venv/bin/python -m evaluation.competition.golden_e2e --write
.venv/bin/python -m evaluation.safety.evaluate_safety
.venv/bin/python -m evaluation.model.evaluate_grouped --write
.venv/bin/python -m data_validation.validate_datasets --data-root data --output-dir data_validation
.venv/bin/python -m pytest
cd frontend && npm run typecheck && npm run test && npm run build
```

机器可读结果：
- `evaluation/competition/evidence_index.json` — 单一权威索引
- `evaluation/competition/eval_matrix.json` — 竞赛评测矩阵
- `evaluation/competition/care_routing_ablation.json` — Care Routing 消融
- `evaluation/competition/golden_e2e.json` — 三案例观测
- `evaluation/competition/number_drift.json` — 文档数字漂移
- `evaluation/care_routing/results/round*.json` — 原始轮次结果（保留失败/阴性：IG≤Random、ECE 未过线）

## 13. 实际结果 / P0 / P1 / 并行接口

**本轮实测**：pytest **215 passed**（+9 竞赛验收）；frontend boundary 17；Safety 142 全绿；Round4 `--quick` 复现 readiness=`RESEARCH_ONLY`；三条黄金路径全过。

**P0**
1. 文档数字漂移（README 135/0.0312、SCORECARD 38-case/108）会让评审抓到不一致 → 材料只准引用 `evidence_index.json`；README/SCORECARD 应由文档 owner 后续对齐（本轮未改以降低冲突）。
2. char LR headline ECE 0.26 未过 0.15 → 不得进 Shadow/产品置信度；温度校准有改善但不足以放行。

**P1**
1. 呼吸内科/泌尿外科/内分泌 recall≈0，accuracy 掩盖低召回科室 → 按 Data Gap Map 补独立表达后再报 per-dept。
2. cal→test coverage 漂移（目标 80% 实得 66%）→ 需要更稳校准或显式 coverage 说明。
3. Adaptive Inquiry 在诚实切分上不优于 Random → 保持 simulation-only，勿写“追问提升路由准确率”。
4. transit 186 问题仅展示层；若未来进入排序须先过质量门。

**与另外两个 Agent 的接口与冲突面**
| 边界 | 依赖 | 冲突风险 |
| --- | --- | --- |
| `backend/app/domain/triage/scsr.py`（算法产品化 Agent） | 阶段契约需与本文架构一致；不得改 Safety | 低：本轮未改该文件；若其把 RESEARCH_ONLY 模型接进 `/api/v1` 需 L3 |
| `frontend/src/**`（UX Agent） | 正在改 TriagePage/TriageResults/CarePath 等 | **高**：本轮零前端改动；合并时勿用其工作树覆盖 |
| `evaluation/`、`tests/test_competition_*` | 本轮独占 | 低 |
| `docs/status/current.md` / README / SCORECARD | 数字对齐 | 中：共享文档，提交前 rebase |
| Safety Gate / 红旗 / `/api/v1` envelope | 硬契约 | 不可动；本轮已用测试锁行为 |

**回滚点**：新增文件均可独立删除（`evaluation/competition/`、`tests/test_competition_*.py`、`docs/evaluation/COMPETITION_ALGORITHM_EVIDENCE.md`）；无核心算法/前端/ Safety 修改。

## 14. 反作弊审计结论（机器可读：`evaluation/competition/anti_cheating_audit.json`）

| 检查项 | 状态 | 证据 |
| --- | --- | --- |
| random vs honest split 区分 | pass_with_disclosure | 主指标只用 honest quota（Jaccard 0.8）；random-split 仅作 leaky baseline 并标注 |
| 禁止 test 调阈值 | pass | Selective 阈值与温度只在 cal 上拟合 |
| 重复/近重复泄漏 | pass | train∩test exact fingerprint = 0；cal∩test = 0 |
| calibration 与 test 独立 | pass | quota 三分组互斥；cal 只用于温度与阈值 |
| 类别不均衡 | disclosed | 感染/皮肤科主导；呼吸内科 recall=0 |
| accuracy 掩盖低召回科室 | disclosed | Acc 0.742 vs Macro-F1 0.642；呼吸/泌尿/内分泌/神经 recall 低 |
| synthetic robustness 不过宣称 | pass_with_limitation | 仅 meaning-preserving 扰动，标注 robustness_simulation |

---

## 15. 交付与并行冲突面（收口）

**新增（本评测 Agent 独占，可整目录回滚）**
- `docs/evaluation/COMPETITION_ALGORITHM_EVIDENCE.md`
- `evaluation/competition/`：`evidence_index.json`、`eval_matrix.json`、`care_routing_ablation.{py,json}`、`golden_e2e.{py,json}`、`run_matrix.py`、`number_drift.json`、`anti_cheating_audit.json`
- `tests/test_competition_golden_e2e.py`、`tests/test_competition_care_routing_ablation.py`
- `docs/status/current.md` 追加一节记录

**实测门禁**
- `pytest`：**215 passed**
- `frontend npm run test`：**17 passed**
- `evaluation.safety.evaluate_safety`：**142 cases / Recall 1.0 / FN 0**
- 复现：`evaluation.competition.* --write` 均成功

**P0**
1. 文档数字漂移：README 仍写 Safety 135 / Over-triage 0.0312；SCORECARD 冻结 38-case / 108 pytest。材料只准引用 `evidence_index.json`。
2. char LR headline ECE 0.26 未过 0.15 门槛 → 维持 `RESEARCH_ONLY`，概率不得作医学置信度。

**P1**
1. 低召回科室（呼吸内科 0.0 等）被 accuracy 掩盖；需按 Data Gap 补数据后再报 per-dept。
2. cal→test coverage 偏移（目标 80% 实得 66%）。
3. Adaptive Inquiry 诚实切分不优于 Random → 保持 simulation-only。
4. transit 186 问题仅展示层；进入排序前须过质量门。

**与另外两个 Agent 的接口 / 冲突**
| 边界 | 风险 | 说明 |
| --- | --- | --- |
| `backend/app/domain/triage/scsr.py`（算法产品化） | 低 | 本轮未改；阶段契约须与本文架构一致，接入 `/api/v1` 需 L3 |
| `frontend/src/**`、`frontend/test/**`、`ALGORITHM_VISIBLE_UX.md`（UX Agent） | **高** | 本轮零前端改动；合并勿覆盖对方工作树 |
| `docs/status/current.md`、README、SCORECARD | 中 | 共享文档，提交前 rebase |
| Safety Gate / 红旗 / `/api/v1` envelope | 不可动 | 已用黄金测试锁行为 |
