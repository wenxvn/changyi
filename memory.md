# Memory — Refactor baseline

Last updated: 2026-09-11

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`; no legacy lazy adapter remains.
- `app.py` is a thin `python app.py` and import compatibility layer. Application services/domain/infrastructure remain under `backend/app/`.

## Safety invariants

- This is an assistive demo, not diagnosis or clinical decision support. Emergency and insufficient-information publication stays safety-first.
- Do not modify red-flag rules, triage thresholds, disease model, recommendation weights, traffic semantics, medical copy or data definitions without a separate L3/L4 review.
- Safety baseline remains 16 cases: recall 0.9231, under-triage 0.0769, over-triage 0.0, emergency false negative 1. Data quality has 187 registered issues; neither baseline is a release claim.

## Current baseline

- Legacy `/api/*` routes, legacy template/JS/CSS, feedback JSONL endpoints, prediction/transit/rerank wrappers, root `doctors.json`, backup logo folders and `tools/cloudflared.exe` were removed after reference checks.
- Canonical characterization now exercises v1 triage/recommendation. Current local verification: 107 pytest passed; frontend typecheck, 9 boundary tests and build passed.
- `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/REFACTOR_CHANGELOG.md` and `docs/POST_REFACTOR_BACKLOG.md` are the primary handoff documents. Process plans/progress/history/reviews were consolidated.

## Next session starts with

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, risks and the relevant ADR. Treat `docs/POST_REFACTOR_BACKLOG.md` as deferred work, not current authorization.
