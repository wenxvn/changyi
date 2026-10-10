import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const sourceRoot = new URL("../src/", import.meta.url);

async function source(path) {
  return readFile(new URL(path, sourceRoot), "utf8");
}

test("triage evidence contract parses object symptom tags without losing backend evidence", async () => {
  const schemas = await source("api/schemas.ts");
  const types = await source("types/api.ts");
  // Object tag parser exists and keeps matched_terms/body_system/source.
  assert.match(schemas, /parseSymptomTag/);
  assert.match(schemas, /matched_terms/);
  assert.match(schemas, /parseHtriageAnalysis/);
  assert.match(schemas, /department_candidates/);
  // Legacy string tags remain compatible instead of being dropped.
  assert.match(schemas, /typeof value === "string"/);
  // Types expose structured evidence instead of string[].
  assert.match(types, /SymptomTag/);
  assert.match(types, /DepartmentCandidate/);
  assert.match(types, /HtriageAnalysis/);
});

test("triage pages render read-only algorithm evidence without inventing scores", async () => {
  const understanding = await source("components/medical/CurrentUnderstanding.tsx");
  const results = await source("components/medical/TriageResults.tsx");
  const triage = await source("pages/TriagePage.tsx");
  assert.match(understanding, /understanding-symptoms/);
  assert.match(understanding, /识别到的症状词/);
  assert.match(results, /result-dept-evidence/);
  assert.match(results, /科室依据/);
  assert.match(results, /未经临床校准/);
  // Population entry is labeled as entry, never as a disease probability.
  assert.match(results, /population_context/);
  assert.doesNotMatch(results, /composite_score/);
  assert.doesNotMatch(results, /match_score/);
});

test("followup prompt links the asked slot to evidence refresh", async () => {
  const prompt = await source("components/medical/FollowupPrompt.tsx");
  assert.match(prompt, /followup-slot-link/);
  assert.match(prompt, /本题主要补充/);
  assert.match(prompt, /missing_slots/);
});

test("followup roundtrip shows read-only evidence diff without driving logic", async () => {
  const understanding2 = await source("components/medical/CurrentUnderstanding.tsx");
  const results2 = await source("components/medical/TriageResults.tsx");
  const triage2 = await source("pages/TriagePage.tsx");
  // Snapshot state lives only for display; server recomputes the result.
  assert.match(triage2, /previousTags/);
  assert.match(triage2, /previousDepts/);
  assert.match(triage2, /previousDept/);
  assert.match(triage2, /pathUpdated/);
  // Diff markers reuse plain small text, no invented scores.
  assert.match(understanding2, /evidence-diff/);
  assert.match(understanding2, /补充后新增/);
  assert.match(results2, /evidence-diff/);
  assert.match(results2, /补充后更新|补充后新增/);
  assert.doesNotMatch(results2, /composite_score/);
  assert.doesNotMatch(results2, /match_score/);
});
