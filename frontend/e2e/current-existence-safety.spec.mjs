import { test, expect } from "@playwright/test";

test("a current existence question is confirmed before the emergency path", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我现在是否喘不上气");
  const first = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const initial = (await (await first).json()).data;
  expect(initial.triage_status).toBe("INSUFFICIENT_INFORMATION");
  expect(initial.matched_department).toBeNull();
  const next = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-present").click();
  const confirmed = (await (await next).json()).data;
  expect(confirmed.triage_status).toBe("EMERGENCY");
  expect(confirmed.original_condition).toBe("我现在是否喘不上气");
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
