# Care Routing Experiments（离线原型）

本轮按任务书实现 **安全约束不确定性感知分层就医路由** 的 P0 最高优先级两项，并做 P1/P2 可行性判断。
**不修改** 正式 Flask API、Safety Gate、红旗规则、前端，也不把未校准概率包装成医学置信度。

## 目标 / 非目标

- 目标：在仓库既有 304 条症状-疾病样本与多项式 NB 模型上，离线验证不确定性感知分诊与信息增益追问是否真实有效。
- 非目标：上线接口、改 Safety baseline、伪造患者问答、训练 Transformer/RL/GNN、重构前端。

## 模块

| 文件 | 职责 |
| --- | --- |
| `uncertainty.py` | 熵 / 置信度 / margin / Temperature Scaling / Split-Conformal LAC / `should_clarify` |
| `inquiry.py` | 期望信息增益选题；held-out 症状集 oracle 协议 |
| `disease_department.py` | 41 病种 → 科室评估映射（元数据，非正式路由表） |
| `metrics.py` | Accuracy / Macro-F1 / ECE / Coverage / Set Size / Error-vs-Confidence |
| `run_experiments.py` | 一键复现实验，写出 `results/` |

## 复现

```bash
.venv/bin/python -m evaluation.care_routing.run_experiments --write
.venv/bin/python -m pytest tests/test_care_routing_experiments.py -q
```

产物：

- `results/care_routing_experiment_report.json` — 完整指标
- `results/uncertainty_examples.json` — 统一输出 payload 样例
- `results/inquiry_traces.json` — 追问轨迹样例

## 切分协议

1. `random_baseline`：按类随机切分（与历史模型报告同协议；存在近重复泄漏）。
2. `grouped_fingerprint`：症状集合 exact fingerprint 分组。
3. `near_duplicate_same_label`：同标签近重复 component 三分组（train/cal/test），**主诚实协议**。

温度与 conformal 只在 calibration 切片上估计，测试集不参与。

## 五方向可行性

| 方向 | 结论 | 原因 |
| --- | --- | --- |
| P0-1 不确定性感知分诊 | **可行** | NB 可输出全类概率；可做温度缩放、conformal、should_clarify；诚实切分下能正确抬高不确定性 |
| P0-2 信息增益追问 | **部分可行** | 阳性症状可经 EIG 选题并提升准确率/降熵；袋状特征无法可靠更新阴性回答，缺真实多轮标注对话 |
| P1-1 Hybrid Safety Gate | **部分可行** | 可叠加不确定性信号；红旗规则必须保持最高优先级；本轮禁止改 baseline，只做独立对照 |
| P1-2 多目标资源路由 | **部分可行** | 已有加权打分；缺可核验号源/等待时间/真实偏好反馈，不能上 Learning-to-Rank |
| P2 Care Path KG | **部分可行** | 症状-疾病-科室边可用；医院/医生仅目录字段，图稀疏，不建议 GNN |

## 真实结果摘要（seed=42）

### 不确定性（uncertainty）

| 切分 | Accuracy | 科室 Acc | ECE raw→T+conformal | should_clarify 率 | Acc \| 不追问 | 平均预测集大小 |
| --- | --- | --- | --- | --- | --- | --- |
| random | 0.973 | 0.986 | 0.103 → 0.034 | 1.4% | 0.973 | 0.86 |
| fingerprint | 0.986 | 0.986 | 0.103 → 0.031 | 0% | 0.986 | 0.92 |
| near-dup 诚实 | 0.188 | 0.188 | 0.182 → 0.215 | **100%** | N/A | 25.2 |

解读：随机切分指标虚高；诚实切分下模型整体不确定，**系统能正确判断“需要追问/不给死答案”**。ECE 在分布漂移下不会自动变好，说明校准也依赖同分布 calibration。

### 信息增益追问（初始 1 个症状，最多 5 问）

| 切分 | 协议 | IG ΔAcc | Random ΔAcc | MostFreq ΔAcc | IG 平均熵降 |
| --- | --- | --- | --- | --- | --- |
| random | adaptive | **+0.108** | +0.068 | +0.068 | 1.24 |
| random | forced 5q | **+0.162** | +0.095 | +0.122 | 1.53 |
| fingerprint | adaptive | **+0.108** | +0.054 | +0.081 | 1.39 |
| fingerprint | forced 5q | **+0.162** | +0.054 | +0.108 | 1.56 |
| near-dup 诚实 | adaptive/forced | 0.0 | 0.0 | 0.0 | 0.11 |

解读：在模型还有区分能力的切分上，**IG 稳定优于随机/高频追问**；在诚实近重复切分上模型无法泛化，追问也救不回来——这说明下一步优先补数据与负特征表示，而不是继续堆策略。

## 安全边界

- 实验包不 import `evaluate_safety_gate` 作为决策路径，不改红旗关键词。
- 所有 payload 带 `assistive_only` / `not_medical_confidence` / disclaimer。
- Safety Evaluation baseline 必须与改动前一致。

## 缺什么数据（下一轮）

1. 同分布、多 component 的真实症状描述（避免 33/41 病只有一个近重复簇）。
2. 显式阴性症状特征（“没有胸痛”），才能正确更新后验。
3. 真实多轮追问日志（问题-回答-最终科室），替代 oracle 模拟。
4. 可核验的号源/距离/等级字段，才谈得上真正的多目标资源路由评测。

## Round2（第二阶段）

详见 **`ROUND2_REPORT.md`**。

新增模块：

- `error_analysis.py` — near-dup 0.188 根因
- `symptom_state.py` — Present/Absent/Unknown + 保守否定解析
- `inquiry_protocol.py` — 三态追问 simulation
- `stopping.py` — 停止策略
- `model_baselines.py` — 纯 Python LR/SVM/TF-IDF 对照
- `data_schema/` — 未来多轮数据 schema（仅 synthetic 示例）
- `run_round2.py` — 一键复现

```bash
.venv/bin/python -m evaluation.care_routing.run_round2 --write
.venv/bin/python -m pytest tests/test_care_routing_round2.py -q
```

**产品接入结论：`RESEARCH_ONLY`**（见 ROUND2_REPORT.md 第 6 问）。
