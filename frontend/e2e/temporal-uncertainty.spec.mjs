import { test, expect } from "@playwright/test";

test("current-time word does not confirm an uncertain symptom", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定是否现在咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.input_assertions.present).toEqual([]);
  expect(data.disease_prediction.input_assertions.unknown).toEqual(["cough"]);
  await expect(page.getByTestId("model-abstention-notice")).toContainText("症状是否存在尚未确认");
});
