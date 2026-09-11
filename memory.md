# Memory — 2026-09-11 Frontend and Triage Boundaries

Last updated: 2026-09-11

## What was built

- 建立 `frontend/` React/TypeScript/Vite 并行前端，包含 strict 类型、集中 API client、运行时响应校验、Warm Precision tokens、App Shell、响应式导航、Homepage、Care Path、AI Journey、Triage Workspace、Follow-up prompt 和四态结果展示。
- 新增 `/api/v1/summary` 只读摘要契约；首页城市指标从运行数据读取，同时展示 Region Pack、来源类别和医院目录 `migration_pending` 状态。
- Triage 首版已接入 `/api/v1/triage`、`/api/v1/triage/followups`、`/api/v1/recommendations`：Routine/Urgent 可回答或跳过追问后读取医院/医生资源，Emergency 独立展示红旗、`tel:120`，不请求普通推荐。
- F7/F8 资源首版已接入 `/api/v1/hospitals`、`/api/v1/doctors`：医院索引首屏加载，医生索引按 tab 加载；支持医院/医生关键词筛选、来源状态和公开资料预览；地图另有 F9 首版。
- 资源详情首版已接入 `/api/v1/hospitals/<id>`、`/api/v1/doctors/<id>`：后端公开字段白名单和 provenance，前端按选择加载详情并保留 loading/error/retry；医院内部评分/床位和医生学术/原始抓取链接未穿过新边界。
- F10 Trust 首版已接入只读 `/api/v1/evidence`：从现有 Safety Evaluation、模型 JSON、data quality report、Region Pack manifest 和配置读取事实；`/trust` 展示 provisional、离线指标、review_required、SHA-256、版本和限制，明确不代表临床验证。
- F9 Map 首版已接入只读 `/api/v1/map`：现有医院坐标生成轻量位置示意，列表/marker 联动、含急诊字段筛选、预览和可选 Haversine 直线距离；默认不请求定位，不生成推荐 marker。
- F11 Profile/History 首版已接入 `/profile`：本地演示资料、默认关闭的历史开关、最多 8 条脱敏状态摘要和二次确认清除；`demoProfile.ts` 集中处理版本化 localStorage、白名单校验和异常降级，原始描述/追问答案/身份字段不进入 history schema。
- F12 accessibility polish 首版已完成：App Shell 提供 skip link、`main-content` landmark、活动路由 `aria-current`、移动菜单 `aria-expanded`/`aria-controls`，JS 跨页滚动遵守 `prefers-reduced-motion`，input/checkbox 纳入共享 focus-visible。
- 前端键盘与交互语义收口首版已完成：共享 `Button` 默认 `type="button"`；Journey、资源和地图 tab/panel 具备显式关联，Journey 支持 Arrow/Home/End；已移除无调用路径的旧占位页。
- Triage Application Service 首版已完成：`backend/app/application/triage.py` 以注入依赖编排现有 triage → Safety Gate → Safety-first publication → model/htriage projection；`app.py` 保留 request/response 和兼容 wrapper，没有改变规则或输出。
- Recommendation Application Service 首版已完成：`backend/app/application/recommendation.py` 以 `RecommendationContext` 编排既有 triage、resource policy、医院/医生 recommenders、位置/权重/版本字段和 Safety-first publication；`app.py` 保留 legacy/v1 校验、位置解析和兼容 wrapper。
- Resource Catalog Application Service 首版已完成：`backend/app/application/resources.py` 以显式 suppliers 编排 v1 医院/医生索引、医院筛选、公开详情投影和兼容医生回退；`app.py` 只保留 query、envelope 和 404 适配。
- legacy 资源 route parity 小步已完成：旧医院/医生索引、详情、医院-医生关系、科室/区域索引和统计均复用 Resource Catalog service；旧 response shape 保持。
- 旧 triage/follow-up/assistant routes 已复用 Triage Application Service；`/api/predict-disease` 已复用 DiseasePredictionApplicationService；五类 `/api/transit/*` 与公交统计已复用 TransitCatalogApplicationService；`/api/recommend/rerank` 已复用 DistanceRerankApplicationService。均未修改业务规则、模型或数据口径。
- legacy 静态资源缺口已收口：`static/favicon.svg` 与 `static/images/leaflet-layers.svg` 已加入，template/CSS 不再引用已知 favicon/layers 404 路径；marker 默认 PNG 尚未扩大审计。
- v1 blueprint 已由 `legacy_adapter` 的 Flask extension registry 显式解析 handler，未注册时仍保留 lazy import fallback；模型 lazy loading 已移入 `SymptomDiseaseModelAdapter`。
- v1 summary、Trust evidence 和 map 只读投影已通过 `SummaryApplicationService`、`EvidenceApplicationService`、`MapViewApplicationService` 编排；保留原数据来源、provisional 限制、坐标错误码和位置示意语义。
- v1 ready/regions 已通过 `RegionReadApplicationService` 编排；`create_app` 以 extension 注册，blueprint 不直接创建 registry，`REGION_ROOT` 配置覆盖保持。
- Frontend CI 首版已加入 `.github/workflows/quality.yml`：Node 22 + `npm ci` + typecheck/boundary tests/build；远端首次运行尚待 push 后确认。
- legacy `/`、legacy API 和现有 v1 路由保持默认兼容，未切换入口。

## Decisions made

- 采用 ADR-0005 的并行迁移策略：新前端独立构建，route parity、E2E、视觉和安全门禁完成前不替换 legacy。
- 浏览器不复制医学规则；triage 状态只展示后端返回，语音入口暂时 disabled。
- UI token、组件模式和可访问性要求已写入 `ui-registry.md` 与 `frontend/docs/design-system.md`。

## Current state

- 本轮验证：frontend typecheck、Node boundary tests 9/9、Vite build（gzip JS 87.4 kB、CSS 13.1 kB）、后端语法检查、pytest 116/116、resource catalog 7/7 API smoke、prediction 3/3、transit 6/6、catalog index/stats 3/3、rerank 2/2、summary/evidence/map service unit 4/4、region read service unit 2/2、summary/triage/followups/recommendations/resource/detail/map/evidence API smoke，以及此前已完成的首页四种 viewport、Triage desktop/mobile、Routine/Urgent/Emergency、Resources/详情、Map、Trust、Profile 和 Shell accessibility desktop/mobile 浏览器运行态检查均通过；本次键盘语义变更的 Journey/Resources/Map 运行态 smoke 已通过，完整 keyboard/contrast 矩阵仍待后续。
- 由于本地依赖缓存不可用，尚未加入 Vitest/Testing Library/Playwright；当前测试不能替代完整 E2E、视觉 baseline 和 keyboard/contrast 审查。
- 关键未完成项：逐字段 provenance、真实附近急诊地图路径、完整 route parity、结构化 follow-up answer API、Playwright/E2E、视觉 baseline、完整键盘/对比度审查和 CI 远端首次运行；Profile 历史仅为本地 demo，不得扩展为账号/病历。

## Next session starts with

先读取 `AGENTS.md`、本文件、`docs/status/current.md`、本次计划和 review；优先补完整 route parity、正式急诊路径/资源 provenance 契约或 Playwright/E2E、截图 baseline 和 accessibility matrix；Profile/History 只允许沿用 ADR-0006 的本地脱敏边界，现有 triage/recommendation/resource catalog/prediction/transit/rerank/summary/evidence/map/region read service 只允许行为保持。

## Open questions

- 红旗与分诊等级的医学审核口径，以及 Safety Evaluation 已登记的 under-triage 缺口。
- 医院/医生数据的逐字段来源、许可证、更新时间和正式发布范围。
- 完成 route parity 后，何时由用户确认切换新前端为默认入口。
