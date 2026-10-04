import { test, expect } from "@playwright/test";

test("a copula presence question is not an asserted model symptom", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("是不是咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.input_assertions.unknown).toEqual(["cough"]);
  expect(data.disease_prediction.input_assertions.present).toEqual([]);
  await expect(page.getByTestId("model-abstention-notice")).toContainText("症状是否存在尚未确认");
});
