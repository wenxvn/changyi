# ROUND2 报告：数据诚实性、负症状表示与可产品化追问

更新时间：2026-09-16  
协议主表：`near_duplicate_same_label` 三分组（train/cal/test）  
复现：`.venv/bin/python -m evaluation/care_routing.run_round2 --write`  
产物：`results/round2_*.json` / `round2_error_analysis.md` / `data_schema/`

**安全边界未变**：Safety Gate / 红旗规则 / Safety Evaluation baseline / 生产 API 均未修改。三态追问为 **simulation**，不是真实患者实验。

---

## 六个必答问题

### 1. near-dup Accuracy≈0.188 的主要根因是什么？

**结论：数据结构与 NB 容量叠加；不能只怪“数据少”。**

| 证据 | 数值 |
| --- | --- |
| 单 component 疾病 | **33/41**（无法诚实拆分） |
| 多 component 疾病 | 8/41 |
| 诚实 test 规模 | 16 行 / 8 病种 |
| unseen combination ratio | **1.0** |
| unseen symptom token ratio | **0.28** |
| NB Top-1 / Top-3 | 0.1875 / 0.25 |
| 同切分 LR / LinearSVM | **1.0 / 1.0** |
| TF-IDF + LR | 0.9375 |

解读：

- random split 在同样 304 条上可到 ~0.98，所以不是“数据绝对量”单因；
- 诚实切分下 test 组合 **全部未见**，且 28% 症状 token 在 train 词表中未出现；
- 但线性模型在同一 test 上可达 1.0，说明 **NB 独立性假设/Laplace 平滑在稀疏组合上明显吃亏**；
- 因此产品化瓶颈仍是数据与表达，但 **正式 Triage 分类器也应考虑脱离纯 NB**（需 L3 与更多数据）。

完整表：`results/round2_error_analysis.json` + `round2_error_analysis.md`。

### 2. 三态症状表示能否正确支持 negative answers？

**结论：解析层可以，且单测 100% 通过；后验更新层也可以把 absent 写成互补似然。**

- 模块：`symptom_state.py`（Present / Absent / Unknown；Unknown 不写特征）
- 否定解析：保守左文窗匹配 `没有 / 无 / 不伴 / 未出现 / 否认…`
- 单测 `run_negation_unit_cases`：**10/10**
  - `胸痛` → present
  - `没有胸痛` / `目前没有明显胸痛` → absent
  - `不知道有没有发热` → unknown
  - 多症状句：`有咳嗽，没有胸痛` → cough present + chest_pain absent
- 安全：红旗否定 **不接入** 生产 Safety；present 优先于 absent（双提时保守保留阳性）

### 3. IG 在加入 negative answers 后是否仍优于 Random / MostFreq？

**结论：在诚实 near-dup 协议上，IG 未稳定优于 Random。**

三态 simulation、forced 5 问、初始 1 症：

| 策略 | Final Acc | Δ vs Random | 科室 Acc |
| --- | --- | --- | --- |
| information_gain | 0.1875 | **-0.0625** | 0.25 |
| random | **0.2500** | — | **0.375** |
| most_frequent | 0.1250 | -0.125 | 0.125 |
| margin | 0.1875 | -0.0625 | 0.3125 |
| fixed_order | 0.1250 | -0.125 | 0.125 |

说明：上一轮 IG 优势主要出现在 **模型仍有区分能力的泄漏切分**；诚实切分上基础模型太弱，IG 选题无法扭转。  
另：Accuracy–Question Cost Pareto 在 IG 上 **0→5 问全程平坦（0.1875）**，继续加问无收益。

### 4. 什么 stopping policy 在准确率与追问次数之间最合理？

**结论：诚实切分上四种策略 Accuracy 全部 0.1875；`combined`/`entropy` 略省问题数。**

| 策略 | Final Acc | Avg Q | Stop Rate | Wrong-but-confident |
| --- | --- | --- | --- | --- |
| fixed_n | 0.1875 | 5.00 | 0.00 | 0.0 |
| entropy_threshold | 0.1875 | 4.81 | 0.06 | 0.0 |
| prediction_set_threshold | 0.1875 | 5.00 | 0.00 | 0.0 |
| combined（校准分位数阈值） | 0.1875 | 4.81 | 0.06 | 0.0 |

推荐研究口径：**combined**（置信度 ∨ 熵比 ∨ set size ∨ margin + max N），阈值只来自 calibration。  
但当前证据下 **不宜把它当生产停问策略**——准确率不随策略变化，说明瓶颈不在停问。

### 5. 换简单模型能否明显改善 near-dup 泛化？

**结论：能，且改善巨大；但 test n=16，只能作为“NB 容量不足”的证据，不能直接上线替换。**

| 模型 | Acc | Top-3 | Macro-F1 |
| --- | --- | --- | --- |
| Multinomial NB（现行族） | 0.1875 | 0.25 | — |
| Logistic Regression（binary） | **1.0** | 1.0 | 1.0 |
| Linear SVM（binary） | **1.0** | 1.0 | 1.0 |
| TF-IDF + LR | 0.9375 | 1.0 | 0.852 |

禁止用 random split 高分选模型；上表 **只看 near-dup**。  
下一步若升级正式 classifier，必须：更大诚实 test、校准、Safety 回归、L3 评审。

### 6. 当前证据是否足够把 Uncertainty → Adaptive Inquiry 接入正式产品？

## **RESEARCH_ONLY**

| 允许 | 不允许 |
| --- | --- |
| 继续离线研究、答辩/技术方案引用 | 把 uncertainty/IG 写进生产分诊决策 |
| Trust/研究页展示 assistive 指标（须标注） | 红旗否定解析进 Safety Gate |
| 准备 opt-in 采集 schema 与质检 | 宣称已有多轮患者数据或临床置信度 |

证据摘要：

1. 否定解析与三态表示可复现（10/10 单测）；
2. 诚实泛化仍弱（NB 0.1875；IG 无额外收益）；
3. conformal/温度缩放在漂移协议下仅 **RESEARCH_ONLY**（ECE mean≈0.20±0.04，set size≈19）；
4. 无真实多轮标注对话（仅 `synthetic_example` schema）；
5. 线性模型暗示 NB 可升级，但样本与安全验证不足。

---

## P1：校准 / Conformal 稳健性（seeds = 42/123/2026/3407/7777）

| 协议 | raw ECE | T 后 ECE | Coverage | mean set size | Acc |
| --- | --- | --- | --- | --- | --- |
| random | 0.112 ± 0.008 | 0.031 ± 0.006 | 0.876 ± 0.020 | 0.88 ± 0.02 | 0.984 ± 0.005 |
| fingerprint | 0.113 ± 0.006 | 0.028 ± 0.003 | 0.870 ± 0.020 | 0.87 ± 0.02 | 0.986 ± 0.000 |
| **near-dup 诚实** | 0.217 ± 0.040 | 0.201 ± 0.041 | 0.913 ± 0.094 | **19.1 ± 5.0** | 0.188 ± 0.000 |

结论：**Conformal 不适合作为当前生产拒答开关**；可作研究展示与不确定信号之一。

---

## P1：多轮数据 Schema

- 目录：`evaluation/care_routing/data_schema/`
- `SCHEMA.md`：字段、质量约束、匿名化要求
- `synthetic_example.json`：标注 `source=synthetic_example`
- 校验器：`validate_dataset`（PII 正则、三态冲突、枚举字段）
- **不声称**已拥有真实患者多轮数据

---

## 模块地图（Round2 新增）

| 文件 | 职责 |
| --- | --- |
| `error_analysis.py` | component 清单、confusion、top-k、coverage、根因 |
| `symptom_state.py` | Present/Absent/Unknown + 保守否定解析 + NB absent 似然 |
| `inquiry_protocol.py` | 三态 IG / Random / MostFreq / Margin / FixedOrder |
| `stopping.py` | Fixed-N / Entropy / Set-size / Combined（calibration 阈值） |
| `model_baselines.py` | 纯 Python LR / LinearSVM / TF-IDF 对照 |
| `data_schema/` | 未来采集 schema + synthetic 示例 |
| `run_round2.py` | 一键复现 |

---

## 暂缓（按任务书）

RL 主动问询、Multi-Agent、GNN、大模型微调、LTR、Hybrid Safety 接生产、uncertainty 进生产 Safety——**全部暂缓**。

---

## 下一轮最值得做

1. **扩数据**：为 33 个单 component 疾病收集更多独立表达；目标是诚实 test 覆盖更多病种。  
2. **分类器升级实验（L3）**：在更大诚实集上对比 NB vs LR/小规模 embedding+线性头，连带校准与 Safety 回归。  
3. **opt-in 真实追问日志**：按 schema 采集；在此之前 IG 优势结论保持 simulation-only。
