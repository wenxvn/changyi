# 中文语料适用度核查（2026-10-02）

## 继续轮8当前结论（2026-10-04）

CMExam已做预登记适用性抽检：完整6811中临床形态启发式1377，固定8类每类Question SHA最小2题共16条，没有模型预测或拟合。16条都不是直接初诊方向标签，且2条只是含患者词的知识题误被启发式纳入；已有确诊、治疗、检查、手术等场景常见。原论文A.2 Figure5明确科室是题目相关类别，例子同时输入选项。全源定义及抽检支持拒绝直接用该考试科室标签训练/验证初诊校准；不把16条抽检推广为1377全部逐条医学审核。证据cmexam-task-fit-preflight-v1.json、cmexam-task-fit-review-v1.json，原题/选项/答案/解释未持久化，当前runtime身份与v7.5 proof完全一致。

MedJourney使用依据重新分层：原论文checklist5 P22明确为复现实验提供开放数据/代码、数据上传GitHub；A.2.1 P14说明DR三医生构造/补标/审核，非患者记录。之前将没有LICENSE一概作为连本地阅读分析也不能继续的条件过度。现在依据该公开复现目的及用户授权，仅开展本地只读结构/映射与不拟合基准分析；许可证仍记unspecified，不推导训练、再分发许可，不持久化原病例/答案、不发送邮件。此为本次技术分析边界，不是对未知许可证作法律认证。

固定60f6f3012c30fd72c6917e2fdce9b37821faa546，dr.json实际NDJSON500行（第一次单JSON读取Extra data在预测前失败，未写原数据/运行模型）。SHA 7ea640389edea6cac2f34b3a3801bc1e26d111f50f758e1229cb78bfde38dace，字段prompt/target/keyentity，source大小150335。完整500均同一角色/输出指令前缀；131含&&后缀，后缀具体语义未在论文解释，已见病名示例；不能未经核对把这些注释当普通主诉。target有232组合、111目标名称并集，不等论文100主类别；complaint-only有499不同文本/1重复，不能宣称500完全独立。keyentity非空240。只存哈希/结构/科室名称计数，没有输入原文/答案/后缀，预测0/拟合0，见medjourney-dr-structure-review-v1.json与medjourney-dr-input-label-preflight-v1.json。

下一先冻结保守科室别名及不可映射项、输入视图（源body保后缀与主诉-only分开）、无&&子集适用性；所有500保原分母，未知、拒答、API错误/目录不命中不删。不能把去后缀视图沿用标签当已重新经医师审核。原型独立科室证据仍未取得成绩，校准/拒答目标未闭，当前不启动训练。

## 2026-10-04继续轮6：CMExam作者源新增核查

[作者仓库](https://github.com/williamliujl/CMExam)、[原论文](https://proceedings.neurips.cc/paper_files/paper/2023/file/a48ad12d588c597f4725a8b84af647b5-Paper-Datasets_and_Benchmarks.pdf)。固定commit fadb22c89beb1b7115dc36460ba792eb96b7b972，仓库LICENSE Apache-2.0。原data/test_with_annotations.csv元数据实际6811行，Clinical Department有36个值，其中未定义1846，非未定义4965；同时有Question/Options/Answer/Explanation等。原文件与许可证SHA及完整类计数见results/cmexam-metadata-audit-v1.json，未持久化题干/答案/解释，没有预测或训练。

论文明确是国家医师考试题、GPT初标后两名医学专业人员审核五维问题标签；Clinical Department按医疗机构诊疗科目目录标注考试问题相关科室。该标签不是初诊主诉的适当就医科室，通用内科1200/外科473等也不等网站细分科室。不用考试题/答案直接训练后声称中文初诊校准达标，不丢未定义分母。是否可用临床情境子集作辅助域验证须先核题干类型、无答案泄漏、科室适用性和预登记病例组；完整目标仍缺匹配域证据，不用较容易的问答主题分类替代。

2026-10-04继续轮2新增合规风险候选：[Ramaswamy作者数据](https://github.com/ashwinra-code/gpt-health-eval)，data/LICENSE为CC0-1.0，全部医师编写虚构情境、无真实患者记录。选原CSV全27实际F参考条件；首评前冻结agent中文译写，英文医生标签不等原生中文临床金标准，也无科室标签。初始12/27等级代理相容、严格D2/2未ER，原失败保存；详见PUBLIC_VIGNETTE_REVIEW.md。可以用于外部来源风险工程评测，不解决中文科室训练/校准的数据缺口。

本轮只核查作者发布的元数据、许可及任务定义，未导入外部患者文本或咨询记录。

| 候选 | 已核验信息 | 核心算法适用度 |
|---|---|---|
| [LCMDC 作者仓库](https://github.com/anord-wang/Chinese-Medical-Dialogue-System)、[Zenodo](https://zenodo.org/records/13771008) | 作者提供分级分诊任务，说明 raw 文件包含患者提问、医生回答和基本信息；[Zenodo API](https://zenodo.org/api/records/13771008) 返回 cc-by-4.0、open | 比现有英文症状码更接近中文任务；原始咨询记录不能直接纳入当前项目。后续必须明确去标识处理、是否允许此类记录、初诊主诉与诊后咨询区分，以及粗/细科室到常州目录的映射 |
| [Huatuo26M-Lite 数据卡](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite)、[作者仓库](https://github.com/FreedomIntelligence/Huatuo-26M) | Apache-2.0；数据卡显示约178k行、16个label值，字段有question/answer/related_diseases；作者说明Lite经过清理和改写并包含科室字段 | 可作为中文分类研究候选。推断：问答类别/咨询科室不等于经过独立审核的初诊就医科室；诊断已知、治疗咨询、急症初诊需要分层，answer与related_diseases不能当模型输入或混进测试标签生成 |

采用前的技术方案：只评估必要的脱敏主诉与科室字段；处理与识别记录进入独立隔离流程；拒绝身份、联系信息、真实病历与不明使用依据的数据进入此仓库；不训练诊疗回答生成器。冻结按来源/文本近重复组/时间划分的独立测试集；先跑中文char-TFIDF/词级稀疏模型，规模与证据足够后再谈中文编码器。

这是数据候选与接入协议，**没有对应训练结果**。已有模型94%左右的英文混合文本内部结果，不能借中文数据卡来宣称完成中文验证。

## 2026-10-04 核心算法继续完成：实时元数据复核

用户确认没有现成医学审核标签，授权先核查公开候选。只读取作者论文、数据卡、仓库树与加载schema；没有下载原始问答/病历或开始新训练。

| 候选 | 本轮核验 | 当前采用判断 |
|---|---|---|
| [MedJourney作者仓库](https://github.com/Medical-AI-Learning/MedJourney)、[论文](https://papers.nips.cc/paper_files/paper/2024/file/9f80af32390984cb709cdeb014d0df41-Paper-Datasets_and_Benchmarks_Track.pdf) | DR为500条、100细科室；A.2.1说明医生撰写、第二位医生补科室、meta-annotator复核。仓库有data/basic/dr.json（150335 bytes）；README和完整tree未列许可证，论文checklist未明确给该新数据集许可 | 任务和隐私边界最匹配；须先取得本次研究/参赛使用依据，再冻结500条外部评测、审核目录映射。无风险等级标签，不可验证急症召回；不能训练后仍称独立测试 |
| [Huatuo26M-Lite数据卡](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite/raw/main/README.md)、[loader](https://huggingface.co/datasets/FreedomIntelligence/Huatuo26M-Lite/raw/main/my_dataset.py) | Apache-2.0，约178k；commit 90ce61699e90568db82cdce4c4035c6918d70aa6。loader实际id/question/answer/score/label且仅TRAIN；旧笔记related_diseases不是当前loader字段。互联网高频问答、答案经ChatGPT改写 | 可研究一般中文问答分类；不能直接认证初诊科室/风险标签。须排除诊后/治疗问题、审核隐私与标签、按来源/近重复建立全新train/cal/test。answer/score不得作输入或临床金标准 |
| [LCMDC论文](https://arxiv.org/html/2410.03521v1)、[Zenodo元数据](https://zenodo.org/api/records/13771008) | API许可cc-by-4.0、zip 342089312 bytes；伦理段声明匿名患者医生对话及公开知情来源。作者仓库同时含raw基本信息，triage标签来自咨询科室 | 作者声明不等项目逐条审查，不引入raw记录。若后续授权最小匿名主诉，仍须隔离审查、初诊/诊后分层和标签核验；咨询科室不等急症标签 |

独立验证入口：`python -m evaluation.core_exploration.independent_validation --dataset <已审查JSON>`。
schema为independent-core-validation/v1，顶层provenance/cases；provenance记录source_url/license/origin/label_origin/privacy_review/patient_records/development_exposure，case仅case_id/condition/acceptable_departments/risk_status。允许匿名专家情境或公开一般问题，拒绝病历与answer字段；格式见模块及测试。输出仅匿名case_id和结果，不另存主诉。目录映射须在评测前审核，不根据test表现更换。

保留所有API错误、拒答与未命中分母，分别给全分母准确率/覆盖/保留准确率/风险准确率/急症失配数量。没有风险标签就不造Safety指标。元数据只是提供方声明，不自动证明许可、隐私、独立性或临床效度，clinical_validation始终false。当前缺有效输入集，所以没有独立成绩，不以合成fixture替代。

补充排查：[RD-Triage](https://github.com/zhelishisongjie/RD-Triage)为MIT、629条罕见病首诊科室任务，但含publication clinical summary/Report及HPO衍生病例，与本项目普通中文主诉域不同；不得导入病历或据其成绩认证一般分诊。[TriageBench](https://huggingface.co/datasets/wongqihan/triagebench)为MIT（commit 35fecabb3683fcafdca626c4d466098e8e4101bb），单一神经症状情境的性别/语言/社会属性一致性，不提供临床正确金标准。[medical-triage-500](https://huggingface.co/datasets/syntech-ai/medical-triage-500)为CC-BY-NC-4.0、英文规则生成合成数据，没有当前中文初诊独立专家标签。以上均仅核查作者声明，不导入原文，不用作临床验证替代。
