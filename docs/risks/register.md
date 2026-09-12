# 风险登记表

更新时间：2026-09-12

| ID | 风险 | 影响 | 可能性 | 状态 | 缓解与触发动作 |
| --- | --- | --- | --- | --- | --- |
| R-001 | 用户把模型/分诊结果误解为诊断；固定样例通过不等于临床安全，仍可能存在未覆盖的红旗表达和信息不足场景 | 严重 | 高 | 开放 | 已建立四态状态契约、v1 safety-first abstain 和 135-case Safety Set；当前固定样例 Red Flag Recall 1.0、Under-triage Rate 0.0、Emergency False Negative 0、Over-triage Rate 0.0312（question-form 过触发已登记）；保留免责声明、红旗优先、专业复核，任何规则扩展按 `L3` 处理 |
| R-002 | 医院/医生/模型数据来源或许可证不完整 | 高 | 中 | 开放 | 医院目录已迁移到 `data/regions/320400/hospitals/catalog.json`，公开事实、派生能力和未支持字段已分开，并增加字段级 provenance；医生照片 provenance 为 v2（`public_url` ≠ `original_source_url`，多为 LEGACY_EXACT_MATCH）；目录保持 `provisional`，没有来源、许可和更新时间说明的数据不得升级为正式事实 |
| R-003 | 测试反馈、日志或未来接入带入真实患者信息 | 严重 | 中 | 开放 | 只收集最小必要字段，默认脱敏；禁止秘密和 PHI 进入 Git、快照、日志和 memory；F11 历史默认关闭且只允许用户主动开启的状态摘要 |
| R-004 | 自动化覆盖不足导致单体拆分引入静默回归 | 高 | 高 | 开放 | 已建立 143 个 pytest、稳定 canonical snapshot、Safety Evaluation、v1 API contract、推荐/Safety-first publication/cache/资源详情/应用 service/Grouped CV/provenance schema/visit intent/routing preferences/import pipeline 测试、17 个 frontend boundary tests、5 个 Playwright smoke tests 和 CI workflow；继续补无障碍边界，远端 workflow 首次运行后再评估风险 |
| R-005 | 推荐排序、交通可达性与展示数据边界混淆 | 高 | 中 | 开放 | 已先抽取 scoring、医院 feature/单候选组合、医院候选遍历、医院 rerank、医生 resource policy、candidate 过滤/医院命中/急症资格/急症医生遍历、医院/急症评分/result builder、Recommendation Application Service 和 traffic feature/index/计算、cache seam 纯函数；交通数据加载与刷新策略、急症整体排序仍需服务化，记录输入输出；分别测试“展示”和“参与排序”的数据 |
| R-006 | 静态资源体量大、更新和发布成本高 | 中 | 中 | 观察 | 已删除旧 Leaflet/legacy UI 和 backup logo；保留医院/医生数据管线使用的正式资源，后续仍需盘点许可证和发布体量 |
| R-007 | 演示登录和 CORS 被误认为生产安全措施 | 严重 | 中 | 开放 | 在文档和 UI 中保持演示标识；生产化需单独 `L4` 认证/授权/部署计划 |
| R-008 | 硬编码规则和数据常量使变更不可审计 | 高 | 高 | 开放 | 先建立规则/数据清单，再逐步外置；每次权重、阈值和模型版本变化写 ADR |
| R-009 | 外部爬取内容过期、错误或带有不一致字段 | 高 | 中 | 开放 | 保留抓取时间和来源 URL，数据加载时做 schema 检查，异常数据降级并记录 |
| R-010 | 项目 skills 未纳入版本控制，跨会话规则可能丢失 | 中 | 中 | 待确认 | 在首次工作流提交前决定是否将 `skills/` 纳入仓库；若不纳入，记录外部来源和同步方式 |
| R-011 | 质量报告暴露公交占位年份、时间先后异常 | 高 | 高 | 开放 | h6 COUNT_MISMATCH 已解决；剩余 186 个问题（PLACEHOLDER_TIMESTAMP/TIME_ORDER）只读不修复；按数据集补来源、口径和校验规则，未通过 quality gate 不进入正式推荐事实 |
| R-012 | v1 endpoint 曾依赖 legacy adapter，切换时可能产生 handler 漂移 | 中 | 中 | 已完成 | v1 blueprint 已直接读取组合根注册的 canonical handler；删除 lazy import、旧 `/api/*` route 后，v1 contract、canonical snapshot 和全量 pytest 通过 |
| R-013 | 浏览器本地历史可能被误解为账号/病历，或在共享设备上被他人看到 | 高 | 中 | 开放 | F11 不提供身份字段；历史默认关闭，最多 8 条脱敏状态摘要，页面声明“仅保存在当前浏览器”并提供二次确认清除；账号/云同步前必须另立 L4 隐私评审 |
| R-014 | 未知位置被静默解释为具体区域，造成虚假距离和排序 | 高 | 中 | 已缓解 | v1 使用 `unknown`、`district` 和 `geolocation` 明确区分；未知位置返回 null 距离并将距离/交通/公平性权重置零，区域只使用显式参考点，保留位置契约回归 |
| R-015 | 系统 Follow-up 问题和答案污染用户原始症状，导致重复分析或不可审计 | 高 | 中 | 已缓解 | `original_condition` 只保存用户输入；答案使用 `question_id` + `value/text_answer` 结构化传递，问题展示为 label/value；保留 red-flag `present/none/unknown` 安全回归 |
| R-016 | 疾病模型 random split 因相同症状集合跨集合而高估指标 | 高 | 高 | 已缓解 | 生成 `evaluation/model/split_manifest.json` 与 grouped fingerprint 报告，同时展示 random baseline、严格近重复隔离（24 样本/8 类/跨 split 0）、5-fold Grouped Near-Duplicate CV（跨 split 近重复 0，覆盖 41/41 类，mean Top-1≈0.084）和近重复审计；严格隔离/CV 指标不可与随机切分横向等价比较；指标仍是小样本 prototype/offline evidence，不代表临床验证 |
| R-017 | 医院硬编码评分、容量或评级缺少来源却参与推荐 | 高 | 中 | 已缓解 | 医院目录移出组合根；公开事实、provisional 派生能力、unsupported null 分开登记，并补充字段级 provenance；缺失的 beds/daily_outpatients/rating/description 不进入公开事实或排序；`derived_capability_scores`/`strength_scores` 仅保留用于 migration/debug，正式 clinical ranking 只依赖公开科室存在事实；Trust Center 展示限制 |
| R-018 | 科研产出（SCI/基金/专利）被误当作临床适配证据主导医生推荐 | 高 | 中 | 已缓解 | academic patient-fit 权重设为 `0.00`，资源层级不依赖学术指标，回归测试证明仅改变 academic 不改变 patient-fit；学术资料仍可展示，展示 ≠ 推荐依据 |
| R-019 | 第三方地图瓦片失效导致地图页不可用或显示水印瓦片 | 中 | 中 | 已缓解 | 底图切换为无需 Key 的 OpenStreetMap 官方瓦片；失败时保留医院列表、坐标 marker、资料预览和高德导航降级 |

## 近期优先级

1. R-001、R-003、R-004：直接影响安全和重构可靠性。
2. R-002、R-005、R-008、R-009：影响推荐可信度和可审计性。
3. R-006、R-007、R-010：在发布、生产化或协作扩展前处理。
