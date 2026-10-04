import { test, expect } from "@playwright/test";

test("uncertain danger asks confirmation before direction or automatic ranking", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定有没有胸痛");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  await expect(page.getByText("是否伴有胸痛、呼吸困难、意识异常、大出血、一侧肢体无力等危险信号？")).toBeVisible();
  expect(rankings).toHaveLength(0);
});

test("confirmed emergency keeps 120 even with another uncertain symptom", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("持续胸痛喘不上气，不确定有没有头痛");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.locator("#emergency-result-title")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("link", { name: /拨打 120/ }).first()).toBeVisible();
});
