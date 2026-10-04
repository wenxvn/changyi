import { test, expect } from "@playwright/test";

test("reported exclusion does not publish the excluded disease as existing history", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("医生已经排除糖尿病");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.htriage_analysis.known_disease.disease).toBe("");
  expect(data.original_condition).toBe("医生已经排除糖尿病");
});
