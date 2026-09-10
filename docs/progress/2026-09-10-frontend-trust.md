# 进度：Frontend Trust Center

日期：2026-09-10  
状态：首版完成，保留后续门禁

## 已完成

- 新增 `backend/app/application/evidence.py`，只读读取安全评估、模型 JSON、数据质量报告和 Region Pack 数据指纹。
- 新增 `/api/v1/evidence`，复用既有 v1 envelope、版本 meta 和 legacy triage evaluator；没有修改红旗、分诊或推荐逻辑。
- 新增前端 Evidence 类型、运行时 parser、`getEvidence()` 和 `/trust` 页面。
- Trust Center 展示安全评估、review_required、离线模型指标、数据质量、SHA-256、版本、限制条件以及资源页入口。
- 页面明确标注原型阶段、provisional 和“不代表临床验证”，并提供 loading/error 降级态。
- 更新迁移计划、契约、架构、评分卡、UI registry、status、history、review 和 memory。

## 验证

- `./.venv/bin/pytest -q`：87 passed。
- `python3 -m py_compile app.py backend/app/api/v1/routes.py backend/app/application/evidence.py`：通过（使用仓库解释器编译）。
- `node --check static/js/app.js`：通过。
- `npm run typecheck`、`npm run test`：5/5；`npm run build`：通过，gzip 约 JS 82.1 kB、CSS 11.0 kB。
- `/api/v1/evidence` Flask smoke：200；当前返回 provisional、16 个 Safety Case、41 个模型类别、27 个数据集条目、187 个已登记质量问题。
- 浏览器运行态：Trust Center desktop 与 390×844 mobile 可加载真实 API 数据，安全/模型/来源/限制内容可见；移动端无明显横向溢出。

## 未完成

- F9 地图、附近急诊路径和真实地图数据契约仍未实现。
- 医院逐字段 provenance、资源详情契约、结构化 follow-up answer API、完整 route parity 仍未完成。
- Playwright/E2E、独立截图 baseline、keyboard/contrast 审查和 frontend CI job 仍需补齐。
- Safety Evaluation 已知 under-triage 与红旗边界仍需医学审核；本切片不修改这些规则。

## 下一步

先完成 F9 地图/急诊路径契约，再补核心流程 E2E、视觉/无障碍门禁和 frontend CI；Trust 页保持并行入口，不切换 legacy 默认路由。
