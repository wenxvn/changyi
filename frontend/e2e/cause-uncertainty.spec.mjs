import { test, expect } from "@playwright/test";

test("uncertain cause does not claim the reported symptom itself is uncertain", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定为什么咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(false);
  expect(data.disease_prediction.input_assertions.present).toEqual(["cough"]);
  expect(data.disease_prediction.input_assertions.unknown).toEqual([]);
  await expect(page.getByTestId("model-scope-notice")).toBeVisible();
  await expect(page.getByTestId("model-abstention-notice")).toHaveCount(0);
});
