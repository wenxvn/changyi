import { test, expect } from "@playwright/test";

test("unverified chest alias is explained without replacing Safety priority", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("胸闷和咳嗽");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  const prediction = data.disease_prediction;
  expect(prediction.abstained).toBe(true);
  expect(prediction.predictions).toEqual([]);
  expect(prediction.auxiliary_abstain_reason ?? prediction.abstain_reason).toBe("unverified_semantic_equivalence");
  if (prediction.abstain_reason === "safety_gate_priority") {
    await expect(page.getByTestId("model-abstention-notice")).toHaveCount(0);
  } else {
    await expect(page.getByTestId("model-abstention-notice")).toContainText("部分症状含义尚未核验");
  }
});
