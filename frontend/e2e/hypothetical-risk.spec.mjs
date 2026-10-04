import { test, expect } from "@playwright/test";

test("explicit hypothetical danger asks for confirmation and defers routing", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("如果我不否认呼吸困难");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  expect(data.matched_department).toBe(null);
  expect(data.triage.defer_resource_routing).toBe(true);
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByTestId("followup-option-present")).toBeVisible();
});
