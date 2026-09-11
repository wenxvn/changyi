# Review：前端键盘与交互语义收口

日期：2026-09-11  
范围：`frontend/src/app/App.tsx`、`frontend/src/components/ui/Button.tsx`、首页 Journey、Resources、Map 和 frontend boundary tests  
计划：[2026-09-11-frontend-keyboard-semantics.md](../plans/2026-09-11-frontend-keyboard-semantics.md)

## 1. 计划对齐

结论：通过。复用按钮默认 type、tab/panel 关系、Journey 键盘切换和占位页清理均已实现；没有扩大到业务策略或 API。

## 2. 系统完整性

结论：通过。tab 只改变既有页面展示状态，资源和地图仍使用原有 v1 接口；`Button` 的提交行为由现有显式 `type="submit"` 调用点保留。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，当前切片没有新的 P1 代码阻断。

- [P1] 完整键盘路径、对比度、视觉 baseline、Playwright/E2E 和远端 CI 首次运行仍开放。
- [P1] Emergency 附近急诊正式路径、逐字段 provenance、完整 route parity 和 Safety Evaluation 缺口不属于本切片。
- [P2] 资源/地图 tab 后续可补完整 roving-focus 矩阵；当前已提供 selected tab 单焦点入口和 Journey 方向键。

## 总结

本切片可作为 F12 accessibility polish 的语义收口继续使用；不能单独宣称完成完整无障碍审查或 competition-ready。
