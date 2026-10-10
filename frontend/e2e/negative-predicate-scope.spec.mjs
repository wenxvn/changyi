import { test, expect } from "@playwright/test";

test("not accompanied by breathing difficulty does not publish an emergency", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我不伴呼吸困难");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).not.toBe("EMERGENCY");
  expect(data.original_condition).toBe("我不伴呼吸困难");
  await expect(page.getByRole("link", { name: "拨打 120" })).toHaveCount(0);
});
