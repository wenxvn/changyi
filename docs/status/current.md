# 当前项目状态

更新时间：2026-09-11

## 总体状态

- 状态：重构收口完成，进入稳定维护基线
- 分支：`main`
- 正式前端：Flask 提供 `frontend/dist` 中的 React build
- 正式 API：`/api/v1/*`
- 根入口：`python app.py`
- 医学、安全、模型、推荐权重和数据口径：冻结，保持既有 baseline

## 本轮收口

- 根 `app.py` 缩为启动/导入兼容层，组合根迁移至 `backend/app/composition.py`。
- v1 blueprint 直接使用组合根注册的 handler，删除 `legacy_adapter` 和 lazy import fallback。
- 删除旧 `/api/*` 路由、旧模板、单体 `static/js/app.js`、`static/css/style.css`、Leaflet 运行时和本地测试反馈写入端点。
- 删除未使用的 prediction/transit application wrapper、旧 route parity tests、根 `doctors.json`、Windows `cloudflared.exe` 和医院 logo backup 目录。
- React build 成为 `/` 以及 `/triage`、`/resources`、`/map`、`/trust`、`/profile` 的正式入口，并通过 Flask SPA fallback 支持刷新。
- characterization 从旧 route 改为 canonical v1 route；新前端 build 作为 Flask demo 的发布构建产物保留。
- 建立单一 `docs/plans/FINAL_REFACTOR.md`，将长期 backlog 集中到 `docs/POST_REFACTOR_BACKLOG.md`，过程记录合并到 `docs/REFACTOR_CHANGELOG.md`。

## 当前基线

| 领域 | 事实 |
| --- | --- |
| Flask 入口 | `app.py` 24 行兼容启动层；`backend/app/composition.py` 为组合根 |
| 正式前端 | `frontend/src/` React/TypeScript；`frontend/dist/` 由 Flask 提供 |
| 正式 API | `/api/v1/health`、`ready`、`regions`、`triage`、`triage/followups`、`recommendations`、`hospitals`、`doctors`、`summary`、`evidence`、`map` |
| 数据 | active Region Pack `320400`；11 份医生 JSON，运行时加载 2,100 条公开资料 |
| 测试 | 107 个 pytest；前端 9 个 boundary tests |
| Safety | 16 cases；Recall `0.9231`、Under-triage `0.0769`、Over-triage `0.0`、Emergency False Negative `1` |
| 推荐快照 | canonical characterization 已覆盖 v1 triage/recommendation；旧 legacy route harness 已移除 |
| 快照 SHA-256 | `435f0595c1801d2a591775563efca4947f5d1d51f7444fb6bdc074536111ab6a` |
| 数据质量 | 27 个文件、187 个异常；报告保留，不自动修复 |

## 验证记录

- `.venv/bin/python -m pytest -q`：107 passed。
- `.venv/bin/python tests/characterization/run_snapshot.py`：通过，canonical snapshot 可重复。
- `.venv/bin/python -m py_compile app.py backend/app/composition.py $(find backend data_validation evaluation tests data/symptom_disease_model -type f -name '*.py' -print)`：通过。
- `frontend/npm run typecheck`、`npm run test`（9/9）、`npm run build`：通过。
- Flask test client：`/`、`/triage`、`/resources`、`/map`、`/trust`、`/profile` 均 200；未知 `/api/*` 不回退到 SPA；v1 health、triage、recommendations、resources、map、evidence 通过既有 contract tests。
- `git diff --check`：通过。

## 未改变的风险

- Safety Evaluation 的 under-triage 与信息不足缺口仍是 `R-001`，本轮未修复。
- 医院/医生逐字段 provenance 和许可证仍不完整，医院目录保持 `migration_pending`（`R-002`）。
- 数据质量 187 个异常未修复（`R-011`）。
- 演示认证、CORS、隐私、审计和部署不具备生产安全属性（`R-003`、`R-007`、`R-013`）。

## 下一步

不要在本轮基线上继续扩展功能；新需求先查看 `docs/POST_REFACTOR_BACKLOG.md`，涉及医学或生产能力时按新的 L3/L4 规则另立计划和评审。
