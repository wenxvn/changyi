import { test, expect } from "@playwright/test";

test("confirmed emergency does not publish the ordinary general fallback", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我现在是否喘不上气，我喘不上气");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.matched_department).toBe("急诊医学科");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
