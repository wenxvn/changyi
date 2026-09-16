# 当前项目状态

更新时间：2026-09-16（算法 Round3：扩大诚实评测 + Triage 分类器升级验证）

## 总体状态

- 状态：**P5 产品打磨完成** + **算法 Round1/2/3 离线实验完成**（`evaluation/care_routing/`，未改正式 API/Safety）
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 产品定位：AI Care Routing；Safety 永远先于个性化
- **Uncertainty → Adaptive Inquiry：`RESEARCH_ONLY`**
- **Triage classifier Shadow Mode：`RESEARCH_ONLY`**

## 算法 Round3（本轮）

详情：`evaluation/care_routing/ROUND3_REPORT.md`
复现：`.venv/bin/python -m evaluation.care_routing.run_round3 --write`

### 关键事实

- expanded_41：**1289** 行（structured 304 + training_long extras，来源可追溯）
- 诚实 quota split（Jaccard 0.8）：test **213 行 / 25 病种**（structured 仅能到 ~8）
- cross-split 泄漏审计：8 对同标签边界近义（Jaccard=0.75），无跨病泄漏
- 5-seed：NB 0.173 / LR 0.265 / SVM 0.267（**Round2 的 1.0 主要是 n=16 偶然**）
- 学习曲线 20%→100% 仍 +9~13pp → **补数据有收益**
- 鲁棒性最稳：LR（mean drop 0.015）
- **Direct Department 0.450 ≫ Disease-first 科室 0.291**
- Shadow Mode：**`RESEARCH_ONLY`**（绝对科室准确率不足）

### 新增模块

`round3_split_audit.py` / `round3_models.py` / `learning_curve.py` / `robustness.py` / `hierarchical_triage.py` / `run_round3.py`

## 算法 Round2（上一轮保留）

详情：`evaluation/care_routing/ROUND2_REPORT.md`
复现：`.venv/bin/python -m evaluation.care_routing.run_round2 --write`

### 六问结论（摘要）

1. **0.188 根因**：表达簇外推（33/41 单 component、test unseen combo=1.0）**+ NB 容量**；同切分 LR/SVM=1.0。
2. **三态表示**：解析层可用，否定单测 **10/10**；absent 用互补似然，Unknown 不写特征。
3. **IG + 阴性回答**：诚实切分上 IG **未**稳定优于 Random（0.1875 vs 0.25）。
4. **停止策略**：Accuracy 全平坦；`combined`/`entropy` 略省问题数；阈值只来自 calibration。
5. **简单模型**：LR/LinearSVM 在 near-dup 上 **1.0** vs NB **0.1875**（test n=16，Round3 已证明不可外推）。
6. **产品接入**：**`RESEARCH_ONLY`**。

### 新增模块

`error_analysis.py` / `symptom_state.py` / `inquiry_protocol.py` / `stopping.py` / `model_baselines.py` / `data_schema/` / `run_round2.py`

### 校准稳健性（5 seeds）

- random/fingerprint：ECE 可降到 ~0.03
- near-dup 诚实：ECE 仍 ~0.20±0.04，set size ~19 → conformal **仅研究可用**

## 算法 Round1（上一轮保留）

### 不确定性感知分诊（P0-1）

- 新增独立实验包：熵 / Top-1 置信度 / margin / Temperature Scaling / Split-Conformal LAC / `should_clarify`。
- 统一 payload：`predicted_department / probability_distribution / confidence / entropy / uncertainty_level / prediction_set / should_clarify`，并强制 `not_medical_confidence` 标注。
- 诚实近重复三分组切分下模型 Accuracy 仅 **0.188**，但 `should_clarify=100%`、平均预测集约 25 类——系统能正确表达不确定。
- 随机切分（有泄漏）ECE 0.103 → 温度校准后 0.034；分布漂移时校准失效，已写入 limitations。

### 信息增益自适应追问（P0-2）

- 候选问题 = 症状词表中未观测症状；IG 用 NB 的 `P(symptom|disease)` 估计 `H(Y|x)-E[H(Y|x,q)]`。
- 离线协议：held-out 标注症状集作 oracle；阴性回答不写入袋状特征（不伪造负特征）。
- 对照：`information_gain` vs `random` vs `most_frequent`，含 adaptive 停止与 forced 5 问。
- 结果：在 random/fingerprint 切分上 IG ΔAcc **+0.11~+0.16**，稳定优于 random/frequent；诚实近重复切分上追问无法挽救弱泛化。

### 五方向可行性结论

| 方向 | 结论 |
| --- | --- |
| P0-1 不确定性分诊 | 可行 |
| P0-2 信息增益追问 | 部分可行（缺阴性特征与真实多轮对话） |
| P1-1 Hybrid Safety Gate | 部分可行（红旗优先级不可动，本轮未改 baseline） |
| P1-2 多目标资源路由 | 部分可行（已有加权打分，缺可核验号源字段） |
| P2 Care Path KG | 部分可行（症状-疾病-科室边可用；资源边稀疏，不建议 GNN） |

复现：`.venv/bin/python -m evaluation.care_routing.run_experiments --write`
详情：`evaluation/care_routing/README.md` 与 `results/care_routing_experiment_report.json`

## P5 产品打磨（上一轮保留）

### Triage 决策工作台（重新设计）

- 结论前置：首屏固定顺序为「安全状态 → 推荐就医方向 → 为什么这样判断 → 下一步」。
- `TriageResults` 拆成结论横幅（`care-result`）与下一步清单（`CareActions`），横幅带状态左侧色条与路径轨（安全门 → 就医方向 → 城市资源）。
- 信息不足状态改为诚实表述：标题仍为「还需要一点信息，才能继续」，科室标为「当前一般性方向」并说明补充后会收窄。
- 右栏 = 当前理解 + 下一步 + 到院位置 + 资源偏好（sticky）；左右栏高度基本对齐，不再出现单侧长期空置。
- 新增 `useRecommendations` hook：唯一持有推荐请求生命周期。请求 identity key 覆盖 condition / 位置 / 偏好 / 收藏 / follow-up 答案，**每个 identity 只发一次请求**（修复了原先依赖数组抖动导致的重复请求），失败后由可见的「重试」显式重发，过期响应按 key 丢弃。
- 普通路径自动加载资源，`查看当前资源路径` 触发按钮始终保留（已加载时跳转完整列表）。

### Emergency（重新设计）


- 急诊结果不再渲染普通推荐，改由 `EmergencyFacilities` 展示公开急诊字段资源（来自只读 `/api/v1/map`）。
- 明确声明「目录记录了急诊科室 ≠ 当前可接诊」，真实急救以 120 调度为准；`拨打 120` 保持最大按钮与首选位置。
- 急诊下隐藏普通「下一步」清单与资源偏好；定位选择保留在地图上方。

### Resources（重新设计）

- 医院/医生卡片改为决策优先结构：身份行 + 公开科室匹配标记 + 地址 + 科室 chip + 主次操作 pill；2 列栅格（≥420px 自动换列）。
- 急诊字段从卡片徽章降级为低对比说明，避免与「公开科室匹配」竞争注意力。
- 资料详情从右侧窄列改为列表下方全宽面板：选中后滚动进入视野、卡片标「查看中」、`Esc` 或关闭按钮收起。

### Map（重新设计）

- 地图优先工作台：地图在左（`min(70vh, 640px)`），同步资源列表在右，提示条在地图下方。
- 距离与资料来源长说明折叠进 `details`，地图不再被推到首屏之外。
- 移动端图例改为底部通栏、与 OSM 归属标注分离，不再互相遮挡。

### 首页与全局

- 症状输入框成为绝对主 CTA：accent 顶边、加强边框与阴影、104px 输入区、44px 主按钮；禁用态保持可读而不是淡出。
- 三条原则改为三卡一行，消除右侧长期空置。
- Trust 证据面板改为可拉伸等高、`--space-5` 内边距；首页可信信息视觉改为 flex 圆圈，修复 `place-items:center` 与绝对定位文字冲突导致文字溢出。
- 路由上下文新增 `insufficient_information` 安全色；`care-path--tone-*` 仍为 dynamic-only。
- 清理 15 个死类（`followup-prompt__actions/progress`、`location-selector__label/note`、`section-heading`、`page-heading`、`speech-input-fallback/listening/message`、`result-loading`、`recommendation-error`、`context-anchor` 等）。

## P4 / P3 保留

- Care Path `idle / analysing / ready` 三态、页面切换 200ms、ProgressiveStatus 步骤对勾全部保留。
- 视觉系统仍为冷灰中性底 `#f3f5f6`、深墨 `#0b1418`、医疗青绿 `#0b6e6a`。
- 不恢复 magazine / Dashboard / Demo Login / Chatbot。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| 测试 | pytest **199**（169 + 11 r1 + 9 r2 + 10 r3）；frontend boundary **17**；Playwright **20/20** |
| Safety | **142** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency FN `0`（三轮算法实验均未改动） |
| 算法实验 | `evaluation/care_routing/results/round3_*`；主报告 `ROUND3_REPORT.md` |
| 诚实评测上限 | structured≈8 病种；expanded test≈**213/25 病种** |
| 产品接入 | Uncertainty→Inquiry = **`RESEARCH_ONLY`**；Triage Shadow Mode = **`RESEARCH_ONLY`** |
| 数据校验 | `validate_datasets` scanned 31 / issues 186（与基线一致，只登记不修复） |
| 前端构建 | CSS 100.9KB gzip 15.3KB；JS 355.7KB gzip 103.6KB（基线 JS 347.2KB，+2.4%） |
| 医生 API | 服务端分页与筛选（P2 保持） |

## 验证记录（算法 Round3）

- `.venv/bin/python -m py_compile evaluation/care_routing/*.py evaluation/care_routing/data_schema/*.py`：通过
- `.venv/bin/python -m pytest tests/test_care_routing_round3.py`：10 passed
- `.venv/bin/python -m pytest`：**199 passed**
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：142 cases；Recall 1.0；FN 0；Over-triage 0（与基线一致）
- `.venv/bin/python -m evaluation.care_routing.run_round3 --write`：split 审计 / 模型矩阵 / 学习曲线 / 鲁棒性 / 层级路由 / 七问答案全部落盘
- 正式 `/api/v1`、Safety Gate、红旗规则、前端 **零改动**

## 未改变的风险

- Safety 固定样例 ≠ 临床覆盖（`R-001`）
- 来源/许可不完整（`R-002`）；照片仍非 `SOURCE_VERIFIED`
- 急诊字段仅为目录标记，不代表实时接诊能力（`R-019` 同源表述）
- 账号/云同步/实时急诊/实时公交仍明确不做
- 原型概率未经临床校准；诚实切分下泛化仍弱，不得当作医学置信度或科室终裁
- 三态追问为 simulation；synthetic schema 不是真实患者数据
- expanded_41 是公开文本集，不是常州真实就诊分布；16 病种仍无法进诚实 test
- Round2 的 LR=1.0 不可外推；Shadow 门槛未达成

## 竞赛提交（2026-09-15 审计，本轮未推进）

对照官方赛道规范，**工程/Safety 基线可演示，但初赛主材料未按规范产出**。完整 P0/P1/P2 见 `docs/competition/2026-ai-medical/SUBMISSION_GAP.md`，执行阶段见 `SUBMISSION_WORKFLOW.md`。初赛截止 2026-10-15 20:00。

## 下一步（算法）

1. 继续扩多 component 可核验症状描述，把 16 个排除病种纳入诚实 test。
2. 以 **Direct Department** 为主模型做更大评测、校准与 Safety 回归。
3. 按 `data_schema/` 准备 opt-in 真实多轮追问采集；IG 结论保持 simulation-only。
4. Hybrid Safety Gate / KG 继续只做研究对照，不接生产。

## 下一步（产品/提交）

- 按 `SUBMISSION_WORKFLOW.md` S0→S9 推进初赛材料；可把 ROUND3 七问与学习曲线写入技术方案
- Trust/研究页若展示不确定性指标，必须标注 assistive_only / not clinical confidence
- 涉及医学或生产能力按 L3/L4 另立计划
