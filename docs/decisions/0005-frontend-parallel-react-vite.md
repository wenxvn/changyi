# ADR-0005：新前端采用 React/TypeScript/Vite 并行迁移

- 状态：已完成（2026-09-11 正式 cutover）
- 日期：2026-09-10
- 收口计划：`docs/plans/FINAL_REFACTOR.md`
- 范围：`frontend/`、前端构建、页面状态和 API 边界

## 背景

当前页面由 `templates/index.html`、4,351 行 `static/js/app.js` 和 7,174 行 `static/css/style.css` 共同驱动，存在全局状态、字符串 HTML、API 请求和展示逻辑耦合。竞赛版需要更清晰的组件、状态、类型和响应式边界，但一次性替换会同时改变既有流程与安全行为。

## 选项

- **选项 A：继续扩展 legacy JS/CSS**。短期接入成本低，但会继续放大全局状态、隐式契约和视觉债务。
- **选项 B：把 legacy 直接翻译成 JSX**。可以快速迁移页面，但不会建立新的数据、状态和组件边界。
- **选项 C：建立 React + TypeScript + Vite 并行前端**。初始有少量构建成本，但可以用 strict 类型、统一 API client、页面级状态和独立视觉 QA 逐步迁移，同时保持 legacy 可回滚。

## 决定

选择选项 C。新前端使用 React、TypeScript strict 和 Vite，开发入口与 Flask API 通过 Vite proxy 连接；默认 `/` 仍由 legacy 提供，直到新前端完成 parity 和发布门禁。新组件只从 API 返回值呈现医学状态，不在浏览器复制红旗、疾病或推荐规则。

> 收口记录：并行阶段已结束；当前 `/` 和 SPA 刷新路径由 Flask 提供 `frontend/dist`，正式前端只调用 `/api/v1/*`。上句关于 legacy 默认入口的描述属于迁移阶段历史事实。

## 理由

- 符合 ADR-0003 的渐进式拆分和可回滚原则。
- TypeScript 能把 triage、recommendation、resource 和 evidence 契约显式化。
- Vite 适合竞赛演示的轻量开发/构建，不引入 Redux、数据库或微服务。
- 并行入口让首页视觉重构不会污染旧演示，也便于用截图和 E2E 做比较。

## 影响

- 新增 Node 依赖和前端质量门禁；CI 需要在后续切片加入 frontend job。
- 需要维护 legacy 与新前端一段时间，直到完成 route、Safety UX 和数据契约 parity。
- `/api/v1/summary` 成为首页城市摘要的版本化只读契约；其中医院目录的 provenance 状态必须随数据一起展示。

## 回滚与替代路径

当前回滚依赖回退到上一个已验证提交；不需要回退数据、模型或后端推荐代码。若后续正式前端变更无法满足发布门禁，应先停止发布并回到该提交，不在当前工作树恢复第二套 legacy 入口。

## 验证

- `npm run typecheck`、`npm run build`、`npm run test`。
- Flask v1 health/summary/triage smoke 与既有 pytest/characterization snapshot。
- 首页四种 viewport 的浏览器运行态、键盘焦点、reduced motion、console/network 检查。
