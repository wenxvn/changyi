import { test, expect } from "@playwright/test";

test("negating denial does not suppress the existing breathing emergency path", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我不否认呼吸困难");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
  await expect(page.getByTestId("model-abstention-notice")).toHaveCount(0);
});
