import { test, expect } from "@playwright/test";

test("a current bystander report keeps emergency priority and never ranks ordinary resources", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我妈妈正在呼吸困难");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.locator("#emergency-result-title")).toBeVisible();
  await expect(page.getByRole("link", { name: /拨打 120/ }).first()).toBeVisible();
  expect(rankings).toHaveLength(0);
});
