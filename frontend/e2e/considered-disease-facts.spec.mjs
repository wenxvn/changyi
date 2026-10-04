import { test, expect } from "@playwright/test";

test("considered disease stays unconfirmed until the user supplies a source confirmation", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("医生考虑糖尿病");
  const first = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await first).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.htriage_analysis.known_disease.source).toBe("unconfirmed_mention");
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
  expect(clarified.htriage_analysis.known_disease.evidence_source).toBe("structured_followup");
  expect(clarified.original_condition).toBe("医生考虑糖尿病");
});
