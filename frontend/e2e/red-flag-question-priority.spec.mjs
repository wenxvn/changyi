import { test, expect } from "@playwright/test";

test("risk confirmation remains available before sparse-symptom questions", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有严重胸痛");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage.followup.questions[0].id).toBe("red_flag_check");
  expect(data.triage.followup.questions.length).toBeLessThanOrEqual(8);
  await expect(page.getByTestId("followup-option-present")).toBeVisible();
  await page.getByTestId("followup-option-present").click();
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
