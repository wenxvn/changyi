# UI Registry

## 2026-10-11 Ambient intelligence layer (CSS-only)

全站环境层：`body::before`三色 mesh aurora（青/蓝/紫，均为 accent 系低透明）+46s 缓慢漂移，`body::after`蓝图网格（顶部径向渐隐）；hero `h1 em`渐变墨字；主按钮 hover 流光（复用空闲 `::after`，子元素提 `z-index:1` 保文字在上）；hero 视觉卡细指针悬停 3D 微倾（2.5°/-3°）；首页在线圆点 2.6s 呼吸；分组卡片 stagger 入场（90ms 步进）；证据数字 tabular-nums。全部 transform/opacity 合成动画，无新依赖；全局 reduced-motion 块自动兜底；未改任何文案/选择器/分支逻辑。

## 2026-10-10 Followup slot linkage (read-only)

`FollowupPrompt`直接展示服务端`missing_slots[0]`为“本题主要补充”，并说明回答后证据卡同步更新。复用`followup-prompt__reason`既有样式，无新token/颜色；空状态不渲染；不改变追问逻辑与Safety。

## 2026-10-10 Followup evidence diff (read-only)

`TriagePage`在追问重算前快照上一轮`symptom_tags/department_candidates/matched_department`（`previousTags/previousDepts/previousDept`），仅用于展示差异，不参与任何医学判断，服务端每次全量重算。新条目用既有`small`文字标注“补充后新增”，科室变化标注“补充后更新：A → B”；首轮（快照为空）不标注，避免误导。复用`context-card__tags`/`care-result__why`既有样式，无新颜色/动画；空状态不渲染，急症分支不走此路径。

## 2026-10-10 Triage evidence read-only cards

`CurrentUnderstanding`新增`understanding-symptoms`症状证据卡，`TriageResults`新增`result-dept-evidence`科室依据卡。复用`context-card__tags`/`care-result__why`/`eyebrow`既有样式与token，不新增颜色/圆角/间距；静态只读列表，无交互、无动画，`prefers-reduced-motion`不受影响；空状态不渲染（长度门控），Safety出口仍优先，`population_context/score0`仅标人群入口，不标疾病概率。源`frontend/src/api/schemas.ts`对象解析、`frontend/src/types/api.ts`结构类型。

## 2026-10-03 Unresolved risk reconfirmation

W48保留未确认红旗原选项，unknown不算完成一步；同qid新答案替换旧答案，避免API拒重复ID。复用FollowupPrompt和既有按钮/focus/token，无新颜色布局；后续present用既有ER 120界面，none仍原政策，未知不当安全确认。源TriagePage与本次dist哈希独立记录，不能把Python实验身份当UI源码证明。

## 2026-10-03 Accepted auxiliary scope explanation

W33已接受辅助结果也显示后端notice，复用`care-result__reason`及现有text-secondary/text-sm，不增CSS、按钮或颜色；`model-scope-notice`区别既有拒答`model-abstention-notice`，不把已提供结果称拒答。普通文字说明可能遗漏其他描述、分值非患病概率，内部input_coverage字段不直接展示。Safety出口仍优先，不显示普通模型范围说明。

## 2026-10-03 Auxiliary abstention explanation

TriageResults的辅助拒答提示沿用`care-result__reason`：margin 0、text-secondary、text-sm，不新增颜色、边框或按钮。显示后端人可读notice与较小的辅助范围说明；内部原因码不在此提示展示。Safety优先时不重复模型说明，信息不足不使用“危险信号已排除”的兜底语句。解释与科室方向分开，模型拒答不被呈现为整体安全结论。

## 2026-10-03 Pending review interaction

FollowupPrompt与CareActions复用现有样式：space-3间距、space-4内边距、radius-lg、border-subtle；前者保留accent-soft背景，后者surface-raised/shadow-xs。待复核按钮沿用secondary Button及既有focus/disabled状态，不增加视觉token。未知状态的跳过按钮写“稍后补充，保留待复核状态”，下一步先确认危险信号；手动“浏览医疗资源目录”不表示已经匹配资源。目录URL保留分诊上下文，刷新仍展示当前状态提示。

## 2026-10-03 DoctorAvatar delivery

DoctorAvatar复用既有颜色/字号/圆角，不重新设计页面。图片按80/160/320派生尺寸响应式加载，保留原图与来源状态；索引懒加载，主入口JS不包含整份索引。加载期间显示姓名首字；派生图失败回退原图，原图失败显示首字；photoUrl变化时不会沿用上一位医生的失败状态或照片。装饰图片保持aria-hidden，医生姓名由卡片正文提供。

## Baseline — Established 2026-09-11

正式 UI 由 `frontend/` 的 React/Vite 构建产物提供；Flask 只负责托管 `frontend/dist/` 和 `/api/v1/*`。本 registry 记录当前组件约束，不再把已删除的 legacy 模板、JS 或 CSS 作为运行时事实。

| Property | Confirmed baseline |
| --- | --- |
| Page background | `--surface-base` |
| Card background | `--surface-raised` |
| Card border | `--border-subtle` |
| Card radius | `--radius-md` = 8px；large panels use `--radius-lg` = 12px |
| Input/button radius | `--radius-sm` = 6px |
| Pill radius | `--radius-pill` = 999px |
| Avatar radius | 50% for circular avatars; 24px allowed for branded avatar tiles |
| Text primary | `--text-primary` |
| Text secondary | `--text-secondary` |
| Text muted | `--text-muted` |
| Spacing | 4px base; new components prefer 8/12/16/24px |
| Primary accent | `--accent-primary` |
| Safety states | `--state-danger`, `--state-warning`, `--state-success` plus explicit text/icon |
| Motion | User-controlled interaction; no auto-advancing content for key explanations |

## Rules for future UI work

- 新组件不得新增未经 token 解释的颜色、圆角或间距值。
- 急症提示必须在结果首屏，使用文字、图标和颜色冗余表达；不得被轮播或浮层遮挡。
- 动态图表允许通过 CSS custom property 设置数据宽度/高度，但不再内联写静态视觉样式。
- 所有可交互卡片必须有 `:focus-visible`；所有异步流程必须有 loading、empty、error 和 model-unavailable 状态。
- 每次新增或修改 UI 组件后运行 imprint 并更新本 registry。
- 结果页的 emergency/urgent/insufficient 状态必须由 v1 返回值驱动，前端不得自行推断。

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

**Home variant:** on the homepage the composer is the primary call to action — a 3px accent top edge, accent-mixed border, `var(--shadow-md)` elevation, a 104px textarea and a 44px submit button. Idle state keeps the submit button at full opacity with a desaturated accent fill (rather than washing it to 0.48 opacity) so the primary action stays readable before typing.

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

### Triage decision surface (conclusion banner + next step)

File: `frontend/src/pages/TriagePage.tsx`, `frontend/src/components/medical/TriageResults.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)`; routine/urgent/emergency/insufficient use semantic soft gradients |
| Border | semantic mixed border per status; 4px left rail repeats the status color |
| Border radius | `var(--radius-xl)` banner; `var(--radius-lg)` next-step card |
| Text — primary | `var(--text-primary)`; status headline is the page's largest text |
| Text — secondary | `var(--text-secondary)` lede; `var(--text-muted)` status note and disclaimer |
| Spacing | 20px banner padding; 12px internal rhythm; steps separated from the rationale by a divider |
| Hover state | only explicit controls react; the banner itself is static |
| Shadow | `var(--shadow-sm)` banner; `var(--shadow-xs)` next-step card |
| Accent usage | Status color is server-returned and never inferred in the frontend; the department block uses the accent surface |

**Pattern notes:** The first screen answers three questions in order — how urgent, which direction, what to do next. Structure is fixed: status pill + plain sentence, headline, one-line explanation, department/direction block, "为什么这样判断" list, then the path rail (安全门 → 就医方向 → 城市资源). Emergency is a separate branch that renders no ranking fields; the call-120 action comes first and takes the largest button size, and the ordinary next-step card is not rendered.

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

### Current understanding (context rail)

File: `frontend/src/components/medical/CurrentUnderstanding.tsx`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)` |
| Border | `var(--border-subtle)` |
| Border radius | `var(--radius-lg)` |
| Text — primary | `var(--text-primary)` for the user description |
| Text — secondary | `var(--text-muted)` for returned facts |
| Spacing | 16px internal padding; 7px fact rows |
| Hover state | none; status is server-returned |
| Shadow | `var(--shadow-xs)` |
| Accent usage | Status pill and fact values use semantic returned-state presentation |

**Pattern notes:** This card lives in the triage context rail and only restates what the system read plus the returned status/direction. It is deliberately short: the long-form path explanation belongs to the decision surface, and this card must never read as a second decision engine or a diagnosis.

### Resource path preview / next-step checklist

Files: `frontend/src/components/medical/ResourcePreview.tsx`, `frontend/src/components/medical/recommendationDisplay.ts`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | `var(--surface-raised)` cards inside a `var(--surface-sage-wash)` headed panel |
| Border | `var(--border-subtle)`; hover uses an accent-mixed border |
| Border radius | `var(--radius-lg)` panel; `var(--radius-md)` cards; `var(--radius-pill)` action pills |
| Text — primary | `var(--text-primary)` hospital/doctor name |
| Text — secondary | `var(--text-secondary)` explanations; `var(--text-muted)` address/notice |
| Spacing | 16–20px card padding; 12px card gap |
| Hover state | card raises 1px and shows the accent border; navigation/details pills fill with `var(--accent-soft)` |
| Shadow | `var(--shadow-xs)` panel and cards |
| Accent usage | Rank badge and matched department use the accent surface; emergency is never shown here |

**Pattern notes:** Ranking payload fields are read once through `recommendationDisplay.ts`. Only explanations, matched department, address, distance and the traffic summary the API actually returns are rendered — no invented score, rating, capacity or real-time status. Distance renders only when the server computed a non-null value. The next-step checklist owns the single "查看当前资源路径" trigger; when the panel is already loaded the same label navigates to the full resource list, so the button is never removed.

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

**Pattern notes:** The page is a read-only resource index, not a recommendation ranking. Hospitals load first; doctors load only after the tab is selected. Cards are decision-first: identity row (logo, name, level · type · district), optional 「公开科室匹配」 flag, address, up to three department chips, then a primary 「查看公开资料」 pill plus the AMap action. Cards render public fields only, and the source pill states the provisional catalog/mixed-source boundary. Selecting a card loads its v1 detail by id into a full-width panel below the list, scrolls it into view, labels the active card 「查看中」, and closes with the panel's close button or Escape; loading/error/retry remain visible, and the provenance note does not imply official validation. Emergency-department presence is a low-key note on the card ("目录记录含急诊字段"), never a badge that competes with the match flag. Map is a separate route and is not impersonated by the index.

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

**Pattern notes:** Map list and marker use the same `/api/v1/map` items. The workbench is map-first (map left, synchronised resource list right, hint below) and the long distance/source notice is folded into a `details` disclosure so it does not push the map below the fold. Markers enlarge on hover but do not overlap-resolve; selecting any marker or row scrolls the matching row into view and reveals the resource preview under the map. The view uses the real OSM base map with a visible attribution and a 「重试底图」 fallback; it does not request location without a user action, fabricate distances, or imply real-time emergency availability. Unknown location keeps distance null; a selected district is visibly a reference-point estimate, and precise coordinates are session-only. Each resource may expose a source-aware AMap navigation/search action, while the source pill keeps the provisional catalog boundary visible. In the emergency context the map defaults to the emergency-field filter and the map page is reachable from the emergency result itself.

### Emergency facilities panel

File: `frontend/src/components/medical/EmergencyFacilities.tsx`, `frontend/src/api/map.ts`, `frontend/src/styles/globals.css`

| Property | Class/value |
| --- | --- |
| Background | danger-soft mixed with `var(--surface-raised)` |
| Border | danger-mixed `var(--border-subtle)` |
| Border radius | `var(--radius-lg)` |
| Text — primary | `var(--text-primary)` hospital name; heading uses the danger mix |
| Text — secondary | `var(--text-muted)` level/type and address |
| Spacing | 16px panel padding; 9px list rows |
| Hover state | navigation pill fills with `var(--state-danger-soft)` |
| Shadow | none; the panel reads as part of the emergency card |
| Accent usage | danger marks emergency framing only; it never implies confirmed availability |

**Pattern notes:** The panel renders only records whose catalogue field already marks an emergency department, taken from the same read-only `/api/v1/map` payload. It states plainly that a recorded emergency department does not mean the hospital can currently admit, and that real emergencies follow 120 dispatch. It never blocks or outranks the call-120 action.

### Flask-served React release shell

Files: `frontend/index.html`, `frontend/src/app/App.tsx`, `backend/app/composition.py`

| Property | Confirmed pattern |
| --- | --- |
| Surface | tokenized React shell and page surfaces from `frontend/src/styles/tokens.css` |
| Asset delivery | Flask serves the versioned `frontend/dist` build and keeps `/static/favicon.svg` local |
| Route behavior | `/`, `/triage`, `/resources`, `/map`, `/trust`, `/profile` all resolve to the same shell on refresh |
| API boundary | page state uses the shared client and `/api/v1/*`; no legacy route fallback |

**Pattern notes:** The built shell is the only formal frontend. Missing build output returns a clear service error rather than silently serving a second UI.

W71（2026-10-04）：Trust模型范围文案区分症状—疾病离线评测与城市资源目录/排序，明确不对应中文患者科室准确率；沿用原面板与tokens，不改变数值/布局。1440/1280源路径及披露验证、最终75浏览器通过。

W73：Trust主模型卡明确保存随机切分的症状编码疾病分类来源，来源不足则待核对；既有数值/组件/tokens保持，近重复风险可见，76浏览器验证通过。

W74：Resources详情加载依赖稳定kind/id与显式重试，同资源目录对象刷新不清空已显示详情；不同资源与关闭仍取消旧请求。固定异步控制10、照片回退20与完整77浏览器通过，样式/医疗规则不改。
