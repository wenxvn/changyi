# Memory — P1 Closeout Complete / Ready for P2 Care Routing

Last updated: 2026-09-12

## Architecture

- React/TypeScript/Vite is the formal frontend. Flask serves the committed `frontend/dist` build and SPA refresh routes.
- `/api/v1/*` is the only formal business API. `backend/app/api/v1/routes.py` resolves handlers from `backend/app/composition.py`.
- `app.py` is a thin `python app.py` and import compatibility layer.
- Do not reopen architecture refactors, Flask/React swaps, LLM/Agent, accounts, cloud records, or extra cities.

## Safety invariants

- Assistive demo only. Emergency and insufficient-information publication stays safety-first.
- Red-flag/triage rule changes, thresholds, disease model, recommendation weights, traffic semantics still require L3/L4.
- Safety Evaluation: **135 cases**, recall 1.0, under-triage 0.0, over-triage **0.0312** (question-stroke-signs), emergency FN 0.
- Data quality: **186** registered issues (PLACEHOLDER_TIMESTAMP 180, TIME_ORDER 6). COUNT_MISMATCH resolved.

## P1 closeout facts

- h6 doctors: declared total_doctors=74 matches 74 rows/photos/provenance.
- Doctor photos provenance **v2**: public_url ≠ original_source_url; original_image_url stays null; no fake SOURCE_VERIFIED. Statuses: 274 LEGACY_EXACT_MATCH + 1 MANUAL_CONFIRMED.
- Hospital catalog: field-level provenance for name/level/type/address/district/phone/departments/emergency. emergency ≠ real-time capacity.
- Academic patient-fit weight is **0.00** for all scenarios; display ≠ ranking.
- Grouped Near-Duplicate CV: 5-fold, same-label components never cross folds, cross-split near-duplicate max pair count 0, class coverage 41/41, mean Top-1 ≈ 0.084. Trust Center shows Random / Exact Fingerprint / Strict Near-Duplicate Single Split / Grouped CV.
- Transit still PROVISIONAL, rankable=false.

## Next session starts with

P2 Care Routing Intelligence in order:
1. Server-side doctor search/pagination API + Resources frontend pagination
2. Visit Intent (after Safety Gate)
3. Resource Routing Preferences
4. Local favorites
5. Provenance-aware import pipeline foundation
6. Recommendation explanations
7. Accessibility
8. Browser QA + full CI + docs

Read `AGENTS.md`, `README.md`, `docs/status/current.md`, `docs/architecture/current-state.md`, `docs/POST_REFACTOR_BACKLOG.md`, risks. Do not restore Dashboard/Demo Login/Chatbot/old capacity scores/academic-driven ranking.
