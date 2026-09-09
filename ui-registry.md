# UI Registry

## Baseline — Established 2026-09-09

本基线依据 `docs/competition/2026-ai-medical/UI_AUDIT_BASELINE.md` 的 legacy UI audit 建立。后续新组件应优先使用语义 token；legacy 组件逐步迁移，不在单个切片中进行无证据的大规模视觉重排。

| Property | Confirmed baseline |
| --- | --- |
| Page background | `--surface-base` / legacy `--bg` |
| Card background | `--surface-raised` / legacy `--card-bg` |
| Card border | `--border-subtle` / legacy `--border` |
| Card radius | `--radius-md` = 8px；large panels use `--radius-lg` = 12px |
| Input/button radius | `--radius-sm` = 6px；small legacy controls may use 8px |
| Pill radius | `--radius-pill` = 999px |
| Avatar radius | 50% for circular avatars; 24px allowed for branded avatar tiles |
| Text primary | `--text-primary` |
| Text secondary | `--text-secondary` |
| Text muted | `--text-muted` |
| Spacing | 4px base; new components prefer 8/12/16/24px |
| Primary accent | `--accent-primary` |
| Safety states | `--state-danger`, `--state-warning`, `--state-success` plus explicit text/icon |
| Motion | User-controlled interaction; no auto-advancing content for key explanations |

## Legacy components — Captured 2026-09-09

### Navigation item

File: `static/css/style.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--primary-light)` on hover/active |
| Border | none |
| Border radius | `var(--radius-sm)` |
| Text — primary | `var(--primary)` |
| Text — secondary | `var(--text-secondary)` |
| Spacing | `12px 24px`, `2px 8px` margin |
| Hover state | `background: var(--primary-light); color: var(--primary)` |
| Shadow | none |
| Accent usage | active state uses primary blue |

### Shared card

File: `static/css/style.css`

| Property | Class/value |
| --- | --- |
| Background | `#fff` or `#ffffff` in legacy; migrate to `--surface-raised` |
| Border | `1px solid #dbeafe` or `var(--border)` in legacy |
| Border radius | 8px, 10px, 12px and 14px variants exist; new cards use 8px |
| Text — primary | `var(--text)` or dark slate legacy values |
| Text — secondary | `var(--text-secondary)` |
| Spacing | 16px/18px/24px depending on density |
| Hover state | component-specific; must add keyboard-visible focus for interactive cards |
| Shadow | `var(--shadow)`, `var(--shadow-md)` or `var(--shadow-lg)` |
| Accent usage | primary blue; safety colors reserved for status meaning |

### Safety alert / triage

File: `static/css/style.css`, `static/js/app.js`

| Property | Class/value |
| --- | --- |
| Background | semantic danger/warning soft surface |
| Border | left accent border plus subtle outline |
| Border radius | 8px |
| Text — primary | explicit emergency/urgent label and action |
| Text — secondary | explanation and disclaimer |
| Spacing | 10–14px internal padding |
| Interactive state | action links/buttons remain visible and keyboard accessible |
| Shadow | none or low elevation |
| Accent usage | red/orange only for safety state; never communicate risk by color alone |

### Tokenized shared controls and manual carousel

Files: `static/css/style.css`, `static/js/app.js`

- Shared cards, form controls, tags and the dashboard carousel use the confirmed surface, border and radius aliases where the legacy selectors are touched.
- A global `:focus-visible` outline provides a keyboard-visible interaction state without changing medical semantics.
- Dashboard explanation content is user-controlled through pagination and touch swipe; no auto-advance timer remains for the carousel.
- This is a low-risk L1 consistency slice. Full viewport matrix, independent console report and remaining hardcoded-style migration remain open.

## Rules for future UI work

- 新组件不得新增未经 token 解释的颜色、圆角或间距值。
- 急症提示必须在结果首屏，使用文字、图标和颜色冗余表达；不得被轮播或浮层遮挡。
- 动态图表允许通过 CSS custom property 设置数据宽度/高度，但不再内联写静态视觉样式。
- 所有可交互卡片必须有 `:focus-visible`；所有异步流程必须有 loading、empty、error 和 model-unavailable 状态。
- 每次新增或修改 UI 组件后运行 imprint 并更新本 registry。
