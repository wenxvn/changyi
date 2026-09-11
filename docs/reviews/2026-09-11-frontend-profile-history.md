# Review：Frontend Profile / History

日期：2026-09-11  
范围：`frontend/src/pages/ProfilePage.tsx`、`frontend/src/state/demoProfile.ts`、`frontend/src/app/App.tsx`、`frontend/src/pages/TriagePage.tsx` 和对应文档  
计划：[2026-09-11-frontend-profile-history.md](../plans/2026-09-11-frontend-profile-history.md)  
决策：[0006-local-demo-profile-history.md](../decisions/0006-local-demo-profile-history.md)

## 1. 计划对齐

结论：通过，F11 首版范围已完成。

- `/profile` 路由、header 入口、空态、开关、清除确认和本地免责声明已实现。
- 历史默认关闭，state module 只允许脱敏状态摘要，最多保留 8 条。
- 没有新增账号、后端历史、医学规则、推荐排序或外部写入。

## 2. 系统完整性

结论：通过。

- 页面通过 `demoProfile` module 读写，不直接使用 `localStorage`；异常读取/写入会降级，不阻断主流程。
- Triage 只传入服务端返回的 `triage_status`、`triage.label`、`matched_department`；原始输入和追问答案不在 history schema 中。
- 移动端保留 profile 入口，页面在 390×844 无横向溢出；focus-visible 和 reduced-motion 继承共享样式门禁。

## 3. 生产准备度

结论：未达到最终 cutover 门槛，但当前切片没有新的 P1 代码阻断。

- [P1] 本地历史可能在共享设备上被看到，页面已默认关闭、明确当前浏览器范围并提供二次确认清除；账号/云同步仍禁止直接扩展。
- [P1] 完整 E2E、视觉 baseline、keyboard/contrast/reduced-motion QA、正式急诊路径和逐字段 provenance 仍待完成。
- [P2] 当前历史只有状态级摘要，不能恢复完整会话；这是隐私边界下的有意取舍。

## 总结

Profile/History 首版可以用于本地并行前端演示，不应被解释为登录用户中心、医疗档案或临床记录；legacy 默认入口继续保留。
