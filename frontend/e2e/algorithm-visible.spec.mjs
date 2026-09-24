import { test, expect } from "@playwright/test";

async function submitTriage(page, condition) {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill(condition);
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await page.locator("#care-result-title, #emergency-result-title").waitFor({ timeout: 20_000 });
}

test("example chips are transparent and still use real triage API", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("example-symptoms")).toBeVisible();
  await expect(page.getByText("演示示例")).toBeVisible();
  await expect(page.getByTestId("example-routine")).toBeVisible();
  await expect(page.getByTestId("example-vague")).toBeVisible();
  await expect(page.getByTestId("example-emergency")).toBeVisible();

  const triageRequests = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/triage")) triageRequests.push(request);
  });

  await page.getByTestId("example-routine").click();
  await page.locator("#care-result-title, #emergency-result-title").waitFor({ timeout: 20_000 });
  expect(triageRequests.length).toBeGreaterThan(0);
});

test("routine example reaches resource routing with ranking explanations", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByTestId("example-routine").click();
  await expect(page.getByTestId("care-result")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/Safety Gate/).first()).toBeVisible();
  await expect(page.getByText(/就医方向|选择性拒答|自适应追问/).first()).toBeVisible();
  await page.getByRole("button", { name: "查看当前资源路径" }).click();
  await expect(page.getByRole("link", { name: /高德导航/ }).first()).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("hospital-why").first()).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("algorithm-routine.png"), fullPage: true });
});

test("vague example shows abstention, inquiry, and path refresh after answers", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByTestId("example-vague").click();
  await expect(page.locator("#care-result-title")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText("暂不强行给出", { exact: false })).toBeVisible();
  await expect(page.getByTestId("result-why")).toBeVisible();
  await expect(page.getByTestId("followup-prompt")).toBeVisible();
  await expect(page.getByText("为什么现在问")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("algorithm-vague-before.png"), fullPage: true });

  const option = page.locator(".followup-option").first();
  if (await option.count()) {
    await option.click();
    await expect(page.getByTestId("path-updated")).toBeVisible({ timeout: 20_000 });
  } else {
    await page.locator("#followup-answer").fill("大概三天");
    await page.getByRole("button", { name: "提交补充" }).click();
    await expect(page.getByTestId("path-updated")).toBeVisible({ timeout: 20_000 });
  }
  await page.screenshot({ path: testInfo.outputPath("algorithm-vague-after.png"), fullPage: true });
});

test("emergency example keeps 120 first and blocks ordinary rankings", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByTestId("example-emergency").click();
  await expect(page.locator("#emergency-result-title")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
  await expect(page.getByTestId("emergency-availability-notice")).toBeVisible();
  await expect(page.getByText("目录存在急诊字段", { exact: false })).toBeVisible();
  expect(await page.getByRole("button", { name: "查看当前资源路径" }).count()).toBe(0);
  expect(await page.getByTestId("hospital-why").count()).toBe(0);
  await page.screenshot({ path: testInfo.outputPath("algorithm-emergency.png"), fullPage: true });
});

test("triage API failure degrades with visible retry instead of fake success", async ({ page }, testInfo) => {
  await page.route("**/api/v1/triage", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        data: null,
        meta: { request_id: "test", model_version: "unavailable", region_code: "320400" },
        error: { code: "MODEL_UNAVAILABLE", message: "模型暂时不可用。" },
      }),
    }),
  );

  await page.goto("/triage");
  await page.locator("#triage-condition").fill("最近皮肤一直很痒，大概一周");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByRole("alert")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText(/智能分析暂时不可用|暂时还无法完成/)).toBeVisible();
  await expect(page.getByRole("button", { name: "重试" })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("algorithm-api-error.png"), fullPage: true });
});

test("recommendation API failure keeps triage result and offers resource retry", async ({ page }, testInfo) => {
  await page.route("**/api/v1/recommendations**", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({
        data: null,
        meta: { request_id: "test", model_version: "unavailable", region_code: "320400" },
        error: { code: "MODEL_UNAVAILABLE", message: "资源推荐暂时不可用。" },
      }),
    }),
  );

  await submitTriage(page, "最近皮肤一直很痒，大概一周，没有呼吸困难，也没有发烧");
  await expect(page.getByTestId("care-result")).toBeVisible();
  await page.getByRole("button", { name: "查看当前资源路径" }).click();
  await expect(page.getByRole("button", { name: "重试" }).first()).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("care-result")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("algorithm-recommendation-error.png"), fullPage: true });
});
