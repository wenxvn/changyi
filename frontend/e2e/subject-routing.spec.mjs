import { test, expect } from "@playwright/test";

test("relative history does not become the current self consultation disease or direction", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我妈妈确诊糖尿病，现在我咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.htriage_analysis.known_disease.background_mentions).toContain("糖尿病");
  await expect(page.locator(".care-result__direction")).not.toContainText("内分泌代谢科");
});
