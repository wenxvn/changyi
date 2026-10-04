import { test, expect } from "@playwright/test";

test("hypothetical symptoms do not become asserted tags or model input", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("假如咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.abstain_reason).toBe("symptom_assertion_uncertain");
  expect(data.disease_prediction.predictions).toEqual([]);
  expect(data.htriage_analysis.symptom_tags.some(tag => tag.matched_terms.includes("咳嗽"))).toBe(false);
});
