# 当前项目状态

更新时间：2026-09-11

## 总体状态

- 状态：P0 正确性与产品闭环完成；本轮完成工程审计与三项高优先级修复
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- Safety Gate 业务语义未改动；推荐排序改为依赖可解释公开事实

## 本轮收口

- 根 `app.py` 缩为启动/导入兼容层，组合根迁移至 `backend/app/composition.py`。
- v1 blueprint 直接使用组合根注册的 handler，删除 `legacy_adapter` 和 lazy import fallback。
- 删除旧 `/api/*` 路由、旧模板、单体 `static/js/app.js`、`static/css/style.css`、Leaflet 运行时和本地测试反馈写入端点。
- 删除未使用的 prediction/transit application wrapper、旧 route parity tests、根 `doctors.json`、Windows `cloudflared.exe` 和医院 logo backup 目录。
- React build 成为 `/` 以及 `/triage`、`/resources`、`/map`、`/trust`、`/profile` 的正式入口，并通过 Flask SPA fallback 支持刷新。
- 完成 P0 产品硬化：38-case Safety regression、口语急症表达与笼统输入降级、医院/地图高德导航 URI、中文产品文案、Triage 分析后上下文侧栏和移动布局。
- 完成 P0 正确性与产品闭环：未知位置不再默认天宁区；区域参考点和主动浏览器定位有明确来源；Follow-up 答案结构化传递；医院目录外置并区分公开事实、派生能力和未支持字段；模型补充 random baseline 与 exact fingerprint grouped split；Trust Center 展示两种切分、医院 provenance 和近重复限制；资源详情、OpenStreetMap 地图、关联医生和导航链路闭环。
- Playwright 在真实 Flask shell 下覆盖首页、分诊普通/信息不足/急症路径、资源、地图、可信信息、导航链接和移动视口，并检查 console/network 与截图。
- characterization 从旧 route 改为 canonical v1 route；新前端 build 作为 Flask demo 的发布构建产物保留。
- 建立单一 `docs/plans/FINAL_REFACTOR.md`，将长期 backlog 集中到 `docs/POST_REFACTOR_BACKLOG.md`，过程记录合并到 `docs/REFACTOR_CHANGELOG.md`。

## 本轮工程审计修复（2026-09-11）

- **地图底图**：CARTO 免费 CDN 在真实浏览器中可能返回 “API KEY REQUIRED” 水印瓦片；已切换为 OpenStreetMap 官方标准瓦片（无需 Key），保留署名、拖动缩放、marker 降级和高德导航。桌面地图改为 viewport 绑定工作区：左侧列表独立滚动，右侧地图 sticky 保持可见。
- **医院排序**：`derived_capability_scores` / `strength_scores` 仍保留在目录中供 migration/debug，但不再参与 clinical ranking。`hospital_strength_for_department` 与 `resolve_hospital_candidate_match` 只使用公开科室存在事实（exact / related / none）。解释文案改为“设有对应科室 / 公开资料显示存在相关专科方向”。
- **医生排序**：`ENHANCED_WEIGHTS` 中 academic 权重从 complex `0.28` 等降至各场景 `0.02`；`doctor_resource_tier` 不再用 SCI/基金/专利定义专家层级；推荐解释不再把科研当作“更适合当前患者”的理由。学术字段仍可在医生详情中展示。
- **交通特征门控**：无具体附近站点/出租车证据或无用户位置时，可达性退回直线距离；稀疏 provisional 交通样本不再默认强参与排序。
- **前端文案**：删除首页未实现的语音按钮及“后续切片接入”开发提示。
- **截图验收**：`/`、`/triage`（普通结果+急症）、`/resources`、`/map`、`/trust` 在 1440×900 与 390×844 完成真实浏览器截图；截图在 `qa-screenshots/`。
- **旧能力盘点**：语音/浮动 Assistant/收藏/Dashboard/Demo Login/公交大屏均已删除且本轮未恢复；状态表见 `docs/POST_REFACTOR_BACKLOG.md`。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 24 行兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 测试 | 116 个 pytest；前端 16 个 boundary tests；5 个 Playwright smoke tests |
| Safety | 38 cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`；信息不足样例全部命中 |
| 推荐快照 | canonical characterization 已覆盖 v1 triage/recommendation；旧 legacy route harness 已移除 |
| 数据质量 | 28 个文件、187 个异常；报告保留，不自动修复 |
| 模型证据 | random baseline 与 exact symptom fingerprint grouped split 已写入 `evaluation/model/`；近重复审计 605 对（Jaccard≥0.8），exact group 不能消除全部近重复泄漏 |
| 医院目录 | `data/regions/320400/hospitals/catalog.json`；目录状态 `provisional`，派生能力字段明确标注且不参与正式排序，床位/门诊量/评级/描述未支持 |
| 地图底图 | OpenStreetMap 官方瓦片 `tile.openstreetmap.org`；无 API Key；失败时列表/marker/导航仍可用 |

## 验证记录

- `.venv/bin/python -m pytest`：116 passed。
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：38 cases；Recall `1.0`；Under-triage `0.0`；Over-triage `0.0`；Emergency False Negative `0`。
- `.venv/bin/python tests/characterization/run_snapshot.py`：通过。
- `frontend`：`npm run typecheck`、`npm run test`（16/16）、`npm run build`、`npm run e2e`（5/5）通过。
- 真实浏览器 `/map` @1440×900：25/25 瓦片加载，无 API KEY REQUIRED；21 markers；列表点击与 marker 点击均打开资料预览；高德导航 URI 存在；列表内部滚动后地图仍可见。
- 真实浏览器 `/map` @390×844：单列布局，25/25 瓦片加载，无 API KEY REQUIRED。
- 首页已无“后续切片/语音”开发文案。

## 未改变的风险

- Safety 固定样例中的已复现 under-triage 与信息不足缺口已修复为回归通过；未覆盖表达、真实临床安全和专业复核仍属于 `R-001`。
- 医院目录已外置并区分公开事实/派生/未支持字段，但逐字段外部来源、许可证和更新时间仍不完整，保持 `provisional`（`R-002`）。
- 数据质量 187 个异常未修复（`R-011`）；交通样本仅在有具体证据时弱参与可达性。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）；高德 URI 只是外部导航跳转，不代表实时路线或急救指令。模型分组评估仍是小样本离线证据，不能替代临床验证（`R-016`）。
- exact fingerprint group split 不能覆盖 Jaccard≥0.8 近重复；建议下一步实施 Near-duplicate Group Split。

## 下一步

不要在本轮基线上继续扩展功能；新需求先查看 `docs/POST_REFACTOR_BACKLOG.md`，涉及医学或生产能力时按新的 L3/L4 规则另立计划和评审。模型评估若继续，优先 Near-duplicate Group Split。
