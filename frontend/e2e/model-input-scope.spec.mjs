import { test, expect } from "@playwright/test";

test("accepted partial evidence explains model input scope without claiming abstention", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("咳嗽和肚脐疼");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(false);
  expect(data.disease_prediction.normalized_symptoms).toEqual(["cough"]);
  expect(data.disease_prediction.input_coverage.full_text_understanding_verified).toBe(false);
  await expect(page.getByTestId("model-scope-notice")).toContainText("可能遗漏其他描述");
  await expect(page.getByTestId("model-abstention-notice")).toHaveCount(0);
});
