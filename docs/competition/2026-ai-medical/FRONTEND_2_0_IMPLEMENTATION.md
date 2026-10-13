# Frontend 2.0 Implementation Record

Date: 2026-10-13

Scope: React/TypeScript frontend and browser-visible UX only. This record tracks the implementation requested in `常医智导-前端智能交互升级-6Luna执行提示词.md`.

## Baseline evidence

- Repository was clean on `main` at `73ebfee` before this task. The current server served the existing Flask/Vite frontend and `/api/v1/health` returned `200`.
- Baseline browser regression: `product-smoke.spec.mjs` passed 8/8 across 1440×900 and 1280×800; `mobile.spec.mjs` passed 10/10 across 768×1024 and 390×844.
- Baseline screenshots and viewport measurements are in `evidence/frontend-2.0/before/`.
- All four tested widths had no horizontal overflow. Home CTA fit above the fold at each size, but measured 44px high on desktop and 44px on mobile. The initial triage CTA was below the 390×844 viewport. The homepage's CarePath panel shared the hero row with the composer.
- A synthetic symptom submitted from home appeared in the `/triage?condition=…` query string. `App.tsx` forwarded it there and `TriagePage.tsx` started the request from a mount effect.

## Existing, reusable, changing, protected

- Reuse: `SpeechInput`, `ExampleSymptomChips`, `FollowupPrompt`, `CurrentUnderstanding`, `TriageResults`, `ResourcePreview`, `AmapNavigationLink`, existing API clients, location context, and emergency short-circuit.
- Change: share the Home/Triage composer, prioritize the composer on the first screen, pass initial input in app memory, add request-owned visual agent states, refine follow-up guidance and profile save feedback, and browser-verify the existing result/resource/map/trust surfaces without changing their API or safety behavior.
- Preserve: Flask `/api/v1/*` contracts, `triage_status` semantics, Safety Gate/red-flag priority, recommendation rules and data, structured `followup_answers`, public-resource/source boundaries, and existing local preference boundaries.
- Do not add: backend triage behavior, model changes, patient-text persistence, analytics, new authentication/cloud storage, unlicensed assets, or claims of diagnosis, live emergency availability, or clinical validation.

## 3D and loading decision

The current frontend uses React 19 and Vite 8 and has no 3D dependency. As of 2026-10-13, npm metadata reports Three.js 0.186.1 (MIT, 20.4 MB unpacked) and React Three Fiber 9.8.1 (React 19 peer range, 2.38 MB unpacked). Use Three.js directly, without the additional React renderer, behind a dynamic import; tree-shake the scene to the primitives it uses and measure the emitted chunk. This keeps the 3D renderer out of the ordinary non-agent route path. Show a static SVG fallback for reduced motion, unavailable WebGL, load errors, and constrained devices.

## Delivery stages

1. **P0-A — Input and entry privacy:** one reusable composer on Home/Triage, prominent labeled CTA, multiline-safe keyboard behavior, real speech/examples, app-memory transfer, friendly blank state after refresh/back, and no symptom text in the URL.
2. **P0-B — Agent and request states:** lazy 3D CareAgent with SVG fallback; composing/submitting/waiting/result/follow-up/emergency/error states are presentation-only and driven by the real request/result; one request owner, abort/stale-response guards, no synthetic progress or result delay; emergency UI immediately takes priority.
3. **P1-A/B — Conversation and result actions:** emphasize the actual server-returned follow-up, one question at a time, and the existing structured answer flow; order result UI by safety and actionable next step, with only returned facts and real actions.
4. **P1-C — Resources and map:** keep filters, paging, source disclosure, favorites, details, OSM map and Amap navigation; improve scanability and maintain list/marker/selected-detail synchronization.
5. **P2 — Trust, profile and shared polish:** make evaluation scope and local-preference limits easy to understand; unify motion, focus, loading/error/empty/safety treatment; keep demos routed through the real API.

## Risks, gates, and rollback

- Three.js WebGL initialization or chunk cost can hurt first paint. Gate it by visibility/support/preferences, cap pixel ratio and particle count, pause when hidden, dispose resources, and fall back to SVG on any failure.
- Home-to-triage state can be lost on refresh by design; the empty triage workspace must remain understandable. Back navigation must not restore symptom text in browser history.
- UI state must not infer risk. Emergency, urgent, routine, information-insufficient, and follow-up content stay driven by backend payloads; error/timeout never renders a result.
- Keep changes frontend-only except this implementation record, the UI registry/status record, tests, and screenshots. Stage and commit only task-owned files; no push. Roll back by reverting the local implementation commit(s), with no migration or backend state to undo.

## Acceptance evidence to attach

- Run `npm ci`, `npm run typecheck`, `npm run test`, `npm run build`, `npm run e2e`, and `npm run e2e:hooks` from `frontend/`; run applicable `python -m pytest` and `python -m evaluation.safety.evaluate_safety` if the configured environment is available.
- Capture and review home, waiting, routine result, follow-up, emergency, resource/map selection, and 390px mobile screenshots; recheck 1440×900, 1280×800, 768×1024, and 390×844.
- Measure built JS entry and lazy 3D chunk sizes from build artifacts. Do not report unmeasured performance or claim engineering tests are clinical validation.

## Completion record

### Implemented

- Replaced the home and initial triage forms with one accessible `SymptomComposer`: stable textarea labels, 2000-character cap, multiline input, Ctrl/⌘+Enter, speech fallback, real API-backed example shortcuts, character count, and a 58px full-width primary action. The original CarePath now sits below the first-screen task.
- Home-to-triage transfer is held in App memory. The compatibility path removes any legacy `condition` query before paint and on browser history navigation. Refresh/back opens an empty triage workspace; no patient text is added to a URL or browser storage by this flow.
- Added the reusable `CareAgent` with a Three.js 0.186.1 WebGL2 scene, shared static SVG fallback, visibility-gated dynamic import, constrained-device/reduced-motion/WebGL/error fallback, skip control, hidden-tab pause, resource disposal, DPR cap 1.5 and a 30fps scene-loop cap. Its status comes from focus, the actual request lifecycle and returned API state. Waiting says only that the request was sent and the system response is pending. Emergency output bypasses the agent and shows the returned safety action immediately.
- Follow-up now has a small static agent cue and explains that the question came from the current server response. It continues to use the first real backend question, preserves options/free text/skip and sends the existing structured answer payload. Existing `TriageResults`/`CareActions`/`EmergencyFacilities` already place returned safety state and urgent action before ordinary resources, so those API-driven branches were retained. Existing resources filters/details/source boundaries and map list-marker-preview synchronization were retained and covered by browser verification. Trust Center evaluation caveats were reviewed and preserved. The profile preference toggle now confirms local-browser saving.
- No backend, Safety Gate, model, clinical data, `/api/v1` schema or medical decision logic changed. Three.js is MIT-licensed; no commercial model, sound, remote animation service or telemetry was added. `ui-registry.md` records the new shared components/tokens and their behavior.

### Verification results (2026-10-13)

| Gate or measurement | Result |
| --- | --- |
| Clean dependency installation | `npm ci` in `frontend/` was blocked by Windows `EPERM` because the already-running Vite process (PID 32780) held the Rolldown native binding. The process was left running. A clean `npm ci` against the exact copied `package.json` and `package-lock.json` succeeded in an isolated temporary directory; missing dependency files were then copied into the project install. |
| `npm run typecheck` | Passed; also included in the successful production build after the final source change. |
| `npm run test` | 21 passed, 0 failed. |
| `npm run build` | Passed. Vite reports one intentional lazy `AgentScene` chunk above its 500 kB raw warning threshold; measured separately below. |
| `npm run e2e` | 104 passed, 0 failed across 1440×900, 1280×800, 768×1024 and 390×844 projects. Includes home input/privacy/one request, multiline keyboard submit, URL cleanup, true waiting, cancellation on route unmount, 503 retry, emergency 120, WebGL/reduced-motion fallback, resource/map selection, and the pre-existing safety/product cases. |
| `npm run e2e:hooks` | 4 passed, 0 failed, including StrictMode replay and superseded-request lifecycle coverage. |
| `.venv\Scripts\python.exe -m pytest` | 1043 passed in 89.31 seconds. |
| `.venv\Scripts\python.exe -m evaluation.safety.evaluate_safety` | Safety142: recall 1.0, under-triage 0, over-triage 0, emergency false negative 0. Engineering regression only; not clinical validation. |
| CTA and horizontal overflow | Home and triage CTA measured 58px and visible without scrolling at all four viewports. No horizontal overflow on any of the eight home/triage viewport checks. After screenshots and raw measurements: `evidence/frontend-2.0/after/`. |
| Local browser paint and animation observation | `domInteractive` ranged 6–262ms across the four local Chromium navigations (first navigation 262ms, later contexts warm); one-second browser `requestAnimationFrame` sample was 60Hz. The Three scene loop is capped at 30fps in code; GPU draw FPS was not separately instrumented. These localhost observations are not production RUM. |
| Built JavaScript entry | Baseline 369,173 raw / 108,592 gzip bytes; after 375,848 raw / 111,118 gzip bytes. Delta: +6,675 raw / +2,526 gzip bytes. Existing doctor-photo chunk remains 172,641 raw / 52,341 gzip bytes. |
| Lazy Three.js scene | `AgentScene` is a separate dynamic chunk: 537,452 raw / 132,827 gzip bytes. Chromium confirmed WebGL2, rendered a canvas on desktop/tablet and requested the scene chunk on the home screen; the 390px/constrained profile used the SVG fallback. The local Flask response was uncompressed (537,752 transfer bytes including headers); gzip values are direct artifact compression with Node zlib. The build-size warning remains documented; routes without `CareAgent` do not import this chunk. |

### Visual evidence and comparison

The baseline and final viewport images are stored in `evidence/frontend-2.0/before/` and `evidence/frontend-2.0/after/`. The after set includes four home and triage sizes plus request-waiting, routine result, backend follow-up, emergency, resources, selected map hospital, trust and profile screens. `measurements.json` records viewport geometry and emitted bundle sizes.

Compared with baseline, the home’s first action moved from a 44px corner control to a unified 58px full-width composer action; all four home and triage CTAs now fit in the first viewport. The algorithm flow no longer shares the home hero row. A desktop WebGL orb visibly changes with request state, while the mobile constrained profile remains on the static orb. The map screenshot shows a selected list row, matching map marker and the same hospital’s open resource preview. During a held API response, the UI reports only that it is waiting; once the backend returns an emergency result, the first action is the real `拨打 120` link.

### Remaining notes and handoff

- `npm ci` could not unlink the locked native binary while the user's existing Vite server was running; the isolated install verified the lockfile and restored missing dependency files without stopping that process. A future clean install after that server releases the file can run the exact in-place command.
- Vite’s raw chunk warning is for the optional 3D scene. The chunk is split from the main entry and has a measured 132,827-byte gzip artifact. Keep the static fallback and visibility/device gates if the chunk changes.
- No live deploy, remote push or clinical effectiveness claim was made. Local changes are ready for a local commit; this worktree has not been pushed.
