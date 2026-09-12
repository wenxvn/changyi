# Frontend Design System

## Direction

Modern medical product UI：冷灰中性底、深墨文字、单一医疗青绿强调色。接近 Linear / Stripe / Apple Health 的产品密度，不使用杂志式 serif、过度负字距或宣传页大留白。

## Palette

| Token | Value | Use |
| --- | --- | --- |
| `--surface-base` | `#f3f5f6` | 页面底 |
| `--surface-raised` | `#ffffff` | 卡片/输入 |
| `--text-primary` | `#0b1418` | 主文字 |
| `--text-secondary` | `#54616a` | 次文字 |
| `--accent-primary` | `#0b6e6a` | 主操作、链接、安全青 |
| `--state-danger` | `#c23b36` | 急症/危险 |

所有新组件从 `src/styles/tokens.css` 取颜色、间距、圆角、阴影和动效。

## Type scale

- Display / H1：`clamp(1.75rem, 3.6vw, 2.75rem)`，weight 650，letter-spacing `-0.02em`
- H2 / H3：`1.375–1.625rem` / `1.125rem`
- Body：`0.9375–1.0625rem`，中文行高 `1.7`
- Caption / eyebrow：`0.6875–0.75rem`

禁止对中文标题使用 serif 与负字距超过 `-0.02em`。

## Layout

- 产品容器：`min(100% - 32px, 1200px)`
- 阅读容器：`960px`；正文最大宽约 `720px`
- Hero 内容自适应高度，不设置 `min-height: 700px+`
- 连续区块垂直间距 `48–64px`，移动端 `24–40px`
- 卡片层级：主任务卡 > 信息卡 > 平面文本；避免万物皆卡片

## Interaction

- 按钮：default / hover / active(scale 0.97) / focus-visible / disabled
- 异步动作使用 loading 图标与文案
- 页面切换与结果出现：`opacity + translateY(6px)`，`220–400ms`
- Care Path：轻微 perspective + 节点 hover 深度；移动端关闭 3D 倾斜
- 地图：列表 hover ↔ marker 高亮联动
- `prefers-reduced-motion: reduce` 关闭路径流动、脉冲与入场动画

## Content

主语言为简体中文。禁止使用“诊断”“最佳”“保证”“AI 医生”等超出系统边界或医疗安全的表达。
