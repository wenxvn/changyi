import { test, expect } from "@playwright/test";

test("unknown asthma response remains confirmable and a later positive uses the emergency exit", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("我有哮喘，过去12小时一直喘鸣胸部发紧，用了4次急救吸入器后症状又回来");
  const initial = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await initial).json()).data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  const question = page.getByRole("region").filter({ has: page.getByRole("heading", { name: "目前是否症状加重、按个人处置方案达到最大救援量后仍不改善，或没有可用救援药？" }) });
  const unknown = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await question.getByRole("button", { name: "不确定", exact: true }).click();
  expect((await (await unknown).json()).data.triage_status).toBe("INSUFFICIENT_INFORMATION");
  const confirmed = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await question.getByRole("button", { name: "有上述危险情况", exact: true }).click();
  const data = (await (await confirmed).json()).data;
  expect(data.triage_status).toBe("EMERGENCY");
  expect(data.followup_answers.filter(answer => answer.question_id === "asthma_rescue_check")).toHaveLength(1);
  expect(data.disease_prediction.predictions).toEqual([]);
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
});
