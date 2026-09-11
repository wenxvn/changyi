# 2026-09-11：完成 F12 Shell 可访问性收口

## 背景

新前端已经有语义 HTML、label、focus-visible 和 reduced-motion CSS，但跨页入口缺少统一的跳过链接、当前路由语义和移动导航控制关系。

## 处理

- App Shell 增加 skip link、main landmark、活动导航 `aria-current` 和移动菜单 `aria-controls`。
- 跨页滚动读取 `prefers-reduced-motion`，避免低动效偏好被 JS 平滑滚动覆盖。
- checkbox/input 纳入共享 focus-visible 边界；Profile 入口在移动端保留。

## 结果

8/8 前端边界测试、typecheck、build、89 个 pytest、静态检查通过；浏览器 AX 树确认 skip link、main landmark、活动导航和移动端无横向溢出。完整 accessibility、视觉和 E2E 门禁仍未完成。
