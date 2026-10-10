import { test, expect } from "@playwright/test";

test("unquantified high blood pressure requires information and professional review", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我52岁，今天量血压发现很高，有轻微头痛");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const d = (await (await response).json()).data;
  expect(d.triage_status).toBe("INSUFFICIENT_INFORMATION");
  expect(d.matched_department).toBeNull();
  await expect(page.getByTestId("care-result")).toContainText("实际完整读数、单位、测量时间和年龄");
  await page.getByRole("button", { name: "修改", exact: true }).click();
  await page.locator("#triage-condition").fill("我52岁，今天血压190/120 mmHg，有轻微头痛");
  const clarified = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "重新分析", exact: true }).click();
  expect((await (await clarified).json()).data.triage_status).toBe("URGENT");
});

test("severe reported adult reading bypasses ordinary expert booking", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我45岁，今天血压190/120 mmHg，没有背痛或麻木");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toContainText("血压读数");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/recommendations") && r.request().method() === "POST");
  await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  const d = (await (await response).json()).data;
  expect(d.resource_strategy.code).toBe("urgent_assessment");
  expect(d.recommended_doctors).toEqual([]);
});

test("severe reading with current back pain shows emergency exit", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我45岁，现在血压190/120 mmHg，背痛");
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await response).json()).data.triage_status).toBe("EMERGENCY");
  await expect(page.getByRole("alert", { name: "需要优先进行紧急医疗评估" })).toContainText("血压读数");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
