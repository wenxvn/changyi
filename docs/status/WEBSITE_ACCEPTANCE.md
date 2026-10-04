# 常医网站验收入口（W50，2026-10-03）

范围仅本地网站与算法，不含PPT、Word、演示视频或部署。核心算法仍最高P0；下面工程验证不能替代临床有效性。

W66拒答负结果：仅cal选择的经验80%目标未迁移test，桥接保留Accuracy56.94%、coverage30.81%。目标失败与执行成功分开披露，见`docs/algorithm/CAL_SELECTED_REFUSAL.md`；此研究没有接入网站，也不作为临床策略。

W64新增同源配对研究：name桥接在合成代理Accuracy0.468202→0.491228，但一seed下降、平均ECE仍0.251；保持RESEARCH_ONLY，未替换网站。30最终模型/180inner、完整未知科室分母及状态哈希证据见`docs/algorithm/PAIRED_NAME_BRIDGE_STUDY.md`，不是临床性能。

W62输入域审计补充：当前结构化中文工程代理304行仅71全部有中文name，233行有英文码回退；这进一步限制中文代理成绩的解释。完整分母与版本说明见`docs/algorithm/CHINESE_RENDER_COVERAGE.md`，不是临床评测，运行时未改。

## 启动与入口

已有环境下在PowerShell运行（启动后才可访问，本文没有启动服务）：

```powershell
Set-Location -LiteralPath 'D:\wenxvn(2)\AIC\changyi'
& .\.venv\Scripts\python.exe -m flask --app app:app run --host 127.0.0.1 --port 5002 --no-reload
```

本地验收页：分诊 [triage](http://127.0.0.1:5002/triage)、资源 [resources](http://127.0.0.1:5002/resources)、地图 [map](http://127.0.0.1:5002/map)、可信度 [trust](http://127.0.0.1:5002/trust)。版本 [health](http://127.0.0.1:5002/api/v1/health)、证据 [evidence](http://127.0.0.1:5002/api/v1/evidence)。

W50 Flask client六入口均200，HTML/JSON类型正确；快照`evaluation/core_exploration/results/website-acceptance-entry-v1.json`含schema3身份。它不是运行中服务、网络/浏览器或临床测试。

## 当前已证实工程版本

**W83最新产品（2026-10-04）**：`legacy-2026.09-qualified-exclusion-scope-v6.7`、aux v3.8，807pytest（156.95s）、82浏览器（57.3s）、Safety142指标不变，front17/typecheck/build。有限未实现排除动作修饰不作病阴性，恢复旧急症优先，保完成/真否认/历史；只限已登记词法范围，非临床排除语言全覆盖。以下为历史阶段。

**W81最新产品（2026-10-04）**：`legacy-2026.09-completed-exclusion-facts-v6.6`、aux v3.8，795pytest（153.10s）、81浏览器（53.8s）、Safety142指标不变，front17/typecheck/build。完成排除的病名不作已知病，前否定/未来不误作完成；原W79全8新复验0、旧失败保留。仅用户事实解析，非临床排除/校准证明；以下均历史阶段。

**W80最新产品（2026-10-04）**：`legacy-2026.09-unresolved-exclusion-risk-v6.5`、aux v3.8，785pytest（149.38s）、80浏览器（52.8s）、Safety142指标不变，front17/typecheck/build。未能/尚未排除危急病不当阴性，恢复既有ER策略；真否认与历史控制保持。已完成排除病名事实仍有2项待修，非临床验证结论；以下为历史阶段。

**W78最新产品（2026-10-04）**：`legacy-2026.09-provisional-report-facts-v6.4`、aux v3.8，777pytest（95.25s）、79浏览器（47.7s）、Safety142指标不变，front17/typecheck/build。暂定报告病名不作已知病事实，另一真实已诊优先；不能排除强危险仍原ER、原文确认闭环保持。所有确认仍用户自述非医生核验，更宽中文与临床校准未完成；以下为历史阶段。

**W76最新产品（2026-10-04）**：`legacy-2026.09-considered-disease-facts-v6.3`、aux v3.8，766pytest（93.36s）、78浏览器（45.1s）、Safety142指标不变，front17/typecheck/build。考虑病名不作已知病事实，另真实已诊病优先；原等级/字典/模型不变。首次浏览器错配响应失败原件保留，匹配确诊确认请求后完整78过，新final-verification包含身份/logSHA。用户确认不是医生核验，以下为历史阶段。

**W74最新前端（2026-10-04）**：资源同ID详情不再随晚到目录对象清空，10受控/20照片回退重复与完整77浏览器（43.6s）通过，front17/typecheck/build。新源码/产物/日志身份见website-w74-detail-verification.json，后端/data同W73，756pytest/142Safety为W73证据、本轮不重测。目录API与Trust均21条，未造假设中的11条缺口；以下为历史阶段。

**W73最新验证（2026-10-04）**：756pytest（92.05s）、76浏览器（44.6s）、Safety142指标不变，front17/typecheck/build。医疗仍v6.2/aux3.8；Trust主卡97.30%已标随机切分症状编码分类，不代表中文临床/严格隔离结果，来源SHA与元数据核对、未知时待核对。指标/模型不改，实际标签/日志/身份见website-w73-metric-source-verification.json。以下为历史阶段。

**W72最新产品（2026-10-04）**：`legacy-2026.09-copula-existence-confirmation-v6.2`、aux v3.8，750pytest（91.99s）、76浏览器（45.0s）、Safety142指标恢复无FN，front17/typecheck/build通过。5个登记cue的“是不是”按存在未知确认，原胸痛诊断担忧/实际报告优先保留。首宽实现固定案例FN1版本明确不接受、失败原件保留；仅缩范围后的after-v2为本次验收。W71范围披露保留，以下均历史阶段。

**W71最新前端（2026-10-04）**：Trust纠正模型数据与城市资源目录混淆，明确非中文临床科室准确率；原指标不改。最终75浏览器（43.3s）、front17/typecheck/build，源码/产物/日志SHA见website-w71-trust-verification.json。backend与医疗数据同W70，740pytest/142Safety为W70证据、本轮不称重测。照片scroll偶发detach原件保留、复验通过但根因未修；下方为历史阶段。

**W70最新产品（2026-10-04）**：`legacy-2026.09-gated-department-publication-v6.1`、aux v3.8，740pytest（95.20s）、75浏览器（43.6s）、Safety142指标不变，front17/typecheck/build通过。ER/INFO公共候选科室清空，INFO/null方向旁不再出现相对分普通方向；确认/急症出口与非Safety普通候选保持。数据输入与W68的31/186校验相同；以下数字均为历史阶段，中文临床泛化/校准缺口未关闭。

**W69最新产品（2026-10-04）**：`legacy-2026.09-emergency-default-direction-v6.0`、aux v3.8，733pytest（92.28s）、74浏览器（42.5s）、Safety142指标不变，front17/typecheck/build通过。急症普通全科fallback改既有急诊默认，已有具体方向保持；医院目录/120与W68医生排行抑制保持。当前数据输入与W68的31/186校验相同。临床语义/中文域/校准缺口与研究失败仍公开，下方为历史证据。

**W68最新产品（2026-10-04）**：`legacy-2026.09-emergency-doctor-publication-v5.9`、aux v3.8，727pytest（90.68s）、73浏览器（42.0s）、Safety142指标不变，front17/typecheck/build通过。急症推荐API不再执行/发布普通医生排行，医院目录与120出口保持；数据新独占校验31/186。ER普通默认全科方向仍待独立完善，核心中文验证/校准缺口与研究负结果保持公开；下方为历史阶段。

**W61最新（2026-10-04）**：`legacy-2026.09-current-existence-confirmation-v5.8`、aux v3.8，710pytest（93.75s）、72浏览器（42.2s）、Safety142指标不变，front17/typecheck/build通过。当前存在疑问走确认，独立真实危险报告仍急症优先；真实INFO→present→ER闭环通过。有限语法证据不替代临床验证，宽中文语义/泛化/校准仍P0；以下为历史阶段结果。

**W59最新（2026-10-04）**：`legacy-2026.09-cough-rule-evidence-v5.7`、aux v3.8，700pytest（91.76s）、71浏览器（40.9s）、Safety142指标不变，front17/typecheck/build通过。咳嗽后置存在未知不再从规则回退重造方向，其他真实症状/疾病与急症保持独立优先。仅有限咳嗽语法，中文临床泛化/校准仍P0；下方为历史阶段证据。

**W58最新（2026-10-04）**：`legacy-2026.09-independent-self-safety-v5.6`、aux v3.8，694pytest（95.12s）、70真实浏览器（40.8s）、Safety142指标不变，front17/typecheck/build通过。独立本人呼吸危险报告不再被另一句症状问题/否认压制，3合成政策缺口恢复既有ER。限定语法非临床安全证明；后置未知规则fallback仍待完善。首UI定位器失败原件保留，最终验证身份/日志SHA见website-w58-verification-identity.json；下方数字均为历史阶段。

**W56最新更新（2026-10-04）**：风险/路线版本`legacy-2026.09-asserted-cough-route-v5.5`，aux v3.8；684pytest（92.89s）、69浏览器（41.4s）、Safety142指标未变，前端17/typecheck/build通过。现在是否/可能咳嗽不再仅凭主题词自动建立呼吸方向，当前肯定与病因未知仍保原方向。仅咳嗽直接map入口，宽路线证据与临床有效性仍P0；下方均为历史阶段数字。

**W53最新更新（2026-10-04）**：风险/追问`legacy-2026.09-current-clause-negation-v5.4`、辅助输入v3.8；677pytest（93.05s）、68浏览器（42.2s）、Safety142指标未变，前端17/typecheck/build通过。明确“没有胸痛，现在咳嗽”恢复原呼吸方向，普通并列否认保留；仅有限语法修复，独立中文临床评测仍P0。以下W51及更早数字为历史阶段证据。

**W51更新**：当前风险/追问v5.3、辅助输入v3.8，最新完整664pytest（website-w51-pytest.log）、67浏览器（website-w51-e2e.log）、Safety142指标未变，front17/typecheck/build通过。schema3 frontend身份测试已纳入本次全量。下面W48/W49数字保留阶段来源，不当作当前全量；W50六入口快照也未重写。

- 网站风险/追问版本`legacy-2026.09-risk-reconfirmation-v5.2`，辅助输入`symptom-nb-v1-asserted-input-v3.8`。
- 最新完整backend：W48 **657 pytest**，`website-w48-pytest.log`；最新完整浏览器：客户端修后 **66通过**，`website-w48-e2e-boundary.log`，不是首1失败/65通过版本。
- 固定Safety142，recall1、under/over0、FN0；仅这套固定样例。
- 前端17/typecheck/build通过，新JS`index-DLx90BFg.js` gzip108.42KB；源/入口/产物SHA在`website-w48-ui-hashes.json`。
- W49只身份机制，17针对测试通过，未重跑657/66/142，不能报662全量。真实身份预检`w49-frontend-identity-preflight`仅PREPARED，无result。
- 所有失败、中间结果、旧schema身份保留，没有远端push/deploy或新患者数据。

## 可在网站核验的流程

| 合成输入/操作 | 已验证的程序行为 | 依据 |
| --- | --- | --- |
| 持续胸痛喘不上气 | 既有急症出口、120链接、隐藏疾病候选 | 固定Safety与浏览器 |
| 我不否认呼吸困难 | 不是实际否认，恢复既有急症出口 | W43前后证据 |
| 如果我不否认呼吸困难 | 限定直接假设进入INFO确认/null方向/defer；另一分句实际急症仍优先 | W44 |
| 有咳嗽但不确定是否咳嗽 | 保未知重叠，aux拒答，不当无病 | W39 |
| 不确定为什么咳嗽 / 不确定是否现在咳嗽 | 病因疑问与存在未知区分，限定当前词不抹未知 | W40/W41 |
| 没有严重胸痛 | W51无答窄独立INFO/null/defer先确认是否当前有任何程度痛；自述none/present/unknown沿旧policy，不以程度否认推有/无或临床正确 | W45/W46/W51/R063 |
| 上例红旗unknown→present | unknown保持待确认、同ID替换、原文保持、既有ER闭环 | W48实际浏览器 |
| 已报告病/假设病 | 先风险确认，再病名来源确认；不凭未知词发用户已知病 | W47及病名回归 |

这张表是工程契约，不是患者应采取的个体诊疗建议，不可把其通过率当临床准确率。

## 真实未闭P0/P1/P2

| 优先级 | 尚需完善 | 当前边界/下一证据 |
| --- | --- | --- |
| P0 | 独立中文初诊输入域、可靠科室标签、完整覆盖 | 公开英文内部研究/中文合成代理不能替代临床中文；新研究模型仍RESEARCH_ONLY；不导入身份/病历 |
| P0 | 校准与拒答质量 | 相对候选分不是患病概率，NB posterior未经中文临床校准；选择/校准只用训练与cal，test不作调参 |
| P0 | R063限定严重/持续否认、主体/引述/明确更正语义 | aux单路径已保守复核，不等于主临床风险分级已解决；需独立语义/医疗审查，不能靠模板量闭合 |
| P0 | 其余旧别名与症状码关系 | 抽搐/胸闷隔离不认证其余映射；胸闷与dyspnea资料存在上下位关系，过度拒答代价保留 |
| P1 | 数据来源、更新时间、许可及异常 | 已保存质量报告31数据集/186 issue（本轮只读，非重新验证）；医生照片/公交/医院能力仍provisional，未升级官方/实时事实 |
| P1 | 跨环境运行与CI | Windows真实测试已过；跨平台脚本修复不等于Linux/CI当前已验证，未远端运行或部署 |
| P1 | 证据身份/构建来源 | schema3捕源/dist/配置，不能证明源确生成dist或全部模块/外部依赖；旧记录不回填 |
| P2 | 更广交互/性能与恢复覆盖 | 已有推荐请求生命周期、重试、刷新、移动布局、照片降载证据；更多设备/低带宽与长期运行不等于当前全部覆盖 |

研究历史见`docs/algorithm/CORE_EXPLORATION_REPORT.md`；当前变更与未闭风险以`docs/status/current.md`、`docs/risks/register.md`、`docs/algorithm/WEBSITE_CONTINUATION.md`为准。自动任务仍15分钟ACTIVE，直到用户验收或明确停止，不能因一个批次完成自行暂停。
