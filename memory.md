# Memory — P1 product completion baseline

Last updated: 2026-09-11

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`.
- `app.py` is a thin `python app.py` and import compatibility layer.

## Safety invariants

- Assistive demo only. Emergency and insufficient-information publication stays safety-first.
- Red-flag/triage rule changes, thresholds, disease model, recommendation weights, traffic semantics still require L3/L4.
- Safety Evaluation: 38 cases, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0. Data quality still has 187 registered issues.

## Product capabilities restored in P1

- `DoctorAvatar` / `HospitalLogo` shared components with onError fallbacks.
- Resources filters: hospital level/type; doctor hospital/department/title; URL state kept.
- Expert preference UI maps to backend `system | wish_expert | no_expert` (default system).
- Voice input is Speech→Text only; no auto-submit, no form auto-fill.
- `TransitQualityGate` currently marks bus/taxi/bike PROVISIONAL and `rankable=false`, so ranking stays distance-only.

## Ranking / evidence trust policy

- Hospital ranking uses public department existence only.
- Doctor academic weight remains 0.02 tie-break, not clinical ability evidence.
- Model evidence now includes Random, Exact fingerprint, Near-duplicate same-label (primary), Near-duplicate global (comparison).
- Near-duplicate same-label metrics are much lower than random/fingerprint; report honestly, do not tune data to restore high scores.

## Next session starts with

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/POST_REFACTOR_BACKLOG.md`, risks. Do not re-open architecture refactors unless authorized.
