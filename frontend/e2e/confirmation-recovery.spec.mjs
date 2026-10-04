import { test, expect } from "@playwright/test";

async function startUnknown(page) {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("不确定有没有胸痛");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("followup-option-present")).toBeVisible({ timeout: 20_000 });
}

test("confirmation of danger reaches emergency exit without ordinary ranking", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await startUnknown(page);
  const reply = page.waitForResponse(response => response.url().endsWith("/api/v1/triage") && response.request().method() === "POST");
  await page.getByTestId("followup-option-present").click();
  const result = await (await reply).json();
  expect(result.data.original_condition).toBe("不确定有没有胸痛");
  expect(result.data.triage_status).toBe("EMERGENCY");
  await expect(page.locator("#emergency-result-title")).toBeVisible();
  await expect(page.getByRole("link", { name: /拨打 120/ }).first()).toBeVisible();
  expect(rankings).toHaveLength(0);
});

test("explicit negative confirmation resumes the ordinary assistive path", async ({ page }) => {
  await startUnknown(page);
  const reply = page.waitForResponse(response => response.url().endsWith("/api/v1/triage") && response.request().method() === "POST");
  await page.getByTestId("followup-option-none").click();
  const result = await (await reply).json();
  expect(result.data.triage_status).toBe("ROUTINE");
  expect(result.data.triage.defer_resource_routing).not.toBe(true);
  expect(result.data.original_condition).toBe("不确定有没有胸痛");
  await expect(page.getByTestId("care-result")).toBeVisible();
  await expect(page.getByTestId("care-result")).not.toContainText("心血管内科");
});

test("unknown confirmation and skip keep the review state without ranking", async ({ page }) => {
  const rankings = [];
  page.on("request", request => { if (request.url().includes("/api/v1/recommendations")) rankings.push(request); });
  await startUnknown(page);
  await page.getByTestId("followup-option-unknown").click();
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  await page.getByRole("button", { name: "稍后补充，保留待复核状态" }).click();
  await expect(page.getByTestId("care-result")).toContainText("暂不强行给出科室方向");
  await page.getByRole("button", { name: "浏览医疗资源目录" }).click();
  await expect.poll(() => new URL(page.url()).pathname).toBe("/resources");
  await expect.poll(() => new URL(page.url()).searchParams.get("safety")).toBe("INSUFFICIENT_INFORMATION");
  await page.reload();
  await expect(page.getByRole("status", { name: "当前就医上下文" })).toBeVisible();
  expect(rankings).toHaveLength(0);
});

test("resource failure retries the real API and preserves the triage result", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/v1/recommendations**", route => {
    attempts += 1;
    if (attempts === 1) return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ data: null, meta: { request_id: "retry-test", model_version: "test", region_code: "320400" }, error: { code: "UNAVAILABLE", message: "资源暂时不可用" } }) });
    return route.continue();
  });
  await page.goto("/triage");
  await page.locator("#triage-condition").fill("皮肤瘙痒一周，没有呼吸困难，没有发热");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("care-result")).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "查看当前资源路径" }).click();
  const retry = page.getByRole("button", { name: "重试" }).first();
  await expect(retry).toBeVisible({ timeout: 20_000 });
  const recovered = page.waitForResponse(response => response.url().includes("/api/v1/recommendations") && response.status() === 200);
  await retry.click();
  const data = await (await recovered).json();
  expect(data.data.recommended_hospitals.length).toBeGreaterThan(0);
  await expect(page.getByTestId("care-result")).toBeVisible();
  await expect(retry).not.toBeVisible();
  expect(attempts).toBe(2);
});
