import { test, expect } from "@playwright/test";

test("historical critical cue stays historical while a current recurrence stays emergency", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("以前呼吸困难，现在我咳嗽");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toBeVisible();
  await expect(page.locator("#emergency-result-title")).not.toBeVisible();
  await page.getByRole("button", { name: "修改", exact: true }).click();
  await page.locator("#triage-condition").fill("以前呼吸困难，现在我又呼吸困难");
  await page.getByRole("button", { name: "重新分析", exact: true }).click();
  await expect(page.locator("#emergency-result-title")).toBeVisible();
  await expect(page.getByRole("link", { name: /拨打 120/ }).first()).toBeVisible();
});
