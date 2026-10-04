import { test, expect } from "@playwright/test";

test("proxy phrasing keeps the relative's reported disease and specialty direction", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我现在替我妈妈问诊她确诊糖尿病");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(true);
  expect(data.original_condition).toBe("我现在替我妈妈问诊她确诊糖尿病");
  await expect(page.locator(".care-result__direction")).toContainText("内分泌代谢科");
});
