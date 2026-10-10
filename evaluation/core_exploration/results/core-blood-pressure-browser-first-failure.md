# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: blood-pressure-assessment.spec.mjs >> unquantified high blood pressure requires information and professional review
- Location: e2e\blood-pressure-assessment.spec.mjs:3:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByTestId('care-result')
Expected substring: "实际血压读数"
Received string:    " 需要补充信息当前描述不足以判断就医方向，系统先给出一般性建议。还需要一点信息，才能继续暂不强行给出确定科室方向。先补充下面的关键信息，系统会重新整理一次；也可以先按当前一般性方向了解资源。 当前一般性方向暂不强行给出科室方向为什么现在不能确定：信息不足时方向会偏保守，补充后可进一步收窄。为什么这样判断当前血压报告的信息或适用范围尚需确认，请补充实际完整读数、单位、测量时间和年龄，并及时专业复核；不能按没有危险信号安排普通预约。安全门已优先处理补充信息完善理解后继续"
Timeout: 5000ms

Call log:
  - Expect "toContainText" getByTestId('care-result') with timeout 5000ms
  - waiting for getByTestId('care-result')
    13 × locator resolved to <article data-testid="care-result" aria-labelledby="care-result-title" class="care-result care-result--insufficient" data-triage-status="INSUFFICIENT_INFORMATION">…</article>
       - unexpected value " 需要补充信息当前描述不足以判断就医方向，系统先给出一般性建议。还需要一点信息，才能继续暂不强行给出确定科室方向。先补充下面的关键信息，系统会重新整理一次；也可以先按当前一般性方向了解资源。 当前一般性方向暂不强行给出科室方向为什么现在不能确定：信息不足时方向会偏保守，补充后可进一步收窄。为什么这样判断当前血压报告的信息或适用范围尚需确认，请补充实际完整读数、单位、测量时间和年龄，并及时专业复核；不能按没有危险信号安排普通预约。安全门已优先处理补充信息完善理解后继续"

```

```yaml
- article "还需要一点信息，才能继续":
  - text: 需要补充信息 当前描述不足以判断就医方向，系统先给出一般性建议。
  - heading "还需要一点信息，才能继续" [level=2]
  - paragraph: 暂不强行给出确定科室方向。先补充下面的关键信息，系统会重新整理一次；也可以先按当前一般性方向了解资源。
  - text: 当前一般性方向
  - strong: 暂不强行给出科室方向
  - text: 为什么现在不能确定：信息不足时方向会偏保守，补充后可进一步收窄。 为什么这样判断
  - list:
    - listitem: 当前血压报告的信息或适用范围尚需确认，请补充实际完整读数、单位、测量时间和年龄，并及时专业复核；不能按没有危险信号安排普通预约。
  - list "就医路径进度":
    - listitem:
      - strong: 安全门
      - text: 已优先处理
    - listitem:
      - strong: 补充信息
      - text: 完善理解后继续
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test("unquantified high blood pressure requires information and professional review", async ({ page }) => {
  4  |   await page.goto("/triage");
  5  |   await page.locator("#triage-condition").fill("我52岁，今天量血压发现很高，有轻微头痛");
  6  |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  7  |   await page.getByRole("button", { name: "查看安全状态" }).click();
  8  |   const d = (await (await response).json()).data;
  9  |   expect(d.triage_status).toBe("INSUFFICIENT_INFORMATION");
  10 |   expect(d.matched_department).toBeNull();
> 11 |   await expect(page.getByTestId("care-result")).toContainText("实际血压读数");
     |                                                 ^ Error: expect(locator).toContainText(expected) failed
  12 |   await page.getByRole("button", { name: "修改", exact: true }).click();
  13 |   await page.locator("#triage-condition").fill("我52岁，今天血压190/120 mmHg，有轻微头痛");
  14 |   const clarified = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  15 |   await page.getByRole("button", { name: "查看安全状态" }).click();
  16 |   expect((await (await clarified).json()).data.triage_status).toBe("URGENT");
  17 | });
  18 | 
  19 | test("severe reported adult reading bypasses ordinary expert booking", async ({ page }) => {
  20 |   await page.goto("/triage");
  21 |   await page.locator("#triage-condition").fill("我45岁，今天血压190/120 mmHg，没有背痛或麻木");
  22 |   await page.getByRole("button", { name: "查看安全状态" }).click();
  23 |   await expect(page.getByTestId("care-result")).toContainText("血压读数");
  24 |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/recommendations") && r.request().method() === "POST");
  25 |   await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  26 |   const d = (await (await response).json()).data;
  27 |   expect(d.resource_strategy.code).toBe("urgent_assessment");
  28 |   expect(d.recommended_doctors).toEqual([]);
  29 | });
  30 | 
  31 | test("severe reading with current back pain shows emergency exit", async ({ page }) => {
  32 |   await page.goto("/triage");
  33 |   await page.locator("#triage-condition").fill("我45岁，现在血压190/120 mmHg，背痛");
  34 |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  35 |   await page.getByRole("button", { name: "查看安全状态" }).click();
  36 |   expect((await (await response).json()).data.triage_status).toBe("EMERGENCY");
  37 |   await expect(page.getByRole("alert", { name: "需要优先进行紧急医疗评估" })).toContainText("血压读数");
  38 |   await expect(page.getByRole("link", { name: "拨打 120" })).toBeVisible();
  39 | });
  40 | 
```