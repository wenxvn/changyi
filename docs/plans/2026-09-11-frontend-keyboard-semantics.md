# 常医前端重构计划：键盘与交互语义收口

状态：已完成  
日期：2026-09-11  
变更等级：L1（无障碍和表单语义；不改变业务、数据或医学逻辑）

## 目标

收口并行前端首版中剩余的交互语义：让复用按钮默认不会提交表单，让首页 AI Journey、资源页和地图筛选的 tab 与 panel 关系可被键盘和辅助技术识别，并移除已经没有调用路径的旧占位页。

## 非目标

- 不修改任何 API、分诊状态、推荐排序、医院/医生数据或急症文案。
- 不把地图“含急诊字段”提升为实时急诊能力，不改变地图数据契约。
- 不引入新的前端依赖或自动化医学判断。

## 验收

- `Button` 默认输出 `type="button"`，提交表单的调用点仍显式使用 `type="submit"`。
- Journey、资源和地图 tab 具有唯一 id、`aria-controls`、选中态和对应 `tabpanel`；Journey 支持方向键/Home/End 移动。
- TypeScript、边界测试、production build、浏览器键盘 smoke 和 diff 检查通过。

## 实施结果

- 已完成上述语义收口；浏览器运行态确认 Journey `ArrowRight` 会切换 selected tab 和 preview panel，Resources/Map 的 tab/panel 在 AX 树中可见。
- frontend boundary tests 9/9、typecheck、build 和 `git diff --check` 通过。

## 回滚

恢复本计划涉及的 JSX/CSS/边界测试即可；不需要回滚 API、数据、模型或 legacy 入口。
