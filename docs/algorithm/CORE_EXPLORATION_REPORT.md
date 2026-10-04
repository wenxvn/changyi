# 常医核心算法探索报告

> 冻结研究批次记录：下文“正式运行时未改/批次完成暂停”只指2026-10-02研究批次，不代表当前网站。用户已恢复持续维护，当前15分钟任务ACTIVE；后续网站输入/Safety证据/追问流程已有版本变更，研究数值与失败原样保留。网站验收及真实未闭P0/P1/P2见`docs/status/WEBSITE_ACCEPTANCE.md`，不得把英文内部研究结果当中文临床效度。

日期：2026-10-02。用户授权自主技术探索，以核心算法为最高P0。原始源码基点 `e82447c`；本轮变更在本地，未推送远端。结果索引：`evaluation/core_exploration/results/summary.json`。

## 结论

已经修复预测器身份、证据口径、追问概率和研究层中文解析的实质错误，并完成有限登记方案的全部对照。标准优化器、特征尺度与训练内选择确实改善当前公开混合文本上的科室分类：五seed主流程 **Acc 94.25%±2.00pp，Macro-F1 94.65%，ECE 0.0321**。

这些指标是内部公开文本研究结果。覆盖全部304条结构化症状样本的分组交叉验证只有 **53.29%–61.51%**；结构化症状→另一来源文本的平均准确率 **56.11%**。当前最重要的剩余P0是**中文主诉输入域、标签一致性、完整科室覆盖与独立评测数据**。新学习模型保持 `RESEARCH_ONLY`，不以内部94%直接替换正式中文规则分诊。

## 1. 已修复的问题

| 问题 | 根因与实际修复 | 验证 |
|---|---|---|
| cal/test/clean/perturbed混不同预测器 | 矩阵char用35/.35，校准与扰动又用70/.4重训。现在保存拟合状态、训练特征定义、模型身份与温度，所有路径复用同一对象 | 先重现失败回归，修后通过；identity差值0；full coverage等于同模型准确率 |
| 历史headline不可复现 | 直接执行Git原版函数，seed42=.624413、T=.7；旧文件=.737089、T=.5。修正五seed旧实现为.608179 | 原版实跑证据 `original-live-seed42.json` 与旧结果快照同时保留；没有把降幅归因本轮修复 |
| 矩阵std字段错误 | `run_matrix.std`曾写整句文本 | 改为实际aggregate numeric std和实际seeds；回归验证类型 |
| Safety研究门禁只比较默认常量 | 142/1.0/0等默认数字无法发现真实回归 | 门禁实际执行142例评估；注入漏判的反例必须失败；Safety/API规则未改 |
| 追问把token概率当yes/no概率 | 多项式分母是token总数，不能表示患者/样本中“有此症状”的概率 | 研究追问用每类记录频率 `n_class+2α`；IG从同一个posterior做Bayes更新；toy的yes概率从错误.3143修为正确.5 |
| 中文研究解析误断 | 会不会/双否定/已缓解历史误记阳性；长短别名重叠能把否定喷嚏反转为阳性 | 保留未知与澄清；最长span只处理一次；无严重度的“发热”只给coarse fever；720组合性质测试先失败12，修后720/720 |
| 不同症状被当“同义、意义不变” | 高热≠低热、头痛≠头晕，随机删症状也不能保证非关键 | 改为输入压力实验；identity/顺序/重复与意义可能变化的扰动分开，不再宣称医学标签保持 |
| 模型跨进程持久化 | `python -m`把回调保存为`__main__` | 本地已知回调加载器+可移植导出；5模型跨模块重载后的预测精确一致 |

研究预测器还对Emergency、信息不足、未知安全状态、未验证临床中文输入域及空特征拒答；症状码推理按训练CSV相同的sorted-set契约规范化。正式运行时未导入此研究预测器。

## 2. 实际尝试量与口径

| 方向 | 已完成量 |
|---|---:|
| 表示：binary/word/concat-char/canonical-char/segmented-char/3种融合比例；模型LR/LinearSVC/ComplementNB/MultinomialNB/ExtraTrees；正则与类权重 | 8表示×5seed×22内层候选 = **880次候选拟合**；40冻结外层模型 |
| 校准、拒答与conformal | raw/temperature/OvR sigmoid/条件partial isotonic/矩阵logit校准；每个outer模型保存3种拒答信号与覆盖曲线、各科室覆盖 |
| 全局症状组阈值敏感性 | 4阈值×5seed = 20任务 |
| 来源迁移 | 2方向×5seed = 10任务（反向5次因训练缺科室unsupported，保留原因） |
| 诊断名遮蔽与文本模板隔离 | 5遮蔽干预；3字符cos阈值×5seed=15隔离任务 |
| 症状词典归一 | 15模型任务，**330次内层候选拟合** |
| 追问 | 两种预测粒度/两种概率/三策略/三预算/三回答条件×5seed = **540设置** |
| 纯症状全覆盖验证 | 3表示×5fold=15拟合，每种表示覆盖所有304行一次 |
| 负对照 | 5次训练标签打乱 |
| 学习曲线 | 5训练量×5seed=25点 |
| 集成 | 每seed全8平均/top3平均/cal-NLL权重，合计15设置 |
| 输入边界 | 720词典组合、12中文Safety工程例、核心回归与5模型精确重载 |

不是1210次统计独立试验：候选共用内层验证，多个seed也复用此公开数据。所有“mean±std”是seed间描述统计；row bootstrap不解决模板依赖。没有因一个好指标提前停，也没有用test挑模型/温度/阈值。

## 3. 主模型与基线

主流程按train内部近重复分组验证的Macro-F1/Accuracy选择表示与参数，再拟合outer train。cal又分为校准拟合与拒答阈值两部分；temperature是预设主校准，不按test挑最漂亮的方法。

| 项目 | 五seed结果 | 数据/限制 |
|---|---:|---|
| 修正的手写Round4 char模型 | Acc **60.82%** | 当前源码实跑；与原版seed42控制一致 |
| 标准模型嵌套选择主流程 | Acc **94.25%±2.00pp** | 1289行公开混合文本；test约213–241行/seed，排除低component疾病仍在 |
| 主流程Macro-F1 | **94.65%** | 同上，不是中文患者科室准确率 |
| 温度校准ECE | **0.0321±0.0101** | cal拟合，不是临床概率校准 |
| NLL/Brier | **0.1822 / 0.0886** | 分类区分与概率评分合看，不能仅凭ECE判定接入 |
| label-masked文本cos隔离(.7/.8/.9) | **92.98% / 92.51% / 92.27%** | 切分与test覆盖改变，只是敏感性证据，不能与原split作等价提升比较 |
| 结构化→扩展来源 | **56.11%** | 五seed，每个test489行；来源迁移暴露分布差异 |
| 全304行症状-only grouped CV | binary **61.51%**；word **60.86%**；segmented-char **53.29%** | 包含23个训练中无对应科室的样本为错误，没从分母移走 |
| 打乱train标签负对照 | **15.62%** | 高分不是实现直接读取测试标签的结果，但仍不构成临床真实性证明 |

旧0.742438与新0.9425不能简单相减当正式提升：旧0.7424无法从该源码重现。本次同数据/outer协议的可复现旧基线是0.608179。

## 4. 数据与任务的关键发现

expanded_41把两种输入混在一起：304条标准症状集合，985条扩展文本字段。其中723条扩展样本有超过80字符的“症状码”，实际上是较长主诉或疾病介绍；33条命中精确疾病名，32条直接命中自身标签。原始数据保持原样，实验转换有单独记录。

诊断名遮蔽没有实质改变seed42结果（仍.957746），所以**不能认定名称泄漏是高分的主要原因**。但混合文本分类、症状集合分类和中文首诊分诊是不同的任务。旧按整个字段做Jaccard的近重复定义未覆盖全部文本改写，本轮补充label-blind字符cos分组检验。

症状词典归一保留911/1289行，378条扩展文本无可识别概念。存在22个跨科室相同症状fingerprint；按当前标签在该表示上的多数投票上界约86.39%（这是此数据/表示的上界，不是医学上界）。归一后binary/word/segmented-char分别约 **67.03%/66.82%/69.84%**。不能通过删除难例或随意修标签把结果包装成更好。

小quota切分的8/8=100%与全304行CV约61%并不矛盾：前者只覆盖很少可拆component的样本。这正是必须避免的“小测试集满分”叙事。

## 5. 选择性拒答与校准

cal/test现在有可验证预测器身份。修正旧模型seed42全覆盖Acc=.624413；目标80%覆盖，实际coverage=.760563、retained Acc=.740741，替代原先模型版本不一致的.657/.807组合。

新流程保存max-prob、margin、负熵的cal-only阈值与每科室coverage；conformal是cal_threshold上的有限样本阈值，交换性未获临床验证。完整曲线在每个`study-v2/*-representation.json`。

集成对照：top3（内层选择）均匀平均Acc **94.63%、ECE .0329**，比单模型94.25%多约0.38pp；没有足够依据宣称显著优势。全8模型均匀平均Acc94.28%，ECE却恶化到 **.1541**，否定了“多加模型一定更好”。cal-NLL权重平均Acc94.08%、ECE.0283，有小幅概率评分收益及少量分类损失。

学习曲线20/40/60/80/100%训练组，Acc约82.58/89.86/91.60/94.45/94.35%。80→100没有稳定上升；不应沿用旧“仍明显上升”的叙事。100%学习曲线重组了训练行顺序，与主任务训练顺序不同；随机优化器/树及重拟合的结果不是主模型的精确重载，0.09pp差异不作为新提升。精确重载另有5个model replay通过。

部分非主校准器出现收敛警告，原始日志保留，不将未收敛的复杂校准器作为最佳主结论。主temperature只拟合单个正标量，保持argmax不变。

## 6. 追问结果

540设置包括closed-world oracle、10%回答翻转、30% unknown，预算1/3/5。样本中未写出的症状只在此模拟中当作阴性，不能推广到真实问诊；真实患者中“未提到”是unknown。

下表为五seed、3问、无回答噪声的直接科室预测：

| 概率/策略 | 起始Acc | 3问后Acc |
|---|---:|---:|
| 旧token likelihood + IG | 23.16% | 24.30% |
| 修正record likelihood + IG | 24.88% | **34.35%** |
| 修正record likelihood + Random | 24.88% | 26.26% |
| 修正record likelihood + Frequency | 24.88% | **33.91%** |

记录频率修正确实重要；但IG只比高频策略高约0.43pp，不能宣称已经证明临床自适应追问优越。Disease-first下IG也未稳定优于Frequency。结论是先保证概率语义与数据，再考虑更复杂问答策略。

## 7. 中文与接入判断

研究解析新增否定、未知、双否定、历史、他人语境、矛盾与无严重度发热的保守处理；720性质挑战与12个中文Safety工程例通过。它们不是医生标注的中文科室评测集，也没有将真实对话伪造成合成数据。

本轮核查了中文候选数据：[LCMDC](https://zenodo.org/records/13771008)与[Huatuo26M-Lite](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite)，许可/字段/任务定义见`CHINESE_DATA_CANDIDATES.md`。尚未将外部真实咨询记录导入。当前公开中文QA类别、已诊断后的咨询科室与初诊主诉正确科室不能等同；需在当前数据边界内明确脱敏与可用范围、独立标注/映射、已知诊断和急症样本的处理。

正式Safety规则、生产API、病人可见默认科室路由和旧NB权重未改。研究代码有安全短路与输入域门禁，可以复现研究推理；**正式中文接入条件仍未满足**。这是技术判断，不是等待用户批准已证实可用的方案。

## 8. 当前核心P0/P1

| 级别 | 项目 | 本轮状态 |
|---|---|---|
| P0 | 预测器/校准/实验证据一致性 | 已修复并重跑，旧失败/旧产物保留 |
| P0 | 输入数据语义、中文主诉与标签口径一致 | 已定位，并做转换/来源/CV对照；独立中文数据验收仍欠缺 |
| P0 | 测试覆盖全部科室、未知输入和来源迁移 | 已补研究对照与守恒检查；不足数据/未见科室不能靠缩小测试集解决 |
| P1 | 可在真实多轮中更新的问答概率与停止策略 | 概率错误修复；模拟结果已全量保存；真实多轮证据仍欠缺 |
| P1 | 复杂融合/集成是否值得 | 集成小增益、全8平均校准明显恶化，保留阴性结果，不继续堆模型 |

下一轮核心工作应以中文输入数据契约和独立测试集为主：先固定coarse/fine科室、多可接受科室与安全退出；分开初诊主诉/已知诊断咨询/治疗问题；保留完整覆盖与不确定性的评价。现有CPU稀疏模型已足以做可信强baseline，再决定是否值得上中文编码器或其他重模型。

## 9. 验证与复现

- 最终本机pytest：**239 passed**，增加24个核心回归；研究依赖另立冻结requirements与CI边界任务。远端新CI尚未执行。
- Safety：**142固定样例，Recall1.0、Under/Over0、Emergency FN0**；真实执行记录`results/final-safety.json`。不代表临床覆盖。
- 前端17 tests、typecheck、build通过；新构建写临时目录，tracked dist未改。26浏览器用例来自接手时的临时Windows配置基线，本轮没有新UI改动。
- 核心模块py_compile通过；git diff --check通过；实验CPU进程已退出。没有占GPU或操作其他项目进程。
- 旧证据位于`evaluation/core_exploration/legacy_evidence/`；输出是完整结束的任务或明确unsupported，无中断数据当最终。

PowerShell复现：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt -r requirements-research.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m evaluation.safety.evaluate_safety
.\.venv\Scripts\python.exe -m evaluation.core_exploration.study
.\.venv\Scripts\python.exe -m evaluation.core_exploration.generalization
.\.venv\Scripts\python.exe -m evaluation.core_exploration.data_audit
.\.venv\Scripts\python.exe -m evaluation.core_exploration.inquiry_study
.\.venv\Scripts\python.exe -m evaluation.core_exploration.bridge_study
.\.venv\Scripts\python.exe -m evaluation.core_exploration.validation
.\.venv\Scripts\python.exe -m evaluation.core_exploration.ensemble_learning
```

同一协议的已完成job跳过；主矩阵若源码/配置身份不同，会拒绝复用。要改研究协议，应使用新的版本输出目录；不要删除旧证据强行续写。joblib模型只加载本地本研究生成的产物。所有源文件与关键产物的最终身份登记在`results/final-manifest.json`。

方法依据：[Guo等，ICML2017](https://proceedings.mlr.press/v70/guo17a.html)、[scikit-learn calibration文档](https://scikit-learn.org/stable/modules/calibration.html)。文献中的校准方法不是本项目临床有效性的证明。

## 10. 工作流完成

本轮全部已登记算法尝试、有限扩展对照及必要核验完成。半小时续执行heartbeat在最终归档后暂停，避免重复训练。目标是完成研究与报告；没有承诺已经获得临床验证，也未推送或部署。
