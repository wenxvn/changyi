import { test, expect } from "@playwright/test";

test("current metabolic symptom cluster does not stay a chronic outpatient route", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我有1型糖尿病，今天口渴、尿多和恶心，但没有意识混乱");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.matched_department).toBe("急诊医学科");
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
