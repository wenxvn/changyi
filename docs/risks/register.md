# 风险登记表

更新时间：2026-09-11

| ID | 风险 | 影响 | 可能性 | 状态 | 缓解与触发动作 |
| --- | --- | --- | --- | --- | --- |
| R-001 | 用户把模型/分诊结果误解为诊断；固定样例通过不等于临床安全，仍可能存在未覆盖的红旗表达和信息不足场景 | 严重 | 高 | 开放 | 已建立四态状态契约、v1 safety-first abstain 和 38-case Safety Set；当前固定样例 Red Flag Recall 1.0、Under-triage Rate 0.0、Emergency False Negative 0，新增胸痛/呼吸困难口语回归和笼统输入降级；保留免责声明、红旗优先、专业复核，任何规则扩展按 `L3` 处理 |
| R-002 | 医院/医生/模型数据来源或许可证不完整 | 高 | 中 | 开放 | 建立数据清单和 provenance 元数据；没有来源和权限说明的数据不得升级为正式事实 |
| R-003 | 测试反馈、日志或未来接入带入真实患者信息 | 严重 | 中 | 开放 | 只收集最小必要字段，默认脱敏；禁止秘密和 PHI 进入 Git、快照、日志和 memory；F11 历史默认关闭且只允许用户主动开启的状态摘要 |
| R-004 | 自动化覆盖不足导致单体拆分引入静默回归 | 高 | 高 | 开放 | 已建立 108 个 pytest、稳定 canonical snapshot、Safety Evaluation、v1 API contract、推荐/Safety-first publication/cache/资源详情/应用 service 测试、15 个 frontend boundary tests、5 个 Playwright smoke tests 和 CI workflow；继续补无障碍边界，远端 workflow 首次运行后再评估风险 |
| R-005 | 推荐排序、交通可达性与展示数据边界混淆 | 高 | 中 | 开放 | 已先抽取 scoring、医院 feature/单候选组合、医院候选遍历、医院 rerank、医生 resource policy、candidate 过滤/医院命中/急症资格/急症医生遍历、医院/急症评分/result builder、Recommendation Application Service 和 traffic feature/index/计算、cache seam 纯函数；交通数据加载与刷新策略、急症整体排序仍需服务化，记录输入输出；分别测试“展示”和“参与排序”的数据 |
| R-006 | 静态资源体量大、更新和发布成本高 | 中 | 中 | 观察 | 已删除旧 Leaflet/legacy UI 和 backup logo；保留医院/医生数据管线使用的正式资源，后续仍需盘点许可证和发布体量 |
| R-007 | 演示登录和 CORS 被误认为生产安全措施 | 严重 | 中 | 开放 | 在文档和 UI 中保持演示标识；生产化需单独 `L4` 认证/授权/部署计划 |
| R-008 | 硬编码规则和数据常量使变更不可审计 | 高 | 高 | 开放 | 先建立规则/数据清单，再逐步外置；每次权重、阈值和模型版本变化写 ADR |
| R-009 | 外部爬取内容过期、错误或带有不一致字段 | 高 | 中 | 开放 | 保留抓取时间和来源 URL，数据加载时做 schema 检查，异常数据降级并记录 |
| R-010 | 项目 skills 未纳入版本控制，跨会话规则可能丢失 | 中 | 中 | 待确认 | 在首次工作流提交前决定是否将 `skills/` 纳入仓库；若不纳入，记录外部来源和同步方式 |
| R-011 | 质量报告暴露公交占位年份、时间先后异常和医生计数不一致 | 高 | 高 | 开放 | 报告只读不修复；按数据集补来源、口径和校验规则，未通过 quality gate 不进入正式推荐事实 |
| R-012 | v1 endpoint 曾依赖 legacy adapter，切换时可能产生 handler 漂移 | 中 | 中 | 已完成 | v1 blueprint 已直接读取组合根注册的 canonical handler；删除 lazy import、旧 `/api/*` route 后，v1 contract、canonical snapshot 和全量 pytest 通过 |
| R-013 | 浏览器本地历史可能被误解为账号/病历，或在共享设备上被他人看到 | 高 | 中 | 开放 | F11 不提供身份字段；历史默认关闭，最多 8 条脱敏状态摘要，页面声明“仅保存在当前浏览器”并提供二次确认清除；账号/云同步前必须另立 L4 隐私评审 |

## 近期优先级

1. R-001、R-003、R-004：直接影响安全和重构可靠性。
2. R-002、R-005、R-008、R-009：影响推荐可信度和可审计性。
3. R-006、R-007、R-010：在发布、生产化或协作扩展前处理。
