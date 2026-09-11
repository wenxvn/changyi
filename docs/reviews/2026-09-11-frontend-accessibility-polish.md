# Review：Frontend F12 Accessibility Polish

日期：2026-09-11  
范围：`frontend/src/app/App.tsx`、`frontend/src/styles/globals.css`、frontend boundary tests 和对应文档  
计划：[2026-09-11-frontend-accessibility-polish.md](../plans/2026-09-11-frontend-accessibility-polish.md)

## 1. 计划对齐

结论：通过，计划中的 Shell 语义与低动效范围已完成。

- skip link、main landmark、活动路由语义、移动导航控制关系和 input focus-visible 均已实现。
- 没有改变医学状态、推荐排序、API 或 Profile 隐私边界。

## 2. 系统完整性

结论：通过。

- App Shell 继续是路由与 UI 交互协调边界；没有把医学逻辑或 API 调用放入 Shell。
- CSS 使用现有语义 token；Profile 移动端入口没有因布局收缩而被隐藏。
- boundary test 覆盖关键属性和 reduced-motion 分支；AX 树确认运行态结构可读。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 完整键盘流程、对比度、屏幕阅读器、视觉 baseline 和 Playwright/E2E 尚未建立。
- [P1] F13 仍需 core/Safety parity、正式急诊路径、逐字段 provenance 和远端 CI 结果。
- [P2] 当前 skip link 的浏览器点击行为依赖原生 anchor；键盘 Enter 运行态已确认可将焦点交给 main。

## 总结

F12 Shell 可访问性收口可以作为并行前端继续迁移的基础，但不能单独宣称 WCAG 合规或允许默认入口 cutover。
