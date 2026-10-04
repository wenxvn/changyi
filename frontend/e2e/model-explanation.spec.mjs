import { test, expect } from "@playwright/test";

test("unsupported auxiliary input has a plain explanation without a disease claim", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("发热和咳嗽");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("model-abstention-notice")).toBeVisible();
  await expect(page.getByTestId("model-abstention-notice")).toContainText("部分症状尚不支持可靠的辅助疾病分析");
  await expect(page.getByTestId("model-abstention-notice")).toContainText("仅针对辅助疾病分析");
  await expect(page.getByTestId("care-result")).not.toContainText("unsupported_model_feature");
});

test("pending danger never claims dangerous signals were absent", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("抽搐");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  await expect(page.getByTestId("care-result")).not.toContainText("描述中未出现需要立即急诊的危险信号");
});
