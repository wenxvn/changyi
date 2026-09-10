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
