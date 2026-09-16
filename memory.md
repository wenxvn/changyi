# Memory — Care Routing Algorithm Round1 + Round2 + Round3

Last updated: 2026-09-16

## Architecture

- React/TypeScript/Vite formal frontend; Flask serves `frontend/dist`.
- `/api/v1/*` only. `app.py` is a thin compatibility layer over `backend/app/composition.py`.
- Do not reopen architecture refactors, Chatbot, accounts, cloud records, extra cities, real-time emergency/transit fakes.
- Do not restore magazine style / Dashboard / Demo Login.
- **Algorithm work lives only in `evaluation/care_routing/`** — never wire it into `/api/v1` or Safety Gate without L3.
- **Uncertainty → Adaptive Inquiry = `RESEARCH_ONLY`**.
- **Triage classifier Shadow Mode = `RESEARCH_ONLY`**.

## Safety invariants

- Safety always precedes personalization.
- Visit Intent and routing preferences never feed Safety Gate, never lower triage, never bypass Emergency.
- Safety Evaluation: **142 cases**, recall 1.0, under-triage 0.0, over-triage 0.0, emergency FN 0.
- Emergency branch renders no ranking fields; `拨打 120` is the first and largest action.
- Model probabilities are uncalibrated assistive scores, not medical confidence.
- Red-flag negation parsing must never enter production Safety.

## Algorithm exploration (2026-09-16)

### Round1
- Reproduce: `.venv/bin/python -m evaluation.care_routing.run_experiments --write`
- Honest split = same-label near-duplicate triple split; random split metrics are leaky.

### Round2
- Report: `evaluation/care_routing/ROUND2_REPORT.md`
- Reproduce: `.venv/bin/python -m evaluation.care_routing.run_round2 --write`
- Three-state negation unit 10/10; IG does **not** beat Random on honest simulation.
- Round2 LR/SVM=1.0 on n=16 was **largely a small-sample fluke**.

### Round3
- Report: `evaluation/care_routing/ROUND3_REPORT.md`
- Reproduce: `.venv/bin/python -m evaluation.care_routing.run_round3 --write`
- expanded_41 = 1289 rows; honest quota test ≈213 / 25 diseases (structured ceiling ≈8).
- 5-seed: NB 0.173 / LR 0.265 / SVM 0.267 — direction real, magnitude modest.
- Learning curve still rising 20%→100% (+9~13pp) → more data helps.
- Direct Department 0.450 ≫ disease-first dept 0.291 → product story should be department-first.

### Round4
- Report: `evaluation/care_routing/ROUND4_REPORT.md`
- Reproduce: `run_round4 --write` or `run_round4_refresh` for selective-only refresh
- Best Direct Dept: **char n-gram TF-IDF + LR = 0.742±0.013** (vs Round3 0.450)
- Selective: target 80% → retained Acc **0.807**, wrong-conf <1%
- Hardest confusions: many depts → 皮肤科; data gaps: 呼吸内科/泌尿外科/内分泌代谢科
- Representation ablation: char n-gram ≫ binary/word/fusion under same LR
- Shadow Mode still `RESEARCH_ONLY` because ECE≈0.26
- Skeleton: `Safety Gate → Direct Department → Selective Abstention → Care Routing`


## Frontend ownership map (P5)

- `pages/TriagePage.tsx` — layout + state owner. Renders: submitted summary, `ProgressiveStatus`, `TriageResults`, `FollowupPrompt`, `ResourcePreview`, context rail (`CurrentUnderstanding` + `CareActions` + `LocationSelector` + `triage-prefs`).
- `components/medical/TriageResults.tsx` — owns the conclusion banner (`care-result`) and exports `CareActions`. Emergency guard lives in TriagePage as `hasActionableResult(result, submittedCondition)` and also inside `TriageResults`.
- `components/medical/ResourcePreview.tsx` + `recommendationDisplay.ts` — single owner of how recommendation fields are formatted. No scores rendered.
- `hooks/useRecommendations.ts` — `requestKey` covers condition/location/preferences/favorites/follow-up answers; **one request per identity** via `inFlightRef`/`settledRef` (do not add `data`/`loading` to the effect deps or duplicates return); `reload()` is the only repeat path.
- `components/medical/EmergencyFacilities.tsx` — public emergency-field list from `/api/v1/map`; never claims real-time availability.
- Resources detail is **in-flow below the grid** (not sticky/overlay): `.resource-detail`, scroll-into-view via `selectResource()`, `Esc` closes.
- Map workbench: `.map-workbench` (map left / list right), long notice inside `details.map-notice`.

## Test contracts that must keep passing

`frontend/test/*.mjs` regex-matches source text. Keep these literals present:

- `TriagePage.tsx`: `followup_answers: followupAnswers`, `submittedCondition`, `if (!result || result.triage_status === "EMERGENCY")`, `name="visit-intent"`, `data-testid="pref-continuity"`.
- `TriageResults.tsx`: `EmergencyResult`, `拨打 120`, no `composite_score` / `match_score`.
- `globals.css`: `.skip-link:focus-visible`, `input:focus-visible`, `.favorite-doctor-button:focus-visible`, `.resource-index-pagination`.

E2E must keep: headings 把症状 / 现在有什么不舒服 / 把城市资源 / 什么时候不该给出答案; buttons 开始分析 / 查看安全状态 / 查看当前资源路径 / 使用本次精确定位 / 暂时跳过，查看当前就医方向; labels 你的描述 / 选择所在区域; region 常州医院真实地理位置地图; texts 未使用用户定位 / 按区域参考点估算 / 区域参考点 / 技术详情 / 关联医生; ids `care-result-title` / `emergency-result-title` / `triage-condition`; data-testids `filter-*`; class `.map-resource-row`.

## Test baseline

- pytest **206** (169 + 11 r1 + 9 r2 + 10 r3 + 7 r4), frontend boundary **17**, Playwright **20/20**, safety **142** cases.
- Bundle: CSS 100.9KB gzip 15.3KB; JS 355.7KB gzip 103.6KB (baseline JS 347.2KB, +2.4%). Single chunk (`App.tsx` uses conditional rendering, no code splitting).
- `data_validation`: scanned 31 / issues 186 (unchanged baseline).

## Local audit tooling (kept outside the repo)

Visual/interaction audit scripts live in `/tmp/changyi-audit/` (`shots.mjs`, `paths.mjs`, `state.mjs`, `state2.mjs`, `crop.mjs`, `drawer3.mjs`). They are not part of the build; re-copy them into `frontend/` temporarily if needed, and delete before committing.

## Next session starts with

Read `AGENTS.md`, `docs/status/current.md`, `docs/risks/register.md`. Maintain P5 decision-first triage + P4 demo polish + P3 visual system. Algorithm next steps are listed under `docs/status/current.md` 「下一步（算法）」.
