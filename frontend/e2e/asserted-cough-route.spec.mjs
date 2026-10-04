import { test, expect } from "@playwright/test";

test("uncertain cough is not presented as an established respiratory route", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("现在是否咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.original_condition).toBe("现在是否咳嗽");
  expect(data.matched_department).not.toBe("呼吸内科");
  expect(data.disease_prediction.abstained).toBe(true);
});
