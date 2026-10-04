import { test, expect } from "@playwright/test";

test("an uncertain disease can be clarified without changing the original condition", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定有没有糖尿病");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("followup-option-none")).toBeVisible();
  await page.getByTestId("followup-option-none").click();
  await expect(page.getByTestId("followup-option-confirmed")).toBeVisible();
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-confirmed").click();
  const data = (await (await response).json()).data;
  expect(data.original_condition).toBe("不确定有没有糖尿病");
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(true);
  expect(data.matched_department).toBe("内分泌代谢科");
  await expect(page.getByTestId("path-updated")).toBeVisible();
});
