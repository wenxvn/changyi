# Memory — Refactor baseline

Last updated: 2026-09-11

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`; no legacy lazy adapter remains.
- `app.py` is a thin `python app.py` and import compatibility layer. Application services/domain/infrastructure remain under `backend/app/`.

## Safety invariants

- This is an assistive demo, not diagnosis or clinical decision support. Emergency and insufficient-information publication stays safety-first.
- Future red-flag/triage rule changes, thresholds, disease model, recommendation weights, traffic semantics or data definitions still require separate L3/L4 review. This P0 explicitly recorded and fixed only the previously reproduced colloquial emergency expressions and vague-input downgrade.
- Current Safety Evaluation has 38 cases: recall 1.0, under-triage 0.0, over-triage 0.0, emergency false negative 0, with all insufficient-information cases matched. This is a fixed regression result, not a clinical release claim. Data quality has 187 registered issues.

## Current baseline

- Legacy `/api/*` routes, legacy template/JS/CSS, feedback JSONL endpoints, prediction/transit/rerank wrappers, root `doctors.json`, backup logo folders and `tools/cloudflared.exe` were removed after reference checks.
- Canonical characterization now exercises v1 triage/recommendation. Current local verification: 114 pytest passed; frontend typecheck, 16 boundary tests, 5 Playwright smoke tests and build passed. Hospital/resource/map surfaces expose a low-dependency AMap URI without an SDK or key.
- `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/REFACTOR_CHANGELOG.md` and `docs/POST_REFACTOR_BACKLOG.md` are the primary handoff documents. Process plans/progress/history/reviews were consolidated.
- P0 correctness completion is recorded in `docs/plans/P0_CORRECTNESS_COMPLETION.md`. The active hospital catalog is `data/regions/320400/hospitals/catalog.json` with provisional provenance; unsupported capacity/rating/description fields are absent and unavailable capacity weights are zero.
- Location is session-only and explicit: `unknown` has null coordinates, `district` uses a labelled Region Pack reference point, and `geolocation` only follows a user-triggered browser permission request. Structured follow-up answers are carried separately from `original_condition`.
- Grouped model evidence lives in `evaluation/model/` and is surfaced by `/api/v1/evidence`; it remains prototype/offline evidence with near-duplicate limitations.

## Next session starts with

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, risks and the relevant plan/ADR. Treat `docs/POST_REFACTOR_BACKLOG.md` as deferred work, not current authorization.
