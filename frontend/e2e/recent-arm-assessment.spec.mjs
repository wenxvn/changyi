import { test, expect } from "@playwright/test";

test("recent recovered whole unilateral arm numbness still bypasses ordinary booking", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("本周整个左臂麻木15分钟后完全恢复");
  const triage = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await triage).json()).data.triage_status).toBe("URGENT");
  await expect(page.getByTestId("care-result")).toContainText("即使已恢复");
  const recommendation = page.waitForResponse(r => r.url().endsWith("/api/v1/recommendations") && r.request().method() === "POST");
  await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  const d = (await (await recommendation).json()).data;
  expect(d.resource_strategy.code).toBe("urgent_assessment");
  expect(d.recommended_doctors).toEqual([]);
});

test("current recurrence cannot borrow an earlier recovery to hide emergency", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("本周整个左臂麻木后完全恢复，今天又突然麻木");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await response).json()).data.triage_status).toBe("EMERGENCY");
  await expect(page.getByRole("alert", { name: "需要优先进行紧急医疗评估" })).toContainText("整侧手臂麻木");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
