import { test, expect } from "@playwright/test";

test("a repeated uncertain symptom defers model analysis rather than discarding uncertainty", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("有咳嗽但不确定是否咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.abstain_reason).toBe("symptom_assertion_uncertain");
  expect(data.disease_prediction.input_assertions.uncertainty_conflicts).toEqual(["cough"]);
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByTestId("model-abstention-notice")).toContainText("症状是否存在尚未确认");
});
