# 核心算法发现

- 继续轮4：F13需要疾病背景+当前组合风险而非慢病默认随访；Raw Type1已报/当前口渴尿增加胃肠不适局部风险独立于aux，原文假设未知否认与主体保持。F9当前治疗反应缺关键信息，不能4次→max或完整说话→无危险；INFO确认可unknown→present，明确个人max后不改善与present ER，none仍及时评估。930/88/142过、开发15/27且D1尚INFO，不称临床完成。新review question与generic none隔离，需8截断前、未知重答、跨排行边界，旧来源/失败不覆盖； native科室/校准仍需要合法匹配标签与审核。

- 继续轮3：F12/F14不是只缺模型，它们的当前复合症状被普通路径/恶心GI方向覆盖。一般单侧腿肿痛、排尿疼痛+发热+腰侧痛进入及时评估，限定真实当前同片段/主体/部位，ER/INFO在先；长短alias覆盖必须含否认/恢复，否则“肿胀好了”的肿重造阳性，不同腿不能因前项prefix并入。急性组合复用慢病bucket又误专科预约，必须跨资源策略抑制普通医生与专家排行。完整898/86/142过，开发源相容12→14，严格D2不闭；不包装临床成功。

- 继续轮2找到作者CC0医师虚构风险源，实际原CSV960行、F参考仅27，不能按README推F30或第三方推39。输入只源年龄/症状/病史、无label/模型回答/强制选项；先冻结忠实译写，再执行v6.8，等级代理12/27且源严格D2/2未ER。译写不等原生中文临床验证，源A等级产品不可表达5项保全分母；缺科室标签，不做科室准确率或伪ECE。
- F11显式无意识混乱或抽搐误触确认；另复现不伴中伴、未出现中出现被当阳性breaker，双否定全局抹后项真否认。纯解析有限修复后12策略7→0、865/85/142通过，真实危险/限定程度复核保持；外部开发复验F11不再INFO但总体等级仍12/27与D2/2，不冒称临床分级改善。下一医学上下文需NHS/NIDDK等来源与一般条件控制，不能对27已看病例硬编码或调标签。

- 2026-10-04继续完成：排除动作共用谓词原只有未token被风险过滤跳过，无/没仍误病阴性；严格锚定病名前动作并局部保护无/没/没有，W84 4→0，不消除后项真否认。aux仅胸痛限定否认门禁不足，“没有严重头痛/咳嗽、没有剧烈腹痛”仍输入模型阳性；扩展已识别症状有限四修饰复核，保独立肯定，不动Safety。尿频→polyuria混频率与总量，MedlinePlus明确二者不同；局部隔离而不造替代特征。原失败证据保留。
- 本次用户没有医学审核中文标签，先核查公开候选。MedJourney为医生构造500科室情境，但README/tree未给明确数据许可且无急症标签；Huatuo26M-Lite loader仅question/answer/score/label，为互联网一般问答分类；LCMDC作者声明匿名但原始患者咨询与本项目记录边界需独立审查。RD-Triage任务域为罕见病、TriageBench仅一致性、英文规则生成500不是中文独立标签。不存在可据目前元数据直接宣布完成临床中文验证的数据。独立评测入口已实现但缺有效输入，保留全分母与source声明边界；不自造“专家已核验”。

- 原始 main=e82447c；215 pytest/142 Safety/17 frontend/26 临时 Windows E2E 均通过。
- direct char 使用 35 epochs/lr .35，selective 与 robustness 又拟合 70/.4；cal/test 和 clean/perturbed 混不同模型。
- 同名 seed42 已提交 accuracy .737089 vs selective full .624413；T .5 vs .7，结果版本不一致。
- run_matrix.std 使用 readiness 描述字符串，不是数值。
- legacy 拼接 char 未分隔症状，且输入顺序改变表示；需顺序与分隔消融。
- 所谓 synonyms 实际改变症状/严重程度；drop_noncritical 随机丢症状，不能保证非关键。需修正研究叙事和压力实验分类。
- 现有追问 probability 由 multinomial token counts 推 yes/no，待核验。
- 严格研究：test 不能选模型/阈值；完整阴性结果保留；无真实患者、无临床宣称。
- 首个标准模型 smoke：binary / seed42，22 个内层候选；选择 LR C=10 unweighted，外层 Acc .4272、temperature ECE .0319。只是 smoke，不是最终结果。后加入完整 OvR sigmoid/isotonic 校准后，正式结果版本固定为 study-v2，smoke-v1 保留。
- 修正 Round4 正在跑；实时五 seed headline 暂为 .608179，而旧文件为 .742438。仅模型身份修复不应改变分类器训练逻辑，需用 git HEAD 原函数单独复现 seed42，排除修复改变主分类器的可能。
- 追问的 Bernoulli 概率错误已用失败用例重现：两类各2样本，fever 一类全有一类全无，混合 yes 应为 .5，原实现为 .3142857。修复记录频率分母为 n_class+2α；IG 的 yes/no 后验直接更新同一输入 posterior，避免混温度分布。
- 更重要的数据发现：training_long_extra 的若干“symptom code”是整段疾病介绍，含 cystic_acne/alcoholic_hepatitis 等真实目标名称，原样合并为1289样本不是一致的标准症状码数据。Jaccard over whole phrase tokens 不能隔离语义/文本模板改写。标准模型内层选择的五seed约94%只是混合文本研究指标，不能解释为中文症状分诊提升。阶段5新增冻结协议：label-mask ablation、字符cosine global components(.7/.8/.9)、纯structured cohort和来源对照；保留所有覆盖缩小/unsupported结果。
- 原版Git函数控制已完成：seed42=.624413、T=.7，与当前修正分类器一致；旧 .737089/T=.5 无法从本次源码复现。
- 疾病名遮蔽被证伪为 headline 的主要成因：seed42 test-only mask 与 mask-refit 都仍 .957746；33条命中精确疾病名，723条extras含>80字符的长字段。不能把所有成绩归因名称泄漏。
- label-masked文本cosine global group(.7/.8/.9) 五seed平均Acc约 .930/.925/.923；跨来源 structured→extras seed42 .532；reverse缺训练科室为unsupported并保留。完整304条症状-only GroupKFold5，binary/word/segmented Acc约 .615/.609/.533（含23个训练中缺失科室样本，不移出分母）。原quota8/8不能代表304条全覆盖。
- Phase6完成：5seeds×108策略/概率/预算/噪声条件，540个设置；均明示closed-world oracle，不代表真实阴性回答。
- Phase7词典归一留911/1289行（378条无可识别概念），存在22个跨科室相同fingerprint；按数据自身标签的多数上界约.864，不是临床上界。12个中文/安全边界工程例通过，尚非临床科室准确率。
- 最后新增有限对照：25个分组训练量学习曲线点，及每seed3个集成规则（全8表示均匀/top3均匀/cal-NLL加权）。理由：验证提高是否依赖训练量、特征集合共性与cal过拟合；权重只拟合cal_fit，threshold_cal/test分开。结束后不再无限扩模型。
- 中文720个词典组合性质挑战发现12个失败：否定“连续打喷嚏”时，较短“喷嚏”别名在同一span被再次判阳性。已定位长短别名重叠根因，改为最长匹配span只处理一次，保留旧失败报告；新增真实caller回归。另修复“担心会不会”疑问及“小时候…现在好了”的研究层当前症状误断。正式Safety规则未改。

2026-10-04继续轮5：用户授权自行审核，外部医师非原型继续前置条件。27源/译文逐条技术比对并在线核验原CSV SHA与所有病例/标签对应，不改原标签或称独立临床认证。v7.3/aux4.0当前红眼+怕光/视力变化ER、同膝关节肿痛+局部热/活动受限URGENT及时评估且禁普通排行；有限scope控制，近期已恢复2误触发修复。最终954pytest165.48s/90browser46.5s/固定142/前端17/typecheck/build通过，数据31/186与权重词典同。首次浏览器ER页错用普通卡定位1失败原件保留，最终定位急诊alert。27开发复验17相容、D尚1INFO/C-D范围外3，不算独立准确率，中文科室/校准目标仍开放。proof core-eye-joint-verification.json及PUBLIC_VIGNETTE_REVIEW。goal ACTIVE，无发送邮件/推送部署。

2026-10-04继续轮6最新v7.4/aux4.0：近期整侧手臂麻木恢复后仍URGENT及时评估/无普通排行，当前突然发作ER；同侧后来复发不借前次恢复降级。新18单元/104关联，修前5行为失败与10因模块缺失不能执行分开；后2部位scope/1复发失败已修并保before日志，正则调用错误已纠正。972pytest89.33s/92browser45.0s/142固定/前端17/typecheck/build过；数据31/186，正式JSONCSV/模型同。27开发18相容、严格D1INFO/C-D范围外2，非独立准确率。identity core-recent-arm-verification.json。新增CMExam元数据核验6811题/4965科室标签、36值含未定义1846，原生中文且专家复核，但为考试题学科标注非初诊GT；没有持久化题干/答案或拟合。不自动把内科泛类/题目类别映射为产品细科室。goal ACTIVE；下一未量化很高血压的缺信息处理/科室校准域，F4源差异按文献另审，不为分数一律ER。无邮件/推送/部署。

2026-10-04继续轮7最新v7.5/aux4.0：当前很高血压缺读数/单位/适用范围INFO/null/defer，明确成年非妊娠单主体完整严重升高mmHg读数URGENT及时评估、当前危险表现ER；不诊断/调药，通用none不能补数值。新28单元/132关联通过，主体混杂1与附加不确定/单位2失配已修。最终1000pytest88.28s/95browser43.4s/142固定/前端17/typecheck/build过，源JSONCSV/权重同、数据31/186。首browser94+1/定向2+1为新测试文案与编辑按钮定位错，失败原件保存，修定位真实INFO→补读数→URGENT通过1后全量95。27开发18相容、INFO2、D1INFO/C-D范围外2，不算独立准确率。proof core-blood-pressure-verification.json。CURRENT已整理成唯一现状，旧全文CORE_COMPLETION_HISTORY保留。中文科室/校准目标开放，下一评估CMExam临床情境子集的标签适用性，不直接套考试学科标签或降低80%目标；goal ACTIVE，无邮件/推送部署。

2026-10-04继续轮8：CMExam6811/临床形态1377的固定16题自审完成，16均无直接初诊GT（包含2个启发式误纳知识题），原标注定义为题目相关科室且含选项，故不训练考试分类替代目标。MedJourney作者P22开放复现实验声明重新核实；不把未列LICENSE变为禁止本地只读分析，仍不声称训练/再分发许可、不发送邮件。固定DR source500 NDJSON，111标签并集/232组合、131&&后缀、499不同主诉/1重复，keyentity240非空，原文未持久化、预测/拟合0，首次单JSON预检失败在预测前。当前v7.5 runtime与1000/95/142 proof身份完全不变，本轮不重复称重测。下一冻结映射/输入与完整分母进行本地不拟合对照，不能给后缀标签迁移或临床认证假证据。CHINESE_DATA_CANDIDATES及cmexam-task-fit-*/medjourney-dr-*-v1.json为当前证据，goal ACTIVE。

2026-10-04继续轮9：MedJourney DR本地只读两视图首评已完成，协议先冻结、500行/499主诉组/131后缀/111标签，target/keyentity不入输入，无拟合或原文持久化。source_body49/500相容（98.8%普通方向覆盖），complaint-only47/500（99%），无API错误；目录严格名字轴222可出现/278无源标签名称，222中仅49/47相容，故不只是目录粒度差异。全科/通用儿科回退主要占301/334条，当前不能称路由有效性完成；没有风险GT/概率校准成绩，去后缀标签迁移未经重新审定。首评不可覆盖，后续该源改进均development。1007pytest过但1子进程GBK/UTF8读线程warning，保原日志并修test捕获编码，19相关重过无warning；runtime源/数据/模型/UI与v7.5身份完全同，本轮未重跑旧95browser/142。证据medjourney-readonly-v1/*与medjourney-readonly-verification.json。下一根因拆解目录粒度/层级、儿童通用分支、全科fallback和输入表示，先保首评，不改标签求高分；goal ACTIVE。无发送/推送部署。

2026-10-04继续轮10最新v7.6/aux4.0：仅登记年龄/性别/人群而无医学主诉或就医目的→INFO/null/defer，清htriage症状/疾病/科候选；真实症状/体检接种挂号等目的不误删，旧ER优先。新11单元修前5行为失配/5模块未建控制不可执行、1原ER过；修后46关联与1018全pytest108.98s过、96browser2workers全量1.2min/142/前端17/typecheck/build/31-186过；首95+1跨页30s总预算timeout原件保留、隔离1过10.7s，不改时限或称根因修复。模型/词典/源JSONCSV同，500开发复验仍49/47相容，不能用此输入修复美化精细路由。根因审计：静态方向可表达源153/500（条件结构上限非所有将来接口）；儿童meta164病例133输出儿科，其中遮蔽年龄98变向，非语义不变/不可部署消融；全科184均只有固定回退病候选。源adultmeta5项儿科为照护孩子真实主诉，不能误当错年龄。证据demographic-only-verification与route-root-causes。下一L4中文检索模型研究，BGE MIT固定revision，独立CPU环境安装进行中，尚未下载/推理/达标或接网站；goal ACTIVE，无推送部署。

2026-10-04继续轮11：已核中断后v7.6完整1018/96(2workers)/142，rootAudit与模型隔离环境未中断训练。新.venv-core-embedding CPU torch2.8.0+cpu/transformers4.57.6、依赖检查通过并完整lock，正式env未改；BGE-small-zh-v1.5 MIT官方revision7999e1d3359715c523056ef9478215996d62a620已下载safetensors并哈希、CPU2线程冻结CLS+L2。已跑111标签名闭集char-TFIDF/BGE两视图全500/499组，源病例不监督训练、权重不fit、无case原文或向量持久化、网站未接。BGE保后缀167/500(旧普通范围166)、主诉162/500(普通范围161)，无&&369都125；char59/54且零重叠拒222/240，不强给首科。BGE拒答0不达到完整路由/校准目标，余弦非概率，无温度/阈值拟合。11研究相关测试过，formal代码/数据/模型/UI身份同v7.6，因此旧1018/96/142适用但本轮未重跑。首模型研究结果与输入protocol不可覆盖，source已开发不能称新未见；下一校准与拒答实验须另预登记数据职责和参数，勿部署最高sim。proof semantic-department-verification-v1及semantic-department-v1/*；goal ACTIVE，无消息/推送部署。

2026-10-04继续轮12：固定BGE预测数值的cal-only统计相容校准/拒答实测已完。五seed各视图40%主诉组cal/60%test，组均权cos+margin二特征sigmoid，监督统计校准fit10、encoderfit0；阈值全部先锁再test，源病例raw不重读或存。每视图仅seed7可行：保后缀cal10/90%→test15/46.67%/4.98%coverage；主诉cal16/81.25%→test24/58.33%/7.97%coverage，均未达80；其他8配置全拒答不能当成功。test兼容ECE约0.04-0.095不等尾部可靠或临床概率；5 textgroups不证明W66五症状组/临床diversity。无&&test诊断用已存参数重放、阈值不改/新增fit0。9研究关联过，formal源/数据/模型/UI与v7.6不变，旧1018/96/142仍适用但本轮不重测。source已开发，not新独立未见；临认证非目标前置，模型能力/校准仍失败不部署。proof semantic-selective-verification-v1及semantic-selective-v1/*。下一增强候选描述/资料检索信息，先冻结来源和原目标不借父折/改test参数美化；goal ACTIVE。

2026-10-04继续轮13：固定资料增强对照完成。仅原4别名后同科specialty/specialties，未跨成人父科给儿细科；36/111类增强，75仍仅名，800字符固定/256tokens截断如实记。原医生原始专长字段2100条审计未命中对应医生/医院名字，没有身份学历进doc或原主诉落盘。BGE两视图155/153相容（原167/162，下降），无&&369仅116（原125）；char102/97（原59/54），均不达目标，保存负结果不改docs/labels/test阈。encoderfit0、病例监督fit0、标签文档词表fit1，无校准拟合/部署。12研究关联过，formal源/数据/模型/UI同v7.6，旧1018/96/142适用但本轮未重测。proof enriched-department-verification-v1及enriched-department-v1/*。下一限定一次交互式重排研究，再检验校准；不得无限在这500调拼法宣未见成绩，goal ACTIVE。

2026-10-04继续轮14：固定重排研究协议已冻结：BGE-small名称索引top10，不按GT挑候选，池已固定500/499组×两视图；oracle召回392/500、376/500。BGE-reranker-base MIT官方revision2cfc18c9415c912f9d8155881c133215df768a70，safetensors已哈希核验，下载曾HTTP读超时由同活进程自动续传成功，未重复启动。CPU2/batch16/256tokens，pair只原输入和候科名，sigmoid(logit)保序不是校准概率，无微调/部署。10相关测试过，formal不改。当前推理exec session19359仍活，日志reranker-first.log首视图最新PROGRESS1600/5000；源视图结果尚未完成，不称成绩/最终。继续先poll该handle或权威进程/结果文件，超时不重启；两视图分别写完整-result.json后才可汇总与校准。原基准/负结果不覆，goal ACTIVE。

2026-10-04继续轮15：同活handle19359最终exit0，重排两完整500/499组/10000pair已完成，源175/500、主诉161/500（原BGE167/162），无&&369均129；top10召回392/376先冻，未改k/GT/词描述。CPU2安全权重，不微调/部署。原cal协议复核监督统计fit10、encoder0：仅保后缀seed7阈可行test保26/50%（未达80），其他9配置全拒；不把全部拒当成功或拿5textgroups证明原五症状组。8相关测试过，formal源/模型/数据/UI同v7.6，旧1018/96/142本轮未重跑。proof reranker-verification-v1及reranked-/reranker-selective-v1；前过程1600/4000字样为历史进度，现已终态不再poll/restart该handle。有限语义检索/资料增强/重排与校准均未达，下一真正完成审计：不能无限在该已曝光源调参数，核哪些目标需要新增可训练与未曝光匹配语料。goal ACTIVE，不claim完成、无外部消息/推送部署。
