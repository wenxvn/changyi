# 设计系统

## 视觉方向

Warm Precision：温暖瓷白背景、深墨蓝文字、克制的医疗青/靛蓝、仅在安全状态使用临床红。目标是 Premium、Editorial、Calm、Trustworthy，而不是传统医院官网、政务大屏或蓝紫色后台。

## Token 计划

```text
--surface-base / --surface-raised / --surface-subtle
--text-primary / --text-secondary / --text-muted
--border-subtle / --border-strong
--accent-primary / --accent-soft
--state-success / --state-warning / --state-danger
--shadow-sm / --shadow-md / --shadow-floating
--radius-sm / --radius-md / --radius-lg / --radius-pill
--space-1 ... --space-12
--duration-fast / --duration-normal / --duration-slow
```

## 首轮 UI 审计基线（历史记录）

以下数据记录旧模板/静态 UI 的审计结果；旧运行时已经删除，当前组件基线以根目录 `ui-registry.md` 和 `frontend/` 为准。

旧版已有 CSS variables，但仍有 572 个 hex 色值、185 处 rgb/rgba、104 处 inline style，且 `app.js` 用脚本直接写图表颜色。已确认的 legacy 基线见 [UI_AUDIT_BASELINE.md](UI_AUDIT_BASELINE.md)，并已写入根目录 [ui-registry.md](../../../ui-registry.md)。后续只按可回滚的小切片迁移视觉债务；新组件不得新增绕过 token 的视觉值。

## 核心页面验收

首页、智能就医、追问、普通推荐、急症、医院/医生详情、地图、可信 AI、空态、错误态和模型不可用状态，都要在 1440×900、1280×800、768×1024、390×844 检查层级、留白、对比度、响应式和安全显著性。

## 动效

动效只沟通状态；急症页面减少动效，支持 `prefers-reduced-motion`，移动端降级。首页不得以自动轮播承载关键说明。
