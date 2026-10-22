# COMPETITION_ALGORITHM_EVIDENCE

更新时间：2026-09-16（任务 03：竞赛级算法评测、消融与系统集成验收）
**2026-10-22 修订：按 P0-01 预测器身份修复后的口径重写数字**（旧 `0.742 / 0.807 / 0.657 / ECE 0.061` 均来自模型版本不一致的旧结果，已作废）。
机器可读索引：`evaluation/competition/evidence_index.json`（权威数字以该文件与 `eval_matrix.json` 为准）
定位：**离线研究证据**，不是临床验证，不可宣传为诊断准确率或临床有效。

> 修订说明：2026-10-02 修复了 cal/test/clean/perturbed 混用不同重训模型的问题（矩阵 `epochs=35,lr=0.35` vs 校准 `epochs=70,lr=0.4`）。修复后同一预测器口径为 char LR Acc **0.608179**、80% 目标 coverage **0.760563** / retained Acc **0.740741**。旧 `0.742438` 无法从当前源码复现，保留在 `evaluation/core_exploration/legacy_evidence/` 仅作历史对照。详见 `docs/algorithm/CORE_EXPLORATION_REPORT.md`。

---

## 0. 权威证据索引（写材料只引用这里）

| 事实 | 权威值 | 来源 | 采信 |
| --- | --- | --- | --- |
| 算法骨架 | Safety Gate → Direct Department → Selective Abstention → Care Routing（Adaptive Inquiry = RESEARCH_ONLY） | `evaluation/care_routing/ROUND4_REPORT.md` | 是 |
| 数据 | expanded_41 **1289** 行（structured 304 + training_long extras），公开文本集 | `round4_report.json` dataset | 是 |
| 诚实划分 seed=42 | train 840 / cal 236 / test **213** 行 / **25** 病种，Jaccard 0.8 | `round4_report.json` split_meta | 是 |
| disease-first 科室 | **0.291 ± 0.026** | `round3_hierarchical.json` | 是 |
| Direct Dept Round3 binary LR | **0.450 ± 0.026** | 同上 | 是 |
| Direct Dept Round4 手写 char LR（修复后） | **0.608179 ± 0.034233**（5 seeds） | `round4_report.json` | 是 |
| 旧 Round4 headline | **0.742438 —— 不可复现，禁引** | `legacy_evidence/` | 否 |
| 标准嵌套选择主流程（新） | **94.25% ± 2.00pp**，Macro-F1 **94.65%**，ECE **0.0321** | `CORE_EXPLORATION_REPORT.md` §3 | 是，限内部公开文本 |
| ECE（未校准，char LR） | **0.195829 ± 0.043508** | `round4_report.json` | 是 |
| ECE（温度校准，seed42） | **0.192779 → 0.106119**（T=0.7，准确率不变 0.624413） | `round4_direct_department_matrix.json` | 是，readiness 仍看未校准门槛 |
| Selective 目标 80% | 实际 coverage **0.760563**，retained Acc **0.740741**，wrong-conf **0.006173** | `round4_selective_routing.json` | 是（目标未达成，如实报） |
| Selective 目标 70% / 60% | Acc **0.81203** / **0.850877**（coverage 0.624413 / 0.535211） | 同上 | 是 |
| 全 304 行症状-only grouped CV | binary **61.51%** / word **60.86%** / segmented-char **53.29%** | `CORE_EXPLORATION_REPORT.md` §3 | 是 |
| 结构化 → 另一来源文本 | **56.11%** | 同上 | 是 |
| 打乱训练标签负对照 | **15.62%** | 同上 | 是 |
| Adaptive Inquiry | IG **34.35%** vs Random **26.26%**；IG vs Frequency **+0.43pp** | `round2_inquiry.json` / `summary.json` | 是，标注未证明优越 |
| Safety Evaluation | **142** cases，Recall **1.0**，Under/Over **0.0**，Emergency FN **0** | `evaluate_safety` 实测（2026-10-22 复跑） | 是 |
| pytest | **1043** collected（2026-10-22 `--collect-only`）；提交前须重跑全量 | 本机实测 | 是 |
| frontend boundary | **22** | `npm run test`（2026-10-22） | 是 |
| 浏览器 E2E | **108** | `npx playwright test --list`（2026-10-22） | 是 |
| 数据质量 | scanned **31** / issues **186**（全部 `bus_routes.json`） | `data_quality_report.json` | 是 |
| Shadow / 产品化 | **`RESEARCH_ONLY`**（未校准 ECE 0.196 未过 0.15 门槛） | `run_round4.readiness_decision` | 是 |

**当前文档漂移状态（2026-10-22 已对齐）**：`README.md`、`SAFETY_CARD.md`、`SCORECARD.md`、`MODEL_CARD.md`、`PINNED_VERSIONS.md`、`memory.md` 的 Safety 142 / Over-triage 0 / 测试计数已更新。`evaluation/competition/number_drift.json` 是 2026-09-16 的历史快照，仅作漂移检测样例，不作为当前值。

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
| 数据构成问题 | 985 条扩展文本中 723 条“症状码”实为长主诉/疾病介绍；33 条命中精确疾病名（已在遮蔽对照中检验） |

## 3. Baseline 矩阵

| Track | 指标 | 值 | 划分 / seeds | 来源 |
| --- | --- | --- | --- | --- |
| legacy disease-first → 科室 | Acc | **0.291 ± 0.026** | honest quota，3 seeds | `round3_hierarchical.json` |
| legacy disease-first → 疾病 | Acc | 0.265 ± 0.026 | 同上 | 同上 |
| Direct Dept binary LR（Round3） | Acc | **0.450 ± 0.026** | 同上 | 同上 |
| Direct Dept char n-gram + LR（Round4，修复后） | Acc | **0.608179 ± 0.034233** | 5 seeds | `round4_report.json` |
| 标准模型嵌套选择主流程（新） | Acc | **94.25% ± 2.00pp** | 5 seeds，1289 行 | `CORE_EXPLORATION_REPORT.md` §3 |
| 生产 NB 疾病模型（对照） | Top-1 | random 0.973 / **near-dup 0.208** / grouped CV 0.084 | 见 grouped 报告 | `grouped_split_report.json` |

**为什么 Direct Department 优于 disease-first**：产品要的是就医方向（科室）而不是疾病名；disease-first 在错误疾病上会把科室也带错（0.291），Direct Dept 在同一诚实切分上 0.450（Round3）→ 0.608（Round4 表示升级）。

**为什么 0.608 与 94.25% 不能混用**：两者是不同流程、不同表示、不同选择协议。0.608 是固定手写配置的 Round4 复现；94.25% 是标准优化器 + 特征尺度 + 训练内嵌套选择的完整主流程。报告必须分别标注，且**旧 0.742 已作废，不得与任一数字并列**。

**char n-gram 提升来自哪里**：固定 LR 的表示消融显示 char n-gram 0.608 ≫ binary 0.459 ≈ three-state 0.459 > fusion 0.431 > word 0.378 > NB 0.327。提升来自**字符 2–4 gram 文本表示**（对症状码拼接文本的子串模式敏感），不是换分类器，也不是 fusion。Limitation：当前 char 作用在症状码拼接，不是原始中文口语全文。

## 4. 核心指标（honest quota，修复后口径）

| 模型 | Acc | Macro-F1 | Top-2 | ECE（未校准） | Wrong-conf |
| --- | --- | --- | --- | --- | --- |
| **char n-gram + LR** | **0.608179 ± 0.034233** | **0.404872** | **0.762639** | **0.195829** | **0.001818** |
| Linear SVM (binary) | 未按修复口径重报 | — | — | — | — |
| LR (binary) / three-state | 0.459129（均值） | — | — | — | — |
| TF-IDF word | 0.377989（均值） | — | — | — | — |
| word + char fusion | 0.430939（均值） | — | — | — | — |
| Multinomial NB | 0.326695（均值） | — | — | — | — |

> 除 char LR 外，其余模型仅有表示消融的均值，**没有**修复后的 Macro-F1/Top-2/ECE 完整统计；不得沿用旧表的 ±/ECE 数值补齐空格。需要时重跑 `evaluation.core_exploration.study --write`。

per-department recall（seed42 char）：皮肤科/呼吸与危重症 1.0，感染 0.93，骨科 0.85，消化 0.78，心血管 0.73，普外 0.6，内分泌/神经 0.3，泌尿 0.18，**呼吸内科 0.0**。Accuracy 被高频科室抬高，**低召回科室不可被掩盖**。

## 5. Calibration / Risk–Coverage

**何时拒答**：max-probability（温度校准后）低于 **calibration 分位阈值**时 abstain；阈值按目标 coverage 在 **cal** 上取分位，**test 只评估**。

| 目标 coverage | 实际 test coverage | Retained Acc | Wrong-conf |
| --- | --- | --- | --- |
| 100% | 0.990610 | 0.625592 | 0.004739 |
| 90% | 0.915493 | 0.646154 | 0.005128 |
| **80%** | **0.760563** | **0.740741** | **0.006173** |
| 70% | 0.624413 | 0.812030 | 0.007519 |
| 60% | 0.535211 | 0.850877 | 0.008772 |
| 50% | 0.474178 | 0.881188 | 0.009901 |

- 全覆盖（阈值 0）Accuracy **0.624413**，与同模型 raw/temperature argmax 一致 —— 这是 P0-01 修复后新增的一致性检查。
- Temperature scaling（cal 上拟合）：seed42 char ECE **0.192779 → 0.106119**（T=0.7），准确率不变。
- 但迁到 test 后 coverage 明显低于目标（80% → 76%）→ **分布偏移仍在**。
- readiness 判定仍用未校准 ECE≈0.196 > 0.15 → **`RESEARCH_ONLY`**。Calibration 有改善，但未稳定过产品门槛，且概率仍**不得**解释为医学置信度。

## 6. 消融

1. **表示**（固定 LR）：char 0.608 > binary/three-state 0.459 > fusion 0.431 > word 0.378 > NB 0.327。
2. **task 形态**：Direct Dept 0.608 ≫ disease-first 科室 0.291。
3. **Selective**：coverage↓ → retained Acc↑（0.63→0.88），wrong-conf 始终 ≤1%。
4. **学习曲线**（新主流程）：20/40/60/80/100% 训练组 Acc 约 82.58/89.86/91.60/94.45/94.35%；80→100 **不再稳定上升**，旧“仍明显上升”叙事作废。
5. **集成**：top3 平均 Acc 94.63% / ECE 0.0329；全 8 平均 Acc 94.28% 但 ECE 恶化到 0.1541 → 不宣称集成优越。
6. **鲁棒性**：meaning-preserving synthetic 扰动下 selective 大体保持；标注 `robustness_simulation`，**不是临床鲁棒性**。
7. **负对照**：打乱训练标签 Acc **15.62%** → 高分不是直接读取测试标签所致，但仍不构成临床真实性证明。

## 7. Care Routing 验证（规则/特征一致性，非临床有效）

复现：`python -m evaluation.competition.care_routing_ablation --write`
结果：`evaluation/competition/care_routing_ablation.json`

| 验证项 | 结果 | 含义 |
| --- | --- | --- |
| feature/weight leave-one-out | 去掉 clinical 权重后分数 76.6→67.7 | 权重真实参与合成 |
| 缺失位置重平衡 | accessibility 置 0，其余归一化和为 1.0 | 缺失特征不参与排序 |
| 距离优先 vs 专科优先 | 近而弱 72.0 > 远而强 49.8；专科档反转为 67.8 > 58.5 | 偏好改变会改变排序 |
| Emergency 绕过 rerank | emergency 调整全 0；routine 第三名 −3.5 | 急症不被常规多样性惩罚 |
| Emergency 风险 | 无急诊字段 penalty 0.45 > 有字段 0.10 | 急症能力显式降风险 |
| 连续照护 | 「慢病复诊」0.82 > 「首次不适」0.55 | 只在授权/语境下影响 |
| 缺失/不可信字段 | beds/daily 缺失时 availability=0；academic 权重 0；provisional 能力分不进排序 | 不完整证据不当高质量证据 |

**表述边界**：以上只证明「符合规则定义」，**不能**写成「临床有效 / 提升治愈率」。

## 8. Safety 回归

- 实测（2026-10-22）：`python -m evaluation.safety.evaluate_safety` → **142 cases，Red Flag Recall 1.0，Under-triage 0.0，Over-triage 0.0，Emergency FN 0**。
- 契约：`round4_safety_check.json` `all_pass=true`（Emergency 不被科室模型改道；拒答不降红旗优先级）。
- 黄金测试 `test_safety_gate_precedes_learning_model_on_conflict`：模糊主诉 + `red_flag_check=present` → **EMERGENCY** 且疾病 abstain。
- 未改任何 Safety 规则 / 红旗 / 生产门禁。

## 9. 三个 E2E 黄金案例

自动验收：`tests/test_competition_golden_e2e.py`（4 tests）+ `tests/test_competition_care_routing_ablation.py`（5 tests）；采集 `evaluation/competition/golden_e2e.py --write`。
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
| 已知可接受 | 上述 186 条只读登记 | 不修，不静默改数 |

其他限制：
1. expanded_41 是公开文本，不是常州就诊分布；类别不均衡（感染/皮肤科主导），呼吸内科 recall=0。
2. char n-gram 作用在症状码拼接，不是原始口语中文。
3. 温度校准在 cal 上有效，迁 test 后 coverage 偏移；conformal 仅研究可用。
4. Adaptive Inquiry 为 three-state **simulation**；IG 仅比高频策略高 0.43pp。
5. Robustness 为 synthetic perturbation，不是临床鲁棒性。
6. Safety 142 固定样例 ≠ 临床覆盖（R-001）。
7. 结构化→另一来源文本仅 **56.11%**，是当前最真实的泛化水平参考。

## 11. 比赛可宣传 / 禁止宣传

**可以写**：
- 离线研究显示 Direct Department 在诚实近重复切分上优于 disease-first 科室映射（0.608 vs 0.291）。
- Selective abstention 在 calibration 阈值下把 retained accuracy 提到 0.74（80% 目标档），wrong-but-confident ≤1%。
- 表示消融表明提升主要来自 char n-gram。
- Safety Gate 永远优先；142-case 固定样例 Red Flag Recall 1.0 / Emergency FN 0（工程回归）。
- Care Routing 对特征/偏好/缺失字段按可解释规则响应（可复现消融）。
- 模型不可用或低可信时 abstain + 追问 + 安全出口；位置缺失时距离权重归零。

**禁止宣传**：
- ❌ 临床准确率 / 诊断能力 / 处方或急救指令。
- ❌ 旧 0.742 / 0.807 / 0.838 / 0.873 / coverage 0.657（P0-01 修复前，禁引）。
- ❌ 用 random-split NB 0.973 或 random-split IG +0.11 冒充诚实结果。
- ❌ 把 ECE 0.106（单 seed 温度）写成“已临床校准的置信度”。
- ❌ 把 synthetic robustness 写成真实临床鲁棒性。
- ❌ 把 Data Gap Map 写成医疗重要性排名。
- ❌ 把 Care Routing 消融写成“临床有效”。
- ❌ 把目录急诊字段写成实时可接诊。
- ❌ 当前结论一律标注 **离线研究证据，非临床验证**。

## 12. 复现命令（材料引用勿手抄）

```bash
# 算法矩阵 / 消融 / 黄金案例 / 安全 / 模型防泄漏 / 数据
python -m evaluation.care_routing.run_round4 --write
python -m evaluation.care_routing.run_round3 --write
python -m evaluation.care_routing.run_round2 --write
python -m evaluation.care_routing.run_experiments --write
python -m evaluation.competition.care_routing_ablation --write
python -m evaluation.competition.run_matrix --write
python -m evaluation.competition.golden_e2e --write
python -m evaluation.safety.evaluate_safety
python -m evaluation.model.evaluate_grouped --write
python -m data_validation.validate_datasets --data-root data --output-dir data_validation
python -m pytest
cd frontend && npm run typecheck && npm run test && npm run build
```

机器可读结果：
- `evaluation/competition/evidence_index.json` — 单一权威索引
- `evaluation/competition/eval_matrix.json` — 竞赛评测矩阵
- `evaluation/competition/care_routing_ablation.json` — Care Routing 消融
- `evaluation/competition/golden_e2e.json` — 三案例观测
- `evaluation/competition/number_drift.json` — 数字漂移快照（2026-09-16）
- `evaluation/care_routing/results/round*.json` — 原始轮次结果（保留失败/阴性）
- `evaluation/core_exploration/results/summary.json` — 修复后主研究汇总

## 13. 实际结果 / P0 / P1 / 并行接口

**本轮实测（2026-10-22）**：pytest 收集 **1043**（提交前须重跑全量）；frontend boundary **22**；浏览器 E2E **108**；Safety **142 全绿**；数据扫描 **31/186**；Round4 readiness=`RESEARCH_ONLY`；三条黄金路径全过。

**P0**
1. 旧口径清理已完成（本文件、`evidence_index.json`、`anti_cheating_audit.json`、`memory.md`、`SCORECARD.md`、`SAFETY_CARD.md`、`PINNED_VERSIONS.md`）。任何材料只准引用本文件 §0 或 `evidence_index.json`。
2. char LR 未校准 ECE 0.196 未过 0.15 → 不得进 Shadow/产品置信度。

**P1**
1. 呼吸内科/泌尿外科/内分泌 recall≈0，accuracy 掩盖低召回科室 → 按 Data Gap Map 补独立表达后再报 per-dept。
2. cal→test coverage 漂移（目标 80% 实得 76%）→ 需要更稳校准或显式 coverage 说明。
3. Adaptive Inquiry 在诚实切分上仅比 Frequency 高 0.43pp → 保持 simulation-only，勿写“追问提升路由准确率”。
4. 非 char 模型缺少修复后的完整指标 → 需要时重跑 `study --write`，不得用旧 ±/ECE 补空。

**与另外两个 Agent 的接口与冲突面**
| 边界 | 依赖 | 冲突风险 |
| --- | --- | --- |
| `backend/app/domain/triage/scsr.py`（算法产品化 Agent） | 阶段契约需与本文架构一致；不得改 Safety | 低：本轮未改该文件；若其把 RESEARCH_ONLY 模型接进 `/api/v1` 需 L3 |
| `frontend/src/**`（UX Agent） | 正在改 TriagePage/TriageResults/CarePath 等 | **高**：本轮零前端改动；合并时勿用其工作树覆盖 |
| `evaluation/`、`tests/test_competition_*` | 本轮独占 | 低 |
| `docs/status/current.md` / README / SCORECARD | 数字对齐 | 中：共享文档，提交前 rebase |
| Safety Gate / 红旗 / `/api/v1` envelope | 硬契约 | 不可动；本轮已用测试锁行为 |

**回滚点**：本轮仅改文档与证据 JSON 数字；`git revert` 单个 commit 即可，不涉及运行时、模型权重或前端。

## 14. 反作弊审计结论（机器可读：`evaluation/competition/anti_cheating_audit.json`）

| 检查项 | 状态 | 证据 |
| --- | --- | --- |
| random vs honest split 区分 | pass_with_disclosure | 主指标只用 honest quota（Jaccard 0.8）；random-split 仅作 leaky baseline 并标注 |
| 禁止 test 调阈值 | pass | Selective 阈值与温度只在 cal 上拟合 |
| 重复/近重复泄漏 | pass | train∩test exact fingerprint = 0；cal∩test = 0 |
| calibration 与 test 独立 | pass | quota 三分组互斥；cal 只用于温度与阈值 |
| 预测器身份一致 | pass | cal/test/clean/perturbed 复用同一拟合模型；全覆盖 Acc = 同模型 argmax Acc（0.624413） |
| 类别不均衡 | disclosed | 感染/皮肤科主导；呼吸内科 recall=0 |
| accuracy 掩盖低召回科室 | disclosed | Acc 0.608 vs Macro-F1 0.405；呼吸/泌尿/内分泌/神经 recall 低 |
| synthetic robustness 不过宣称 | pass_with_limitation | 仅 meaning-preserving 扰动，标注 robustness_simulation |

## 15. 交付与并行冲突面（收口）

**证据文件**
- `docs/evaluation/COMPETITION_ALGORITHM_EVIDENCE.md`（本文件，2026-10-22 修订）
- `evaluation/competition/`：`evidence_index.json`、`eval_matrix.json`、`care_routing_ablation.{py,json}`、`golden_e2e.{py,json}`、`run_matrix.py`、`number_drift.json`、`anti_cheating_audit.json`
- `tests/test_competition_golden_e2e.py`、`tests/test_competition_care_routing_ablation.py`

**实测门禁（2026-10-22）**
- `pytest --collect-only`：**1043**
- `frontend npm run test`：**22 passed**
- `npx playwright test --list`：**108**
- `evaluation.safety.evaluate_safety`：**142 cases / Recall 1.0 / FN 0**
- `data_validation`：**31 / 186**

**P0**
1. 数字口径统一：只引本文件 §0 或 `evidence_index.json`。
2. 未校准 ECE 0.196 未过 0.15 门槛 → 维持 `RESEARCH_ONLY`。

**P1**
1. 低召回科室（呼吸内科 0.0 等）被 accuracy 掩盖。
2. cal→test coverage 偏移（80%→76%）。
3. Adaptive Inquiry 未证明优于高频策略。
4. transit 186 问题仅展示层；进入排序前须过质量门。
