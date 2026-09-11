# Memory — Refactor baseline

Last updated: 2026-09-11

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`; no legacy lazy adapter remains.
- `app.py` is a thin `python app.py` and import compatibility layer. Application services/domain/infrastructure remain under `backend/app/`.

## Safety invariants

- This is an assistive demo, not diagnosis or clinical decision support. Emergency and insufficient-information publication stays safety-first.
- Future red-flag/triage rule changes, thresholds, disease model, recommendation weights, traffic semantics or data definitions still require separate L3/L4 review.
- Current Safety Evaluation has 38 cases: recall 1.0, under-triage 0.0, over-triage 0.0, emergency false negative 0. This is a fixed regression result, not a clinical release claim. Data quality has 187 registered issues.

## Ranking trust policy (2026-09-11)

- Hospital ranking uses public department existence only. Provisional `derived_capability_scores`/`strength_scores` stay in the catalog for migration/debug and must not decide clinical order.
- Doctor ranking: academic weight is 0.02 across scenarios; `doctor_resource_tier` is clinical/specialty/title based, not SCI/funding based. Academic fields remain display metadata.
- Transit samples only blend into accessibility when concrete nearby evidence exists; otherwise distance-only.
- Map basemap is OSM official tiles (`tile.openstreetmap.org`), no API key. CARTO free CDN is not used.

## Current baseline

- Legacy `/api/*` routes, legacy template/JS/CSS, feedback JSONL endpoints, prediction/transit/rerank wrappers, root `doctors.json`, backup logo folders and `tools/cloudflared.exe` were removed after reference checks.
- Canonical characterization now exercises v1 triage/recommendation. Current local verification: 116 pytest passed; frontend typecheck, 16 boundary tests, 5 Playwright smoke tests and build passed.
- `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/REFACTOR_CHANGELOG.md` and `docs/POST_REFACTOR_BACKLOG.md` are the primary handoff documents.
- Location is session-only and explicit: `unknown` has null coordinates, `district` uses a labelled Region Pack reference point, and `geolocation` only follows a user-triggered browser permission request.
- Grouped model evidence lives in `evaluation/model/`. Exact fingerprint group split does not remove Jaccard≥0.8 near-duplicates (605 pairs). Next evaluation step should be Near-duplicate Group Split.

## Next session starts with

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, risks and the relevant plan/ADR. Treat `docs/POST_REFACTOR_BACKLOG.md` as deferred work, not current authorization.
