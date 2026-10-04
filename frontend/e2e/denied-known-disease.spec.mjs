import { test, expect } from "@playwright/test";

test("denied diabetes cannot become the displayed endocrine direction", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有糖尿病但有咳嗽");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toBeVisible();
  await expect(page.locator(".care-result__direction")).not.toContainText("内分泌代谢科");
});
