import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const sourceRoot = new URL("../src/", import.meta.url);

async function source(path) {
  return readFile(new URL(path, sourceRoot), "utf8");
}

test("pages and components do not own direct fetch or legacy global state", async () => {
  const files = [
    "app/App.tsx",
    "pages/HomePage.tsx",
    "pages/TriagePage.tsx",
    "pages/ResourcesPage.tsx",
    "pages/TrustPage.tsx",
    "pages/MapPage.tsx",
    "pages/ProfilePage.tsx",
    "components/visualization/CarePath.tsx",
    "components/visualization/JourneyPreview.tsx",
    "components/medical/CurrentUnderstanding.tsx",
    "components/medical/FollowupPrompt.tsx",
    "components/medical/TriageResults.tsx",
  ];
  const contents = await Promise.all(files.map(source));
  for (const content of contents) {
    assert.equal(/\bfetch\s*\(/.test(content), false);
    assert.equal(/window\._/.test(content), false);
  }
});

test("resource browsing stays on versioned read-only endpoints", async () => {
  const page = await source("pages/ResourcesPage.tsx");
  const api = await source("api/resources.ts");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/hospitals/);
  assert.match(api, /\/api\/v1\/doctors/);
  assert.match(api, /getHospitalDetail/);
  assert.match(api, /getDoctorDetail/);
  assert.match(page, /RESOURCE DETAIL/);
  assert.match(page, /provenance/);
  assert.match(page, /来源待补齐/);
  assert.match(page, /地图（建设中）/);
});

test("Trust Center reads provisional evidence from the shared v1 API", async () => {
  const page = await source("pages/TrustPage.tsx");
  const api = await source("api/evidence.ts");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/evidence/);
  assert.match(page, /PROVISIONAL EVALUATION/);
  assert.match(page, /不代表临床验证/);
  assert.match(page, /review_required/);
});

test("map view keeps list and markers on one read-only endpoint", async () => {
  const page = await source("pages/MapPage.tsx");
  const api = await source("api/map.ts");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/map/);
  assert.match(page, /aria-label=\{`查看/);
  assert.match(page, /非导航地图/);
  assert.doesNotMatch(page, /geolocation/);
});

test("triage result boundary short-circuits ordinary recommendations for emergency", async () => {
  const page = await source("pages/TriagePage.tsx");
  const result = await source("components/medical/TriageResults.tsx");
  assert.match(page, /result\.triage_status === "EMERGENCY"/);
  assert.match(page, /if \(!result \|\| result\.triage_status === "EMERGENCY"/);
  assert.match(result, /EmergencyResult/);
  assert.match(result, /拨打 120/);
  assert.doesNotMatch(result, /composite_score/);
  assert.doesNotMatch(result, /match_score/);
});

test("the shared client owns fetch and request id handling", async () => {
  const client = await source("api/client.ts");
  assert.match(client, /fetch\(/);
  assert.match(client, /X-Request-ID/);
  assert.match(client, /AbortController/);
  assert.match(client, /timeoutMs/);
});

test("profile history is opt-in, local-only, and redacted", async () => {
  const page = await source("pages/ProfilePage.tsx");
  const state = await source("state/demoProfile.ts");
  assert.match(page, /仅保存在当前浏览器/);
  assert.match(page, /不需要登录/);
  assert.match(page, /确定清除/);
  assert.doesNotMatch(page, /localStorage/);
  assert.match(state, /changyi\.demo\.history\.v1/);
  assert.match(state, /historyEnabled/);
  assert.match(state, /MAX_HISTORY_ITEMS = 8/);
  assert.doesNotMatch(state, /condition|symptoms|patient|phone|contact/i);
});

test("the app shell exposes keyboard landmarks and reduced-motion navigation", async () => {
  const app = await source("app/App.tsx");
  const styles = await source("styles/globals.css");
  assert.match(app, /skip-link/);
  assert.match(app, /id="main-content"/);
  assert.match(app, /aria-current=\{route === item\.route \? "page"/);
  assert.match(app, /aria-controls="primary-navigation"/);
  assert.match(app, /prefers-reduced-motion/);
  assert.match(styles, /input:focus-visible/);
  assert.match(styles, /\.skip-link:focus-visible/);
});

test("interactive tabs have explicit controls and form-safe button defaults", async () => {
  const app = await source("app/App.tsx");
  const button = await source("components/ui/Button.tsx");
  const home = await source("pages/HomePage.tsx");
  const resources = await source("pages/ResourcesPage.tsx");
  const map = await source("pages/MapPage.tsx");
  assert.match(app, /<button type="button" onClick=\{\(\) => navigate\("\/trust"\)/);
  assert.match(button, /type = "button"/);
  assert.match(home, /role="tabpanel"/);
  assert.match(home, /aria-controls="journey-step-panel"/);
  assert.match(home, /ArrowRight|ArrowLeft/);
  assert.match(resources, /aria-controls="resource-results-panel"/);
  assert.match(resources, /role="tabpanel"/);
  assert.match(map, /aria-controls="map-resource-panel"/);
  assert.match(map, /role="tabpanel"/);
});
