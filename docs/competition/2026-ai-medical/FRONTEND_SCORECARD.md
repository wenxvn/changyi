# Frontend Scorecard — 常医智导

评分范围：1–5；首个切片只记录已实现或已验证的范围，未实现项不得用视觉推测代替证据。

## 当前切片评分

| 维度 | 分数 | 证据 | 待改进 |
| --- | ---: | --- | --- |
| First impression | 4 | 首页首屏包含产品名、价值主张、症状输入和常州示范区；Playwright 已保存桌面/移动运行态截图 | 仍需完成 1440/1280/768/390 完整截图矩阵 |
| Product clarity | 4 | Hero 与 Editorial 观点明确“先安全、再路径”；Triage 已接入当前理解、追问、跳过和结果路径；资源详情按选择从 v1 读取；Profile 明确本地演示与历史边界 | 完整跨页会话上下文待补齐 |
| Visual hierarchy | 4 | Hero、Care Path、scroll narrative 和 Trust 分层 | 需按实际运行态微调密度 |
| Interaction | 3 | 导航、输入入口、AI Journey 手动切换/键盘切换、追问回答/跳过、资源搜索/切换/详情加载/重试、地图列表/marker 联动和急诊字段筛选、医院资料高德导航 URI、Profile 历史开关/清除可用 | 语音、正式路线/实时急诊可用性待后续 |
| Safety UX | 3 | 首页有辅助边界；Emergency 结果独立展示高风险提示、红旗标签和 `tel:120`，且不请求普通推荐 | 附近急诊地图入口仍为“建设中”，需完成真实急诊路径复核 |
| Mobile | 3 | 新增移动导航和响应式布局；Playwright 已检查 390×844 的分诊初始视图、主操作和移动导航 | 需完成资源/地图/Trust 完整移动矩阵与 768×1024 复核 |
| Accessibility | 3 | 语义 HTML、label、skip link、main landmark、活动路由语义、focus-visible、reduced motion、Journey/资源/地图 tab/panel 关系和部分键盘导航已接入；运行态 AX 树可读 | 需补完整键盘路径与对比度审查 |
| Performance | 4 | 首页只加载摘要 API，SVG/CSS 为主；资源页按 tab 读取医生索引，详情按选择读取；Map/Trust 各单次读取 API；最新构建 gzip 约 JS 87.4 kB、CSS 13.1 kB | 需记录真实网络 waterfall |
| Evidence | 4 | 城市指标来自 `/api/v1/summary`；Triage/Follow-up/Recommendation/Resources/Resource Detail/Trust 使用 v1 契约，Trust 展示真实评测、数据质量、SHA-256、版本和限制；Profile 明确本地摘要不是病历 | 医院逐字段来源、正式发布时间和更完整的评测治理待实现 |
| Demo reliability | 4 | Flask 默认入口已切换为 React build；新入口有错误/空态，summary/triage/resource/detail/map/evidence smoke 通过；5 个 Playwright smoke 覆盖真实 shell、console/network、导航链接和移动视口；Profile 本地存储异常静默降级 | 需补模型不可用演示和远端 CI 首次结果 |

当前平均：`3.6 / 5`（未达到 competition-ready 门槛；正式实时急诊路径、完整视觉矩阵、对比度和无障碍门禁仍未完成）。

## 评分规则

- 只能依据运行态、测试或可追溯文档评分。
- 任意 Emergency 首屏安全信息被遮挡、弱化或被普通推荐覆盖时，Safety UX 最高为 1。
- API 错误静默渲染成功、硬编码数据冒充运行指标或前端复制医学规则时，Demo reliability / Evidence 不得通过。
- 主要页面平均分达到 `≥4.0` 且核心 E2E、mobile、visual、accessibility 门禁通过后，才允许标记 competition-ready。

## 后续复核

每完成一个 Homepage、Triage、Result、Resources、Map、Trust、Profile/History 切片，更新对应分数、证据、截图路径、已知问题和下一步；不以设计稿代替浏览器验证。
