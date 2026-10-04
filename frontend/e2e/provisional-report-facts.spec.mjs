import { test, expect } from "@playwright/test";

test("a provisional report remains a mention until explicit source confirmation", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("报告倾向糖尿病");
  const first = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  expect((await (await first).json()).data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  const riskReply = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByTestId("followup-option-none").click();
  await riskReply;
  await expect(page.getByTestId("followup-option-confirmed")).toBeEnabled();
  const next = page.waitForResponse(value => value.url().endsWith("/api/v1/triage")
    && value.request().method() === "POST"
    && value.request().postDataJSON().followup_answers?.some(answer => answer.question_id === "known_disease_status" && answer.value === "confirmed"));
  await page.getByTestId("followup-option-confirmed").click();
  const clarified = (await (await next).json()).data;
  expect(clarified.htriage_analysis.known_disease.has_known_disease).toBe(true);
  expect(clarified.original_condition).toBe("报告倾向糖尿病");
});
