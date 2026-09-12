import assert from "node:assert/strict";
import { test as base } from "@playwright/test";

const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    const consoleErrors = [];
    const pageErrors = [];
    const failedResponses = [];
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(message.text());
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400) failedResponses.push(`${response.status()} ${response.url()}`);
    });

    await use(page);

    assert.deepEqual(consoleErrors, [], `browser console errors: ${consoleErrors.join(" | ")}`);
    assert.deepEqual(pageErrors, [], `browser page errors: ${pageErrors.join(" | ")}`);
    assert.deepEqual(failedResponses, [], `failed HTTP responses: ${failedResponses.join(" | ")}`);
    await page.screenshot({ path: testInfo.outputPath("final.png"), fullPage: true });
  },
});

async function submitTriage(page, condition) {
  await page.goto("/triage");
  await page.locator("#triage-condition").fill(condition);
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await page.locator("#care-result-title, #emergency-result-title").waitFor();
}

test("home and core resource pages render with actionable navigation", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByRole("heading", { name: /把症状/ }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("home-desktop.png"), fullPage: true });
  await page.getByRole("button", { name: "开始智能分诊" }).click();
  await page.waitForURL("**/triage");
  await page.getByRole("heading", { name: /现在有什么不舒服/ }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("triage-initial-desktop.png"), fullPage: true });

  await page.goto("/resources");
  await page.getByRole("heading", { name: /把城市资源/ }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("resources-desktop.png"), fullPage: true });
  const navigation = page.getByRole("link", { name: /高德导航/ }).first();
  await navigation.waitFor();
  const href = await navigation.getAttribute("href");
  assert.match(href ?? "", /^https:\/\/(uri\.amap\.com\/navigation|www\.amap\.com\/search)/);

  await page.goto("/map");
  await page.getByRole("region", { name: "常州医院真实地理位置地图" }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("map-desktop.png"), fullPage: true });
  await page.getByText("未使用用户定位", { exact: true }).waitFor();
  await page.getByRole("combobox", { name: "选择所在区域" }).selectOption("武进区");
  await page.getByText("按区域参考点估算", { exact: true }).waitFor();
  await page.getByText("区域参考点", { exact: true }).waitFor();
  await page.locator(".map-resource-row").first().click();
  await page.getByRole("link", { name: /高德导航/ }).waitFor();

  await page.goto("/trust");
  await page.getByRole("heading", { name: /什么时候不该给出答案/ }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("trust-desktop.png"), fullPage: true });
  await page.getByText("技术详情", { exact: true }).click();
  await page.getByText("版本、校验信息与完整资料记录", { exact: true }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("trust-technical-desktop.png"), fullPage: true });
});

test("routine triage can continue to a sourced hospital path", async ({ page }, testInfo) => {
  await submitTriage(page, "最近皮肤一直很痒，大概一周，没有呼吸困难，也没有发烧");
  await page.getByRole("heading", { name: "可以继续了解合适的就医路径" }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("followup-desktop.png"), fullPage: true });
  await page.getByRole("button", { name: "查看当前资源路径" }).click();
  await page.getByRole("link", { name: /高德导航/ }).first().waitFor();
  await page.getByRole("button", { name: /公开资料详情/ }).first().click();
  await page.waitForURL(/\/resources\?.*hospital=\d+/, { waitUntil: "commit" });
  await page.getByText("关联医生", { exact: true }).waitFor();
});

test("insufficient triage asks for one more piece of information", async ({ page }) => {
  await submitTriage(page, "最近总是头晕");
  await page.getByRole("heading", { name: "可以继续了解合适的就医路径" }).waitFor();
  await page.getByText("需要补充信息", { exact: true }).waitFor();
  await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).waitFor();
});

test("emergency triage keeps urgent action ahead of recommendations", async ({ page }, testInfo) => {
  await submitTriage(page, "胸口压榨样疼痛，喘不过气，还一直冒冷汗");
  await page.getByRole("heading", { name: "需要优先进行紧急医疗评估" }).waitFor();
  await page.screenshot({ path: testInfo.outputPath("emergency-desktop.png"), fullPage: true });
  await page.getByRole("link", { name: "拨打 120" }).waitFor();
  assert.equal(await page.getByRole("button", { name: "查看当前资源路径" }).count(), 0);
  assert.equal(await page.getByText("公开医生资料预览", { exact: true }).count(), 0);
});
