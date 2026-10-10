import { test, expect } from "@playwright/test";

test("failed exclusion is not presented as a routine route", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("医生没有排除心梗");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.original_condition).toBe("医生没有排除心梗");
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
