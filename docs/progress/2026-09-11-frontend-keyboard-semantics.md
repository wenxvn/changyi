# 2026-09-11 前端键盘与交互语义收口进度

## 本次完成

- `Button` 组件默认使用 `type="button"`，避免在未来被放入表单时产生隐式提交。
- App Shell footer、首页 Journey 和摘要重试按钮补齐显式 button type，并移除无调用路径的旧占位页。
- 首页 Journey 增加 tab/panel 语义、选中 tab 单焦点入口及 Arrow/Home/End 键盘切换；资源页和地图筛选增加 tab/panel 关联。
- 新增前端边界测试，锁定这些语义和表单安全约束。

## 验证

- `npm run typecheck`：通过。
- `npm run test`：9/9 通过。
- `npm run build`：通过，gzip 约 JS 87.4 kB、CSS 13.1 kB。
- 浏览器键盘 smoke：通过；Journey `ArrowRight` 切换 selected tab 和 preview panel，Resources/Map AX 树显示稳定 tab/panel 关联。

## 未完成与下一步

完整 keyboard/contrast 矩阵、Playwright/E2E、截图 baseline 和远端 CI 首次运行仍开放；本切片不改变医学逻辑和 API。

## 回滚

回退本切片的前端 JSX/CSS、测试和文档即可恢复 F12 之前的交互语义；不影响 legacy 默认入口。
