# Memory — P4 Competition Demo Experience Polish Complete

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite formal frontend; Flask serves `frontend/dist`.
- `/api/v1/*` only. `app.py` is a thin compatibility layer over `backend/app/composition.py`.
- Do not reopen architecture refactors, Chatbot, accounts, cloud records, extra cities, real-time emergency/transit fakes.
- Do not restore magazine style / Dashboard / Demo Login.

## Safety invariants

- Safety always precedes personalization.
- Visit Intent and routing preferences never feed Safety Gate, never lower triage, never bypass Emergency.
- Safety Evaluation: **142 cases**, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0.

## P3+P4 visual/product facts

- Design language: cool medical SaaS. Tokens in `tokens.css` (base `#f3f5f6`, ink `#0b1418`, accent `#0b6e6a`, danger `#c23b36`).
- Container 1200px; hero auto-height.
- Care Path: CSS 3D + `idle|analysing|ready` phases; home submit lights nodes then navigates.
- Triage: ProgressiveStatus stages + steps with check marks; **results before LocationSelector/prefs** (prefs never auto-open).
- Mobile triage layout: workspace order 1, CurrentUnderstanding order 2.
- Page transition: `.page-view` 200ms opacity+6px; disabled under reduced-motion.
- Resources/Map Context Bar via `?from=triage&direction=&safety=`.
- Resources display-only: public `departments` matching `direction` are sorted first + badge「公开科室匹配」; does not change server ranking.
- Map: selected list row scrolls into view; emergency context defaults filter to emergency; tile failure shows「重试底图」.
- Footer is one compact row (~85px). Header hides region-mark below 1100px.
- Map list ↔ marker hover **and focus** via `hoveredKey`.
- DoctorAvatar class is `doctor-index-avatar`. FavoriteDoctorButton active class is `.is-active`.
- Trust model splits collapsed under `details.trust-model-details`.

## Test baseline

- pytest **169**, frontend boundary 17, Playwright 20/20, safety **142** cases.
- Bundle: CSS ~92.3KB gzip ~14.1KB; JS ~347.2KB gzip ~103.1KB.
- E2E contract must keep: headings 把症状 / 现在有什么不舒服 / 把城市资源 / 什么时候不该给出答案; buttons 开始分析 / 查看安全状态 / 开始智能分诊 / 使用本次精确定位; labels 你的描述 / 选择所在区域; map region 常州医院真实地理位置地图; texts 未使用用户定位 / 按区域参考点估算 / 区域参考点 / 技术详情; care-result-title / emergency-result-title; data-testids on resource filters.

## Next session starts with

Read `AGENTS.md`, `docs/status/current.md`, `docs/risks/register.md`. Maintain P4 demo polish + P3 visual system + P2 care-routing path.
