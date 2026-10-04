import { test, expect } from "@playwright/test";

test("denial of severe pain asks about any current pain and none retains the original text", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有严重胸痛");
  const first = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await first).json()).data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  await expect(page.getByText(/任何程度的胸痛/)).toBeVisible();
  const next = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-none").click();
  const data = (await (await next).json()).data;
  expect(data.triage_status).toBe("ROUTINE");
  expect(data.original_condition).toBe("没有严重胸痛");
});
