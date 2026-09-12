# Memory — P2 Baseline Fix Round Complete

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite formal frontend; Flask serves `frontend/dist`.
- `/api/v1/*` only. `app.py` is a thin compatibility layer over `backend/app/composition.py`.
- Do not reopen architecture refactors, Chatbot, accounts, cloud records, extra cities, real-time emergency/transit fakes.

## Safety invariants

- Safety always precedes personalization.
- Visit Intent and routing preferences never feed Safety Gate, never lower triage, never bypass Emergency.
- Question/history context is distinguished from first-person current symptoms; critical keywords do not escalate general medical questions.
- Safety Evaluation: **142 cases**, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0.
- Data quality: **186** registered issues. COUNT_MISMATCH resolved.

## P2 product facts

- Doctor list is server-side paginated: page_size default 24 max 100; filters q/hospital/department/title; facets included.
- Visit intent contract: first_visit / follow_up / review_results / procedure_consult / unsure → ranking scenario only.
- `procedure_consult` has its own ranking profile and does **not** inherit emergency surgery semantics.
- Routing preferences: district/distance/continuity, default off. Distance and district preferences enter scoring **before** candidate ranking. Continuity boosts favorites only when enabled.
- Disease model is secondary evidence only; it must not alone decide patient-facing `matched_department`.
- Favorites: localStorage `changyi.favorite_doctors.v1`, only `doctor_id` + `created_at`.
- Import pipeline: `data/raw` snapshots are read-only; app layer must not read them. Quality gate: rankable only with source+license+timestamp+schema.
- Academic patient-fit weight is 0.00. Transit PROVISIONAL, rankable=false.
- Grouped CV: 5-fold, cross-split near-duplicate max 0, mean Top-1 ≈ 0.084; model may not decide department alone.

## Test baseline

- pytest **169**, frontend boundary 17, Playwright 20/20, safety **142** cases.
- Canonical snapshot includes `excluded_evidence` / `routing_preferences` / `triage_scenario` / `visit_intent`.

## Next session starts with

Read `AGENTS.md`, `docs/status/current.md`, `docs/risks/register.md`. Maintain P2 care-routing path; do not restore Dashboard/Demo Login/Chatbot/old scores/academic-driven ranking. Remote CI should be green after push; confirm if requested.
