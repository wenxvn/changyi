import { test, expect } from "@playwright/test";

test("API distinguishes relative candidate scores from uncalibrated model posterior", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.candidate_score_semantics.kind).toBe("relative_support_score");
  expect(data.htriage_analysis.candidate_score_semantics.clinical_probability).toBe(false);
  expect(data.htriage_analysis.disease_candidates[0].relative_support_score).toBe(82);
  expect(data.disease_prediction.probability_semantics.kind).toBe("uncalibrated_model_posterior");
  expect(data.disease_prediction.probability_semantics.calibrated).toBe(false);
});
