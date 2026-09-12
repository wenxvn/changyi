# Memory — P1 Closeout + P2 Care Routing Baseline Complete

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite formal frontend; Flask serves `frontend/dist`.
- `/api/v1/*` only. `app.py` is a thin compatibility layer over `backend/app/composition.py`.
- Do not reopen architecture refactors, Chatbot, accounts, cloud records, extra cities, real-time emergency/transit fakes.

## Safety invariants

- Safety always precedes personalization.
- Visit Intent and routing preferences never feed Safety Gate, never lower triage, never bypass Emergency.
- Safety Evaluation: **135 cases**, recall 1.0, under-triage 0.0, over-triage 0.0312, emergency FN 0.
- Data quality: **186** registered issues. COUNT_MISMATCH resolved.

## P2 product facts

- Doctor list is server-side paginated: page_size default 24 max 100; filters q/hospital/department/title; facets included.
- Visit intent contract: first_visit / follow_up / review_results / procedure_consult / unsure → ranking scenario only.
- Routing preferences: district/distance/continuity, default off. Continuity boosts favorites only when enabled.
- Favorites: localStorage `changyi.favorite_doctors.v1`, only `doctor_id` + `created_at`.
- Import pipeline: `data/raw` snapshots are read-only; app layer must not read them. Quality gate: rankable only with source+license+timestamp+schema.
- Academic patient-fit weight is 0.00. Transit PROVISIONAL, rankable=false.
- Grouped CV: 5-fold, cross-split near-duplicate max 0, mean Top-1 ≈ 0.084.

## Test baseline

- pytest 143, frontend boundary 17, Playwright 20/20, safety 135 cases.

## Next session starts with

Read `AGENTS.md`, `docs/status/current.md`, `docs/risks/register.md`. Maintain P2 care-routing path; do not restore Dashboard/Demo Login/Chatbot/old scores/academic-driven ranking. Full CI still needs remote push confirmation if requested.
