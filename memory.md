# Memory — 2026-09-10 Frontend Foundation / Triage Results

Last updated: 2026-09-10

## What was built

- 建立 `frontend/` React/TypeScript/Vite 并行前端，包含 strict 类型、集中 API client、运行时响应校验、Warm Precision tokens、App Shell、响应式导航、Homepage、Care Path、AI Journey、Triage Workspace、Follow-up prompt 和四态结果展示。
- 新增 `/api/v1/summary` 只读摘要契约；首页城市指标从运行数据读取，同时展示 Region Pack、来源类别和医院目录 `migration_pending` 状态。
- Triage 首版已接入 `/api/v1/triage`、`/api/v1/triage/followups`、`/api/v1/recommendations`：Routine/Urgent 可回答或跳过追问后读取医院/医生资源，Emergency 独立展示红旗、`tel:120`，不请求普通推荐。
- F7/F8 资源首版已接入 `/api/v1/hospitals`、`/api/v1/doctors`：医院索引首屏加载，医生索引按 tab 加载；支持医院/医生关键词筛选、来源状态和公开资料预览；地图另有 F9 首版。
- 资源详情首版已接入 `/api/v1/hospitals/<id>`、`/api/v1/doctors/<id>`：后端公开字段白名单和 provenance，前端按选择加载详情并保留 loading/error/retry；医院内部评分/床位和医生学术/原始抓取链接未穿过新边界。
- F10 Trust 首版已接入只读 `/api/v1/evidence`：从现有 Safety Evaluation、模型 JSON、data quality report、Region Pack manifest 和配置读取事实；`/trust` 展示 provisional、离线指标、review_required、SHA-256、版本和限制，明确不代表临床验证。
- F9 Map 首版已接入只读 `/api/v1/map`：现有医院坐标生成轻量位置示意，列表/marker 联动、含急诊字段筛选、预览和可选 Haversine 直线距离；默认不请求定位，不生成推荐 marker。
- Frontend CI 首版已加入 `.github/workflows/quality.yml`：Node 22 + `npm ci` + typecheck/boundary tests/build；远端首次运行尚待 push 后确认。
- legacy `/`、legacy API 和现有 v1 路由保持默认兼容，未切换入口。

## Decisions made

- 采用 ADR-0005 的并行迁移策略：新前端独立构建，route parity、E2E、视觉和安全门禁完成前不替换 legacy。
- 浏览器不复制医学规则；triage 状态只展示后端返回，语音入口暂时 disabled。
- UI token、组件模式和可访问性要求已写入 `ui-registry.md` 与 `frontend/docs/design-system.md`。

## Current state

- 本轮验证：frontend typecheck、Node boundary tests 6/6、Vite build（gzip JS 84.8 kB、CSS 12.3 kB）、后端语法检查、pytest 89/89、summary/triage/followups/recommendations/resource/detail/map/evidence API smoke，以及首页四种 viewport、Triage desktop/mobile、Routine/Urgent/Emergency、Resources/详情、Map 和 Trust desktop/mobile 浏览器运行态检查均通过。
- 由于本地依赖缓存不可用，尚未加入 Vitest/Testing Library/Playwright；当前测试不能替代完整 E2E、视觉 baseline 和 keyboard/contrast 审查。
- 关键未完成项：逐字段 provenance、真实附近急诊地图路径、完整 route parity、结构化 follow-up answer API、Playwright/E2E、视觉 baseline、键盘/对比度审查和 CI 远端首次运行。

## Next session starts with

先读取 `AGENTS.md`、本文件、`docs/status/current.md`、本次计划和 review；优先补正式急诊路径/资源详情与 provenance 契约，然后补 Playwright/E2E，继续保持所有状态来自 `/api/v1`。

## Open questions

- 红旗与分诊等级的医学审核口径，以及 Safety Evaluation 已登记的 under-triage 缺口。
- 医院/医生数据的逐字段来源、许可证、更新时间和正式发布范围。
- 完成 route parity 后，何时由用户确认切换新前端为默认入口。
