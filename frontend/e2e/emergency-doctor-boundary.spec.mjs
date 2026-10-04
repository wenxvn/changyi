import { test, expect } from "@playwright/test";

test("emergency API omits regular doctor ranking while retaining the emergency UI", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我现在喘不上气");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
  const response = await page.request.post("/api/v1/recommendations", { data: { condition: "我现在喘不上气" } });
  expect(response.status()).toBe(200);
  const data = (await response.json()).data;
  expect(data.recommended_doctors).toEqual([]);
  expect(data.weights_used).toEqual({});
  expect(data.recommended_hospitals.length).toBeGreaterThan(0);
});
