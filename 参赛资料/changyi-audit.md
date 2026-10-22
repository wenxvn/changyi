# 常医智导：2026 AIC AI+医学参赛审计

审计日期：2026-10-02（北京时间）  
代码目录：`D:\wenxvn(2)\AIC\changyi`  
仓库：<https://github.com/wenxvn/changyi>  
审计版本：`main` / `e82447c8e6eef26eccaaf328e2c158d6f23472bf`  
范围：比赛规则、现有代码与证据、Windows 复现、核心业务与浏览器回归。运行时源码及已提交实验结果保持原样；审计产物独立于仓库。

## 结论

当前工程基线可演示，本机复现了 215 个 Python 测试、17 个前端测试和 26 个浏览器用例。初赛交付仍存在阻断项；算法证据另有本轮新发现的模型口径错误，不能仅凭测试全绿发布原有研究结论。

本轮共登记 **P0 4 项、P1 7 项、P2 3 项**。P0 表示在提交或引用对应结论前必须处理；P1 表示显著影响评分、可信度或复现；P2 表示已隔离的数据债务与后续维护事项。算法研究问题与当前线上规则分诊问题分开定级。

## 官方要求

来源：[赛道官网](https://www.aicomp.cn/tracks/4723.html)及同目录 `official-rules.pdf`（从官网附件取得，全文与两页渲染已核对）。

- 报名与初赛作品提交截止：**2026-10-15 20:00**。截至审计日，距离截止为 13 个日历日。
- 开放式 AI+医学主题赛，以技术报告呈现；初赛检查材料完整性、主题与科技伦理。
- 作品名不超过 20 字；简介不超过 300 字。
- 技术报告按官方模板编写，正文不超过 8000 字（附录除外），PDF 不超过 10 MB。
- 答辩 PPT 为 PDF；佐证材料合并为一个 PDF。
- 演示视频为“若有”：MP4，3–5 分钟，不超过 300 MB。视频缺失单独列为 P1 演示准备项。
- 作品方案、视频、PPT 等均不得含学校名、LOGO 和指导教师信息。
- 代码等其他大材料按规定命名，提交永久有效的百度网盘分享链接与提取码。
- 引用的技术、算法、数据要明确注明，并有合法使用依据；原创性与材料真实性为资格要求。
- 评分：创新 20、需求背景 15、AI 技术 20、实施规范 20、成效 15、总结展望 10，附加分最多 5。

官方模板：[百度网盘模板](https://pan.baidu.com/s/16FpEasklPEoVL1EqBjc4yg?pwd=2026)。本轮未进入报名账号，也未验证团队报名、缴费、平台提交回执或仓库外已有材料；下面的材料缺失结论限定于此次克隆的仓库。

## P0：提交与证据阻断项

### P0-01 选择性拒答与鲁棒性评测混用了不同模型；已提交证据也不一致

**本轮新发现，优先处理。**

- [direct_department.py:227](<D:/wenxvn(2)/AIC/changyi/evaluation/care_routing/direct_department.py:227>) 的 char/fusion LR 使用 `epochs=35, lr=0.35`，这里产生 test 预测和温度。
- [selective_routing.py:188](<D:/wenxvn(2)/AIC/changyi/evaluation/care_routing/selective_routing.py:188>) 又用 `epochs=70, lr=0.4` 重训 cal 模型；190 行用它计算 cal 分数，191 行却使用前一个模型的 test 分数。
- 温度取自前一个模型，随后施加到重训模型的 cal 分数上。由模型 B 的校准分数确定阈值、再用模型 A 的 test 分数评估，破坏了同一预测器的校准/拒答协议。
- [round4_robustness_safety.py:46](<D:/wenxvn(2)/AIC/changyi/evaluation/care_routing/round4_robustness_safety.py:46>) 有相同问题：clean 使用矩阵模型，扰动预测使用另一份重新训练的模型。clean 与 perturbed 的差值混入了模型变化。
- 小型调用探针实际捕获了两组训练参数，见 `audit-probes.json`。探针仅使用构造样例，在内存中验证调用，没有写入模型权重。
- 已提交 seed42 char 模型 raw/temperature Accuracy 都为 **0.737089，T=0.5**；同名同 seed 的 selective 全覆盖 Accuracy 却为 **0.624413，T=0.7**。全覆盖且无拒答时，温度缩放不应改变同一模型的 argmax 准确率；这显示结果文件未统一到同一模型版本。

影响：现有 0.807/0.838/0.873 retained Accuracy、risk–coverage 与鲁棒性结论，在修复和重新生成前不能作为当前版本同一预测器的可靠证据。该问题位于离线研究包；未发现它接入当前正式 `/api/v1`。

验收：cal/test/clean/perturbed 复用同一个拟合模型与训练期特征转换；温度只在 cal 上拟合；阈值只来自该模型的 cal 分数；阈值 0 时 selective 全覆盖准确率等于同模型 raw/temperature 准确率；统一重跑结果、矩阵、索引、CSV 和引用文稿。补充能检测模型身份与全覆盖一致性的回归，再复核 Safety。不要仅修改 JSON 数字。

### P0-02 初赛正式交付包尚未产出

仓库有比赛计划、台本和内部文档，未检出正式提交的技术报告 PDF、PPT PDF、佐证 PDF 或完整 submission 目录，也未检出 MP4/PPTX/PDF 成品。旧 `SUBMISSION_GAP.md` 引用的本地临时 PPT 不在此次 Git 克隆中。

影响：缺少按官方模板成文的技术方案以及有效提交材料，会阻断形式审查。仓库外可能已有成果，需要在材料阶段汇入核对。

验收：形成正式名称/300 字简介、按官方模板的报告 PDF、PPT PDF、佐证 PDF、其他材料网盘包与链接清单；按报名系统实际字段要求核对；完成匿名、字数、大小、链接可访问性检查，保存提交回执。核验团队报名、成员信息与缴费状态。

### P0-03 实际展示与打包的第三方数据、照片使用依据未闭环

- [医院目录](<D:/wenxvn(2)/AIC/changyi/data/regions/320400/hospitals/catalog.json:9>) 和 [区域 manifest](<D:/wenxvn(2)/AIC/changyi/data/regions/320400/manifest.json:20>) 仍为 `provisional`、`source_url=null`、`license_status=not_recorded`。
- [照片 provenance](<D:/wenxvn(2)/AIC/changyi/data/resource_provenance/doctor_photos.json:16>) 有 275 条记录，274 条 `LEGACY_EXACT_MATCH`、1 条 `MANUAL_CONFIRMED`；**275 条 license 和 original_source_url 均缺失**。目录中公开网页链接不等于图片再分发许可。

影响：官方要求明确注明引用、合法授权/使用依据。当前记录无法证明可将这些素材随参赛代码、截图、视频一并再分发；这不是对已侵权的认定。

验收：逐项给出原始来源、许可或授权、时间、用途与允许发布范围；无法证明使用依据的素材从参赛包和录屏中排除或替换为具备依据的素材；同时对模型训练数据保留原始数据卡和许可文本。来源与许可由真实证据补齐，不能用公开可下载来替代。

### P0-04 对外数字与算法能力边界需要统一

- [README.md:44](<D:/wenxvn(2)/AIC/changyi/README.md:44>) 写 Safety 135 条、Over-triage 0.0312；本机实测为 **142 条、0.0**。
- [SCORECARD.md:9](<D:/wenxvn(2)/AIC/changyi/docs/competition/2026-ai-medical/SCORECARD.md:9>) 仍为 38-case/108 pytest/5 Playwright 的旧冻结基线。
- [MODEL_CARD.md:12](<D:/wenxvn(2)/AIC/changyi/docs/competition/2026-ai-medical/MODEL_CARD.md:12>) 写尚未完成 fingerprint 防泄漏分组，与已有 grouped 报告冲突。
- `evidence_index.json` 的 Playwright 文档数仍为 20；本轮实际跑到 26。`number_drift.json` 的 pytest authoritative 仍为 206，而实际为 215。
- 正式 [TriageApplicationService](<D:/wenxvn(2)/AIC/changyi/backend/app/application/triage.py:109>) 使用既有规则分诊、Safety 和旧疾病模型辅助；char LR、Selective 和 IG 研究实现位于 `evaluation/`。UI 的阶段名称不能用来证明这些研究模型已经接入。

验收：正式材料按“网站当前能力 / 离线算法研究 / 后续计划”分别陈述；每个数字绑定算法、数据、split、seed、源码版本与证据；修复 P0-01 后再冻结研究数字；同步主要模型卡和提交文稿。142 条 Safety 指标表述为固定样例工程回归，避免写成临床验证或诊断准确率。

## P1：评分、研究质量与复现问题

| ID | 当前问题与证据 | 影响 | 验收方向 |
| --- | --- | --- | --- |
| P1-01 | 缺可核验的一手需求调研、用户任务对比和试点/转化资料；相关内容出现在缺口与计划文档中 | 需求 15 分、成效 15 分 | 汇总真实访谈/问卷的方法、样本、匿名结果；与关键词搜索/普通目录对照测任务完成、时间、错误、解释理解；可以给出可行性证据，不能将离线分类结果写成医疗疗效 |
| P1-02 | 模型覆盖和输入域不足：expanded_41 为公开文本，char 实际作用于英文症状码拼接；seed42 呼吸内科 recall 0、泌尿约 0.18；五 seed ECE 均值约 0.259，温度校准优势目前主要展示单 seed | AI 20 分及可信度 | 补独立中文口语/多症状/未知输入测试、分科室 Recall 与 Macro-F1、跨来源测试；校准按多 seed 统一评估，保留独立 test。当前保持研究状态，产品接入另作医学行为评审 |
| P1-03 | IG 自适应追问尚无真实多轮证据；诚实 split 中 IG−Random 为 −0.0625，正收益主要出现在泄漏风险较高的 random split | 创新 20 分、AI 20 分 | 以规则追问与研究 IG 分别描述；保留阴性结果；补合法、匿名、结构化问答的独立验证，比较 IG/随机/固定策略的准确率与问答成本 |
| P1-04 | Windows 原始 E2E 命令失败：[package.json:13](<D:/wenxvn(2)/AIC/changyi/frontend/package.json:13>) 使用 POSIX 变量赋值；[playwright.config.mjs:3](<D:/wenxvn(2)/AIC/changyi/frontend/playwright.config.mjs:3>) 硬编码 `.venv/bin/python` | 本机维护及评审复现 | 提供跨平台启动与 E2E 入口，明确 Windows `.venv/Scripts/python.exe` 与浏览器安装。本轮临时配置 26/26 通过仅证明绕过环境差异后交互可用，原始脚本仍需修复 |
| P1-05 | 研究证据门禁不足：[run_matrix.py:67](<D:/wenxvn(2)/AIC/changyi/evaluation/competition/run_matrix.py:67>) 将整句 readiness 文本写入 `std`，探针确认不是数值；现有 CI 只拒绝部分 grouped/质量/snapshot 漂移，未覆盖 Round4 结果一致性 | 实施规范与报告可信度 | 增加矩阵 schema 校验、std 数值类型、模型/温度/seed/split 一致性与全覆盖守恒检查；Safety 证据从真实回归结果汇入，区别描述性契约声明与实际执行 |
| P1-06 | 2090 个图片文件约 609.9 MiB，最大单张 13.1 MiB；DoctorAvatar 使用原图 URL，虽有 lazy/async，尚无尺寸变体 | 页面加载、克隆、打包、发布 | 在素材使用依据明确后生成合适尺寸缩略图/图片格式变体，核对实际引用和提交包范围；测列表加载流量。原始资产的处理需要独立保留/回滚策略 |
| P1-07 | 有三案例台本和自动化交互验收，未检出已录制视频或面向评审的演示证据包 | 演示与答辩表达 | 依据当前真实 API 录制普通、信息不足、急症三路径；若提交视频，严格满足 3–5 分钟/300 MB/匿名；清楚区分研究动画和实际功能。官方“若有”不将视频缺失单独作为资格阻断 |

算法数值除本轮 Safety/工程回归与探针外，均来自已提交研究文件；本轮没有重跑完整五 seed 算法矩阵。P0-01 涉及的派生数字需修复后重新验证。

## P2：后续维护

| ID | 当前事项 | 建议验收 |
| --- | --- | --- |
| P2-01 | `bus_routes.json` 有 180 个占位时间戳、6 个时间顺序异常，共 186 个；已隔离为 `PROVISIONAL rankable=False`，不进入正式排序 | 在上游来源可核验后补时间语义和数据更新流程；保留异常记录。当前不能将 186 个展示元数据问题算成 186 个分诊安全问题 |
| P2-02 | Python `requirements.txt` 仅设下界，未固定完整版本；此次新安装为 Flask 3.1.3/flask-cors 6.0.5，工程行为虽通过回归，评审仍可能安装其他版本 | 为冻结提交版登记 Python/Node、依赖版本和跨平台复现步骤；保留现有 npm lock；评审通过最短路径安装、启动并验收三案例 |
| P2-03 | 仓库根目录无代码 LICENSE/版权授权声明，参考文献与数据引用尚未汇总进正式报告 | 确认代码版权归属和希望授予的权限，选择相应许可/参赛授权声明；补完整相关研究与数据引用。代码缺少开源许可证本身不等于资格必然不合格，第三方素材依据见 P0-03 |

## 本轮验证结果

| 验证 | 结果 | 口径 |
| --- | --- | --- |
| Python 3.11.9 / Node 24.12.0 | 已安装本地 `.venv` 与 npm ci | 环境准备，不等于算法改进 |
| `.venv/Scripts/python.exe -m pytest -q` | **215 passed，53.25 秒** | 当前原始项目代码 |
| Safety Evaluation | **142 条、Recall 1.0、Under/Over 0、Emergency FN 0** | 固定样例工程回归 |
| 前端 typecheck | 通过 | 原始 TS 源码 |
| 前端测试 | **17 passed** | boundary/基础逻辑 |
| 前端 build | 通过 | 输出到审计临时目录；不覆盖 tracked dist |
| 原始 `npm run e2e -- --list` | **失败**，NO_PROXY 不是 Windows 命令 | Windows 脚本缺陷，已记录 P1-04 |
| Playwright（临时 Windows 配置） | **26 passed，19.9 秒** | 已安装 Chromium，1440/1280/768/390 视口；复用仓库用例，运行时未修改 |
| 数据质量 | scanned 31 / issues **186** | 输出至独立临时目录，原始数据保持原样 |
| API 与 SPA | health/ready、六页面返回 200；普通 ROUTINE、模糊 INSUFFICIENT_INFORMATION、急症 EMERGENCY；空输入 400 | Flask test client，见 `api-smoke.json` |
| 审计探针 | cal/test 训练参数不同；保存结果不一致；std 非数值；275 个照片许可缺失 | 见 `audit-probes.json` |
| 远端最新 main CI | success | [GitHub run 35977285859](https://github.com/wenxvn/changyi/actions/runs/35977285859)，与审计 commit 一致 |
| 工作区 | tracked 文件无变化，diff --check 通过 | 报告与辅助证据位于项目之外 |

仓库为 main 最新提交的浅克隆，origin 与 tracking 已设置；历史可按需补全。中断下载留下两个 `.git/objects/pack/tmp_pack_*` 文件，合计约 587 MiB。自动审批审查拒绝清理（`blocked by policy`），故保留；不影响当前 checkout，也不应被复制进参赛代码包。

## 推荐推进顺序

1. 修复 P0-01，统一预测器并重跑受影响研究，建立 P1-05 的证据一致性门禁。
2. 同时核验 P0-03 的素材/数据使用依据，明确可进入截图、视频和代码包的范围。
3. 基于有效证据统一 P0-04 的数字与能力描述，按官方模板完成 P0-02 的报告、PPT、佐证与平台材料。
4. 初赛材料阶段优先补 P1-01 的需求和成效证据，修复 Windows 复现入口，录制三案例（若提交视频），完成匿名和格式检查。
5. 完成提交回执与冻结清单；后续算法扩展、真实多轮数据、实时资源和账号能力另立任务。

本轮以审计报告作为维护接手基线；后续修改逐项关联问题 ID、验收与回滚。未经用户具体推进指令，本轮没有实施修复、改变医学规则或推送远端。
