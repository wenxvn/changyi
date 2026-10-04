import { test, expect } from "@playwright/test";

test("denying one fever grade does not erase an independently reported grade", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有高烧但有低烧");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(false);
  expect(data.disease_prediction.normalized_symptoms).toEqual(["fever", "mild_fever"]);
  expect(data.disease_prediction.input_coverage.model_feature_count).toBe(1);
  expect(data.disease_prediction.input_assertions.contradiction).toEqual([]);
  expect(data.disease_prediction.input_assertions.absent).toEqual(["high_fever"]);
  expect(data.matched_department).toBe("全科医学科");
  await expect(page.getByTestId("model-scope-notice")).toBeVisible();
});
