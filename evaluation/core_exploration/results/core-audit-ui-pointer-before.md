# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: blood-pressure-assessment.spec.mjs >> unquantified high blood pressure requires information and professional review
- Location: e2e\blood-pressure-assessment.spec.mjs:3:1

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForResponse: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "跳转到主要内容" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=e5]:
    - button "返回常医智导首页" [ref=e6] [cursor=pointer]:
      - generic [ref=e12]:
        - strong [ref=e13]: 常医智导
        - generic [ref=e14]: Care Intelligence
    - navigation "主导航" [ref=e15]:
      - button "智能就医" [ref=e16] [cursor=pointer]
      - button "医疗资源" [ref=e17] [cursor=pointer]
      - button "就医地图" [ref=e18] [cursor=pointer]
      - button "可信 AI" [ref=e19] [cursor=pointer]
      - button "开始智能分诊" [ref=e20] [cursor=pointer]
    - generic [ref=e25]:
      - generic [ref=e26]: 常州 · 320400
      - button "打开本地偏好" [ref=e28] [cursor=pointer]
  - main [ref=e33]:
    - generic [ref=e35]:
      - button "返回首页" [ref=e37] [cursor=pointer]
      - generic [ref=e40]:
        - generic [ref=e41]:
          - generic [ref=e42]:
            - generic [ref=e43]: 智能就医 · 从描述开始
            - generic [ref=e44]: 先看安全信号
          - heading [level=1] [ref=e48]:
            - text: 先说说，
            - emphasis [ref=e49]: 现在有什么不舒服？
          - paragraph [ref=e50]: 用自己的话描述即可。常医智导会先整理安全信号，再决定是否需要更多信息和就医资源。
          - generic [ref=e51]: 这里的结果是辅助信息，不替代医生诊断。急症信号会优先提示急救出口。
          - list [ref=e56]:
            - listitem [ref=e57]:
              - strong [ref=e58]: 安全状态
              - generic [ref=e59]: 是否需要优先急诊或尽快评估
            - listitem [ref=e60]:
              - strong [ref=e61]: 就医方向
              - generic [ref=e62]: 建议首先了解的科室方向
            - listitem [ref=e63]:
              - strong [ref=e64]: 资源路径
              - generic [ref=e65]: 常州医院、公开医生与导航入口
          - generic "算法处理链路" [ref=e66]:
            - generic [ref=e67]: 算法链路可见
            - paragraph [ref=e68]: Safety Gate → Direct Department → Selective Abstention → Adaptive Inquiry → Multi-objective Care Routing
        - generic [ref=e69]:
          - generic [ref=e70]:
            - generic [ref=e71]: 你的描述
            - textbox "你的描述" [active] [ref=e72]:
              - /placeholder: 例如：最近总是头晕，大概有几天了。
              - text: 我52岁，今天量血压发现很高，有轻微头痛
            - generic [ref=e73]:
              - generic [ref=e74]:
                - button "语音输入" [ref=e76] [cursor=pointer]
                - generic [ref=e80]: 20 / 2000
              - button "查看安全状态" [ref=e81] [cursor=pointer]
          - generic [ref=e86]:
            - generic [ref=e87]:
              - generic [ref=e90]: 演示示例
              - generic [ref=e91]: 仅预填描述，结果仍由真实 API 计算
            - group "示例症状快捷入口" [ref=e92]:
              - button "示例 普通路径 信息较明确" [ref=e93] [cursor=pointer]:
                - generic [ref=e94]: 示例
                - strong [ref=e95]: 普通路径
                - generic [ref=e96]: 信息较明确
              - button "示例 模糊 / 追问 信息不足时会追问" [ref=e97] [cursor=pointer]:
                - generic [ref=e98]: 示例
                - strong [ref=e99]: 模糊 / 追问
                - generic [ref=e100]: 信息不足时会追问
              - button "示例 红旗 / 急诊 安全门优先" [ref=e101] [cursor=pointer]:
                - generic [ref=e102]: 示例
                - strong [ref=e103]: 红旗 / 急诊
                - generic [ref=e104]: 安全门优先
          - generic [ref=e105]:
            - strong [ref=e107]: 提交后会在这里呈现安全状态和下一步
            - generic [ref=e108]: 先用一句话描述不适；系统会先过安全门，再给科室方向与常州资源。
          - region [ref=e110]:
            - paragraph [ref=e116]: 未提供位置
            - generic [ref=e117]:
              - button "使用本次精确定位" [ref=e118] [cursor=pointer]
              - generic [ref=e124]:
                - generic [ref=e125]: 选择所在区域
                - combobox "选择所在区域" [ref=e126]:
                  - option "选择所在区域" [selected]
                  - option "天宁区（参考点估算）"
                  - option "钟楼区（参考点估算）"
                  - option "武进区（参考点估算）"
                  - option "新北区（参考点估算）"
                  - option "金坛区（参考点估算）"
                  - option "溧阳市（参考点估算）"
                  - option "经开区（参考点估算）"
            - paragraph [ref=e127]: 未使用用户位置；距离和交通可达性不会影响推荐排序。
  - contentinfo [ref=e128]:
    - generic [ref=e129]:
      - generic [ref=e130]: 常医智导
      - generic [ref=e137]:
        - button "可信 AI" [ref=e138] [cursor=pointer]
        - button "医疗资源" [ref=e142] [cursor=pointer]
        - button "就医地图" [ref=e147] [cursor=pointer]
    - generic [ref=e152]: 面向常州示范区的就医方向与资源信息参考，不替代医生诊断、急救或处方。
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test("unquantified high blood pressure requires information and professional review", async ({ page }) => {
  4  |   await page.goto("/triage");
  5  |   await page.locator("#triage-condition").fill("我52岁，今天量血压发现很高，有轻微头痛");
> 6  |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
     |                         ^ Error: page.waitForResponse: Test timeout of 30000ms exceeded.
  7  |   await page.getByRole("button", { name: "查看安全状态" }).click();
  8  |   const d = (await (await response).json()).data;
  9  |   expect(d.triage_status).toBe("INSUFFICIENT_INFORMATION");
  10 |   expect(d.matched_department).toBeNull();
  11 |   await expect(page.getByTestId("care-result")).toContainText("实际完整读数、单位、测量时间和年龄");
  12 |   await page.getByRole("button", { name: "修改", exact: true }).click();
  13 |   await page.locator("#triage-condition").fill("我52岁，今天血压190/120 mmHg，有轻微头痛");
  14 |   const clarified = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  15 |   await page.getByRole("button", { name: "重新分析", exact: true }).click();
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