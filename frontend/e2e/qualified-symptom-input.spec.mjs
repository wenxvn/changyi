import { test, expect } from "@playwright/test";

test("qualified symptom denial publishes a review notice rather than disease predictions", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有严重头痛");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.predictions).toEqual([]);
  expect(data.disease_prediction.input_assertions.unknown).toEqual(["headache"]);
  await expect(page.getByTestId("model-abstention-notice")).toContainText("描述包含对症状程度的否认，辅助疾病分析暂需复核");
});
