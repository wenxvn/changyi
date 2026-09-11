# 当前项目状态

更新时间：2026-09-11

## 总体状态

- 状态：P0 产品硬化完成，进入稳定维护基线
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 模型、推荐权重和数据口径：保持既有 baseline；P0 仅补齐已复现的安全表达与信息不足降级，并单独更新评估证据

## 本轮收口

- 根 `app.py` 缩为启动/导入兼容层，组合根迁移至 `backend/app/composition.py`。
- v1 blueprint 直接使用组合根注册的 handler，删除 `legacy_adapter` 和 lazy import fallback。
- 删除旧 `/api/*` 路由、旧模板、单体 `static/js/app.js`、`static/css/style.css`、Leaflet 运行时和本地测试反馈写入端点。
- 删除未使用的 prediction/transit application wrapper、旧 route parity tests、根 `doctors.json`、Windows `cloudflared.exe` 和医院 logo backup 目录。
- React build 成为 `/` 以及 `/triage`、`/resources`、`/map`、`/trust`、`/profile` 的正式入口，并通过 Flask SPA fallback 支持刷新。
- 完成 P0 产品硬化：38-case Safety regression、口语急症表达与笼统输入降级、医院/地图高德导航 URI、中文产品文案、Triage 分析后上下文侧栏和移动布局。
- Playwright 在真实 Flask shell 下覆盖首页、分诊普通/信息不足/急症路径、资源、地图、可信信息、导航链接和移动视口，并检查 console/network 与截图。
- characterization 从旧 route 改为 canonical v1 route；新前端 build 作为 Flask demo 的发布构建产物保留。
- 建立单一 `docs/plans/FINAL_REFACTOR.md`，将长期 backlog 集中到 `docs/POST_REFACTOR_BACKLOG.md`，过程记录合并到 `docs/REFACTOR_CHANGELOG.md`。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 24 行兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 测试 | 108 个 pytest；前端 15 个 boundary tests；5 个 Playwright smoke tests |
| Safety | 38 cases；Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`；信息不足样例全部命中 |
| 推荐快照 | canonical characterization 已覆盖 v1 triage/recommendation；旧 legacy route harness 已移除 |
| 快照 SHA-256 | `2b0637630eb52013c9cba3a5cc20f1a536602d2cf7bbf4e91170d638f0754d59` |
| 数据质量 | 27 个文件、187 个异常；报告保留，不自动修复 |

## 验证记录

- `.venv/bin/python -m pytest -q`：108 passed。
- `.venv/bin/python -m evaluation.safety.evaluate_safety`：38 cases；Recall `1.0`；Under-triage `0.0`；Over-triage `0.0`；Emergency False Negative `0`；无 review required。
- `.venv/bin/python tests/characterization/run_snapshot.py`：通过，canonical snapshot 可重复。
- `.venv/bin/python -m py_compile app.py backend/app/composition.py $(find backend data_validation evaluation tests data/symptom_disease_model -type f -name '*.py' -print)`：通过。
- `frontend/npm run typecheck`、`npm run test`（15/15）、`npm run build`：通过。
- `cd frontend && npm run e2e`：通过，5 个 Playwright smoke tests；桌面/移动截图已写入 `frontend/test-results/`。
- Flask test client：`/`、`/triage`、`/resources`、`/map`、`/trust`、`/profile` 均 200；未知 `/api/*` 不回退到 SPA；v1 health、triage、recommendations、resources、map、evidence 通过既有 contract tests。
- `git diff --check`：通过。

## 未改变的风险

- Safety 固定样例中的已复现 under-triage 与信息不足缺口已修复为回归通过；未覆盖表达、真实临床安全和专业复核仍属于 `R-001`。
- 医院/医生逐字段 provenance 和许可证仍不完整，医院目录保持 `migration_pending`（`R-002`）。
- 数据质量 187 个异常未修复（`R-011`）。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）；高德 URI 只是外部导航跳转，不代表实时路线或急救指令。

## 下一步

不要在本轮基线上继续扩展功能；新需求先查看 `docs/POST_REFACTOR_BACKLOG.md`，涉及医学或生产能力时按新的 L3/L4 规则另立计划和评审。
