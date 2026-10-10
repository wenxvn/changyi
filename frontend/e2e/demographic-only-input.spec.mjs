import { test, expect } from "@playwright/test";

test("age and gender alone request a medical complaint, then allow reanalysis", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("年龄儿童，性别男");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const d = (await (await response).json()).data;
  expect(d.triage_status).toBe("INSUFFICIENT_INFORMATION");
  expect(d.matched_department).toBeNull();
  expect(d.triage.disease_candidates).toEqual([]);
  await expect(page.getByTestId("care-result")).toContainText("只提供了年龄");
  await page.getByRole("button", { name: "修改", exact: true }).click();
  await page.locator("#triage-condition").fill("儿童现在呼吸困难");
  await page.getByRole("button", { name: "重新分析", exact: true }).click();
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
