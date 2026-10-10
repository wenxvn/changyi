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
      - generic [ref=e36]:
        - button "返回首页" [ref=e37] [cursor=pointer]
        - list "分诊进度" [ref=e40]:
          - listitem [ref=e41]:
            - generic [ref=e42]: ✓
            - generic [ref=e43]: 描述症状
          - listitem [ref=e44]:
            - generic [ref=e45]: "2"
            - generic [ref=e46]: 补充信息
          - listitem [ref=e47]:
            - generic [ref=e48]: "3"
            - generic [ref=e49]: 安全方向
          - listitem [ref=e50]:
            - generic [ref=e51]: "4"
            - generic [ref=e52]: 资源路径
      - generic [ref=e53]:
        - generic [ref=e54]:
          - generic [ref=e55]: 你的描述
          - paragraph [ref=e56]: “我52岁，今天量血压发现很高，有轻微头痛”
        - button "修改" [ref=e57] [cursor=pointer]
      - generic [ref=e58]:
        - generic [ref=e59]: 你的描述
        - textbox "你的描述" [active] [ref=e60]:
          - /placeholder: 例如：最近总是头晕，大概有几天了。
          - text: 我52岁，今天血压190/120 mmHg，有轻微头痛
        - generic [ref=e61]:
          - generic [ref=e62]:
            - button "语音输入" [ref=e64] [cursor=pointer]
            - generic [ref=e68]: 27 / 2000
          - button "重新分析" [ref=e69] [cursor=pointer]
      - list "分析进度" [ref=e75]:
        - listitem [ref=e76]:
          - strong [ref=e81]: 已读取描述
        - listitem [ref=e82]:
          - strong [ref=e87]: Safety Gate 完成
        - listitem [ref=e88]:
          - generic [ref=e92]:
            - strong [ref=e93]: 选择性拒答
            - generic [ref=e94]: 暂不强行给出确定科室方向
        - listitem [ref=e95]:
          - generic [ref=e99]:
            - strong [ref=e100]: 自适应追问
            - generic [ref=e101]: 补充关键信息后重新计算
        - listitem [ref=e102]:
          - strong [ref=e108]: 多目标资源路由
      - generic [ref=e109]:
        - generic [ref=e110]:
          - article [ref=e112]:
            - generic [ref=e114]:
              - generic [ref=e115]: 需要补充信息
              - generic [ref=e120]: 当前描述不足以判断就医方向，系统先给出一般性建议。
            - heading "还需要一点信息，才能继续" [level=2] [ref=e121]
            - paragraph [ref=e122]: 暂不强行给出确定科室方向。先补充下面的关键信息，系统会重新整理一次；也可以先按当前一般性方向了解资源。
            - generic [ref=e123]:
              - generic [ref=e124]: 当前一般性方向
              - strong [ref=e129]: 暂不强行给出科室方向
              - generic [ref=e130]: 为什么现在不能确定：信息不足时方向会偏保守，补充后可进一步收窄。
            - generic [ref=e131]:
              - generic [ref=e132]: 为什么这样判断
              - list [ref=e133]:
                - listitem [ref=e134]: 当前血压报告的信息或适用范围尚需确认，请补充实际完整读数、单位、测量时间和年龄，并及时专业复核；不能按没有危险信号安排普通预约。
            - list "就医路径进度" [ref=e135]:
              - listitem [ref=e136]:
                - generic [ref=e140]:
                  - strong [ref=e141]: 安全门
                  - generic [ref=e142]: 已优先处理
              - listitem [ref=e144]:
                - generic [ref=e147]:
                  - strong [ref=e148]: 补充信息
                  - generic [ref=e149]: 完善理解后继续
          - region [ref=e150]:
            - generic [ref=e151]:
              - generic [ref=e152]:
                - text: 自适应追问 ·
                - generic [ref=e156]: 需要补充信息
              - generic [ref=e157]: 第 1 问 / 共 8 问
            - paragraph [ref=e158]: 为什么现在问：当前信息不足以稳定给出科室方向，补充后路径会重新计算。
            - heading "是否伴有胸痛、呼吸困难、意识异常、大出血、一侧肢体无力等危险信号？" [level=2] [ref=e163]
            - paragraph [ref=e164]: 补充急诊红旗规则
            - group "追问选项" [ref=e165]:
              - button "没有" [ref=e166] [cursor=pointer]
              - button "有其中一种" [ref=e170] [cursor=pointer]
              - button "不确定" [ref=e174] [cursor=pointer]
            - button "稍后补充，保留待复核状态" [ref=e178] [cursor=pointer]
            - paragraph [ref=e179]: 稍后补充不会解除待复核状态，确认前不进行资源排序。
          - region [ref=e180]:
            - generic [ref=e181]:
              - heading "资源路径" [level=3] [ref=e182]
              - generic [ref=e183]: 等待匹配
            - generic [ref=e184]: 补充信息后会自动匹配资源；也可以先跳过追问查看当前方向。
        - complementary "当前上下文" [ref=e186]:
          - complementary [ref=e187]:
            - generic [ref=e188]:
              - generic [ref=e189]: 当前理解
              - generic [ref=e193]: 需要补充信息
            - paragraph [ref=e195]: “我52岁，今天量血压发现很高，有轻微头痛”
            - generic [ref=e196]:
              - generic [ref=e197]:
                - term [ref=e198]: 安全门
                - definition [ref=e199]: 需要补充信息
              - generic [ref=e200]:
                - term [ref=e201]: 就医方向
                - definition [ref=e202]:
                  - text: 暂不强行给出科室方向
                  - generic [ref=e203]: 信息不足 · 需要补充后再收窄
            - paragraph [ref=e204]: 系统对当前输入的辅助整理，不是诊断结论。
          - region [ref=e208]:
            - generic [ref=e209]:
              - heading "下一步" [level=3] [ref=e210]
              - generic [ref=e211]: 待补充与复核
            - list [ref=e212]:
              - listitem [ref=e213]:
                - generic [ref=e218]:
                  - strong [ref=e219]: 先确认危险信号
                  - generic [ref=e220]: 请先补充信息并结合专业复核，再整理就医方向。
            - button "浏览医疗资源目录" [ref=e222] [cursor=pointer]
          - region [ref=e228]:
            - paragraph [ref=e234]: 未提供位置
            - generic [ref=e235]:
              - button "使用本次精确定位" [ref=e236] [cursor=pointer]
              - generic [ref=e242]:
                - generic [ref=e243]: 选择所在区域
                - combobox "选择所在区域" [ref=e244]:
                  - option "选择所在区域" [selected]
                  - option "天宁区（参考点估算）"
                  - option "钟楼区（参考点估算）"
                  - option "武进区（参考点估算）"
                  - option "新北区（参考点估算）"
                  - option "金坛区（参考点估算）"
                  - option "溧阳市（参考点估算）"
                  - option "经开区（参考点估算）"
            - paragraph [ref=e245]: 未使用用户位置；距离和交通可达性不会影响推荐排序。
          - group [ref=e246]:
            - generic "资源偏好 只影响匹配，不改变安全分诊" [ref=e247] [cursor=pointer]:
              - generic [ref=e248]: 资源偏好
              - generic [ref=e249]: 只影响匹配，不改变安全分诊
            - option "优先本区"
            - option "可接受跨区"
            - option "不限" [selected]
            - option "就近优先"
            - option "可接受更远但资源更匹配"
            - option "不特别在意距离" [selected]
  - contentinfo [ref=e250]:
    - generic [ref=e251]:
      - generic [ref=e252]: 常医智导
      - generic [ref=e259]:
        - button "可信 AI" [ref=e260] [cursor=pointer]
        - button "医疗资源" [ref=e264] [cursor=pointer]
        - button "就医地图" [ref=e269] [cursor=pointer]
    - generic [ref=e274]: 面向常州示范区的就医方向与资源信息参考，不替代医生诊断、急救或处方。
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
  11 |   await expect(page.getByTestId("care-result")).toContainText("实际完整读数、单位、测量时间和年龄");
  12 |   await page.getByRole("button", { name: "修改", exact: true }).click();
  13 |   await page.locator("#triage-condition").fill("我52岁，今天血压190/120 mmHg，有轻微头痛");
> 14 |   const clarified = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
     |                          ^ Error: page.waitForResponse: Test timeout of 30000ms exceeded.
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