import { test, expect } from "@playwright/test";

test("compound current symptoms publish urgent assessment rather than ordinary care", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("排尿灼痛两天，现在有腰侧疼痛和发热，还有恶心");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.triage_status).toBe("URGENT");
  expect(data.matched_department).toBe("急诊医学科");
  await expect(page.getByTestId("care-result")).toContainText("排尿疼痛合并发热和腰背侧疼痛");
  const recommendation = page.waitForResponse(value => value.url().endsWith("/api/v1/recommendations") && value.request().method() === "POST");
  await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  const resources = (await (await recommendation).json()).data;
  expect(resources.resource_strategy.code).toBe("urgent_assessment");
  expect(resources.recommended_doctors).toEqual([]);
  expect(resources.weights_used).toEqual({});
});
