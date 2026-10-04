import { test, expect } from "@playwright/test";

test("a department request keeps its direction without asking if that department is a diagnosed disease", async ({ page }) => {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("产科");
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  const data = (await (await response).json()).data;
  expect(data.htriage_analysis.known_disease.has_known_disease).toBe(false);
  expect(data.matched_department).toBe("产科");
  await expect(page.locator(".care-result__direction")).toContainText("产科");
  await expect(page.locator(".followup-prompt")).not.toContainText("已确诊、复诊，还是自己判断");
});
