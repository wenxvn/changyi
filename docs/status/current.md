# 当前项目状态

2026-10-10核心算法收敛L2：前端只读展示已接通，后端医学规则未改。`triage.symptom_tags`对象解析（兼容旧字符串），`htriage_analysis.department_candidates[].source`只读显示，`population_context/score0`仅人群入口。`CurrentUnderstanding`新增症状证据卡，`TriageResults`新增科室依据卡，均不触发推荐、不标临床概率。验证：前端typecheck/17test/build过，Safety142 recall1/under0/over0/FN0不变，diff-check过。研究侧冻结：已曝光500不再调参，BGE/重排/增强负结果保留，独立验证入口`independent_validation`待新匹配数据。PPT/视频/报告仍最后再写。

2026-10-10核心算法收敛L2（续）：回归加固完成。新增`frontend/test/triage-evidence.test.mjs`2用例，前端19/19过；typecheck/build过。Flask test client：health/ready 200，普通咳嗽triage 200 ROUTINE且`symptom_tags`为对象数组，空/缺字段400，医院404，非API路由200系SPA fallback。数据校验31/186基线不变。`ui-registry.md`已登记两只读卡。全量pytest后台运行中，待回执再冻数。

2026-10-10核心算法收敛L2（续2）：类型统一+三路径实测。`FollowupResponse.htriage_analysis`统一为`HtriageAnalysis`；`TriageResults`无`composite_score/match_score`复核通过。实测：普通咳嗽ROUTINE+3对象症状词+2科室候选+校准false展示证据卡；纯人口INFO+0候选只追问；急症EMERGENCY+4症状词+0候选+追问defer，120优先不变。前端19/19、typecheck/build、diff-check过。

2026-10-10核心算法收敛L2（续3）：全量pytest 1042/1042通过（409.49s），与v7.7基线一致，数字冻结。前端19/19、Safety142、数据31/186均已对齐。

2026-10-10核心算法收敛L2（续4）：追问往返只读差异已接通，后端零改动。`TriagePage`快照上一轮证据，`CurrentUnderstanding`标症状新增、`TriageResults`标科室新增/方向更新，首轮不标注。验证：前端20/20、typecheck/build过；Safety142不变；相关pytest 304通过（35.82s）。

2026-10-10追问槽位联动+全量E2E回执：`FollowupPrompt`展示`missing_slots[0]`为本题补充目标；前端21/21、build过。全量E2E 94通过/2失败，失败为同一用例（product-smoke首页-资源-地图-可信链在/trust页等待标题超时），与本轮改动文件无关（未碰TrustPage/首页/地图/资源页），待隔离重跑判定是否为并行负载下偶发。

2026-10-10 E2E根因与修复（后端性能，医学零改动）：`api_v1_evidence`每次请求同步重跑142例评估，冷进程首请求约13s超过前端10s超时，Trust页直接进错误态；另本机`data_validation`输出曾以Windows反斜杠路径污染已跟踪报告致`training_data_source=null`（已还原）。修复：`EvidenceApplicationService`加进程内缓存（版本+源文件指纹为key，数字不变）+`app.py`启动时`prewarm_evidence()`预热；新增缓存回归测试。验证：evidence首请求2.63s→缓存命中0.00s且载荷一致；product-smoke 8/8通过（含Trust链4.5s/4.4s）；Safety142（1.0/0/0/0）不变；data_validation/已干净。 regression测试文件`tests/test_read_only_application_services.py` 7通过。

2026-10-10本轮冻结：全量E2E 96/96通过（51.6s，含四视口与三条核心演示路径）；pytest 1042/1042；前端21/21；Safety142 recall1.0/under0/over0/FN0；数据31/186。医学规则、权重、正式数据零改动。

2026-10-10收尾补齐：e2e:hooks 4/4通过（曾被10-06残留node占用5174阻塞，已确认 stale 后清理）；后端evidence缓存+预热改动后全量pytest后台重跑完成：**1043/1043通过（396.48s）**，比v7.7基线多1（新增缓存回归测试），最终数冻结。

2026-10-10 P0/P1/P2收口（报告/PPT/视频除外）：SCORECARD/MODEL_CARD对齐冻结数（142例、1043/21/96、random 74行0.973 + strict 24行0.208）；新增PINNED_VERSIONS（Python3.11.9/Flask3.1.3/Node24.12等）、ASSET_EXCLUSION（275照片无许可+目录provisional+186异常+构建产物排除）、DEMAND_RESEARCH_PLAN（待执行，零虚构数据）；run_matrix的std数值化与预测器身份门禁经核查已有回归覆盖（test_core_predictor_identity 10/10），未改代码；真实截图目检首页/分诊页无可举证视觉缺陷，“可门诊”实为“可及门诊”误读。仍开且需外部输入：独立中文标签/校准（缺新数据）、照片许可（需真实依据）、需求调研执行。前端21/21复核通过。

2026-10-11 前端科技感升级（CSS-only，零文案/逻辑改动）：mesh aurora + 蓝图网格全站环境层、hero 渐变墨字、主按钮流光、hero 视觉卡细指针 3D 微倾、在线圆点呼吸、分组卡片 stagger 入场、证据数字等宽。token 已文档化，reduced-motion 全兜底。验证：typecheck/前端21/build过，product-smoke 4/4截图目检通过，全量E2E 96/96（57.6s）。

2026-10-06：核心v7.7已分离人口词与症状/疾病证据，非医学人群入口source=population_context/score0；保纯人口INFO、真实证据与ER优先。修前7失败/2过，修后定向20、全1042pytest205.78s、96browser1.7min、Safety142过。只修网页伪元素拦截提交，保已有CSS视觉修改；前96当前UI复验也终态通过。权重/正式数据未改，检索/校准未部署、精细科室目标仍未达；网页算法字段方案ALGORITHM_WEB_PRESENTATION.md。proof population-evidence-verification-v1.json。

2026-10-04继续轮15：同活handle19359最终exit0，重排两完整500/499组/10000pair已完成，源175/500、主诉161/500（原BGE167/162），无&&369均129；top10召回392/376先冻，未改k/GT/词描述。CPU2安全权重，不微调/部署。原cal协议复核监督统计fit10、encoder0：仅保后缀seed7阈可行test保26/50%（未达80），其他9配置全拒；不把全部拒当成功或拿5textgroups证明原五症状组。8相关测试过，formal源/模型/数据/UI同v7.6，旧1018/96/142本轮未重跑。proof reranker-verification-v1及reranked-/reranker-selective-v1；前过程1600/4000字样为历史进度，现已终态不再poll/restart该handle。有限语义检索/资料增强/重排与校准均未达，下一真正完成审计：不能无限在该已曝光源调参数，核哪些目标需要新增可训练与未曝光匹配语料。goal ACTIVE，不claim完成、无外部消息/推送部署。

2026-10-04继续轮14：固定重排研究协议已冻结：BGE-small名称索引top10，不按GT挑候选，池已固定500/499组×两视图；oracle召回392/500、376/500。BGE-reranker-base MIT官方revision2cfc18c9415c912f9d8155881c133215df768a70，safetensors已哈希核验，下载曾HTTP读超时由同活进程自动续传成功，未重复启动。CPU2/batch16/256tokens，pair只原输入和候科名，sigmoid(logit)保序不是校准概率，无微调/部署。10相关测试过，formal不改。当前推理exec session19359仍活，日志reranker-first.log首视图最新PROGRESS1600/5000；源视图结果尚未完成，不称成绩/最终。继续先poll该handle或权威进程/结果文件，超时不重启；两视图分别写完整-result.json后才可汇总与校准。原基准/负结果不覆，goal ACTIVE。

2026-10-04继续轮13：固定资料增强对照完成。仅原4别名后同科specialty/specialties，未跨成人父科给儿细科；36/111类增强，75仍仅名，800字符固定/256tokens截断如实记。原医生原始专长字段2100条审计未命中对应医生/医院名字，没有身份学历进doc或原主诉落盘。BGE两视图155/153相容（原167/162，下降），无&&369仅116（原125）；char102/97（原59/54），均不达目标，保存负结果不改docs/labels/test阈。encoderfit0、病例监督fit0、标签文档词表fit1，无校准拟合/部署。12研究关联过，formal源/数据/模型/UI同v7.6，旧1018/96/142适用但本轮未重测。proof enriched-department-verification-v1及enriched-department-v1/*。下一限定一次交互式重排研究，再检验校准；不得无限在这500调拼法宣未见成绩，goal ACTIVE。

2026-10-04继续轮12：固定BGE预测数值的cal-only统计相容校准/拒答实测已完。五seed各视图40%主诉组cal/60%test，组均权cos+margin二特征sigmoid，监督统计校准fit10、encoderfit0；阈值全部先锁再test，源病例raw不重读或存。每视图仅seed7可行：保后缀cal10/90%→test15/46.67%/4.98%coverage；主诉cal16/81.25%→test24/58.33%/7.97%coverage，均未达80；其他8配置全拒答不能当成功。test兼容ECE约0.04-0.095不等尾部可靠或临床概率；5 textgroups不证明W66五症状组/临床diversity。无&&test诊断用已存参数重放、阈值不改/新增fit0。9研究关联过，formal源/数据/模型/UI与v7.6不变，旧1018/96/142仍适用但本轮不重测。source已开发，not新独立未见；临认证非目标前置，模型能力/校准仍失败不部署。proof semantic-selective-verification-v1及semantic-selective-v1/*。下一增强候选描述/资料检索信息，先冻结来源和原目标不借父折/改test参数美化；goal ACTIVE。

2026-10-04继续轮11：已核中断后v7.6完整1018/96(2workers)/142，rootAudit与模型隔离环境未中断训练。新.venv-core-embedding CPU torch2.8.0+cpu/transformers4.57.6、依赖检查通过并完整lock，正式env未改；BGE-small-zh-v1.5 MIT官方revision7999e1d3359715c523056ef9478215996d62a620已下载safetensors并哈希、CPU2线程冻结CLS+L2。已跑111标签名闭集char-TFIDF/BGE两视图全500/499组，源病例不监督训练、权重不fit、无case原文或向量持久化、网站未接。BGE保后缀167/500(旧普通范围166)、主诉162/500(普通范围161)，无&&369都125；char59/54且零重叠拒222/240，不强给首科。BGE拒答0不达到完整路由/校准目标，余弦非概率，无温度/阈值拟合。11研究相关测试过，formal代码/数据/模型/UI身份同v7.6，因此旧1018/96/142适用但本轮未重跑。首模型研究结果与输入protocol不可覆盖，source已开发不能称新未见；下一校准与拒答实验须另预登记数据职责和参数，勿部署最高sim。proof semantic-department-verification-v1及semantic-department-v1/*；goal ACTIVE，无消息/推送部署。

2026-10-04继续轮10最新v7.6/aux4.0：仅登记年龄/性别/人群而无医学主诉或就医目的→INFO/null/defer，清htriage症状/疾病/科候选；真实症状/体检接种挂号等目的不误删，旧ER优先。新11单元修前5行为失配/5模块未建控制不可执行、1原ER过；修后46关联与1018全pytest108.98s过、96browser2workers全量1.2min/142/前端17/typecheck/build/31-186过；首95+1跨页30s总预算timeout原件保留、隔离1过10.7s，不改时限或称根因修复。模型/词典/源JSONCSV同，500开发复验仍49/47相容，不能用此输入修复美化精细路由。根因审计：静态方向可表达源153/500（条件结构上限非所有将来接口）；儿童meta164病例133输出儿科，其中遮蔽年龄98变向，非语义不变/不可部署消融；全科184均只有固定回退病候选。源adultmeta5项儿科为照护孩子真实主诉，不能误当错年龄。证据demographic-only-verification与route-root-causes。下一L4中文检索模型研究，BGE MIT固定revision，独立CPU环境安装进行中，尚未下载/推理/达标或接网站；goal ACTIVE，无推送部署。

2026-10-04继续轮9：MedJourney DR本地只读两视图首评已完成，协议先冻结、500行/499主诉组/131后缀/111标签，target/keyentity不入输入，无拟合或原文持久化。source_body49/500相容（98.8%普通方向覆盖），complaint-only47/500（99%），无API错误；目录严格名字轴222可出现/278无源标签名称，222中仅49/47相容，故不只是目录粒度差异。全科/通用儿科回退主要占301/334条，当前不能称路由有效性完成；没有风险GT/概率校准成绩，去后缀标签迁移未经重新审定。首评不可覆盖，后续该源改进均development。1007pytest过但1子进程GBK/UTF8读线程warning，保原日志并修test捕获编码，19相关重过无warning；runtime源/数据/模型/UI与v7.5身份完全同，本轮未重跑旧95browser/142。证据medjourney-readonly-v1/*与medjourney-readonly-verification.json。下一根因拆解目录粒度/层级、儿童通用分支、全科fallback和输入表示，先保首评，不改标签求高分；goal ACTIVE。无发送/推送部署。

2026-10-04继续轮8：CMExam6811/临床形态1377的固定16题自审完成，16均无直接初诊GT（包含2个启发式误纳知识题），原标注定义为题目相关科室且含选项，故不训练考试分类替代目标。MedJourney作者P22开放复现实验声明重新核实；不把未列LICENSE变为禁止本地只读分析，仍不声称训练/再分发许可、不发送邮件。固定DR source500 NDJSON，111标签并集/232组合、131&&后缀、499不同主诉/1重复，keyentity240非空，原文未持久化、预测/拟合0，首次单JSON预检失败在预测前。当前v7.5 runtime与1000/95/142 proof身份完全不变，本轮不重复称重测。下一冻结映射/输入与完整分母进行本地不拟合对照，不能给后缀标签迁移或临床认证假证据。CHINESE_DATA_CANDIDATES及cmexam-task-fit-*/medjourney-dr-*-v1.json为当前证据，goal ACTIVE。

2026-10-04继续轮7最新v7.5/aux4.0：当前很高血压缺读数/单位/适用范围INFO/null/defer，明确成年非妊娠单主体完整严重升高mmHg读数URGENT及时评估、当前危险表现ER；不诊断/调药，通用none不能补数值。新28单元/132关联通过，主体混杂1与附加不确定/单位2失配已修。最终1000pytest88.28s/95browser43.4s/142固定/前端17/typecheck/build过，源JSONCSV/权重同、数据31/186。首browser94+1/定向2+1为新测试文案与编辑按钮定位错，失败原件保存，修定位真实INFO→补读数→URGENT通过1后全量95。27开发18相容、INFO2、D1INFO/C-D范围外2，不算独立准确率。proof core-blood-pressure-verification.json。CURRENT已整理成唯一现状，旧全文CORE_COMPLETION_HISTORY保留。中文科室/校准目标开放，下一评估CMExam临床情境子集的标签适用性，不直接套考试学科标签或降低80%目标；goal ACTIVE，无邮件/推送部署。

2026-10-04继续轮6最新v7.4/aux4.0：近期整侧手臂麻木恢复后仍URGENT及时评估/无普通排行，当前突然发作ER；同侧后来复发不借前次恢复降级。新18单元/104关联，修前5行为失败与10因模块缺失不能执行分开；后2部位scope/1复发失败已修并保before日志，正则调用错误已纠正。972pytest89.33s/92browser45.0s/142固定/前端17/typecheck/build过；数据31/186，正式JSONCSV/模型同。27开发18相容、严格D1INFO/C-D范围外2，非独立准确率。identity core-recent-arm-verification.json。新增CMExam元数据核验6811题/4965科室标签、36值含未定义1846，原生中文且专家复核，但为考试题学科标注非初诊GT；没有持久化题干/答案或拟合。不自动把内科泛类/题目类别映射为产品细科室。goal ACTIVE；下一未量化很高血压的缺信息处理/科室校准域，F4源差异按文献另审，不为分数一律ER。无邮件/推送/部署。

2026-10-04继续轮5：用户授权自行审核，外部医师非原型继续前置条件。27源/译文逐条技术比对并在线核验原CSV SHA与所有病例/标签对应，不改原标签或称独立临床认证。v7.3/aux4.0当前红眼+怕光/视力变化ER、同膝关节肿痛+局部热/活动受限URGENT及时评估且禁普通排行；有限scope控制，近期已恢复2误触发修复。最终954pytest165.48s/90browser46.5s/固定142/前端17/typecheck/build通过，数据31/186与权重词典同。首次浏览器ER页错用普通卡定位1失败原件保留，最终定位急诊alert。27开发复验17相容、D尚1INFO/C-D范围外3，不算独立准确率，中文科室/校准目标仍开放。proof core-eye-joint-verification.json及PUBLIC_VIGNETTE_REVIEW。goal ACTIVE，无发送邮件/推送部署。

2026-10-04最新：用户授权agent自行审核。goal ACTIVE，继续原型技术/译文/文献与评测口径审核，外部审核者非继续前置条件；不声称独立临床认证，不发送许可邮件。27源和译文逐条比对，无分级事实增删；下一L3为当前红眼+怕光/视力变化及急性同一关节肿痛及时评估，task_plan已先登记。下方BLOCKED为历史。

## 2026-10-04 goal恢复后的数据条件核查

goal工具当前active，独立中文标签/医学审核条件尚未变化；用户仍暂无审核者。MedJourney树复核仍60f6f3012c30fd72c6917e2fdce9b37821faa546、无license文件；本地未发现新增native/expert标签数据，现有930/88/142为原已验代码，不重复称本轮重测。新增MEDJOURNEY_DATA_REQUEST.md为获取使用依据的可审核草稿，未向作者发送，未下载数据/训练/改医学规则。源科室数据及风险审核分别需要解决，目标未完成。

## 2026-10-04 当前控制状态：goal BLOCKED（不是完成）

用户确认没有独立医学审核数据且暂时没有医学审核者。工程v7.2/aux4.0、930pytest/88browser/固定142已通过，完整证明见core-context-rescue-verification.json；整个核心算法有效性未完成。连续各goal轮原生中文初诊科室标签/审核与匹配校准证据缺口未关闭；作者MedJourney树实时复核60f6f3012c30fd72c6917e2fdce9b37821faa546仍未列数据许可，现有CC0英文专家27译写没有科室GT且已开发暴露。不能靠重复已看test选择阈值、自产医学标签或增加模板来完成独立验证。goal已正式blocked，旧automation仍paused，无训练/推送部署。

恢复条件：取得本次允许使用的、非患者病历的独立中文初诊情境与经审核的科室/风险标签，或先完成公开专家情境译写/目标映射的医学审核与使用依据。新训练/cal/test按源/近重复/病例分组先冻结，保持完整分母，再验证路由/校准/拒答。材料原文/译文/源标签/当前结果在results/public-vignettes-v1/，CURRENT/PUBLIC_VIGNETTE_REVIEW列已闭代码与未闭医学策略/域。下方active均历史，禁止据旧文自动恢复。

## 2026-10-04 核心算法继续轮4（当前产品）

v7.2/aux4.0，已报告1型糖尿病当前代谢症状组合ER，哮喘治疗反应需确认通道（unknown保持INFO可复核、present/原文个人最大量后仍不缓解ER、none仍URGENT及时评估），不推药量/不诊断。930pytest116.27s/88browser37.6s/固定142通过；首浏览器87+1跨页总预算超时保留，单独与顺序全过不称根因修复。源权重/词典/JSONCSV同。27开发复验15相容、D尚1未ER（F9 INFO不造max剂量），中文科室/校准目标及宽语义不闭。已经准备译文/来源/标签/结果，询问医学审核安排；goal active，旧automation暂停，无训练/推送部署。最新PUBLIC_VIGNETTE_REVIEW和core-context-rescue-verification.json。

## 2026-10-04 核心算法继续轮3（当前产品）

v7.0/aux4.0：新纯domain当前单侧腿肿痛、尿痛+腰侧痛+发热及时评估，已接triage/followups/recommendations；URGENT资源为urgent_assessment，不作普通医生/专家号排行，保医院目录且不保证实时接诊。一般否认/历史/已恢复/不同主体部位控制与既有ER/INFO保持。898pytest97.70s/86browser38.9s/固定142通过，权重词典JSONCSV不动。已看外部27开发复验14相容、C/D不相容5、严格D仍2未ER；F13/F9下一最高，整体有效性不关闭。见PUBLIC_VIGNETTE_REVIEW与core-compound-urgency-verification.json。goal active、旧automation暂停，无推送部署。

## 2026-10-04 核心算法继续轮2（当前产品）

v6.9/aux4.0，已修不伴/未出现谓词、双否定局部与有限协调否认；865pytest98.21s/85真实浏览器40.5s/固定142不变，另3外部来源测试通过。公开CC0医师虚构情境源27输入已冻结及首评：源代理等级12/27相容、严格D2项均未ER，未达整体核心有效性；开发复验单列，不造独立临床成绩。正式JSONCSV/权重不变，未推送部署。完整来源与病例缺口见docs/algorithm/PUBLIC_VIGNETTE_REVIEW.md，下一优先L3上下文风险（哮喘救援反复、代谢急症风险、单侧小腿肿痛、尿痛发热腰侧痛）与时间/方向；goal active，旧automation仍PAUSED。

## 2026-10-04 用户恢复核心算法持续工作（当前控制状态）

本次用户明确授权继续至核心算法完成，当前goal active；此前停止/PAUSED是历史控制状态，automation没有恢复。已修R074无/没排除动作、辅助症状限定否认及尿频polyuria错误等价，v6.8/aux3.9；最终846pytest129.88s、84真实浏览器51.8s、Safety142不变、front17/typecheck/build、数据31/186通过，JSONCSV/模型权重保持。独立评测入口7回归通过但无有效外部标签数据；用户确认没有医学审核集，公开六候选只核查元数据。工程完成不等中文初诊有效性完成，历史拒答研究仍目标失败；继续目标不标complete。当前证据/剩余门禁见docs/algorithm/CORE_COMPLETION_CURRENT.md。

## 2026-10-04 用户要求停止（当前控制状态）

已停止自主完善，automation已PAUSED（原15分钟计划保留），本次核查无本项目训练/测试进程。没有推送或部署；未开始W84后续修复。当前医疗v6.7/aux3.8，最近完整807pytest/82浏览器/固定Safety142通过，但W84新增8对照有4个排除能力语态风险失配未修（无法/无法完全/没能/没有排除心梗仍普通路径），不得以旧固定集通过宣称全部安全。后续各阶段ACTIVE均为历史记录；恢复必须由用户授权。

## 2026-10-04 W84无/没排除能力观察（运行时未改）

8新对照4失配：无法/无法完全/没能/没有排除危急词仍普通路径，对同义未实现策略不一致；部分病factsunknown也未保护风险。真否认/历史/后项否认控制正确，临床标签0、失败与身份留。17回归/compile/diff通过，下一R074局部动作token护栏L3，当前门禁仍W83 807/82/142，15分钟ACTIVE。

## 2026-10-04 W83排除动作有限修饰（最新产品）

局部未实现排除动作共享predicate，能/能够+明确/完全不再被未当病阴性，病facts保未知、真否认/历史/完成控制保持。8政策4→0，807pytest（156.95s）/82浏览器（57.3s）/Safety142指标不变，33关联/前端17/typecheck/build/compile/diff通过，v6.7 aux3.8、JSONCSV模型同。其他否认token/修饰/时序与临床中文/cal效度仍开放，15分钟ACTIVE。

## 2026-10-04 W82排除修饰语作用域观察（运行时未改）

8新对照4失配：未能明确/尚未明确/未能完全/未能够排除心梗仍普通路径，与旧未能排除ER不等价；部分已识别unknown事实也未保护Safety。真否认/历史/后项否认控制保持，临床标签0，新失败/身份留。17回归/compile/diff通过，下一最高R074有限动作语义范围L3，门禁仍W81 795/81/142，15分钟ACTIVE。

## 2026-10-04 W81完成排除的病名事实（最新产品）

已/已经/明确排除不建该病已知事实，动作前否定/未来保未确认，真病史与非疾病任务保持。7事实3→0、新完整W79原8复验0（旧失败不覆盖）；795pytest（153.10s）/81浏览器（53.8s）/Safety142指标不变，32关联/前端17/typecheck/build/compile/diff通过。v6.6 aux3.8、JSONCSV模型同，Safety逻辑未改；用户自述不等临床排除，修饰语/时序与独立中文校准仍开放，15分钟ACTIVE。

## 2026-10-04 W80排除未实现的风险作用域（最新产品）

未能/尚未排除不再当病阴性，事实保未确认、后续真否认/历史保持；6风险子集4→0、2心梗普通路径恢复既有ER策略。785pytest（149.38s）/80浏览器（52.8s）/Safety142指标不变，177关联/前端17/typecheck/build/compile/diff通过，v6.5 aux3.8、JSONCSV模型同。W79完成排除的前2事实仍开放，不声称全8或临床验证完成，15分钟ACTIVE。

## 2026-10-04 W79排除作用域缺口（下一最高P0，运行时未改）

8对照6失配：未能/尚未排除心梗实际ROUTINE而既有不能排除为ER，否定动作被当病阴性；已明确排除病名又误已知。R074优先局部否定能力保护，真否认/历史/固定142不能破坏；临床标签0，不称临床漏诊率。独占身份失败证据保留、17回归/compile/diff通过，当前门禁仍W78 777/79/142，15分钟ACTIVE。

## 2026-10-04 W78暂定报告事实（最新产品）

病名前局部考虑诊断/倾向/不能排除/排查保未确认，不建已知病或抢另一真病史；8事实5→0、原等级全部同，不能排除心梗仍ER。777pytest（95.25s）/79浏览器（47.7s）/Safety142指标不变，30关联/前端17/typecheck/build/compile/diff通过，v6.4 aux3.8、JSONCSV模型同。真实来源确认闭环保留，临床标签/宽语言与cal负证据不闭，15分钟ACTIVE。

## 2026-10-04 W77暂定报告语言观察（运行时未改）

8新对照5事实失配：考虑诊断为/倾向/不能排除/排查误作已知病，倾向长病名抢另一真实已确诊病。可能/真实确诊/非疾病考虑控制正确，临床标签0，原source/confidence与等级留作对照。独占身份稳定、17回归/compile/diff通过；下一R073局部暂定谓词L3须保不能排除危急病的原Safety、真病史与确认通道，门禁仍W76 766/78/142，15分钟ACTIVE。

## 2026-10-04 W76考虑病名事实（最新产品）

局部考虑病名保未确认，另一真实已确诊疾病优先，非疾病考虑与真病史保持。8事实4→0/原等级全部同，766pytest（93.36s）/78浏览器（45.1s）/Safety142指标不变，19关联/前端17/typecheck/build/compile/diff通过，v6.3 aux3.8、JSONCSV模型同。首浏览器等错先前风险响应的失败保留，匹配confirmed请求后完整78过，实际API闭环正确。结构化仍用户自述非医生核验，宽语义/临床中文与cal证据缺口不闭，15分钟ACTIVE。

## 2026-10-04 W75未确认病名事实观察（运行时未改）

8新对照4失配：医生/报告考虑病名被记已知病source user_stated/confidence.92，另已确诊乙肝主事实被未确认长病名抢。真实确诊/否认/考虑饮食控制保持，临床标签0，失败与新身份完整保存；17身份回归/compile/diff通过。R073下一核心P0局部考虑述谓L3、旧Safety与真实病史独立保，产品门禁仍W73 756/142+W74 77浏览器，15分钟ACTIVE。

## 2026-10-04 W74资源详情异步稳定（仅前端）

控制晚到catalog复现同ID对象更新清空详情，改kind/id+显式重试驱动，保不同资源取消/刷新。before1失败保留，10控制（8.4s）/20照片回退（16.2s）/完整77浏览器（43.6s）及前端17/typecheck/build/diff通过。后端/医疗数据同W73、756/142不称重跑，新身份/logSHA保存。实际目录与Trust均21，旧11疑问不成立；核心中文与cal负证据不闭，15分钟ACTIVE。

## 2026-10-04 W73模型主卡切分来源（最新）

97.30%主卡标清随机切分症状编码疾病分类与近重复参考风险，实际模型SHA/报告/指标一致才标源，否则待核对；原数值、模型与医学规则不改。756pytest（92.05s）/76浏览器（44.6s）/Safety142指标不变，6来源单元/15关联/前端17/typecheck/build/compile/diff通过，实际API标签/指标与日志SHA新身份保存。仍v6.2 aux3.8，临床中文/校准负结果不闭，15分钟ACTIVE。

## 2026-10-04 W72限定存在问句（最新产品）

登记5个呼吸/意识/抽搐cue的“是不是”与明确否定存在问题进入确认，真实报告/结构化present及原胸痛诊断担忧保持优先。8局部5→0；首宽实现曾使固定Safety胸痛案例FN1，after明确不接受/失败保留，缩新增范围并追加控制后新v2通过。最终750pytest（91.99s）/76浏览器（45.0s）/Safety142无FN，23定向/前端17/typecheck/build/compile/diff通过。v6.2 aux3.8、JSONCSV模型同，宽语义/中文独立验证仍P0，15分钟ACTIVE。

## 2026-10-04 W71 Trust数据范围披露（仅前端）

两段明确模型症状—疾病样本与城市资源目录用途，不能换算中文主诉科室准确率，非常州患者中文临床评测；原数值与后端不改。前端17/typecheck/build、最终75浏览器（43.3s）、1440/1280真实源路径与文案/截图通过。新增测试漏expect导入的失败原件保留；照片scroll偶发DOM detach后单独与全量通过，未称根因修复。新身份/日志SHA确认backend/data同W70，740/142不称本轮重测。核心中文/校准缺口继续，15分钟ACTIVE。

## 2026-10-04 W70候选科室Safety发布（最新产品）

ER/INFO在triage与htriage公共投影清普通科室候选，保顶层方向/红旗/确认，内部证据与ROUTINE/URGENT不变。12跨API契约8→0、740pytest（95.20s）/75浏览器（43.6s）/Safety142指标未变，22关联/前端17/typecheck/build/compile/diff通过。v6.1 aux3.8、JSONCSV模型同，急症医生抑制/默认与医院目录保持；数据同W68已验31/186。中文独立验证/校准研究失败仍P0，下一网站Trust与研究口径可核对，15分钟ACTIVE。

## 2026-10-04 W69急症默认方向（最新产品）

ER不再沿普通全科fallback，改既有急诊默认/原红旗方向；具体旧方向与INFO/ROUTINE/URGENT保持。6政策2→0、733pytest（92.28s）/74浏览器（42.5s）/Safety142指标不变，31关联/前端17/typecheck/build/compile/diff通过。v6.0 aux3.8、JSONCSV模型同，W68普通医生排行抑制/医院目录保持，同数据输入已有W68独占31/186校验。普通department_candidates解释仍另审，核心中文/校准证据缺口不包装完成，15分钟ACTIVE。

## 2026-10-04 W68急症医生发布边界（最新产品）

ER不调用普通医生排行，兼容字段doctor[]/weights{}与急症说明，医院目录保留；INFO/ROUTINE/URGENT保持。6政策3→0，727pytest（90.68s）/73浏览器（42.0s）/Safety142指标未变，16关联/前端17/typecheck/build/compile/diff通过。v5.9 aux3.8、JSONCSV模型同，数据新独占校验31/186不覆盖旧报告。R072医生发布部分缓解，ER普通全科fallback方向仍需单独L3；研究负结果仍不接网站，15分钟ACTIVE。

## 2026-10-04 W67急症跨API发布观察（运行时未改）

4控制Safety等级一致/模型隐藏/INFO无排行；3ER推荐API仍发布医生rank8/6/8，其中1方向仍普通全科fallback，R072需跨API发布政策一致。未记录身份资料、不从数量判临床可接诊。首audit错误解读legacy INFO产生1误判，复用唯一转换后新v2独占0契约失败，原件保留。17身份/compile/diff通过，最近产品门禁仍W61 710/72/142，下一L3保急症医院目录/120并抑制普通排行，15分钟ACTIVE。

## 2026-10-04 W66拒答研究目标失守（运行时未改）

cal-only经验80%目标未迁移test：原alias覆盖45.94%/保留Acc54.65%，name桥接30.81%/56.94%；完整912case/方法与82未见科室留分母，无cal可行5/8模型拒全。assessment明确算法目标失败，执行身份稳定不等于达标；23测试4.20s/compile/diff与30保存模型核对通过，无新fits/温度变更，临床标签0。正式网站未改、门禁仍W61 710/72/142，不依据已查看test重选阈值或降目标，15分钟ACTIVE。

## 2026-10-04 W65保存模型校准分层（运行时未改）

30状态固定温度/0新拟合重现原test三指标，完整1824渲染行分已见1660/未见164。bridge pooledECE0.142171不能替代mean-fold0.251024宣称通过校准，未知科室全错且28行分数≥0.7；仍RESEARCH_ONLY。20测试4.23s/compile/diff、来源身份核对通过，无临床标签/发布或test阈值选择，产品门禁仍W61 710/72/142。下一cal-only拒答协议，15分钟ACTIVE。

## 2026-10-04 W64配对核心研究（运行时未改）

当前同源name桥接30final/180inner完成，Acc原alias0.468202→0.491228，meanECE0.276210→0.251024，但seed42反降；完整各1824渲染test行/164未知科室保留，临床标签0、混合输入缺口未解。保持RESEARCH_ONLY，不替换网站；21预检4.19s/compile/diff、30模型状态哈希/finite/分组全分区核验、身份稳定/exit0/进程清理证据齐全。研究不覆盖旧45job，最近产品门禁仍W61 710/72/142，15分钟ACTIVE。

## 2026-10-04 W63研究name桥接（运行时未改）

结构化已有name48项×4状态192契约，原alias48失败→研究候选0（14新增声明别名），是字典回收契约，不是泛化或临床性能；83缺name/696英文回退仍未填。首whole50项/200范围偏差保留并scope-review不接受作192验收，v2新run独占。22测试3.34s/compile/diff通过，正式数据模型同、无训练/运行时变化，710/72/142仍W61门禁。下一可新登记配对研究训练，train选择/cal校准不看test，15分钟ACTIVE。

## 2026-10-04 W62中文代理输入域缺口（运行时未改）

当前304结构化样本仅71全部有中文name，233含英文码回退；83/131code缺name、696/2325次回退英文（29.94%），另12已命名code238次未被当前alias找回。新独占身份与完整分母保存，19聚合/身份测试3.24s/compile/diff通过。R070核心P0，旧45job结果未重跑/覆盖，不把当前parser回填旧实验或称临床准确率。运行时/模型/数据未改，最新完整门禁仍W61 710/72/142，15分钟ACTIVE。

## 2026-10-04 W61逐出现存在确认（最新）

明确当前是否/有没有不再算该次已确认强cue，同局部谓词保INFO/null/确认；同词另一真实报告、其他危险、病因未知及结构化present仍ER。8政策2→0、710pytest（93.75s）/72浏览器（42.2s）/Safety142指标不变，178关联/前端17/typecheck/build/compile/diff通过。真实INFO→present→ER、空格确认与原文保留验证。v5.8 aux3.8、JSONCSV模型同；R069仅有限缓解，宽语义与中文独立临床效度/校准仍P0，15分钟ACTIVE。

## 2026-10-04 W60当前存在疑问观察（运行时未改）

8新Safety政策对照2失配：明确是否喘不上气/不确定是否呼吸困难进入ER且无存在确认，而同类其他风险词为INFO；真实报告、同词独立肯定、病因未知控制保持ER。新身份失败证据保留、临床标签0，不能作为临床过分诊率。17身份回归/compile/diff通过；R069下一逐出现未知护栏L3，最近全量仍W59 700/71/142，15分钟ACTIVE。

## 2026-10-04 W59咳嗽回退证据一致性（最新）

后置未知不再从规则tags/计分/map回退重造呼吸方向，8政策3→0；独立发烧/已知糖尿病与危险ER保留。700pytest（91.76s）/71浏览器（40.9s）/Safety142指标不变，24关联/前端17/typecheck/build/compile/diff通过。测试误把发烧方向预期写成呼吸的首失败保留，最终比较真实发烧独立控制，未改产品迁就。v5.7 aux3.8，JSONCSV模型同；R067仅咳嗽有限缓解，其他词/复杂语义/中文独立临床效度仍P0，15分钟ACTIVE。

## 2026-10-04 W58独立本人危险分句（最新）

另一句问题/否认不再压掉直接本人强cue：10政策3→0，2URGENT与1ROUTINE恢复既有ER，历史/假设/局部疑问/否认/已解决控制保持。694pytest（95.12s）/70浏览器（40.8s）/Safety142指标不变，220关联/前端17/typecheck/build/compile/diff通过。首浏览器1失败69过仅测试内部label误用，改真实紧急alert/120后完整70过，旧证据与新后验身份保留。v5.6 aux3.8，JSONCSV模型同；R068仅有限缓解、R067后置unknown规则回退仍下一P0，15分钟ACTIVE。

## 2026-10-04 W57新Safety作用域缺口（下一最高P0）

8后置未知新政策对照4失败：3项咳嗽纯门禁拒绝但rule fallback又提供呼吸方向；另“现在咳嗽是不是，我喘不上气”实际URGENT，未进入原强cue ER门禁。R068全局问题上下文影响后项本人危险报告需优先L3定位修复，不以固定Safety142通过宣称覆盖。失败与身份完整保留，17身份回归3.15s/compile/diff通过；本轮运行时未改、临床标签0，最近全量仍W56 684/69/142，15分钟ACTIVE。

## 2026-10-04 W56咳嗽路线断言门禁（最新运行时）

仅直接map咳嗽入口要求独立原文肯定，未知主题不再自动当存在证据；9政策对照3→0、3未知方向回一般评估，肯定/病因未知/已知病/急症保留。最终684pytest（92.89s）/69浏览器（41.4s）/Safety142指标未变，27定向/前端17/typecheck/build/compile/diff通过。v5.5/aux3.8，JSONCSV/模型同；R067仅有限缓解，其他词与fallback及中文临床效度仍开放，15分钟ACTIVE。

## 2026-10-04 W55未知路线来源定位（运行时未改）

3新无前项否认控制与W54旧快照均同普通呼吸方向/aux未知拒答，直接match_department也相同；定位map关键词只检查否认，未知未区分。旧输入未重跑，来源SHA及声明runtime子集核对保留，不能作W53因果或临床方向结论。17身份回归/compile/diff通过；R067下一轮有限非Safety证据L3，最近全量仍W53 677/68/142，15分钟ACTIVE。

## 2026-10-04 W54跨层未知观察（运行时未改）

8项新当前分句观察：aux三态契约0失配，legacy词法存在与未知预期3项不同，真实unknown咳嗽仍普通呼吸方向但疾病aux拒答。执行失败0、临床标签0，不把差异当临床错误或W53因果；R067路线证据政策待核对。独占身份稳定、17身份回归3.32s/compile/diff通过；最近完整运行时门禁仍下方W53的677/68/142，15分钟ACTIVE。

## 2026-10-04 W53有限当前分句修复（最新）

前项否认不再跨逗号压掉明确现在/目前等新分句，后项新否认与普通并列否认保持。7项语言失配3→0、3方向恢复呼吸内科而等级未变；初5失败/8通过证据保留。最终677pytest（93.05s）/68浏览器（42.2s）/Safety142指标未变，171关联、前端17/typecheck/build/compile/diff通过。版本v5.4/aux v3.8，JSONCSV与模型输入相同；R066仅有限缓解，中文临床独立有效性与宽语义仍核心P0，15分钟ACTIVE。

## 2026-10-04 W52核心语言边界观察

7项固定当前分句语言对照3失配、0执行失败：前项否认跨逗号抹掉明确“现在/目前咳嗽”证据，真实API回全科/ROUTINE，R066仍开放P0。新独占v2身份稳定，首次观察导入错误记录保留；17身份回归3.27s、compile/diff-check通过。运行时/模型/数据未改，临床标签0；W51的664pytest/67浏览器/142为上轮门禁，本轮不声称重测。下一轮优先有限当前分句L3修复，保护并列否认与Safety，15分钟任务持续ACTIVE。

## 2026-10-03 网站持续完善（当前）

- W51限定胸痛父存在确认：没有严重胸痛不再当当前安全普通，窄独立原文门禁进入INFO/null/defer，明确问任何程度胸痛；none/present/unknown沿原政策，实际轻微父报告仍原URGENT、真正强cue先ER、历史否认控保留，不依赖模型可用性。7项1失败→0、JSONCSV同，追问/门禁v5.3。最终 **664pytest（76.63s）/67浏览器（38.6s）/固定Safety142指标未变**，158定向、前端17/typecheck/build、compile/diff-check通过。限定信息不足入口非新医学阈值/临床验证，R063宽语义仍P0，15分钟ACTIVE。

- W50网站验收索引：`docs/status/WEBSITE_ACCEPTANCE.md`集中本地启动/四页面/两API、W48实际验证版本与真实未闭P0/P1/P2；旧研究报告加冻结说明，不把早期暂停/运行时未改当当前状态。新Flask client六入口200/type正确，schema3身份快照保存，但未启动服务/不当当前浏览器或临床全验。运行时未改、未重复657/66/142或训练；临床中文/校准/R063仍最高P0，15分钟ACTIVE。

- W49网站身份schema3：补UI源码/脚本/测试/固定配置锁文件与dist分开哈希，Node及5依赖版本校验，不读取env/缓存/trace/模块内容。首4失败/1排除通过保留，修后17身份回归（3.14s）/compile/diff-check通过；真实w49-frontend-identity-preflight仅PREPARED，97源/4产物、Node24.12，无started/result。未改医疗/网站运行时，未重复657/66/142（不称662全量）；不证明构建来源/全动态依赖，旧身份不回填，15分钟ACTIVE。

- W48未确认风险闭环：unknown不再被当已完成而移除问题，同qid再次答复替换旧答案、未知不加完成步数，API重复校验仍在。5项2失败→0、原Safety/科室与JSONCSV同；首浏览器1失败/65通过暴露duplicate400并保留，客户端修后 **66浏览器（44.8s）** 通过，真实unknown→present原文/单ID/ER链完成。后端 **657pytest（140.45s）/Safety142指标未变**；16定向、前端17/typecheck/build、compile/diff-check通过。v5.2、UI新bundle gzip108.42KB及独立SHA记录，临床限定语义仍P0，15分钟ACTIVE。

- W47风险确认通道：生成的未答红旗问题不再被基本8问截断丢弃，统一先排红旗再截8项；已答不重复、急症不追问，疾病来源确认在风险确认后仍可完成。5项3失败→0失败、原Safety/科室与JSONCSV哈希同，追问版本v5.1。最终 **656pytest（140.93s）/65浏览器（42.4s）/固定Safety142指标未变**，24定向、前端17/typecheck/build、compile/diff-check通过。未增医疗阈值或改变初始分级，R063限定语义/临床验证仍P0，15分钟ACTIVE。

- W46 R-063仅aux缓解：限定胸痛严重/剧烈否认不再未经确认作为父阳性输入，scope_review待复核并拒疾病推测；独立后项轻微胸痛原present保留，无独立父报告则unknown，主Safety/科室未改。7项4失败→0失败、JSONCSV哈希同，输入v3.8。最终 **655pytest（132.59s）/64浏览器（38.8s）/固定Safety142指标未变**，17定向、前端17/typecheck/build、compile/diff-check通过。临床分级、明显/持续等宽限定仍P0开放，不称完整问题已解决，15分钟ACTIVE。

- W45限定程度否认观察：新9输入完整分母，1层间不一致“没有严重胸痛”原规则阴性但aux chest_pain阳性并提供预测，公开ROUTINE；临床标签0，clinical_accuracy=null，**执行契约失败0不代表风险已解决**，R-063开放P0。15聚合/身份测试（1.53s）/compile/diff-check通过，源/结果SHA可审。未改医疗/网站运行时、未重复651/63/142（不称654全量），限定程度/持续需要独立语义核验，15分钟ACTIVE。

- W44假设风险边界：明确直接“如果/假如+我+现在/不否认+危险cue”不再等同当前报告，3个合成假设ER→既有INFO待确认/null/defer，实际当前与另一分句急症仍ER、阴性/历史控制保留。9项3失败→0失败，JSONCSV哈希同，输入v3.7/断言v5.0。最终 **651pytest（183.20s）/63浏览器（43.0s）/固定Safety142指标未变**，214定向、前端17/typecheck/build、compile/diff-check通过。未加医学阈值、模型不参与Safety判定，限定语法不证明全部假设/临床语言覆盖，15分钟ACTIVE。

- W43 P0危险否认过滤：不否认不再被当否认，4个合成危险报告从误ROUTINE恢复既有ER；后续真实否认和阴性控制保留，aux仍未知拒答、未确认病名不作已知确病。9项7失败→0失败，JSONCSV哈希同，输入v3.6/断言v4.9。最终 **650pytest（96.49s）/62浏览器（40.6s）/固定Safety142指标未变**，39定向、前端17/typecheck/build、compile/diff-check通过。等级变化明确记录、非临床敏感度或全语义完成；多重否认/主体与中文独立效度仍P0，15分钟ACTIVE。

- W42是不是/不是：区分存在问句、清楚否认、而是后项和双否定，当前否定问句不变肯定；共享肯定检查避免把是不是中的不是当否认，并保不是X导致Y不误否认Y。9项8失败→0失败，JSONCSV哈希同；两科室变化有意修复：不是咳嗽→全科，否咳嗽而明确呼吸急症→呼吸危重方向（仍ER）。最终 **648pytest（65.56s）/61浏览器（31.8s）/固定Safety142指标未变**，76定向、前端17/typecheck/build、compile/diff-check通过。输入v3.5/断言v4.8，未新建医疗阈值或训练，宽语法与临床效度仍P0，15分钟ACTIVE。

- W41现在与限定词：直接“是否/假设+现在”不再被切成肯定症状，含空格/有限修饰控制；前一症状未知不污染现在明确另一症状，病因疑问保持。8项5失败→0失败，Safety/科室前后同、JSONCSV哈希同，输入v3.4。最终 **646pytest（65.65s）/60浏览器（31.3s）/固定Safety142指标未变**，15定向、前端17/typecheck/build、compile/diff-check通过。未改医学规则/权重，否定疑问/长距/主体及中文独立效度仍P0，15分钟ACTIVE。

- W40病因与存在：局部“不确定/说不清为什么/为何”不再抹掉症状存在证据；否认、是否、假设、历史仍原语义，补“现在”不得取消假设控制，不确定病因不等于确认病因。8项5失败→0失败，原Safety/科室与JSONCSV哈希同，输入v3.3。最终 **645pytest（65.18s）/59浏览器（30.3s）/固定Safety142指标未变**，14定向、前端17/typecheck/build、compile/diff-check通过。未改模型权重/已知病/Safety规则，宽语法与中文独立临床效度仍P0，15分钟ACTIVE。

- W39重复提及：未知与同code肯定/否认重叠不再被集合去重静默丢弃，uncertainty_conflicts保重叠、aux待确认拒答，原肯定证据/历史及真肯否优先级保留。8项6失败→0失败，Safety/科室前后相同、JSONCSV哈希不变，输入v3.2。最终 **643pytest（64.91s）/58浏览器（31.0s）/固定Safety142指标未变**，16定向、前端17/typecheck/build、compile/diff-check通过。可能增加保守拒答，显式更正/多主体及病因vs存在未知仍未全覆盖；中文独立效度P0，15分钟ACTIVE。

- W38公开模型错误：内部异常不再原样进响应，error固定model_unavailable，内部诊断/人可读notice与Safety优先保持；3纯合成marker对照3失败→0失败，所有adapter状态恢复。输出元数据v3.1，不改模型数学/字典/方向或医学规则。最终 **642pytest（66.68s）/57浏览器（30.1s）/固定Safety142指标未变**，15定向、前端17/typecheck/build、compile/diff-check通过。浏览器不可用提示用合成响应，真实API异常对照另计，非完整安全审计；中文独立效度P0仍开，15分钟ACTIVE。

- W37真实共享adapter失效对照：8基准×注入None/合成缺失文件两入口=16比较，内外公开结果均available=false/无预测，Safety/科室/defer不变、Safety优先原因正确且全部adapter状态恢复。schema2唯一执行0契约失败，17针对通过（2.34s）、compile/diff-check；未改运行时/真实权重、未重复640/56/142，不称641全量或整站离线兼容。AUXILIARY_ROUTE_INDEPENDENCE区分W36 helper与本轮adapter层，中文独立效度仍P0，15分钟ACTIVE。

- W36辅助依赖：8基准/24受控htriage helper对照，公开Safety/科室/defer均不变，patch恢复；不称全模型离线演练。首13过/1失败揭露模型搜索路径把后续app导入误指CLI，改独立命名空间加载，不污染sys.path或裸模块，裸CLI/包导入兼容。3固定数学完整结果与原CLI相同、权重SHA未变。最终 **640pytest（65.90s）/56浏览器（29.4s）/固定Safety142指标未变**，20定向、前端17/typecheck/build、compile/diff-check通过；输入v3.0/路线v4.7不改，AUXILIARY_ROUTE_INDEPENDENCE可审。中文独立效度仍P0，15分钟ACTIVE。

- W35父特征逻辑：特定grade阴性/未知不再推通用fever阴性/未知，修伪冲突；保generic/同grade真冲突。连带修正已知code标签对齐/实际特征计数，并保普通非模型默认方向，原8项Safety/科室恢复相同、JSONCSV哈希不变。旧oracle声明v2，首1/22关联失败及1/55浏览器失败、634中间结果均保留；最终 **636pytest（147.21s）/56浏览器（33.4s）/固定Safety142指标未变**，26定向、前端17/typecheck/build、compile/diff-check通过。输入v3.0/路线边界v4.7；FEVER_PARENT_LOGIC可审，无模型权重/临床阈值或校准训练变化，中文独立效度仍P0，15分钟ACTIVE。

- W34胸闷关联：仅aux隔离尚未认证的中文二值等价，明确否认胸闷不再污染另肯定呼吸困难同码。NIH/NHS分列不同感受，ATS也支持胸部紧缩感可属dyspnea，**不称原映射医学错误或临床准确率提升**；保守处理可能增加拒答，CHEST_ALIAS_REVIEW明记。8项6失败→0失败，Safety状态/科室前后相同、全JSONCSV哈希不变，元数据策略v2.9。最终 **633pytest（65.98s）/55浏览器（28.9s）/固定Safety142指标未变**，23定向、前端17/typecheck/build、compile/diff-check通过。W32分母是旧版历史不能当当前接受率，独立语义/中文标签仍P0，15分钟ACTIVE。

- W33辅助范围：词表外肚脐疼混咳嗽仍只取cough提供预测，本轮明确解释这一限制，未声称识别或处理未知描述。所有aux详情input_coverage标仅识别词证据/full_text_understanding_verified=false/纳入特征数；已接受普通页面提示可能遗漏其他描述，区别拒答，Safety优先保持。新6项协议6失败→0失败，元数据版本v2.8；最终 **632pytest（139.96s）/54浏览器（31.8s）/固定Safety142指标未变**，16定向、前端17/typecheck/build、compile/diff-check通过。复用reason token，JS gzip108.37KB；无模型权重/接受拒答/排序/医学分值变化。中文完整覆盖与域外检测仍P0，15分钟ACTIVE。

- W32完整服务分母：新协议98旧别名×单独/混咳嗽=196输入（仅48旧代码），adapter接受182/拒答14；公开保留172、Safety隐藏10、意外隐藏0、契约异常0。拒答不支持12/未核验语义2，全部留分母；已接受top posterior≥0.90为0，仅分布计数不证明校准。schema2执行身份与result SHA已保存，SERVING_DENOMINATOR可审；7新口径+12身份共 **19通过（1.43s）**，初测试收集语法错误日志也保留，compile/diff-check通过。医疗/网站运行时未改、624/53/142未重跑；无临床准确率或新训练声明，15分钟ACTIVE。

- W31分数口径：候选旧probability为本次结果内相对分，不是患病概率；新增relative_support_score保原数值/排序，并与NB未校准posterior分别声明非临床概率、未校准语义，notice解释。新schema2固定6项发布协议6失败→0失败，输入元数据版本v2.7/规则candidate-score-semantics-v4.6。最终 **624pytest（133.10s）/53浏览器（32.0s）/固定Safety142指标未变**，22定向、前端17/typecheck/build、compile/diff-check通过。无模型权重/阈值/排名/医学分值或训练改动，SCORE_SEMANTICS可审；未宣称临床校准或ECE改善，15分钟ACTIVE。

- W30评测身份：核实正式NB权重是JSON，原输入哈希已覆盖；补的是未记录的运行配置覆盖。身份schema2仅对9项已使用CHANGYI配置记录set/unset与值SHA，不收原值或其他环境；四服务依赖显式角色/路径/哈希。首配置漂移2失败/原权重覆盖1通过保留，修后6新身份+6生命周期+6口径共 **18通过（1.49s）**，compile/diff-check通过。真实w30-configuration-preflight仅PREPARED，无started/result。未改医疗/网站运行时、不重跑W29的616/52/142或训练；旧身份不回填环境记录，仍非全动态依赖/签名，15分钟automation ACTIVE。

- W29条件症状输入/标签：假如/假设/倘若与直接后置举例不再当辅助模型阳性，规则不发布肯定症状标签；局部假设识别复用纯MedicalInput helper，疾病语态保持、转折后的实际肯定症状保留。新9项版本协议8失败→0失败，模型输入v2.6/规则symptom-evidence-v4.5。最终 **616pytest（134.51s）/52浏览器（31.4s）/固定Safety142指标未变**，24定向、前端17/typecheck/build、compile/diff-check通过。未改原文、Safety、模型权重/字典/医学分值；中文独立验证与校准仍P0。自动任务当前 **15分钟ACTIVE**，旧结果不覆盖、无训练/推送部署。

- W28候选证据一致性：KnownDisease未知/冲突已被识别，但同词仍从规则或fallback生成带相对分的疾病候选；新9项协议6失败→0失败。候选入口复用局部陈述状态，只肯定alias计分，另真实已报告疾病、明确症状、结构化用户自述与Safety优先保持。版本candidate-evidence-v4.4，模型/原文/Safety/咨询方向/医学分值未改。最终 **615pytest（127.03s）/51浏览器（30.6s）/固定Safety142指标未变**，36定向、前端17/typecheck/build、compile/diff-check通过。源与结果身份/原失败已保留；相对分校准、症状标签语义及独立中文有效性仍P0，automation ACTIVE。

- W27直接后置假设：病名后“只是一个假设/是假设的情况/只是举例/仅是一种假想”不作既有病；肯定与同病假设混合待核对，肯定乙肝不被条件糖尿病抢占。新固定8项独立版本挑战7失败→0失败，before/after源与结果哈希已记录，原失败保留。版本postposed-hypothesis-v4.3，原文/模型/Safety/医学分值未改。最终 **614pytest（183.48s）/50浏览器（44.9s）/固定Safety142指标未变**，35定向、前端17/typecheck/build、compile/diff-check通过。直接述谓识别不等于完整中文/临床验证；远距引述与独立数据仍P0，automation ACTIVE。

- W26条件病名语态：如果/假如/假设/倘若局部病名保提及但不作用户既有病；已报告疾病与另一条件疾病并存时保留肯定证据。新固定6项协议用独立before/after身份运行，5失败→0失败；两次EXECUTED_IDENTITY_STABLE仅说明记录身份稳定。版本conditional-disease-v4.2，原文/模型/Safety全文及医学分值未改。最终 **605pytest（172.38s）/49浏览器（40.9s）/固定Safety142指标未变**，前端17/typecheck/build、compile/diff-check通过。失败与版本结果不覆盖；远距条件/复杂引述与独立中文临床验证仍P0开放，automation ACTIVE。

- W25新增挑战身份入口：prepare记代码/JSON-CSV输入/软件/HEAD，执行前漂移拒绝，执行后漂移结果留但无效，各阶段文件独占/目录不复用。6生命周期与6口径测试共12通过；真实首预检因工具更新被拒且未启动，v2新预检仅PREPARED未执行，无旧挑战重跑/训练/临床新证据。声明文件根哈希非完整动态依赖或签名认证；旧快照身份仍unknown。医疗/网站运行时未改，W23全591/48/142本轮未重跑；VERSIONED_CHALLENGE_RUNS可审，automation ACTIVE。

- W24评测口径：6历史快照2,042行合并同层重复90行后1,952层内文本，跨层原文1,949；分开辅助字典/Safety/已知报告/目录主题，不统计为临床准确率或独立病例数。新inventory-verified含源SHA256与历史未重放标记，原运行代码身份缺失明确unknown，当前整合代码hash不冒原运行身份。6项计数/去重/冲突/失败保留测试与compile/diff-check通过。医疗/网站运行时未改，上一W23全591/48/Safety142本轮未重跑；详细ACCEPTANCE_EVIDENCE_INVENTORY。自动任务保持ACTIVE，核心中文独立数据/语义/覆盖P0不因模板通过闭合。

- W23代理意图收口：替/代替未识别、不是代/帮却覆盖本人，首8定向4失败保留后补代理词及本地否认；较后本人改口仍胜前代理，17关联通过，原描述/模型/Safety全文及分值未改。版本proxy-intent-v4.1。最终 **591pytest（131.09s）/48浏览器（37.0s）/固定Safety142指标未变**、compile/diff-check通过。追加heartbeat承接同批未重复实验；复杂引述/长否认仍开放，automation ACTIVE。

- W22同句主体：无标点时整句归最后角色导致家人病混本人、本病被覆盖，“其他症状”的他亦误判。首5定向4失败保存后，按角色词位置分片并排同形词；15关联通过，原self/proxy资格、背景、原输入/模型/Safety全文保持，代理与他人急症控制保留。版本subject-spans-v4.0，不改分值/词表/模型。最终 **583pytest（132.75s）/47浏览器（27.9s）/固定Safety142指标未变**、compile/diff-check通过。复杂省略/引述/更多同形词仍开放；automation ACTIVE。

- W21主体：明确当前本人咨询时，亲属病仅作受控背景提及，不记本人已病/抢非Safety方向；本人病不被亲属更长病名抢，代家人咨询保原逻辑。首4定向2失败保留，22关联与宽7项全过，原始描述/模型/Safety仍全文，当前他人急症仍优先；有限匿名scope不采身份/病历。版本consultation-subject-v3.9，分值/词表/模型未改。最终 **578pytest（123.72s）/46浏览器（28.9s）/固定Safety142指标未变**、compile/diff-check通过。R-043登记路径缓解，同句多主体/省略/复杂代理仍开放；automation ACTIVE。

- W20同病冲突/更正：首6定向3失败保留后，肯定+否认/未知不再任意取肯定，标待核对conflicting且不发用户已知候选；误诊+更正不作确病历史，真实病史+别症否认保留。34关联回归通过，7宽审计原4失败降至**仍1主体失败**（母病+当前我症状），after保留；R-043下一P0。版本disease-conflict-v3.8，不改模型/数据/危险阈值。最终 **574pytest（123.74s）/45浏览器（27.9s）/固定Safety142指标未变**，compile/diff-check通过。此为程序证据聚合，不判断实际病真假或临床效度；automation ACTIVE。

- W19实体类型：非疾病就诊主题/阶段不再被发用户已知病或同名疾病候选；7真实主题对照首全部失败、10单测首9失败保留后修有限类型过滤，修后7全过、38关联回归通过。原中医/针灸/产科等方向保留，不能用confirmed造非病，真实疾病与孕产急症保留。版本routing-topic-types-v3.7，不改字典映射/模型/阈值。最终 **568pytest（94.44s）/44浏览器（35.7s）/固定Safety142指标未变**，compile/diff-check通过；R-041登记路径缓解，不称完整医学实体/临床验证。下一核心P0冲突/更正与主体归属，automation ACTIVE。

- W18未知疾病状态：首8失败保留，逐提及区分肯定/未知/否认，未知保留咨询名称/方向但has_known=false、confidence0，不加用户已知候选；已报告B优先未知A，真正病史保留。结构化确认只标用户自述，兼容旧option值，不改原condition或凭无病名造病；确诊补充能精化原一般性全科回退，具体方向和Safety门禁在先，追加1失败证据保留。known-disease宽8项全过，28定向通过，版本disease-assertion-v3.6。最终 **558pytest（167.30s）/43浏览器（37.9s）/固定Safety142指标未变**，compile/diff-check通过。R-040登记路径缓解；R-041“中医/产科被当疾病”实际probe下一词表P0，角色/冲突仍开放；automation ACTIVE。

- W17已知疾病否认：明确否认病名原仍has_known=true且抢科室，首10失败保存后修病名/alias肯定入口；同长度粗病类别名不再抢具体字面病名。追加阳性保护发现新guard跨分句误把无力/没力气/无发热作用于确诊，3失败保留后以独立本地确诊证据恢复；真实病史/复诊保留。16定向回归通过，版本known-disease-evidence-v3.5，Safety阈值/模型未改。最终 **546pytest（93.29s）/42浏览器（26.9s）/固定Safety142指标未变**、compile/diff-check通过。宽8项审计原6失败修至**仍2未知失败**，R-040下一P0，不能宣称8全过；automation ACTIVE。

- W16拒答解释：7后端/2浏览器失败保留，adapter v2.5输出真实空结果的abstained/原因/notice，支持结果不称拒答；Safety仍首要原因priority且保留独立auxiliary原因。普通页面显示人可读辅助说明，INFO不再暗示危险已排除；可选schema兼容旧响应、内部模型码不直接展示。原医学判定/权重/字典未改。最终 **530pytest（68.35s）/41浏览器（26.9s）/前端17/typecheck/build/固定Safety142指标未变**，compile/diff-check通过，Imprint复用reason文字token已记。下一核心任务科室方向与原始症状肯定/历史/未知证据审计，automation ACTIVE。

- W15明确未恢复：查权威TIA资料后保留近期卒中样信号即使消失的急症控制，不按“已好”自动降级。4既有直接呼吸/意识强信号+明确未恢复首8失败，有限当前资格修后14反例通过；其他历史病名/未知恢复不扩。167定向回归/250语境对照通过，版本unresolved-signal-v3.4，不改模型/字典/分值。最终 **523pytest（58.27s）/39浏览器（24.5s）/固定Safety142指标未变**，compile/diff-check通过。失败日志保留，浏览器独立output保护证据。下一核心任务审计拒答原因与网站解释一致性；语法/临床有效性仍开放，automation ACTIVE。

- W14历史Safety证据：按每次词出现的位置区分历史/当前，修复47历史误升及旧同词窗口误命中；250对照最终全过。追加“现在又”省略我再复现47失败后修复，当前同词复发仍急症；153历史/复发/否认反例通过。版本local-history-v3.3，只接Safety，不改原condition/科室模型/危险词阈值。最终 **509pytest（60.37s）/38浏览器（22.6s）/固定Safety142指标未变**、compile/diff-check通过。浏览器脚本起初未走修改入口失败，补实际修改→重新分析后通过，原日志保留。R-036代码路径缓解不等于全面语言/临床验证；下一轮已解决/含糊当前表达继续独立审计，automation ACTIVE。

- W13全危急词语境审计：50词×5家族=250真实API工程句，修前94失败；当前他人47被降级已修，修后当前本人/当前他人/否认/未知各50无契约失败。**历史+另一当前症状仍47失败**，完整before/after保留，R-036下一最高P0；不是250全过或临床指标。版本current-bystander-v3.2，无新危险词/阈值/模型变更。最终 **356pytest（56.59s）/37浏览器（22.8s）/固定Safety142指标未变**、compile/diff-check通过。下一轮处理历史匹配证据，不能全局删词降低真急症；automation ACTIVE。

- W12 Safety确认范围/主体：首10例7失败，修复未知症状被危险条件none误解除、无“正在”的他人持续报告降级、纯科普急症。共享独立Safety局部证据，症状未知持续INFO无方向/排行，明确持续仍急症，其他急症优先；版本seizure-context-v3.1，不读模型/不新增阈值。最终 **302pytest（56.50s）/36浏览器（22.6s）/Safety142指标未变**，compile/diff-check通过，失败原件保留。下一P0扩大既有危险词语境与确认交错，医学/语言覆盖仍开放；automation ACTIVE。

- W11最高Safety P0代码路径已缓解：未确认抽搐/惊厥进入独立复核，显式无方向/无排行；确认危险条件急症，none仍需尽快专业评估，持续抽搐/明确急症在先。当前他人持续抽搐被旧历史过滤的问题补查1失败后修复；否认/历史/科普及模型不可用均有回归。版本seizure-review-v3；不诊断癫痫、不依赖模型字典。最终 **292pytest（56.20s）/35浏览器（20.4s）/Safety142 Recall1、Under/Over0、FN0**，compile/diff-check通过。首7失败与补查失败保留。R-033代码缓解不代表临床或语言全面覆盖；下一轮继续独立Safety语境边界，automation ACTIVE。

- W10词典可信度：真实caller确认“抽搐→肌肉疼痛”发布模型标签/疾病，另3个码不在正式模型词汇表（1缺name）。adapter v2.4隔离可疑别名，不支持混合输入/通用fever明确拒答，mapping_review记录原因；明确否认不屏蔽独立肌肉痛。原alias/name/model SHA256相同，研究旧词典挑战不改口径。先9失败，首全量277通过/1失败为旧通用发热loading smoke；保留失败并新增原输入拒答回归，支持输入加载断言不弱化。最终 **279pytest（52.42s）/34浏览器（20.8s）/Safety142指标未变**。最高未解决P0：抽搐独立Safety仍ROUTINE，R-033开放，W11已预登记确认/复核门禁，不能把模型隔离当Safety完成。来源/证据见ALIAS_SEMANTIC_AUDIT，automation ACTIVE。

- W9核心断言作用域：全98别名×15模板原已1470通过，新增90混合句先全失败，真实adapter4回归失败；修复完整后置“都没有/都不确定”范围及“但”后独立阳性，最终 **1560/1560**。未缓解症状保持阳性，未知前项仍使模型整体拒答。版本v2.3，正式词典/权重/Safety未变。最终 **269 pytest（55.73s）/34浏览器（20.7s）/Safety142指标不变**，compile/diff-check通过。下一P0审计词典语义可信度（存在抽搐→muscle_pain待核验）；模板通过不证明医学标签正确，R-031开放。automation ACTIVE。

- W8核心中文断言：基础150句先54失败，6类真实模型adapter误把否认/未知/已解决症状作阳性；修后又复现扩展并列60失败，最终 **210/210**。新增程度词、“否认有/未出现”、完整后置否认/未知与历史/已解决识别，保留“没有减轻/没有好”和明确阳性。辅助模型版本v2.2，正式NB权重与Safety词典/阈值未改。最终 **263 pytest（65.70s）/34浏览器（22.2s）/Safety142 Recall1、Under/Over0、FN0**，compile/diff-check通过。失败原件保留在assertion-scope-v1；仅合成工程回归，不作临床准确率。下一轮继续中文全词典/混合子句挑战，automation ACTIVE。

- W7推荐请求生命周期：真实React hook浏览器装载先复现3失败（StrictMode不发布、A提前结束B加载、禁用后写旧结果）；修复effect重放与唯一尝试身份，禁用/换输入使旧尝试失效，仅当前尝试发布或结束加载。新增A→B→A反例，4/4通过，完整网站34/34（21.1s）、前端17/build通过。CI增加独立e2e:hooks；远端CI未运行。只改前端异步状态，后端医学与排序未改；下一轮优先中文断言/拒答挑战，定时任务保持ACTIVE。

- 用户恢复半小时工作，核心算法优先，同时处理网站P0/P1/P2，验收前持续；**不做PPT/Word/视频**。automation=automation为ACTIVE，批次结束不自动暂停。计划 `docs/algorithm/WEBSITE_CONTINUATION.md`。
- 辅助模型输入L3：否定/未知/矛盾/非当前描述不再当作阳性；domain `symptom_assertions.py`为唯一owner，研究挑战也复用。Safety规则/原始condition/正式NB权重未改；模型管线版本`asserted-input-v2`。新增真实网站caller回归，首轮243通过，头像回归后245通过。
- Windows原始`npm run e2e`已修复；安装对应1243浏览器后26/26通过，头像构建后再次26/26。无需临时配置。README有可直接使用的Windows验收步骤。
- DoctorAvatar responsive 80/160/320派生，保留2035个源图与来源身份，不裁剪/不生成医生；首24位可映射17张：3,750,732→43,628 bytes（160尺寸，-98.84%）。索引懒载，主JS gzip107.82KB，单独索引52.40KB。失败回退原图/首字，换医生不会沿用旧图/失败；WebP精确路径补Windows MIME和immutable缓存。
- 下一步：中文渲染器与真实完整组件分组覆盖算法对照、输入协调否定/历史挑战、图片fallback浏览器断网路径与网站可信度。之前独立研究结果保持归档，不重复880/330拟合。

- W3已完成45个Chinese proxy任务/270个训练内候选：global组件与未见renderer隔离，完整304案例×3重复；char24/char13/asserted-binary约46.00%/47.64%/46.82%，164个渲染样例的科室不在训练中，仍在分母。仅synthetic工程适配，结果表明不能直接把英文94%用于中文网站。
- W4修复：明确否认/不确定胸痛不再被htriage无肯定检查的fallback指定心血管方向；口语别名原位替换，避免追加词变阳性；并列否定不再把后项放入模型。新增3个失败caller回归先复现，修后全量250通过；对应模型input-v2.1及方向版本标识。原始症状、已知病复诊、对比转折阳性和Safety优先保留。
- W5已完成L3保守确认门禁：既有风险词前的“有没有/是否”不作明确否认，需补充/专业复核；已确认急症先于未知回答。显式null方向不被fallback重填；未确认路径不调用医院/医生ranker，前端不自动请求排行。确认问题优先展示，可通过已有present/none/unknown回答继续。新增4个API与2个浏览器回归，先复现3失败后修复；全量254/浏览器28/前端17/build通过，原Safety142 Recall1、Under/Over0、FN0。没有改红旗词或分值阈值，新增确认政策版本uncertainty-review-v2，不称临床验证。

下文2026-10-02“已暂停/已结束”是上一批记录，不适用于当前持续任务。

- W6确认闭环和故障恢复已验收：肯定回答转急症且无普通排行；明确否认返回辅助普通路径；未知/稍后补充保持待复核。修复误导性的“查看当前就医方向”文案，待复核仅提供手动目录浏览。资源页URL规范化曾删除Safety上下文，现保留from/direction/已知safety/preference，刷新仍显示待复核。真实API首次503后重试200、派生照片失败回源图、全部照片失败回姓名首字均通过。浏览器全量 **34/34（20.8s）**，前端17/build通过；后端未改，254与Safety142为W5验证结果。失败日志保留，定时工作继续ACTIVE。

## 2026-10-02 核心算法自主探索（最新权威状态）

- 用户明确核心算法最高P0，授权自主技术决策。本轮完整有限方案已完成；报告 `docs/algorithm/CORE_EXPLORATION_REPORT.md`，索引 `evaluation/core_exploration/results/summary.json`。
- cal/test/clean/perturbed复用同一拟合预测器、特征与温度，研究Safety门禁真实执行；修复矩阵std、追问Bernoulli记录概率、中文研究parser否定/未知/历史/span重叠。
- 原版源码控制seed42=.624413/T=.7；旧Round4 .737089/T=.5及mean .742438不可复现。修正Round4五seedmean **.608179**；旧产物保留在legacy_evidence。
- 新嵌套标准模型：**公开混合文本内部Acc .942533±.019970、Macro-F1 .946517、ECE .032082**；文本cos隔离约.923–.930。全304行症状-only grouped CV约.533–.615，来源迁移mean .561。**不能宣传为中文临床分诊准确率**。
- 1210次train-inner候选拟合、540追问模拟设置、15完整症状CV、5负对照及全部有限泛化/校准/集成/学习曲线；5可移植模型精确重载。720词典组合修后全过；12中文Safety工程例通过。
- pytest **239 passed**；Safety **142 cases / Recall1 / Under0 / Over0 / FN0**；前端17 tests/typecheck/build通过。新增冻结研究依赖和CI边界任务，新远端CI未执行。
- 正式Safety/API/NB权重/默认分诊路径未改；新模型/研究parser仍 **RESEARCH_ONLY**。当前核心P0：中文主诉输入契约、独立标签与完整科室覆盖；中文候选源见 `CHINESE_DATA_CANDIDATES.md`，本轮未导入外部患者记录。
- 所有研究进程已结束；半小时续执行heartbeat在最终归档后暂停。当前变更本地保留，未推送。

下文保留历史。与本节冲突的Round4 headline/测试数以本节和最新原始证据为准。

更新时间：2026-09-24（产品：Algorithm-visible UX）

## Algorithm-visible UX（本轮前端）

- 核心 Journey 对齐 `Safety Gate → Direct Department → Selective Abstention → Adaptive Inquiry → Multi-objective Care Routing`
- 首页 CarePath / 提交去掉装饰性计时；阶段由请求与 `/api/v1` 结果驱动
- 三个透明「示例」入口（普通 / 模糊追问 / 红旗急诊）只预填描述并走真实 API
- 信息不足明确「暂不强行给出科室方向」；追问后展示「信息补充 → 路径更新」
- Emergency：`拨打 120` 优先，声明「目录急诊字段 ≠ 实时可接诊」，无普通排行
- 资源偏好修改会重排并展示 `explanations`；可选 `abstain_reason`/`uncertainty_level` 有则展示
- 交付文档：`docs/competition/2026-ai-medical/ALGORITHM_VISIBLE_UX.md`、`FRONTEND_SCORECARD.md`
- 验证：typecheck 通过；frontend tests 17；Playwright **26/26**（含 algorithm-visible 6 项）；pytest 215 通过

更新时间：2026-09-16（算法 Round4：Safety-Constrained Selective Care Routing）

## 总体状态

- 状态：**P5 产品打磨完成** + **算法 Round1–4 离线实验完成**（`evaluation/care_routing/`，未改正式 API/Safety）
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 产品定位：AI Care Routing；Safety 永远先于个性化
- **Uncertainty → Adaptive Inquiry：`RESEARCH_ONLY`**
- **Direct Department Shadow Mode：`RESEARCH_ONLY`**（ECE 未过门槛）
- 研究主骨架：`Safety Gate → Direct Department → Selective Abstention → Care Routing`

## 算法 Round4（本轮）

详情：`evaluation/care_routing/ROUND4_REPORT.md`
复现：`.venv/bin/python -m evaluation.care_routing.run_round4 --write`

### 关键事实

- 最佳 Direct Department：**char n-gram TF-IDF + LR = 0.742±0.013**（Round3 0.450，**+29pp**）
- 表示消融：提升主要来自 **char n-gram**，不是换分类器；fusion 未超过 char-only
- Selective（阈值只来自 cal）：目标 80/70/60% → 实际 coverage 0.66/0.55/0.48，retained Acc **0.81/0.84/0.87**，wrong-conf ≤1%
- 最难混淆：多科室 → **皮肤科**（呼吸/泌尿/内分泌/神经等）
- Data Gap Top：呼吸内科、泌尿外科、内分泌代谢科、神经内科、消化内科（模型数据优先级，非医疗排名）
- 学习曲线 char：20%→100% **0.44→0.74**，still_rising
- Safety 契约 all_pass；Safety Evaluation 142 不变
- Shadow：**`RESEARCH_ONLY`**（ECE≈0.26 未过 0.15）

### 新增模块

`direct_department.py` / `selective_routing.py` / `department_confusion.py` / `round4_learning.py` / `round4_robustness_safety.py` / `run_round4.py`

## 算法 Round3（上一轮保留）

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
| 测试 | pytest **206**（169 + 11 r1 + 9 r2 + 10 r3 + 7 r4）；frontend boundary **17**；Playwright **20/20** |
| Safety | **142** cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency FN `0`（四轮算法实验均未改动） |
| 算法实验 | `evaluation/care_routing/results/round4_*`；主报告 `ROUND4_REPORT.md` |
| 最佳 Direct Dept | **char n-gram + LR = 0.742±0.013** |
| Selective | 目标 80% coverage → retained Acc **0.807**（wrong-conf <1%） |
| 诚实评测 | structured≈8 病种；expanded test≈**213/25 病种** / 11 科室 |
| 产品接入 | Uncertainty→Inquiry = **`RESEARCH_ONLY`**；Direct Dept Shadow = **`RESEARCH_ONLY`**（ECE 0.26） |
| 数据校验 | `validate_datasets` scanned 31 / issues 186（与基线一致，只登记不修复） |
| 前端构建 | CSS 100.9KB gzip 15.3KB；JS 355.7KB gzip 103.6KB（基线 JS 347.2KB，+2.4%） |
| 医生 API | 服务端分页与筛选（P2 保持） |

## 验证记录（算法 Round4）

- `.venv/bin/python -m py_compile evaluation/care_routing/*.py evaluation/care_routing/data_schema/*.py`：通过
- `.venv/bin/python -m pytest tests/test_care_routing_round4.py`：7 passed
- `.venv/bin/python -m pytest`：**206 passed**
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：142 cases；Recall 1.0；FN 0；Over-triage 0（与基线一致）
- `.venv/bin/python -m evaluation.care_routing.run_round4 --write` + `run_round4_refresh`：矩阵 / selective / 混淆 / gap / 曲线 / 鲁棒性 / Safety 落盘
- 正式 `/api/v1`、Safety Gate、红旗规则、前端 **零改动**

## 未改变的风险

- Safety 固定样例 ≠ 临床覆盖（`R-001`）
- 来源/许可不完整（`R-002`）；照片仍非 `SOURCE_VERIFIED`
- 急诊字段仅为目录标记，不代表实时接诊能力（`R-019` 同源表述）
- 账号/云同步/实时急诊/实时公交仍明确不做
- 原型概率未经临床校准；char LR ECE≈0.26，不得当作医学置信度
- 三态追问为 simulation；synthetic schema 不是真实患者数据
- expanded_41 是公开文本集，不是常州真实就诊分布
- Data Gap Map 是模型数据优先级，不是医疗重要性排名
- Selective 阈值来自 calibration；迁到 test 后 coverage 低于目标

## 竞赛提交（2026-09-15 审计，本轮未推进）

对照官方赛道规范，**工程/Safety 基线可演示，但初赛主材料未按规范产出**。完整 P0/P1/P2 见 `docs/competition/2026-ai-medical/SUBMISSION_GAP.md`，执行阶段见 `SUBMISSION_WORKFLOW.md`。初赛截止 2026-10-15 20:00。

## 下一步（算法）

1. **校准修复**：char LR 温度/Platt，目标 ECE≤0.15 后再评 Shadow。
2. 按 Data Gap Map 补呼吸内科/泌尿外科/内分泌代谢科等独立表达。
3. 重做 word+char fusion；评估原始中文口语 char n-gram。
4. 按 `data_schema/` 准备 opt-in 多轮追问采集；IG 保持 simulation-only。

## 下一步（产品/提交）

- 按 `SUBMISSION_WORKFLOW.md` S0→S9 推进初赛材料；可把 ROUND4 的 Selective Care Routing 骨架写入技术方案
- Trust/研究页若展示不确定性/拒答率，必须标注 assistive_only / not clinical confidence
- 涉及医学或生产能力按 L3/L4 另立计划

## 竞赛算法评测（2026-09-16，任务 03）

- 权威证据索引：`evaluation/competition/evidence_index.json`；叙事见 `docs/evaluation/COMPETITION_ALGORITHM_EVIDENCE.md`。
- 新增可复现：`evaluation/competition/{run_matrix,care_routing_ablation,golden_e2e}.py`。
- 新增测试：`tests/test_competition_golden_e2e.py`、`tests/test_competition_care_routing_ablation.py`（pytest 206→**215**）。
- 数字漂移：README 仍写 Safety 135 / Over-triage 0.0312；SCORECARD 冻结 38-case/108 pytest。材料只引用 evidence_index。
- Care Routing 消融证明规则一致性（偏好翻转、缺失重平衡、Emergency bypass）；**非临床有效**。
- Shadow 仍 `RESEARCH_ONLY`：温度校准后 seed42 ECE 0.269→0.061，但 headline ECE 0.26 未过 0.15，且 cal→test coverage 偏移。
