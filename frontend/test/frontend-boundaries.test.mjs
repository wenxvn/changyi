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
    "components/medical/ExampleSymptomChips.tsx",
  ];
  const contents = await Promise.all(files.map(source));
  for (const content of contents) {
    assert.equal(/\bfetch\s*\(/.test(content), false);
    assert.equal(/window\._/.test(content), false);
  }
});

test("resource browsing stays on versioned read-only endpoints and exposes navigation", async () => {
  const page = await source("pages/ResourcesPage.tsx");
  const api = await source("api/resources.ts");
  const navigation = await source("components/ui/AmapNavigationLink.tsx");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/hospitals/);
  assert.match(api, /\/api\/v1\/doctors/);
  assert.match(api, /getHospitalDetail/);
  assert.match(api, /getDoctorDetail/);
  assert.match(page, /资料详情/);
  assert.match(page, /AmapNavigationLink/);
  assert.match(navigation, /高德导航/);
  assert.match(page, /资料核验中/);
  assert.match(page, /打开医院地图/);
});

test("Trust Center presents evidence in user-facing language with technical detail available", async () => {
  const page = await source("pages/TrustPage.tsx");
  const api = await source("api/evidence.ts");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/evidence/);
  assert.match(page, /可信信息 · 系统评估/);
  assert.match(page, /研究与演示阶段/);
  assert.match(page, /不代表临床验证/);
  assert.match(page, /技术详情/);
});

test("map view keeps list and markers on one read-only endpoint", async () => {
  const page = await source("pages/MapPage.tsx");
  const api = await source("api/map.ts");
  assert.doesNotMatch(page, /fetch\(/);
  assert.match(api, /\/api\/v1\/map/);
  assert.match(page, /aria-label=\{"查看/);
  assert.match(page, /真实地理地图/);
  assert.match(page, /AmapNavigationLink/);
  assert.doesNotMatch(page, /navigator\.geolocation/);
  const location = await source("state/locationContext.tsx");
  assert.match(location, /getCurrentPosition/);
  assert.match(location, /不会保存到本地/);
});

test("location and follow-up state remain explicit and session-only", async () => {
  const location = await source("state/locationContext.tsx");
  const selector = await source("components/ui/LocationSelector.tsx");
  const triage = await source("pages/TriagePage.tsx");
  const followup = await source("components/medical/FollowupPrompt.tsx");
  assert.match(location, /source: LocationSource/);
  assert.match(location, /source: "unknown"/);
  assert.doesNotMatch(location, /localStorage|sessionStorage/);
  assert.match(selector, /区域参考点/);
  assert.match(triage, /followup_answers: followupAnswers/);
  assert.match(triage, /submittedCondition/);
  assert.doesNotMatch(triage, /appendAnswer/);
  assert.match(followup, /question_id/);
  assert.match(followup, /option\.label/);
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

test("care routing controls expose accessible names and live regions", async () => {
  const triage = await source("pages/TriagePage.tsx");
  const resources = await source("pages/ResourcesPage.tsx");
  const favorite = await source("components/ui/FavoriteDoctorButton.tsx");
  const styles = await source("styles/globals.css");

  assert.match(triage, /name="visit-intent"/);
  assert.match(triage, /这次主要想解决什么/);
  assert.match(triage, /就医资源偏好/);
  assert.match(triage, /data-testid="pref-continuity"/);
  assert.match(favorite, /aria-pressed=\{active\}/);
  assert.match(favorite, /aria-label=\{active \? "取消收藏该医生" : "收藏该医生"\}/);
  assert.match(resources, /加载更多/);
  assert.match(resources, /aria-live="polite"/);
  assert.match(styles, /\.favorite-doctor-button:focus-visible/);
  assert.match(styles, /\.resource-index-pagination/);
});
