# 2026-09-11 Frontend F12 Accessibility Polish

状态：首版完成，保留完整 accessibility matrix 门禁  
变更等级：L1  
计划：[2026-09-11-frontend-accessibility-polish.md](../plans/2026-09-11-frontend-accessibility-polish.md)

## 已完成

- App Shell 增加 skip link 和可聚焦的 `main#main-content` landmark。
- 主导航活动项增加 `aria-current="page"`；Profile button 在 Profile 页也暴露当前页语义。
- 移动菜单增加稳定 `id`、`aria-expanded` 和 `aria-controls`；品牌/导航/菜单按钮显式声明 `type="button"`。
- 跨页滚动根据 `prefers-reduced-motion` 在 `auto` 与 `smooth` 之间选择；共享 focus-visible 覆盖 input。
- 更新 frontend boundary tests、architecture、scorecard、migration scorecard、status、history、review 和 UI registry。

## 验证

- `npm run typecheck`、`npm run test`：8/8 boundary tests 通过。
- `npm run build`：通过；gzip JS 约 87.1 kB，CSS 约 13.0 kB。
- `./.venv/bin/pytest -q`：89 passed。
- `node --check static/js/app.js`、`git diff --check`：通过。
- 浏览器运行态：首页 AX 树显示 skip link/main landmark；`/triage` 活动导航返回“智能就医”；skip link 通过 Enter 将焦点移动到 `main-content`；390×844 页面保持 `clientWidth=375`、`scrollWidth=375`。

## 未完成与边界

- 尚未形成完整屏幕阅读器、键盘流程、对比度和截图 baseline 报告；当前仅完成 Shell 级语义和低动效收口。
- 仍需引入或接入可复现的 Playwright/E2E、视觉和 accessibility matrix 后，才能评估 F13 cutover。

## 回滚

回退 App Shell 语义属性、滚动偏好、focus-visible CSS、边界测试和本 slice 文档即可；不影响业务状态、后端或 Profile 数据边界。
