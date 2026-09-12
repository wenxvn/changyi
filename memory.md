# Memory — P1 Final Closeout / Legacy Migration Complete

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`.
- `app.py` is a thin `python app.py` and import compatibility layer.
- Do not reopen architecture refactors, Flask/React swaps, LLM/Agent, accounts, cloud records, or extra cities.

## Safety invariants

- Assistive demo only. Emergency and insufficient-information publication stays safety-first.
- Red-flag/triage rule changes, thresholds, disease model, recommendation weights, traffic semantics still require L3/L4.
- Safety Evaluation: 38 cases, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0. Data quality still has 187 registered issues.

## Closeout facts

- Doctor photos: h6 czsetyy 74 mapped (73 exact name + 1 manual 郭海滨（兼）→59_郭海滨.jpg); h11 czdqyy 201 via `photo_file`. Manifest: `data/resource_provenance/doctor_photos.json`. Display only LEGACY_EXACT_MATCH / MANUAL_CONFIRMED / SOURCE_VERIFIED.
- Hospital `district` lives in Region Pack catalog from public address/name tokens; null when unreliable. Frontend must not parse addresses.
- Resources filters are tab-specific: hospital level/type/district/emergency-field; doctor hospital/department/title.
- Transit quality is per-dataset (bus_stations / taxi_operations / bike). All PROVISIONAL, rankable=false. Metadata: `data/transit/metadata.json`.
- Strict near-duplicate isolation: 24 test rows, 8/41 classes, cross-split 0, seed 42, threshold 0.8. Not comparable to random split accuracy.

## Ranking / evidence trust policy

- Hospital ranking uses public department existence only.
- Doctor academic weight remains 0.02 tie-break, not clinical ability evidence.
- Images never affect ranking scores.
- Report strict metrics honestly; do not tune data/seed to restore high scores.

## Next session starts with

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/POST_REFACTOR_BACKLOG.md`, risks. Legacy migration is closed; work from P2 backlog unless a real regression appears.
