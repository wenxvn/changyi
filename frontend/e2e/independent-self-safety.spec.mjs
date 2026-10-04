import { test, expect } from "@playwright/test";

test("a separate cough question does not suppress a direct breathing danger report", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("现在咳嗽是不是，我喘不上气");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.original_condition).toBe("现在咳嗽是不是，我喘不上气");
  await expect(page.getByRole("alert", { name: "需要优先进行紧急医疗评估" })).toBeVisible();
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
