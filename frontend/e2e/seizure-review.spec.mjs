import { test, expect } from "@playwright/test";

test("seizure report waits for danger confirmation and confirmed danger reaches 120", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("抽搐");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  await expect(page.getByTestId("followup-option-present")).toBeVisible();
  await expect(page.locator(".followup-prompt")).toContainText("抽搐");
  expect(rankings).toHaveLength(0);
  await page.getByTestId("followup-option-present").click();
  await expect(page.locator("#emergency-result-title")).toBeVisible();
  await expect(page.getByRole("link", { name: /拨打 120/ }).first()).toBeVisible();
  expect(rankings).toHaveLength(0);
});

test("denying danger conditions does not resolve an uncertain seizure mention", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定有没有抽搐");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("followup-option-none")).toBeVisible();
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-none").click();
  expect((await (await response).json()).data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  expect(rankings).toHaveLength(0);
});
