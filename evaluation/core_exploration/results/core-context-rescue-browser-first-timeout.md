# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-smoke.spec.mjs >> home and core resource pages render with actionable navigation
- Location: e2e\product-smoke.spec.mjs:33:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.waitFor: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('heading', { name: /什么时候不该给出答案/ }) to be visible

```

# Page snapshot

```yaml
- generic [ref=f3e3]:
  - link "跳转到主要内容" [ref=f3e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f3e5]:
    - button "返回常医智导首页" [ref=f3e6] [cursor=pointer]:
      - generic [ref=f3e12]:
        - strong [ref=f3e13]: 常医智导
        - generic [ref=f3e14]: Care Intelligence
    - navigation "主导航" [ref=f3e15]:
      - button "智能就医" [ref=f3e16] [cursor=pointer]
      - button "医疗资源" [ref=f3e17] [cursor=pointer]
      - button "就医地图" [ref=f3e18] [cursor=pointer]
      - button "可信 AI" [ref=f3e19] [cursor=pointer]
      - button "开始智能分诊" [ref=f3e20] [cursor=pointer]
    - generic [ref=f3e25]:
      - generic [ref=f3e26]: 常州 · 320400
      - button "打开本地偏好" [ref=f3e28] [cursor=pointer]
  - main [ref=f3e33]:
    - alert [ref=f3e36]:
      - text: 请求超时，请检查网络后重试。
      - button "重试" [ref=f3e39] [cursor=pointer]
  - contentinfo [ref=f3e40]:
    - generic [ref=f3e41]:
      - generic [ref=f3e42]: 常医智导
      - generic [ref=f3e49]:
        - button "可信 AI" [ref=f3e50] [cursor=pointer]
        - button "医疗资源" [ref=f3e54] [cursor=pointer]
        - button "就医地图" [ref=f3e59] [cursor=pointer]
    - generic [ref=f3e64]: 面向常州示范区的就医方向与资源信息参考，不替代医生诊断、急救或处方。
```

# Test source

```ts
  1   | import assert from "node:assert/strict";
  2   | import { test as base, expect } from "@playwright/test";
  3   | 
  4   | const test = base.extend({
  5   |   page: async ({ page }, use, testInfo) => {
  6   |     const consoleErrors = [];
  7   |     const pageErrors = [];
  8   |     const failedResponses = [];
  9   |     page.on("console", (message) => {
  10  |       if (message.type() === "error") consoleErrors.push(message.text());
  11  |     });
  12  |     page.on("pageerror", (error) => pageErrors.push(error.message));
  13  |     page.on("response", (response) => {
  14  |       if (response.status() >= 400) failedResponses.push(`${response.status()} ${response.url()}`);
  15  |     });
  16  | 
  17  |     await use(page);
  18  | 
  19  |     assert.deepEqual(consoleErrors, [], `browser console errors: ${consoleErrors.join(" | ")}`);
  20  |     assert.deepEqual(pageErrors, [], `browser page errors: ${pageErrors.join(" | ")}`);
  21  |     assert.deepEqual(failedResponses, [], `failed HTTP responses: ${failedResponses.join(" | ")}`);
  22  |     await page.screenshot({ path: testInfo.outputPath("final.png"), fullPage: true });
  23  |   },
  24  | });
  25  | 
  26  | async function submitTriage(page, condition) {
  27  |   await page.goto("/triage");
  28  |   await page.locator("#triage-condition").fill(condition);
  29  |   await page.getByRole("button", { name: "查看安全状态" }).click();
  30  |   await page.locator("#care-result-title, #emergency-result-title").waitFor();
  31  | }
  32  | 
  33  | test("home and core resource pages render with actionable navigation", async ({ page }, testInfo) => {
  34  |   await page.goto("/");
  35  |   await page.getByRole("heading", { name: /把症状/ }).waitFor();
  36  |   await page.screenshot({ path: testInfo.outputPath("home-desktop.png"), fullPage: true });
  37  |   await page.getByRole("button", { name: "开始智能分诊" }).click();
  38  |   await page.waitForURL("**/triage");
  39  |   await page.getByRole("heading", { name: /现在有什么不舒服/ }).waitFor();
  40  |   await page.screenshot({ path: testInfo.outputPath("triage-initial-desktop.png"), fullPage: true });
  41  | 
  42  |   await page.goto("/resources");
  43  |   await page.getByRole("heading", { name: /把城市资源/ }).waitFor();
  44  |   await page.screenshot({ path: testInfo.outputPath("resources-desktop.png"), fullPage: true });
  45  |   const navigation = page.getByRole("link", { name: /高德导航/ }).first();
  46  |   await navigation.waitFor();
  47  |   const href = await navigation.getAttribute("href");
  48  |   assert.match(href ?? "", /^https:\/\/(uri\.amap\.com\/navigation|www\.amap\.com\/search)/);
  49  | 
  50  |   await page.goto("/map");
  51  |   await page.getByRole("region", { name: "常州医院真实地理位置地图" }).waitFor();
  52  |   await page.screenshot({ path: testInfo.outputPath("map-desktop.png"), fullPage: true });
  53  |   await page.getByText("未使用用户定位", { exact: true }).waitFor();
  54  |   await page.getByRole("combobox", { name: "选择所在区域" }).selectOption("武进区");
  55  |   await page.getByText("按区域参考点估算", { exact: true }).waitFor();
  56  |   await page.getByText("区域参考点", { exact: true }).waitFor();
  57  |   await page.locator(".map-resource-row").first().click();
  58  |   await page.getByRole("link", { name: /高德导航/ }).waitFor();
  59  | 
  60  |   await page.goto("/trust");
> 61  |   await page.getByRole("heading", { name: /什么时候不该给出答案/ }).waitFor();
      |                                                           ^ Error: locator.waitFor: Test timeout of 30000ms exceeded.
  62  |   await expect(page.getByText(/不能换算为中文主诉的就医科室准确率/)).toBeVisible();
  63  |   await expect(page.getByText(/不是常州患者的中文临床评测/)).toBeVisible();
  64  |   await expect(page.getByText("随机切分基线 · 症状编码疾病分类", { exact: true })).toBeVisible();
  65  |   await expect(page.getByText(/随机切分参考可能受近重复样本影响/)).toBeVisible();
  66  |   const evidence = (await (await page.request.get("/api/v1/evidence")).json()).data;
  67  |   expect(evidence.model.training_data_source.path).toContain("disease_symptom_structured_41diseases_long.csv");
  68  |   await page.screenshot({ path: testInfo.outputPath("trust-desktop.png"), fullPage: true });
  69  |   await page.getByText("技术详情", { exact: true }).click();
  70  |   await page.getByText("版本、校验信息与完整资料记录", { exact: true }).waitFor();
  71  |   await page.screenshot({ path: testInfo.outputPath("trust-technical-desktop.png"), fullPage: true });
  72  | });
  73  | 
  74  | test("routine triage can continue to a sourced hospital path", async ({ page }, testInfo) => {
  75  |   await submitTriage(page, "最近皮肤一直很痒，大概一周，没有呼吸困难，也没有发烧");
  76  |   await page.getByRole("heading", { name: "可以继续了解合适的就医路径" }).waitFor();
  77  |   await page.screenshot({ path: testInfo.outputPath("followup-desktop.png"), fullPage: true });
  78  |   await page.getByRole("button", { name: "查看当前资源路径" }).click();
  79  |   await page.getByRole("link", { name: /高德导航/ }).first().waitFor();
  80  |   await page.getByRole("button", { name: /公开资料详情/ }).first().click();
  81  |   await page.waitForURL(/\/resources\?.*hospital=\d+/, { waitUntil: "commit" });
  82  |   await page.getByText("关联医生", { exact: true }).waitFor();
  83  | });
  84  | 
  85  | test("insufficient triage asks for one more piece of information", async ({ page }) => {
  86  |   await submitTriage(page, "最近总是头晕");
  87  |   await page.getByRole("heading", { name: /可以继续了解合适的就医路径|还需要一点信息/ }).waitFor();
  88  |   await page.getByText("需要补充信息", { exact: true }).first().waitFor();
  89  |   await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).waitFor();
  90  | });
  91  | 
  92  | test("emergency triage keeps urgent action ahead of recommendations", async ({ page }, testInfo) => {
  93  |   await submitTriage(page, "胸口压榨样疼痛，喘不过气，还一直冒冷汗");
  94  |   await page.getByRole("heading", { name: "需要优先进行紧急医疗评估" }).waitFor();
  95  |   await page.screenshot({ path: testInfo.outputPath("emergency-desktop.png"), fullPage: true });
  96  |   await page.getByRole("link", { name: "拨打 120" }).waitFor();
  97  |   assert.equal(await page.getByRole("button", { name: "查看当前资源路径" }).count(), 0);
  98  |   assert.equal(await page.getByText("公开医生资料预览", { exact: true }).count(), 0);
  99  | });
  100 | 
```