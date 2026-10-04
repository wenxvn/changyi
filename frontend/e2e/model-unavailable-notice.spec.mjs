import { test, expect } from "@playwright/test";

test("synthetic unavailable-model envelope renders human notice rather than error code", async ({ page }) => {
  await page.route("**/api/v1/triage", async route => {
    const response = await route.fetch();
    const envelope = await response.json();
    envelope.data.disease_prediction = {
      available: false, abstained: true, abstain_reason: "model_unavailable",
      error: "model_unavailable", disease: "", predictions: [],
      notice: "辅助疾病分析暂时不可用，请结合症状信息与专业评估。",
    };
    await route.fulfill({ response, json: envelope });
  });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("咳嗽");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("model-abstention-notice")).toContainText("辅助疾病分析暂时不可用");
  await expect(page.getByText("model_unavailable", { exact: true })).toHaveCount(0);
});
