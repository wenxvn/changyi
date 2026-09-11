# P0 Product Hardening Review

日期：2026-09-11

## Layer 1 — 计划对齐：PASS

- `docs/plans/P0_PRODUCT_HARDENING.md` 的五项 P0 均完成：Safety 回归、AMap URI、产品文案、Triage/资源/地图布局和真实 Flask + Playwright smoke。
- 变更范围未扩展到账号、数据库、实时急诊、实时交通、模型训练或新城市；模型文件、推荐权重和数据口径保持不变。

## Layer 2 — 系统完整性：PASS

- 安全规则和输入归一化仍由后端 domain/composition 负责，前端只消费 `triage_status` 和公开资源字段；AMap 仅由共享 utility 生成外部 URI，不引入 SDK、API key 或地图判断逻辑。
- 资源来源、更新时间、许可状态和免责声明仍保留；技术版本与校验字段仅在 Trust Center 折叠的“技术详情”中展示。
- Triage 分析后的上下文侧栏、资源动作区和 Map preview 使用现有 CSS token/组件模式，并保留加载、错误、空态、focus-visible、reduced-motion 与红旗急救动作。

## Layer 3 — 交付准备度：PASS（保留已登记风险）

- `.venv/bin/python -m pytest -q`：108 passed。
- Safety Evaluation：38 cases，Red Flag Recall `1.0`、Under-triage `0.0`、Over-triage `0.0`、Emergency False Negative `0`；信息不足样例全部命中，结果仍是固定样例工程回归，不是临床验证。
- `cd frontend && npm run typecheck && npm run test && npm run build`：通过；15 个前端测试通过。
- `cd frontend && npm run e2e -- --workers=1`：5 个真实 Chromium smoke 通过，覆盖首页、分诊普通/信息不足/急症、资源/地图/可信信息、AMap href、桌面与移动视口；fixture 检查 console、page error 和 HTTP 4xx/5xx，并保存截图。
- 数据扫描为 27 个文件、187 个已登记问题；未静默修复。固定样例通过不能消除 `R-001` 的医学覆盖风险、`R-002` 的来源/许可证风险或 `R-011` 的数据质量风险。

### 未发现的问题

未发现计划缺口、架构越界、未处理的核心空态/错误态或浏览器 console/network 回归；可进入稳定维护。
