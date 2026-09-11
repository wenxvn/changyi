# 常医智导前端迁移计划：F12 键盘与响应式可访问性收口

状态：已完成  
日期：2026-09-11  
变更等级：L1（语义、焦点和动效偏好；不改变医学状态、推荐策略或数据契约）

## 目标

完成 F12 的一组低风险可访问性收口：为并行前端增加跳过链接、当前路由语义、移动导航控制关系和 reduced-motion 一致性，让键盘用户能够快速进入主要内容并识别当前页面。

## 非目标

- 不改变页面布局、医学文案、分诊规则、红旗判断、推荐排序或 API。
- 不引入新的路由/无障碍运行时依赖；不把当前静态检查包装成完整 WCAG 合规声明。
- 不在本切片中承诺完整对比度、屏幕阅读器、E2E 或视觉 baseline 通过。

## 实施步骤

1. 更新 App Shell 的 skip link、main landmark、nav current state 和 mobile menu controls。
2. 让页面跳转滚动遵守 `prefers-reduced-motion`，补充共享 focus-visible 到 checkbox/input。
3. 增加前端边界断言，更新 architecture、scorecard、status、progress、history、review 和 UI registry。
4. 运行 typecheck、boundary/test/build、Python 回归、静态检查和 desktop/390×844 键盘语义检查。

## 验收标准

- 键盘进入页面后可见“跳转到主要内容”，main 有稳定 landmark；活动主导航具有 `aria-current="page"`。
- 移动菜单按钮有 `aria-expanded` 与 `aria-controls`，导航有稳定 id。
- reduced-motion 下 App Shell 不强制平滑滚动；共享焦点样式覆盖 checkbox/input。
- legacy `/`、既有 API、Safety/Emergency 路径和 Profile 本地隐私边界保持不变。

## 回滚

回退 App Shell 语义属性、滚动偏好、focus-visible CSS、边界测试和对应文档即可，不影响业务状态和后端。
