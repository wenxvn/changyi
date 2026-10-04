import { test, expect } from "@playwright/test";

test("uncertain disease does not independently produce a rule disease candidate", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("怀疑糖尿病");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.htriage_analysis.disease_candidates.some(row => row.recommended_department === "内分泌代谢科")).toBe(false);
  await expect(page.getByTestId("followup-option-none")).toBeVisible();
  await page.getByTestId("followup-option-none").click();
  await expect(page.getByTestId("followup-option-confirmed")).toBeVisible();
});
