# 竞赛迁移计划

状态：已完成（2026-09-11）

本文件保留迁移结论，不再作为进行中的切片清单。完整验收标准和回滚方案见 [`docs/plans/FINAL_REFACTOR.md`](../../plans/FINAL_REFACTOR.md)。

## 已完成

- React/Vite 构建产物 `frontend/dist/` 成为 Flask 默认前端，SPA 路由由 Flask 回退到 `index.html`。
- 正式前端只使用 `/api/v1/*`；旧 `/api/*` 路由、legacy adapter、旧模板和旧静态 UI 已删除。
- Flask 组合根收敛到 `backend/app/composition.py`；根 `app.py` 仅保留兼容启动入口。
- 删除未使用的 prediction/transit/rerank 包装、反馈写入端点、根 `doctors.json`、旧备份目录和 `tools/cloudflared.exe`。
- 保留医学规则、模型文件、推荐权重、交通数据语义、免责声明和 Safety 基线不变。

## 验收基线

- `.venv/bin/python -m pytest -q`：107 passed。
- `cd frontend && npm run typecheck && npm run test && npm run build`：通过，9 个前端边界测试通过。
- Safety Evaluation：16 cases，Red Flag Recall `0.9231`，Under-triage `0.0769`，Over-triage `0.0`，Emergency False Negative `1`。
- 数据质量：27 个文件、187 个已知问题，保持登记，不在重构中静默修复。
- 稳定快照：`tests/characterization/canonical_snapshot.json` 可重复生成。

## 后续

医学审核、Safety 反例修复、数据质量治理、E2E/视觉/无障碍门禁和远端 CI 首次运行转入 [`docs/POST_REFACTOR_BACKLOG.md`](../../POST_REFACTOR_BACKLOG.md)。
