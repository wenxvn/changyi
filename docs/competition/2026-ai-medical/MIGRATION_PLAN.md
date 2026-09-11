# 竞赛迁移计划

状态：已完成（2026-09-11）

本文件保留迁移结论，不再作为进行中的切片清单。完整验收标准和回滚方案见 [`docs/plans/FINAL_REFACTOR.md`](../../plans/FINAL_REFACTOR.md)。

## 已完成

- React/Vite 构建产物 `frontend/dist/` 成为 Flask 默认前端，SPA 路由由 Flask 回退到 `index.html`。
- 正式前端只使用 `/api/v1/*`；旧 `/api/*` 路由、legacy adapter、旧模板和旧静态 UI 已删除。
- Flask 组合根收敛到 `backend/app/composition.py`；根 `app.py` 仅保留兼容启动入口。
- 删除未使用的 prediction/transit/rerank 包装、反馈写入端点、根 `doctors.json`、旧备份目录和 `tools/cloudflared.exe`。
- 保留模型文件、推荐权重、交通数据语义和免责声明；后续 P0 产品硬化对已记录的安全反例做了最小规则补齐，并单独更新 Safety 回归证据。

## 验收基线

- `.venv/bin/python -m pytest -q`：108 passed。
- `cd frontend && npm run typecheck && npm run test && npm run build`：通过，15 个前端边界测试通过。
- Safety Evaluation：38 cases，Red Flag Recall `1.0`，Under-triage `0.0`，Over-triage `0.0`，Emergency False Negative `0`。
- `cd frontend && npm run e2e`：通过，5 个 Playwright smoke tests 覆盖首页、分诊、资源、地图、可信信息和移动视口。
- 数据质量：27 个文件、187 个已知问题，保持登记，不在重构中静默修复。
- 稳定快照：`tests/characterization/canonical_snapshot.json` 可重复生成。

## 后续

医学覆盖扩展、数据质量治理、无障碍深化和远端 CI 首次运行转入 [`docs/POST_REFACTOR_BACKLOG.md`](../../POST_REFACTOR_BACKLOG.md)。
