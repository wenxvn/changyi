# 当前项目状态

更新时间：2026-09-10

## 总体状态

- 状态：进行中，P2-S3 推荐边界与竞赛前端 F0/F1/F2、Triage/Follow-up/Result、F7/F8 Resources、资源详情、F9 Map、F10 Trust、Frontend CI 首版已完成，待继续正式急诊路径与远端 CI 复核
- 当前阶段：竞赛迁移 Phase 3（parallel frontend foundation、核心就医流程、资源与可信证据首版）
- 当前分支：`main`
- 基线提交：`b8eafec`（上一轮推荐边界已提交；本轮前端与 summary 变更尚未提交）
- 本次工作流文件：已创建，当前变更尚未提交

## 已完成

- Git 仓库已初始化并推送到远端 `main`。
- 建立根级协作规则、项目章程、当前架构说明、ADR、历史、进度、风险和质量门禁。
- 读取并纳入项目已有的 `architect`、`imprint`、`recover`、`remember`、`review` skills。
- 明确医疗辅助、数据治理、渐进式拆分和会话交接边界。
- 建立竞赛工作区：产品、目标架构、数据溯源、模型/安全卡、评估、评分、演示、发布和迁移计划。
- 建立 `320400` active Region Pack；未来城市仅登记为未连接状态。
- 建立 `JsonDataLoader`、RegionRegistry、医生/交通 repositories 和应用配置工厂。
- 将旧推荐入口的组合逻辑收敛到一个 helper，并新增 `/api/v1` triage、followups、recommendations、hospitals、doctors 外壳。
- 建立 `data_validation`，输出带 SHA-256 和异常明细的 JSON/Markdown 质量报告。
- 将医院解析脚本改为显式输入/输出 CLI，移除 Windows 绝对路径依赖。
- 建立 `requirements-dev.txt`、pytest 配置、模型加载/降级 smoke 测试和 `.github/workflows/quality.yml` 质量门禁。
- 将口语症状归一化、否定窗口判断和兼容常量抽取到 `backend.app.domain.medical_input`，保留 `app.py` 旧名称并新增输入边界反例测试。
- 建立 `TriageStatus` 四态枚举、`SafetyGateDecision` 和 `evaluation/safety` 评估集；v1 状态映射已改为调用 domain，未改变既有红旗规则或 API 字段。
- `/api/v1` 急症/信息不足公共输出已接入 Safety-first abstain：不公开疾病候选，急症不公开普通追问；脱敏发布纯函数已抽取到 `backend.app.domain.triage.publication`，legacy `/api/*` 保持兼容，未改变旧快照。
- 将推荐共用的数值、文本、科室关系、医生职称和内部资源分层纯函数抽取到 `backend.app.domain.recommendation.scoring`，保留 `app.py` 兼容名称，推荐快照不变。
- 将医院能力、可用性、质量、连续照护、特殊人群适配、风险惩罚和解释纯函数抽取到 `backend.app.domain.recommendation.features`，保留推荐快照和 API 行为。
- 将医院候选基础排序、区域多样性和普通场景三甲数量约束抽取到 `backend.app.domain.recommendation.pipeline`，急症旁路保持原行为。
- 将医院 feature 的权重组合、风险惩罚和 feature snapshot 组装抽取到 `backend.app.domain.recommendation.scoring`，保留 legacy 兼容调用。
- 以 ADR-0004 固化推荐 domain 的显式输入边界和渐进式拆分策略。
- 将医生基础 feature 的权重组合、可用性/连续照护/历史 `fairness` 加权和专长加成抽取到 `backend.app.domain.recommendation.scoring`，保留资源错配与专家策略在 legacy。
- 将医生就诊资源策略、专家偏好修正和资源错配惩罚抽取到 `backend.app.domain.recommendation.resource_policy`，保留候选循环和急症兜底在 legacy。
- 将医生普通候选的解释生成、分数快照和结果对象组装抽取到 `backend.app.domain.recommendation.candidate`，并抽取急症兜底结果组装；急症候选筛选与分数计算仍在 legacy。
- 将医生查询词构建、科室关系过滤、无科室关键词召回和医院科室命中/强项回退抽取到 `backend.app.domain.recommendation.candidates`。
- 将交通摘要、展示字段、医院可达性 score、样本行索引和四类医院样本计算抽取到 `backend.app.domain.recommendation.traffic`，保留数据加载与缓存生命周期在 legacy。
- 将医院普通候选的单候选 feature/score/explain/result 组合、急症医生兜底评分和结果字典组装抽取到 `backend.app.domain.recommendation.candidate`，保留医院遍历、样本生成、急症候选筛选与整体排序在 legacy。
- 将急症医院兜底资格判断抽取到 `backend.app.domain.recommendation.candidates`，并将急症医生兜底候选遍历抽取到 `backend.app.domain.recommendation.candidate`，保留整体排序在 legacy。
- 将医院候选遍历和交通 ranking policy 上下文准备抽取到 `backend.app.domain.recommendation.candidate`，通过显式回调连接 legacy 数据、交通和单候选组合，保留 rerank 在兼容入口。
- 建立 React/TypeScript/Vite 并行前端，使用 strict 类型、集中 API client、运行时响应校验和不依赖全局 `window._*` 的页面状态。
- 建立 `/api/v1/summary` 只读摘要契约：首页城市指标由当前运行数据计算，并携带 Region Pack、来源类别和迁移状态。
- 完成新 App Shell、响应式 Top Navigation、Warm Precision tokens、Brand Mark、Care Path Visual、Editorial Homepage、手动 AI Journey、城市智能层、Trust CTA 和最小 Triage Workspace 首步；legacy `/` 未切换。
- 完成 Triage/Follow-up/Result 首版：一次一个追问、Current Understanding、Routine/Urgent 资源路径、Emergency 独立安全结果、120 入口和推荐失败/空态；状态由 `/api/v1` 返回，Emergency 不请求普通推荐。
- 完成 F7/F8 Resources 首版：医院索引首屏加载、医生索引按 tab 懒加载、医院/医生关键词筛选、来源状态、资料预览和地图入口；未把 pending provenance 包装成官方资料。
- 完成资源详情首版：新增 `/api/v1/hospitals/<id>`、`/api/v1/doctors/<id>`，后端通过公开字段白名单和显式 provenance 返回详情；前端按选择加载详情并提供 loading/error/retry。
- 完成 F10 Trust 首版：新增只读 `/api/v1/evidence`，统一提供 Safety Evaluation、模型离线指标、数据质量、SHA-256、运行版本和已知限制；前端 `/trust` 从 API 渲染并明确标注 provisional/不代表临床验证。
- 完成 F9 Map 首版：新增只读 `/api/v1/map`，从医院坐标构建资源位置示意、列表/marker 联动、含急诊字段筛选和资料预览；默认不请求定位，不把直线距离或急诊字段包装成导航/实时可用性。
- 完成 Frontend CI 首版：GitHub Actions 新增独立 frontend job，使用 Node 22、lockfile 安装并运行 typecheck、边界测试和 production build；远端首次运行仍待推送确认。

## 当前基线

| 领域 | 当前情况 | 证据 |
| --- | --- | --- |
| 后端 | Flask 单体，约 3,172 行 | `app.py` |
| 前端 | 单体 JS，约 4,351 行 | `static/js/app.js` |
| 样式 | 单体 CSS，约 7,174 行 | `static/css/style.css` |
| 并行前端 | React/TypeScript/Vite；API client、tokens、Homepage、Triage/Follow-up/Result、Resources、Map、Trust 首版已建立 | `frontend/`、`docs/competition/2026-ai-medical/FRONTEND_ARCHITECTURE.md` |
| 数据 | 本地 JSON/CSV/模型和图片；11 份医生 JSON、2,100 条 | `data/`、`static/images/` |
| 依赖 | runtime/dev/data-tools 三层；运行时仍为 Flask、Flask-CORS | `requirements*.txt` |
| 测试 | 89 个 pytest 测试；API smoke、Safety Evaluation 和推荐快照已单独运行 | `tests/`、`pyproject.toml`、`evaluation/safety/` |
| CI | GitHub Actions 已覆盖 Python 矩阵、数据/模型/Safety/快照和 frontend typecheck/test/build；远端首次运行待推送后确认 | `.github/workflows/quality.yml` |
| 认证 | 演示登录，非生产认证 | `templates/index.html`、`static/js/app.js` |
| UI 规范 | legacy 基线已确认；新前端 token、App Shell、Homepage、Care Path、Journey、Triage、Resources、Map、Trust 模式已登记 | `ui-registry.md`、`frontend/src/styles/tokens.css` |

## 当前未解决问题

- API 和关键纯函数已有可重复的字段快照；输入归一化/否定边界已有测试，但模型不可用、低置信度和更多红旗反例仍需扩展。
- 推荐的交通数据加载、缓存接入和急症整体排序仍在同一后端文件内交织；医院候选遍历和急症医生候选遍历已通过显式回调抽取；医院/医生 scoring、医院 feature、医院候选单项组合、医院 rerank、医生资源策略、candidate 过滤/医院命中/急症资格、交通样本索引/计算、缓存生命周期、医院/医生/急症兜底评分与 result builder、Safety-first publication 和 v1 legacy adapter 已先行抽取。
- legacy 前端仍依赖全局 `window.*` 状态，页面控制、API 请求和渲染耦合较高；新前端已建立独立状态边界，Triage/Follow-up/Result 首版可用，但尚未完成与 legacy 的完整 route/Safety parity。
- 数据来源、许可证、更新时间和版本口径需要进一步补全。
- 生产级认证、授权、审计、隐私和部署安全尚未实现。
- 数据质量报告当前有 187 个异常，主要为公交疑似占位年份、6 条时间先后异常和 h6 计数不一致；未自动修复。
- 医院目录仍是 `app.py` 常量，逐字段 provenance 尚未完成；v1 医院读取接口明确标记为 pending。
- v1 路由已由 blueprint 统一注册，独立 factory 与 `app.py` 兼容入口均可访问；其业务实现仍通过独立延迟 legacy adapter，完整 legacy route parity 仍待后续拆分。医学输入和 Safety Gate 状态契约已有 domain 边界，v1 已在发布层保护急症候选展示，但红旗规则和 follow-up 组合逻辑仍在 legacy；新前端当前以补充文本重新提交既有 follow-up 契约，尚无结构化答案接口。
- legacy UI 已完成一次 localhost desktop 运行态 audit；新前端首页已在 1440×900、1280×800、768×1024、390×844 检查，Triage/Follow-up/Result、Resources/详情、Map 和 Trust 首版已在 desktop、390×844 检查。独立截图 baseline、完整核心流程矩阵和 legacy 静态资源 404 修复仍待后续切片。

## 本次验证

- 文档路径检查：通过。
- Python 语法编译：通过（`app.py`、脚本和症状模型模块）。
- JavaScript 语法检查：通过（`node --check static/js/app.js`）。
- 新前端：`npm run typecheck`、`npm run test`（6/6 边界测试）、`npm run build` 通过；Map/Trust/资源详情切片最新构建产物 gzip 约 JS 84.8 kB、CSS 12.3 kB。
- 新增 `/api/v1/summary`：health/summary/regions、triage 正常与非法输入 smoke 通过；summary 数值来自运行数据，医院来源仍标记 `migration_pending`。
- 浏览器：首页四个目标 viewport 均可加载，无横向溢出；Triage 在桌面/移动端支持连续追问、跳过并读取医院路径；Routine、Urgent 和 Emergency 结果均已运行态检查，Emergency 不显示普通医院路径并提供 `tel:120`；Resources 已检查医院索引、医院/医生切换、关键词筛选、资料预览和 390×844 无溢出；console error/warning 为空。
- Flask smoke test：系统 Python 仍缺少 Flask；使用 `uv run --with flask --with flask-cors` 临时环境通过 health/ready/regions、v1 triage/recommendations、旧推荐入口、400 和 404 边界。
- 最终 API 主 smoke：11/11 通过，另加空输入 400 与未知路径 404 边界检查 2/2 通过；急症样例的 v1 `triage_status=EMERGENCY`，候选疾病和普通追问已 abstain，红旗与急诊文案保留。资源详情成功/404/字段白名单 smoke 通过；最新全量 pytest 89/89 通过。
- Safety Evaluation Set：16 个 case；Red Flag Recall `0.9231`、Under-triage Rate `0.0769`、Over-triage Rate `0.0`、Emergency False Negative `1`；`colloquial-breathlessness` 和 `vague-discomfort` 等已知缺口保留为 `review_required`，不视为发布放行。
- Trust evidence smoke：`/api/v1/evidence` 200；返回 `provisional`、16 个 Safety Case、41 个模型类别、27 个数据集条目、187 个已登记质量问题；浏览器 desktop/390×844 可见真实 API 数据、版本和限制。
- Map smoke：`/api/v1/map` 默认 200 返回 21 个坐标资源，带完整 `lat/lng` 返回直线距离，不完整坐标返回 400；浏览器 desktop/390×844 可见列表/marker 联动、含急诊字段筛选和资源预览。
- Resource detail smoke：医院/医生详情返回 v1 envelope、公开字段白名单和 provenance；未知 id 返回 `404 RESOURCE_NOT_FOUND`；浏览器 desktop/390×844 可见详情按选择加载、来源登记、加载态和错误重试边界。
- 表征快照：连续运行两次 SHA-256 均为 `f25776066ed2c9664fadffec2b34a71e11bd28e7c232c87780081e41aa0bac9d`。
- 数据质量：`python3 -m data_validation.validate_datasets --data-root data --output-dir data_validation`，扫描 27 个文件、发现 187 个异常；报告已生成，未以 strict 作为放行门。

## 下一步

1. 补正式地图/附近急诊路径，再扩展医院/医生逐字段 provenance 和正式发布审核。
2. 在已接入 frontend CI 的基础上，建立 Playwright smoke、关键页面截图 baseline、keyboard/contrast/reduced-motion 矩阵，并等待远端 job 首次结果。
3. 继续 P2-S3/P2-S4：拆出医院/急症 candidate 遍历、应用服务层和完整 API route parity；交通 cache 的刷新/一致性另立计划，保持推荐快照。
4. 在医学审核后处理 Safety Evaluation 的 1 个 under-triage 和信息不足缺口；规则修改需另立 L3 计划/ADR。
5. 为医院目录补逐字段来源/许可/时间/脱敏元数据，再考虑激活正式资源。
6. 推送后确认 GitHub Actions 首次运行并记录远端结果。

## 阻塞与需要确认

当前没有必须阻塞实施的问题。以下事项会在对应阶段需要用户或领域审核者确认：

- 哪些医院/医生数据可以正式发布，哪些只能用于演示。
- 红旗症状和分诊等级的医学审核口径。
- 是否需要生产化认证、数据库和外部部署。
