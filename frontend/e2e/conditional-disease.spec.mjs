import { test, expect } from "@playwright/test";

test("a hypothetical disease is a consultation mention rather than an existing illness", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("如果我有糖尿病应该挂什么科");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.htriage_analysis.known_disease.assertion_status).toBe("uncertain");
  await expect(page.getByTestId("followup-option-none")).toBeVisible();
  await page.getByTestId("followup-option-none").click();
  await expect(page.getByTestId("followup-option-confirmed")).toBeVisible();
});
