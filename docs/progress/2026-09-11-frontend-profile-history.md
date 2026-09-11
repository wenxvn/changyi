# 2026-09-11 Frontend Profile / History

状态：首版完成，保留本地隐私边界与后续 L4 门禁  
变更等级：L2  
计划：[2026-09-11-frontend-profile-history.md](../plans/2026-09-11-frontend-profile-history.md)  
决策：[0006-local-demo-profile-history.md](../decisions/0006-local-demo-profile-history.md)

## 已完成

- 新增 `/profile` 路由和 Profile/History 页面，header profile button 在桌面和移动端均可访问。
- 新增 `demoProfile.ts`，集中处理版本化浏览器存储、四态校验、最多 8 条容量限制、异常降级和跨页面刷新事件。
- 历史默认关闭；开启后只写入时间、固定 `common` 场景、服务端分诊状态/标签和匹配科室，不写入原始描述、追问答案或身份字段。
- Triage 仅在无后续追问或用户跳过追问时记录摘要；Emergency 不触发普通推荐，既有安全路径未改动。
- Profile 提供本地边界说明、空态、关闭记录和二次确认清除；页面不直接访问 `localStorage`。
- 更新 frontend architecture/scorecard、迁移 scorecard、status、risk、history、review、UI registry 和 memory。

## 验证

- `npm run typecheck`：通过。
- `npm run test`：7/7 boundary tests 通过。
- `npm run build`：通过；gzip JS 约 87.1 kB，CSS 约 13.0 kB。
- `node --check static/js/app.js`、`git diff --check`：通过。
- 浏览器运行态：Profile header 入口可打开；默认空态和本地说明可见；开启开关后状态可见；390×844 下 `clientWidth=375`、`scrollWidth=375`，无横向溢出；error/warn 日志为空。

## 未完成与边界

- 未通过浏览器真实输入验证历史写入，避免在 UI 测试中传输医疗描述；源码白名单和 boundary test 已覆盖持久化边界。
- 该功能不是账号、病历、云同步或跨设备历史；若未来扩展，必须另立 L4 隐私/认证计划。
- Playwright/E2E、独立截图 baseline、对比度审查和完整 keyboard matrix 仍是 F12/F13 门禁。

## 回滚

移除 Profile route/page、`demoProfile` state module、triage 记录调用、样式和本 slice 文档即可；不影响后端 API、legacy 默认入口、Safety Gate 或推荐快照。
