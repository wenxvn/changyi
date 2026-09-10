# 常医智导前端迁移计划：Foundation、App Shell 与 Homepage

状态：进行中  
日期：2026-09-10  
变更等级：L2（前端状态/API 边界与只读摘要契约；不改变医学规则、模型或推荐排序）

## 目标

建立与 legacy 页面并行的新 `frontend/`，先完成 Warm Precision 设计基础、无侧边栏 App Shell 和可直接体验的首页。首页以自然语言症状输入和 Care Path Visual 为首屏核心，城市指标全部来自版本化只读 API；保留现有 `/`、`/api/*` 和 `/api/v1/*` 作为回滚与行为基线。

## 非目标

- 不删除或改写 `templates/index.html`、`static/js/app.js`、`static/css/style.css`。
- 不改变红旗规则、分诊状态、模型输出、推荐权重或推荐排序。
- 不在本切片实现完整追问、结果页、急症页、资源页、地图和 Trust Center。
- 不引入登录、真实患者数据、外部付费服务或不可回滚部署变化。

## 已对齐的术语

- **并行前端**：新应用通过 Vite 独立开发和构建，legacy 继续作为默认入口，直到 parity 和发布门禁完成。
- **Care Path Visual**：展示“症状 → 安全门 → 就医方向 → 资源路径”的产品状态视觉，不在前端推断医学状态。
- **城市智能层**：展示 active Region Pack 与后端摘要返回的资源统计，数值必须可回到 API/数据源。
- **Competition-quality 首页**：首屏在 10 秒内说明产品、常州示范区、症状入口和安全边界，并通过四种 viewport 的运行态检查。

## 验收标准

- `frontend/` 具备 strict TypeScript、Vite build、typecheck 和 Node boundary smoke test；Vitest/Testing Library 待依赖可用后补入。
- API 请求统一经过 `frontend/src/api/client.ts`，具备 base URL、超时、AbortController、request id 和错误规范化。
- 首页包含产品定位、自然语言输入、Care Path Visual、产品观点、AI Journey、城市智能层、Trust CTA 和免责声明。
- 首页无登录门面、侧边栏、后台统计大屏、硬编码城市指标或前端医学关键词判断。
- App Shell 支持首页、智能就医、医疗资源、就医地图、可信 AI 四个路径；未实现页面使用明确的建设中空态。
- 通过 1440×900、1280×800、768×1024、390×844 运行态检查；记录 overflow、焦点、控制台和网络结果。

## 回滚方式

删除或回退本切片新增的 `frontend/`、摘要 API 与文档即可；默认 `/` 和旧 API 不依赖新前端，legacy 演示不会被切换。

## 实施步骤

1. 建立 ADR、前端架构说明、评分卡和本计划，明确并行迁移与 rollback 边界。
2. 增加 `/api/v1/summary` 只读契约，返回 Region Pack、医院、医生公开资料、公交线路和城市区域摘要。
3. 创建 Vite/React/TypeScript 工程、严格类型、统一 API client、共享 token 和全局样式。
4. 实现 App Shell、响应式导航、品牌标记、页脚和四类路径空态。
5. 实现 Homepage：Hero、输入入口、Care Path、Editorial 观点、手动 AI Journey、API 驱动城市层与 Trust 区域。
6. 实现最小 Triage Workspace 首步，仅提交用户文本到 `/api/v1/triage` 并呈现后端返回状态；不复制医学判断。
7. 运行前端 typecheck/build/boundary test、后端相关 pytest 与 Flask API smoke，记录未验证项。
8. 启动浏览器执行四 viewport 视觉/可访问性/网络检查，更新 UI registry、进度、历史、评分卡和 review。

## 风险与观察项

- `/api/v1/summary` 复用当前 legacy 数据聚合，医院目录仍是 `migration_pending`，UI 必须保留来源状态，不能称为“真实数据”。
- Vite 开发入口不是默认发布入口；切换前必须完成 parity、E2E、Safety UX、视觉和移动端门禁。
- 本切片不修复已登记的 Safety Evaluation false negative、数据质量异常或 provenance 缺口。
