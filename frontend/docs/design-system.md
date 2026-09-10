# Frontend Design System

## Direction

Warm Precision：温暖瓷白、深墨蓝、克制的医疗青与灰绿，语义安全色只用于表达安全状态。页面以编辑式排版、留白、细线和少量功能卡片组织信息，不使用后台侧边栏或 Dashboard Everywhere。

## Token usage

所有新组件从 `src/styles/tokens.css` 取颜色、间距、圆角、阴影和动效。组件 CSS 不直接写 hex、rgb/rgba 或未经说明的色板值。

## Type scale

- Display：`clamp(2.75rem, 7vw, 6.5rem)`，用于首页主标题。
- Section：`clamp(2rem, 4vw, 4rem)`，用于 Editorial 章节。
- Body：`1rem–1.125rem`，中文阅读行高 `1.7`。
- Label：`0.6875rem–0.8125rem`，英文采用 letter spacing 表达元信息。

## Layout

- 内容最大宽度 `min(100% - 2 * 24px, 1440px)`。
- 桌面首页使用 1/1.1 比例 Hero；移动端改为单列并把 Care Path 放在输入之后。
- Editorial 内容尽量使用 grid、divider 和 whitespace；Card 只表示功能对象。

## Interaction

- 所有按钮有 hover、focus-visible、active、disabled 和 loading 语义。
- 关键说明不自动轮播；AI Journey 由用户选择步骤。
- `prefers-reduced-motion: reduce` 下关闭路径绘制和入场动画。

## Content

主语言为简体中文，英文仅作小型 eyebrow/label。禁止使用“诊断”“最佳”“保证”“真实数据”等未经证据或超出系统边界的表达。
