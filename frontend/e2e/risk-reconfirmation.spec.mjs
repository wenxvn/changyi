import { test, expect } from "@playwright/test";

test("unknown risk remains confirmable and later present uses the emergency path", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有严重胸痛");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("followup-option-unknown")).toBeVisible();
  const uncertainResponse = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-unknown").click();
  expect((await (await uncertainResponse).json()).data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  await expect(page.getByTestId("followup-option-present")).toBeVisible();
  const confirmedResponse = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-present").click();
  const data = (await (await confirmedResponse).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.original_condition).toBe("没有严重胸痛");
  expect(data.followup_answers.filter(item => item.question_id === "red_flag_check")).toHaveLength(1);
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
