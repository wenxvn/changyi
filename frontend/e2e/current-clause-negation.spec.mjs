import { test, expect } from "@playwright/test";

test("current cough retains evidence after a separate denied symptom", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有胸痛，现在咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.original_condition).toBe("没有胸痛，现在咳嗽");
  expect(data.triage_status).toBe("ROUTINE");
  expect(data.matched_department).toBe("呼吸内科");
});
