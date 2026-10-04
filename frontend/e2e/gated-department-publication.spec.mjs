import { test, expect } from "@playwright/test";

test("pending risk does not publish a scored ordinary department beside the null direction", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我现在是否呼吸困难，但有咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  expect(data.matched_department).toBeNull();
  expect(data.triage.department_candidates).toEqual([]);
  expect(data.htriage_analysis.department_candidates).toEqual([]);
  await expect(page.getByTestId("followup-option-present")).toBeVisible();
});
