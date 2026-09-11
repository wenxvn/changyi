# 竞赛评分卡（重构收口基线）

更新时间：2026-09-11

本文件只记录本次重构后的工程基线；医学规则、模型文件、推荐权重和数据口径没有在本轮改变。后续产品或医学改进见 [`docs/POST_REFACTOR_BACKLOG.md`](../../POST_REFACTOR_BACKLOG.md)。

| 评分项 | 当前证据 | 当前边界 | 状态 |
| --- | --- | --- | --- |
| 安全分诊 | 四态 `TriageStatus`、`SafetyGateDecision`、Safety-first publication、38-case Safety Evaluation；急症 v1 输出 abstain 疾病候选 | 固定样例 Red Flag Recall `1.0`，Emergency False Negative `0`；仍不代表临床覆盖或验证 | P0 回归通过 |
| 模型可信度 | 既有模型适配器和训练报告保留在数据层 | 小数据和单次切分限制仍存在，不作临床准确率承诺 | 延后 |
| 推荐质量 | 推荐 application/domain/infrastructure 边界和 canonical v1 输出已建立 | 排序质量、交通新鲜度和逐字段 provenance 仍需独立产品/数据切片 | 工程收口 |
| 数据可信度 | 数据加载、来源字段、质量扫描和 Trust evidence 接口可复现 | 数据质量扫描仍报告 27 个文件、187 个已知问题，不在重构中静默修复 | 基线冻结 |
| 产品体验 | React/Vite 已成为 Flask 默认前端；Triage、Resources、Map、Trust、Profile/History 页面可运行，恢复高德导航 URI | 视觉复核已覆盖桌面/移动截图，无障碍深化仍需独立切片 | P0 回归通过 |
| 工程交付 | 108 个 pytest、frontend typecheck/15 个 boundary tests/build、5 个 Playwright smoke、Safety、数据扫描和 canonical snapshot 均可本地运行 | 远端 workflow 首次运行和分支保护不属于本地重构收口 | P0 回归通过 |

## 当前入口

- 前端：Flask 托管 `frontend/dist/`，SPA 路由回退到 `index.html`。
- API：正式前端只使用 `/api/v1/*`；旧 `/api/*` 路径已删除并返回 404。
- 后端：`app.py` 是兼容启动器，`backend/app/composition.py` 是 Flask 组合根。
