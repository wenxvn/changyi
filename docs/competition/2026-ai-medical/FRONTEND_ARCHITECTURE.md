# Frontend Architecture — 常医智导

状态：进行中  
已完成切片：2026-09-10 Foundation / App Shell / Homepage / Triage / Follow-up / Result / Resources / Map / Trust 首版

## 目标

新前端是 AI-native、可信、面向用户的就医导航产品界面。它负责采集输入、呈现 API 返回的分诊/推荐/资源事实和解释，不拥有医学判断、红旗检测、疾病预测或排序权重。

## 迁移边界

```text
legacy default `/`
  └─ templates/index.html + static/js/app.js + static/css/style.css

parallel frontend
  └─ frontend/index.html
      └─ React routes / page state
          ├─ api/client.ts
          ├─ api/triage.ts / resources.ts / evidence.ts
          ├─ features/*
          ├─ components/*
          └─ styles/*
                  ↓
              `/api/v1/*`
```

开发时 Vite 代理 `/api` 和 `/static` 到本地 Flask；本切片不改变 legacy 默认路由。未来 cutover 前，需要先建立构建产物托管方式、route parity 和回滚入口 `/legacy`。

## 页面与路由

| Route | 页面 | 当前状态 | 责任 |
| --- | --- | --- | --- |
| `/` | Homepage | 首个切片 | 产品说明、症状输入入口、Care Path、证据/信任入口 |
| `/triage` | 智能就医 | Triage / Follow-up / Result 首版 | 文本采集、一次一个追问、后端状态、安全结果和 v1 资源路径 |
| `/resources` | 医疗资源 | F7/F8 资源浏览与详情首版 | 医院/医生索引、关键词筛选、来源状态和按选择加载的公开详情；逐字段 provenance 待后续 |
| `/map` | 就医地图 | F9 Map 首版 | `/api/v1/map` 医院位置示意、列表/marker 联动、急诊字段筛选和资料预览；正式导航待后续 |
| `/trust` | 可信 AI | F10 Trust 首版 | 安全评估、模型/数据证据、版本、SHA-256 和限制；指标标记为 provisional |

路由使用浏览器 History API 的轻量控制器，不引入大型路由依赖。页面组件通过 `App` 接收当前路径，导航事件只改变页面状态和 URL，不写入 `window._*`。

## 状态边界

- `RouteState`：当前 pathname 和导航历史。
- `TriageSession`：用户输入、补充描述、请求状态、API 返回的 triage/follow-up/recommendation payload 和错误；不计算医学状态。
- `RegionState`：active Region Pack 和城市摘要的 loading/success/error。
- `EvidenceState`：`/api/v1/evidence` 的 loading/success/error；只展示评测、来源、版本和限制，不在前端重算医学指标。
- `ResourceDetailState`：用户选择的医院/医生详情、loading/error/retry；详情只由后端公开字段白名单和 provenance 契约提供。
- `MapState`：`/api/v1/map` 的资源 items、筛选和 selected marker；距离只由后端在明确提供坐标时返回。
- `UiState`：AI Journey 当前手动选择、toast 和移动导航开关。
- 收藏、历史和认证状态暂不在此切片实现；未来应使用明确的 local demo profile store，而不是全局变量。

## API 规则

所有请求都经过 `frontend/src/api/client.ts`：

- 默认 base URL 为当前 origin；开发环境由 Vite proxy 转发到 Flask。
- 每次请求生成 `X-Request-ID`，设置 timeout，并在组件卸载时传入 AbortSignal。
- 统一解析 v1 `{ data, meta, error }` envelope；非 2xx、业务 error、JSON 解析失败和超时统一为 `ApiError`。
- 页面组件不能直接调用 `fetch`，也不能从 legacy `/api/*` 复制业务数据。
- API 缺字段时先补 v1 契约；当前前端使用 `/api/v1/summary`、`/api/v1/triage`、`/api/v1/triage/followups`、`/api/v1/recommendations`、`/api/v1/hospitals`、`/api/v1/hospitals/<id>`、`/api/v1/doctors`、`/api/v1/doctors/<id>` 和 `/api/v1/evidence`，数值、推荐对象、资源资料、评测、数据指纹和版本由运行数据/后端返回。
- Trust Center 只读取 Evidence payload；`provisional`、`review_required`、数据质量问题和来源状态必须伴随指标显示，不得改写为临床验证或发布放行。
- Map 只读取 `/api/v1/map`；列表与 marker 使用同一 items，`distance_km` 只有明确合法坐标时才出现，直线距离不展示为导航/急救时间。

## 医学安全边界

前端仅根据 `triage_status`、`triage.label`、`triage.followup` 和服务端返回的安全动作展示状态。不得新增关键词表、疾病识别、年龄/场景推断、红旗判断或推荐排序。`EMERGENCY` 进入独立安全结果并短路普通推荐；`INSUFFICIENT_INFORMATION` 和 `followup.needed` 只触发补充信息 UI，具体发布策略由 backend Safety Gate / publication 契约控制。

## 组件分层

```text
components/ui          Button, IconButton, Input, Badge, Skeleton
components/visualization CarePath, JourneyPreview, CityMapSketch
components/medical     CurrentUnderstanding, FollowupPrompt, TriageResults
features/triage        TriageWorkspace (当前由 TriagePage 编排)
  pages                  HomePage, TriagePage, ResourcesPage, MapPage, TrustPage
```

Editorial 内容优先使用 grid、分隔线、排版和留白；Card 只用于医院、医生、证据和安全状态等功能对象。

## 样式与动效

- 语义 token 位于 `frontend/src/styles/tokens.css`，组件不散落 hex/rgb 色值。
- Warm Precision：Warm Porcelain、Ink、Deep Navy、Medical Teal、Muted Sage；红/琥珀只表达安全状态。Emergency 同时使用文字、图标和语义颜色，降低动效。
- 交互状态使用 `:focus-visible`、disabled、loading 和 error；支持 keyboard 与 `prefers-reduced-motion`。
- 首页 Care Path 使用 SVG/CSS 线条与节点，动效只表达输入/选择状态，不自动轮播、不持续高耗动画。

## 数据与性能

首页只加载 `/api/v1/summary` 和 `/api/v1/regions` 摘要，不加载全部医生、医院详情或交通明细；资源页首屏只加载医院索引，切到医生视图才读取 2,100 条医生公开资料，详情只在用户选择后按 id 读取，并只渲染前 48 条；Map 页只读取一次坐标资源索引，Trust 页只发起一次轻量 Evidence 请求，manifest 首屏展示前 8 条。图片使用明确的 fallback 和 lazy 策略；本切片主要使用 CSS/SVG，避免额外大资源。

## 迁移与回滚

每个 Slice 依次完成 read → design → implement → run → screenshot → compare → improve → test → review → document。新前端在 `core flow parity`、Safety parity、E2E、mobile、visual QA 全部通过前，不成为默认入口；legacy 作为 `/legacy` 的目标回滚路径保留。
