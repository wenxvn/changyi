import { test, expect } from "@playwright/test";

test("red eye with photophobia shows emergency assessment and 120 exit", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("左眼发红疼痛，非常怕光");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const d = (await (await response).json()).data;
  expect(d.triage_status).toBe("EMERGENCY");
  await expect(page.getByRole("alert", { name: "需要优先进行紧急医疗评估" })).toContainText("红眼");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});

test("current joint swelling pain and restricted movement bypass ordinary booking", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("右膝肿胀疼痛，不能弯曲");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toContainText("关节肿痛");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/recommendations") && r.request().method() === "POST");
  await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  const d = (await (await response).json()).data;
  expect(d.resource_strategy.code).toBe("urgent_assessment");
  expect(d.recommended_doctors).toEqual([]);
  expect(d.weights_used).toEqual({});
});
