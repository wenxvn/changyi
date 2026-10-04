import { test, expect } from "@playwright/test";

test("failure to exclude a critical condition does not publish the ordinary pathway", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("医生未能排除心梗");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.disease_prediction.predictions).toEqual([]);
  expect(data.original_condition).toBe("医生未能排除心梗");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
