# 核心算法自主探索（2026-10-02）

## 授权与目标
用户明确要求核心算法为最高 P0，自主深入探索、重要技术决策不需确认；每半小时承接至所有登记尝试结束。允许研究代码、模型训练、实验与必要修复；不代表授权远端推送、生产部署或引入真实患者记录。

目标：恢复可信评测，探索科室路由表示/分类/校准/拒答/泛化/追问，保留阴性结果，形成可复現研究结论和明确接入判断。Safety 规则与正式接口保持安全优先；上线候选仍需有与中文产品输入匹配的验证。

术语：模型身份=相同拟合权重/特征转换/温度；主评测=grouped quota 外层切分；模型选择=外层 train 内部近重复分组验证；cal=只拟合校准与拒答阈值；test=只评估冻结方案。既有 test 已用于历史研究，新的结果称内部研究复评，不能冒充从未使用的外部测试。

## 根因假设与可证伪预测
1. cal/test 重新拟合参数不同 → 同一拟合实例输出 cal/test 后，full coverage 必须等于该实例准确率；未扰动样例必须等于 clean。
2. 结果文件漂移 → 当前代码重跑 seed42 后，两份 accuracy/temperature 统一；旧数据独立保留为历史证据。
3. 英文症状码拼接包含顺序和跨症状子串捷径 → shuffle/canonical/segmented 对照能测量真实影响，bag 表示必须顺序不变。
4. 手写 OvR/特征尺度及不均衡限制性能 → 同 split 的标准优化器、归一化、类权重、融合与正则对照可验证，选择只用内部 validation。
5. 追问 likelihood 使用 token 总数代替记录频率 → 明确 Bernoulli yes/no 概率后比较 IG/random/frequency；缺失症状不是临床阴性，oracle 仅模拟。

## 登记阶段与完成定义
1. 修复预测器身份、鲁棒性语义、矩阵 schema；先写真实失败回归，再修复并跑回归。
2. 重跑修正的 Round4 全五 seeds 与衍生 selective/robustness，保存旧证据快照和新身份元数据。
3. 表示与模型矩阵：binary、word-TFIDF、legacy-concat-char、canonical-char、segmented-char、normalized word/char fusion；LR 正则网格、balanced/unweighted、LinearSVC、ComplementNB/MultinomialNB，选择只在 train 内层 grouped validation；固定 5 外层 seeds。
4. 校准与拒答：raw/temperature/sigmoid（样本足够才 isotonic），只用 cal；max-prob/margin/entropy/conformal 候选，给 NLL/Brier/ECE、risk–coverage、per-dept coverage、置信区间和阈值迁移误差。
5. 泛化与表示压力：global near-duplicate 敏感性、跨数据源、shuffle/去重/未知/OOD/删症状/加症状；改症状是输入压力，不声明医学语义不变。
6. 追问：审计 Bernoulli 似然、比较修复 IG/random/frequency，明确 oracle 的缺失≠临床阴性；报告增益和问答成本，不伪造真实对话。
7. 中文输入与 Safety 边界：审计当前中文→症状码桥接，构造明确标注的工程输入挑战集，分析冲突/否定/OOD及研究模型失效；不把合成挑战集包装为临床数据。
8. 冻结与审阅：基于完整候选矩阵汇总阴性/阳性、可复现命令、模型与数据身份、测试、性能和接入结论；更新当前状态与本地研究报告，完成后暂停 heartbeat。

## 执行与恢复
- 进度：`docs/algorithm/task_plan.md`、`findings.md`、`progress.md`。
- 新探索：`evaluation/core_exploration/`；每个 job 独立 JSON，原子写入状态，有已完成 job 则校验配置身份后跳过。
- 历史与修正 Round4：分别保存；禁止静默将中断结果标成最终，禁止反复根据 test 改候选。
- 使用本地 CPU，科学计算线程限制为 2；不占 GPU，不操作其他项目进程。
- 每个阶段可独立恢复；失败进入结果登记和诊断。遇到新且重要假设，先在 findings 登记理由再增加有限对照。
- 回滚：新实验包独立；旧实现/产物有快照；正式 Safety/API 不改。未经授权不 git push。
- 停止条件：上述阶段所有已登记 job 完成/明确失败且原因已解释，核验通过并生成最终报告；不能因单个好指标提前结束，也不无限追加无关模型。

## 文献依据
- Guo et al., ICML 2017, On Calibration of Modern Neural Networks：https://proceedings.mlr.press/v70/guo17a.html
- scikit-learn probability calibration：https://scikit-learn.org/stable/modules/calibration.html

## 定时任务
半小时 heartbeat：`automation`（创建响应 ID；续执行时核对本地 automation.toml 的真实配置）。首个创建请求因缺 destination=thread 失败，补齐后创建成功。
