# Memory — P3 Frontend Product Redesign Complete

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite formal frontend; Flask serves `frontend/dist`.
- `/api/v1/*` only. `app.py` is a thin compatibility layer over `backend/app/composition.py`.
- Do not reopen architecture refactors, Chatbot, accounts, cloud records, extra cities, real-time emergency/transit fakes.

## Safety invariants

- Safety always precedes personalization.
- Visit Intent and routing preferences never feed Safety Gate, never lower triage, never bypass Emergency.
- Safety Evaluation: **142 cases**, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0.
- Data quality: **186** registered issues.

## P3 visual/product facts

- Design language: cool medical SaaS (Linear/Stripe/Apple Health feel). No serif, no magazine letter-spacing.
- Tokens: base `#f3f5f6`, ink `#0b1418`, accent `#0b6e6a`, danger `#c23b36`. All from `tokens.css`.
- Container 1200px; hero auto-height (never min-height 700+).
- Care Path uses lightweight CSS 3D + flow dash; disable 3D on mobile; respect prefers-reduced-motion.
- Triage is a decision workbench: stepper + CurrentUnderstanding sidebar + collapsible prefs (`<details>`).
- Map list ↔ marker hover linkage via `hoveredKey`.
- DoctorAvatar class is `doctor-index-avatar` (not `doctor-avatar`).
- FavoriteDoctorButton active class is `.is-active`.

## Test baseline

- pytest **169**, frontend boundary 17, Playwright 20/20, safety **142** cases.
- E2E contract must keep: headings 把症状 / 现在有什么不舒服 / 把城市资源 / 什么时候不该给出答案; buttons 开始分析 / 查看安全状态 / 开始智能分诊 / 使用本次精确定位; labels 你的描述 / 选择所在区域; map region 常州医院真实地理位置地图; texts 未使用用户定位 / 按区域参考点估算 / 区域参考点 / 技术详情; care-result-title / emergency-result-title; data-testids on resource filters.

## Deleted this round

- `app.py.bak_algorithm_feedback_20260619`, root session notes, audit screenshots.
- Magazine CSS (serif, -0.075em, 790px hero, 650px trust, 100vh empty shells).

## Next session starts with

Read `AGENTS.md`, `docs/status/current.md`, `docs/risks/register.md`. Maintain P3 visual system + P2 care-routing path; do not restore magazine style / Dashboard / Demo Login / Chatbot / academic-driven ranking.
