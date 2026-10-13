import { expect, test } from "@playwright/test";

const privateMarker = "synthetic-private-marker-7c91";

test("home transfers multiline input in memory, sends one real request, and keeps it out of the URL", async ({ page }) => {
  let triageRequests = 0;
  let submittedBody;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/v1/triage") && request.method() === "POST") {
      triageRequests += 1;
      submittedBody = request.postDataJSON();
    }
  });

  await page.goto("/");
  const composer = page.getByTestId("symptom-composer").first();
  const input = composer.getByTestId("symptom-input");
  const submit = page.getByRole("button", { name: "开始智能分析" });
  await expect(submit).toBeDisabled();
  await input.fill(`合成回归描述第一行\n${privateMarker}`);
  await expect(submit).toBeEnabled();
  await input.press("Control+Enter");
  await page.locator("#care-result-title, #emergency-result-title").waitFor({ timeout: 20_000 });

  await expect(page).toHaveURL(/\/triage$/);
  expect(page.url()).not.toContain(privateMarker);
  expect(triageRequests).toBe(1);
  expect(submittedBody.condition).toContain(`${privateMarker}`);
  expect(submittedBody.condition).toContain("\n");
});

test("legacy symptom query is scrubbed before the triage screen is painted and does not auto-submit", async ({ page }) => {
  let triageRequests = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/v1/triage") && request.method() === "POST") triageRequests += 1;
  });
  await page.goto(`/triage?condition=${encodeURIComponent(privateMarker)}`);
  await expect(page).toHaveURL(/\/triage$/);
  await expect(page.getByTestId("symptom-input")).toHaveValue("");
  expect(triageRequests).toBe(0);
});

test("waiting UI reports only the real request state and supports unmount cancellation", async ({ page }) => {
  let releaseResponse;
  const responseGate = new Promise((resolve) => { releaseResponse = resolve; });
  await page.route("**/api/v1/triage", async (route) => {
    const response = await route.fetch();
    await responseGate;
    try { await route.fulfill({ response }); } catch { /* The page may abort while navigating away. */ }
  });

  await page.goto("/triage");
  await page.getByTestId("symptom-input").fill("最近总是头晕");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByTestId("triage-waiting")).toBeVisible();
  await expect(page.getByTestId("care-agent")).toHaveAttribute("data-agent-stage", "waiting");
  await expect(page.locator(".progressive-status")).toHaveCount(0);

  await page.getByRole("button", { name: "返回首页" }).click();
  await expect(page.getByRole("heading", { name: /哪里不舒服/ })).toBeVisible();
  releaseResponse();
  await page.getByRole("button", { name: "开始智能分诊" }).click();
  await expect(page.getByTestId("symptom-input")).toHaveValue("");
});

test("503 shows an actionable error, and retry makes a fresh request", async ({ page }) => {
  let requests = 0;
  await page.route("**/api/v1/triage", async (route) => {
    requests += 1;
    if (requests === 1) {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          data: null,
          meta: { request_id: "e2e-503", model_version: "test", region_code: "320400" },
          error: { code: "MODEL_UNAVAILABLE", message: "合成回归：服务暂时不可用。" },
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/triage");
  await page.getByTestId("symptom-input").fill("最近总是头晕");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByRole("alert")).toContainText("服务暂时不可用");
  await expect(page.locator("#care-result-title, #emergency-result-title")).toHaveCount(0);
  await page.getByRole("button", { name: "重试" }).click();
  await page.locator("#care-result-title, #emergency-result-title").waitFor({ timeout: 20_000 });
  expect(requests).toBe(2);
});

test("reduced motion and unavailable WebGL retain the same static agent fallback", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const agent = page.getByTestId("care-agent").first();
  await expect(agent.locator("svg.care-agent__fallback")).toBeVisible();
  await expect(agent.locator("canvas.care-agent__canvas")).toHaveCount(0);

  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, ...args) {
      if (type === "webgl2" || type === "webgl" || type === "experimental-webgl") return null;
      return original.call(this, type, ...args);
    };
  });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  await page.reload();
  const fallbackAgent = page.getByTestId("care-agent").first();
  await expect(fallbackAgent.locator("svg.care-agent__fallback")).toBeVisible();
  await expect(fallbackAgent.locator("canvas.care-agent__canvas")).toHaveCount(0);
});

test("emergency response exposes 120 immediately and skips the agent scene", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/triage");
  await page.getByTestId("symptom-input").fill("胸口压榨样疼痛，喘不过气，还一直冒冷汗");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByRole("heading", { name: "需要优先进行紧急医疗评估" })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
  await expect(page.getByTestId("care-agent")).toHaveCount(0);
});

test("map marker and resource row select the same hospital and preview", async ({ page }) => {
  await page.goto("/map");
  const firstRow = page.locator(".map-resource-row").first();
  const hospitalName = await firstRow.locator("strong").innerText();
  await firstRow.click();
  await expect(firstRow).toHaveAttribute("aria-pressed", "true");
  const marker = page.getByRole("button", { name: `查看 ${hospitalName}` });
  await expect(marker).toHaveAttribute("aria-pressed", "true");
  await marker.click();
  await expect(page.getByRole("heading", { name: hospitalName, exact: true })).toBeVisible();
  await expect(firstRow).toHaveAttribute("aria-pressed", "true");
});

test("profile preference change confirms it was saved in this browser", async ({ page }) => {
  await page.goto("/profile");
  const historyToggle = page.getByRole("checkbox", { name: /记录最近分析/ });
  await historyToggle.check();
  await expect(page.getByRole("status")).toContainText("偏好已保存到当前浏览器");
});
