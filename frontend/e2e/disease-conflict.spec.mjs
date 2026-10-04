import { test, expect } from "@playwright/test";

test("conflicting disease reports ask for clarification instead of asserting known illness", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("有糖尿病，但现在否认糖尿病");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await response).json()).data.htriage_analysis.known_disease.assertion_status).toBe("conflicting");
  await expect(page.getByTestId("followup-option-none")).toBeVisible();
  await page.getByTestId("followup-option-none").click();
  await expect(page.getByTestId("followup-option-report_unconfirmed")).toBeVisible();
});
