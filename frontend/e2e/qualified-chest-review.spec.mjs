import { test, expect } from "@playwright/test";

test("qualified severity denial is reviewed instead of a learned chest-pain claim", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("没有严重胸痛");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.disease_prediction.abstained).toBe(true);
  expect(data.disease_prediction.input_assertions.present).toEqual([]);
  expect(data.disease_prediction.input_assertions.unknown).toEqual(["chest_pain"]);
  expect(data.disease_prediction.input_scope_review.required).toBe(true);
  expect(data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  await expect(page.getByText(/任何程度的胸痛/)).toBeVisible();
  await expect(page.getByTestId("model-abstention-notice")).toHaveCount(0);
});
