import { test, expect } from "@playwright/test";

test("mobile layout keeps the primary triage action and navigation usable", async ({ page }) => {
  await page.goto("/triage");
  await expect(page.getByRole("heading", { name: /现在有什么不舒服/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "查看安全状态" })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("mobile-triage-initial.png"), fullPage: true });

  await page.getByRole("button", { name: "打开导航" }).click();
  await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
  await expect(page.getByRole("button", { name: "开始智能分诊" })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("mobile-navigation.png"), fullPage: true });
});
