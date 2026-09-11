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

## New frontend components — Captured 2026-09-10

新前端位于 `frontend/`，独立使用语义 token；以下模式是 Homepage、App Shell 和最小 Triage Workspace 的一致性基线。

### New App Shell / navigation

File: `frontend/src/app/App.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `color-mix(in srgb, var(--surface-base) 82%, transparent)` with backdrop blur |
| Border | `var(--border-subtle)` |
| Border radius | navigation item uses pill-like underline; profile uses 50% |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` |
| Spacing | 10/15px nav item padding; 76px desktop header |
| Hover state | accent underline and `var(--accent-soft)` profile surface |
| Shadow | shell none; open mobile nav uses `var(--shadow-soft)` |
| Accent usage | `var(--accent-primary)` for active route and CTA |

**Pattern notes:** Desktop uses top navigation rather than a sidebar. Mobile collapses the same route set into a keyboard-accessible menu; the primary CTA remains available in the opened menu.

### Primary button

File: `frontend/src/components/ui/Button.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--accent-primary)` |
| Border | transparent; secondary uses `var(--border-default)` |
| Border radius | `var(--radius-pill)` |
| Text — primary | `var(--text-inverse)` |
| Text — secondary | `var(--text-primary)` on secondary |
| Spacing | min-height 46px, horizontal padding 19px |
| Hover state | primary `var(--accent-ink)` plus 2px lift; secondary `var(--accent-soft)` |
| Shadow | primary accent-tinted shadow; secondary none |
| Accent usage | Primary action only; disabled maps to border/muted tokens |

**Pattern notes:** Buttons communicate intent with text and optional Lucide icon. Do not use a raw color or rely on icon-only meaning for medical actions.

### Symptom composer

File: `frontend/src/pages/HomePage.tsx`, `frontend/src/pages/TriagePage.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `color-mix(in srgb, var(--surface-raised) 87%, transparent)` |
| Border | `var(--border-default)`; focus-within uses `var(--accent-primary)` |
| Border radius | `var(--radius-md)`; large workspace keeps same family |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-muted)` for placeholder/label |
| Spacing | 17–23px internal padding; 9px divider before actions |
| Hover state | focus-within accent border and low accent shadow |
| Shadow | `var(--shadow-soft)` plus `var(--shadow-inset)` |
| Accent usage | Accent only for focus and primary submit |

**Pattern notes:** Natural language is the only first-step field. Voice is visibly unavailable in this slice and is not represented as a working control. Any future structured fields must be progressive disclosure.

### Care Path visual

File: `frontend/src/components/visualization/CarePath.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | layered `var(--surface-raised)` / `var(--surface-tinted)` |
| Border | `var(--border-default)` |
| Border radius | `var(--radius-xl)` desktop, `var(--radius-lg)` mobile |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-muted)` and `var(--text-secondary)` |
| Spacing | 34px panel padding; 88px node rhythm |
| Hover state | not interactive; state is communicated by node styling |
| Shadow | `var(--shadow-float)` and `var(--shadow-inset)` |
| Accent usage | `var(--accent-primary)` active node and rail; inactive nodes stay neutral |

**Pattern notes:** The path is SVG/CSS, vertical, quiet and state-oriented. No rotation, particle effect, auto-progress or continuous expensive animation.

### Journey preview

File: `frontend/src/components/visualization/JourneyPreview.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | translucent inverse surface on `var(--text-primary)` journey section |
| Border | inverse text mixed at low opacity |
| Border radius | `var(--radius-lg)` |
| Text — primary | `var(--text-inverse)` |
| Text — secondary | inverse text mixed with transparency |
| Spacing | 25–29px panel padding; 17px footer divider spacing |
| Hover state | step list changes text and reveals directional icon |
| Shadow | `var(--shadow-inset)` |
| Accent usage | `var(--accent-primary)` stage icon, `var(--accent-soft)` line/halo |

**Pattern notes:** Key explanation is user-controlled through tabs/list buttons. There is no auto-advancing carousel. The tab set uses one selected keyboard entry point and Arrow/Home/End navigation; the preview is an explicitly labelled `tabpanel`.

### Triage result preview

File: `frontend/src/pages/TriagePage.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)`; success/warning use semantic soft surfaces |
| Border | `var(--border-default)` with semantic mixed border for status |
| Border radius | `var(--radius-md)` |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` |
| Spacing | 23px internal padding; 35px status-to-title rhythm |
| Hover state | action/retry buttons retain visible focus |
| Shadow | `var(--shadow-soft)` |
| Accent usage | Status text and surface follow server-returned status; never inferred in frontend |

**Pattern notes:** The v1 status is an assistive output. Emergency/urgent presentation must remain text-first and later receive a dedicated high-salience page before cutover.

### Follow-up prompt

File: `frontend/src/components/medical/FollowupPrompt.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-tinted)` prompt; `var(--surface-raised)` option |
| Border | accent-mixed prompt border; `var(--border-default)` option |
| Border radius | `var(--radius-md)` prompt; `var(--radius-sm)` option |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-muted)` reason/step |
| Spacing | 21px prompt padding; 9px option rhythm |
| Hover state | option accent border and `var(--accent-soft)` surface |
| Shadow | `var(--shadow-soft)` |
| Accent usage | Accent marks the next question; it does not imply a medical conclusion |

**Pattern notes:** Only one question is visible at a time. Options are buttons; free-text follow-up uses a labeled textarea. The skip action is explicit and explains that the current direction may be incomplete.

### Current understanding

File: `frontend/src/components/medical/CurrentUnderstanding.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)` |
| Border | `var(--border-default)` |
| Border radius | `var(--radius-md)` |
| Text — primary | `var(--text-primary)` for the user description |
| Text — secondary | `var(--text-secondary)` / `var(--text-muted)` for returned facts |
| Spacing | 20–21px internal padding; 12px fact rows |
| Hover state | none; status is server-returned |
| Shadow | `var(--shadow-soft)` |
| Accent usage | Status and department use semantic returned-state presentation |

**Pattern notes:** This panel separates the user’s input from system-returned status and department. It is a summary of understanding, not a diagnosis or a second decision engine.

### Safety result / resource preview

File: `frontend/src/components/medical/TriageResults.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | routine/urgent/emergency/insufficient semantic soft surfaces |
| Border | semantic mixed border with `var(--border-default)` fallback |
| Border radius | `var(--radius-md)` result; `var(--radius-sm)` resource card |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` and `var(--text-muted)` |
| Spacing | 22–25px result padding; 16px resource card padding |
| Hover state | only explicit action/retry controls; disabled detail links remain visibly unavailable |
| Shadow | `var(--shadow-soft)`; emergency uses restrained danger-tinted elevation |
| Accent usage | emergency uses icon + text + danger semantic color; recommendation explanations come from v1 |

**Pattern notes:** EmergencyResult is a separate branch and does not render ordinary ranking fields. Routine/Urgent show the hospital path before a small public-doctor preview. Recommendation scores are intentionally not rendered as percentages or user-facing confidence.

### Resource index / public data preview

File: `frontend/src/pages/ResourcesPage.tsx`, `frontend/src/api/resources.ts`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)` cards on the warm base; preview uses `var(--surface-tinted)` |
| Border | `var(--border-default)`; selected preview uses `var(--border-strong)` |
| Border radius | `var(--radius-md)` card/preview; `var(--radius-pill)` search/chips |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` / `var(--text-muted)` |
| Spacing | 20px card padding; 12px grid gap; 22px preview padding |
| Hover state | resource card raises subtly; explicit preview button keeps focus-visible state |
| Shadow | `var(--shadow-soft)` on selected/preview surfaces; inset shadow on cards |
| Accent usage | teal marks search focus, selected tab and resource action; source warning stays amber |

**Pattern notes:** The page is a read-only resource index, not a recommendation ranking. Hospitals load first; doctors load only after the tab is selected. Cards show public fields only, while the source pill states `legacy_catalog_pending_provenance` or `public_source_mixed`. Missing fields remain explicit. Selecting a card loads its v1 detail by id; loading/error/retry remain visible, and the detail provenance note does not imply official validation. Map is a separate route and is not impersonated by the index.

### Trust Center / evidence panels

File: `frontend/src/pages/TrustPage.tsx`, `frontend/src/api/evidence.ts`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)` panels on the warm base; warning notice uses `var(--state-warning-soft)` |
| Border | `var(--border-default)`; safety accent uses `var(--border-strong)`; semantic warning follows token |
| Border radius | `var(--radius-md)` panels; `var(--radius-pill)` status pill |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` / `var(--text-muted)` for scope, source and limitations |
| Spacing | 22px panel padding; 15px panel grid gap; 72px evidence section rhythm |
| Hover state | no metric hover affordance; explicit resource action retains button focus |
| Shadow | `var(--shadow-inset)` on evidence panels; no attention-grabbing metric animation |
| Accent usage | teal identifies evidence structure; amber identifies provisional/known limitations; values come from `/api/v1/evidence` |

**Pattern notes:** The Trust Center is a read-only evidence view, not a clinical validation dashboard. It must show `provisional`, “不代表临床验证”, review-required cases, data quality issues, source fingerprints and version identifiers together. Null or unavailable metrics remain “未提供”; dataset hashes support reproducibility only and do not imply provenance approval or clinical suitability.

### Local demo profile / history

File: `frontend/src/pages/ProfilePage.tsx`, `frontend/src/state/demoProfile.ts`, `frontend/src/styles/globals.css`

| Property | Confirmed pattern |
| --- | --- |
| Background | `var(--surface-raised)` and `var(--surface-tinted)` with tokenized accent notice |
| Border | `var(--border-default)`; privacy notice uses a low-opacity `var(--accent-primary)` mix |
| Border radius | `var(--radius-md)` cards, `var(--radius-sm)` preference row, circular identity/history icons |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` / `var(--text-muted)` for storage limitations |
| Spacing | 15/17/23px card rhythm; history rows separated by `var(--border-default)` |
| Interactive state | profile header button, explicit checkbox, two-step clear action and visible focus outline |
| Accent usage | teal marks local boundary and preference; danger is reserved for the clear action |

**Pattern notes:** This page is a local demo boundary, not an account page. History is opt-in and shows only a redacted status summary. The “仅保存在当前浏览器” notice, default-off state and explicit clear confirmation are part of the component contract, not optional copy.

### Accessibility shell controls

File: `frontend/src/app/App.tsx`, `frontend/src/styles/globals.css`

| Property | Confirmed pattern |
| --- | --- |
| Skip link surface | `var(--accent-ink)` with `var(--text-inverse)` and `var(--border-strong)` |
| Focus state | shared `:focus-visible` outline using the accent token; applies to buttons, anchors, textareas and inputs |
| Navigation state | active route uses accent underline plus `aria-current="page"`; mobile menu exposes `aria-expanded` and `aria-controls` |
| Spacing | skip link uses the existing 12px/16px rhythm and token spacing for viewport offset |
| Motion | route scroll uses `auto` when `prefers-reduced-motion: reduce`; CSS transitions/animations also collapse |

**Pattern notes:** The skip link is visually quiet until keyboard focus and points to a focusable main landmark. These semantics are part of the shell contract; new routes should keep a stable main target and expose their active navigation state.

### Keyboard tab and form semantics

Files: `frontend/src/pages/HomePage.tsx`, `frontend/src/pages/ResourcesPage.tsx`, `frontend/src/pages/MapPage.tsx`, `frontend/src/components/ui/Button.tsx`, `frontend/src/styles/globals.css`

| Property | Confirmed pattern |
| --- | --- |
| Tab relationship | Each visible tab has a stable id, `aria-controls` and `aria-selected`; the active content exposes the matching `tabpanel` and `aria-labelledby` |
| Keyboard behavior | Journey uses Arrow keys plus Home/End to move the selected tab; inactive tabs are removed from the normal tab sequence |
| Form safety | Shared `Button` defaults to `type="button"`; submit actions opt in explicitly with `type="submit"` |
| Focus state | Journey panel has a tokenized focus-visible outline; resource/map panels remain focusable for assistive technology navigation |

**Pattern notes:** These semantics improve navigation without introducing a second state source. Tab changes still only select already-loaded presentation data; they do not change triage, recommendation or map meaning.

### Map / resource location view

File: `frontend/src/pages/MapPage.tsx`, `frontend/src/api/map.ts`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-subtle)` map canvas with `var(--surface-raised)` resource rows and preview |
| Border | `var(--border-default)` canvas/rows; selected preview uses `var(--border-strong)` |
| Border radius | `var(--radius-lg)` map canvas; `var(--radius-md)` preview; tabs remain unboxed |
| Text — primary | `var(--text-primary)` |
| Text — secondary | `var(--text-secondary)` / `var(--text-muted)` for address, distance and provenance |
| Spacing | 24px map grid inset; 11px resource row padding; 22px preview padding |
| Hover state | marker enlarges subtly; selected list row and marker share teal state; focus-visible remains visible |
| Shadow | `var(--shadow-soft)` canvas and preview; no map auto-animation |
| Accent usage | teal marks normal resource points; danger marks the server-provided emergency field; no recommendation color without recommendation context |

**Pattern notes:** Map list and marker use the same `/api/v1/map` items. The view is a lightweight coordinate projection labeled “非导航地图”; it does not request location, fabricate distances, or imply real-time emergency availability. The source pill keeps `legacy_catalog_pending_provenance` visible.

### Legacy static asset fallback

Files: `templates/index.html`, `static/favicon.svg`, `static/images/leaflet-layers.svg`, `static/css/leaflet.css`

| Property | Confirmed pattern |
| --- | --- |
| Favicon | Explicit local `/static/favicon.svg`; no external host or tracking asset |
| Leaflet layers icon | Local SVG used for standard and retina CSS states; control dimensions remain Leaflet defaults |
| Scope | Static asset hardening only; no map data, marker behavior or navigation semantics changed |

**Pattern notes:** These assets close the two known legacy 404s from the audit without treating the legacy interface as the competition-ready frontend. Marker PNG/default-icon handling remains outside this slice until it has a separate asset inventory and visual check.
