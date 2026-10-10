# 竞赛评分卡（2026-10-10 冻结基线）

更新时间：2026-10-10

本文件记录当前可复现的工程基线；医学规则、模型文件、推荐权重和数据口径以正文数字为准，均为固定样例与离线原型上的工程回归结果，不是临床验证。旧 2026-09-11 基线数字已过期，不再引用。

| 评分项 | 当前证据 | 当前边界 | 状态 |
| --- | --- | --- | --- |
| 安全分诊 | 四态 `TriageStatus`、`SafetyGateDecision`、Safety-first publication、142-case Safety Evaluation；急症 v1 输出 abstain 疾病候选 | 固定样例 Red Flag Recall `1.0`，Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`；仍不代表临床覆盖或验证 | P0 回归通过 |
| 模型可信度 | 既有 NB 适配器（次要证据，上限封顶）+ random / exact fingerprint / strict near-duplicate single split / 5-fold Grouped CV（跨 split 近重复 0） | random Top-1 高但泄漏风险高；strict 隔离子集仅 24 行覆盖部分类别；不作临床准确率承诺 | 研究原型 |
| 推荐质量 | 推荐 application/domain/infrastructure 边界和 canonical v1 输出已建立 | 排序质量、交通新鲜度和逐字段 provenance 仍需独立产品/数据切片 | 工程收口 |
| 数据可信度 | 数据加载、来源字段、质量扫描和 Trust evidence 接口可复现 | 数据质量扫描 31 个数据集、186 个已知异常（`PLACEHOLDER_TIMESTAMP` / `TIME_ORDER`），只登记不静默修复 | 基线冻结 |
| 产品体验 | React/Vite 已成为 Flask 默认前端；Triage、Resources、Map、Trust、Profile/History 页面可运行，恢复高德导航 URI；算法证据只读卡（症状词/科室依据/追问差异） | 急症与信息不足出口优先；相对分数未经临床校准，不标患病概率 | P0 回归通过 |
| 工程交付 | 1043 个 pytest、前端 typecheck/21 个 boundary tests/build、96 个浏览器 E2E + 4 个 hooks、Safety142、数据扫描和 canonical snapshot 均可本地运行 | 证据端点进程缓存 + 启动预热（数字不变）；Windows 本机复现通过 | P0 回归通过 |

## 当前入口

- 前端：Flask 托管 `frontend/dist/`，SPA 路由回退到 `index.html`。
- API：正式前端只使用 `/api/v1/*`；旧 `/api/*` 路径已删除并返回 404。
- 后端：`app.py` 是兼容启动器，`backend/app/composition.py` 是 Flask 组合根。
