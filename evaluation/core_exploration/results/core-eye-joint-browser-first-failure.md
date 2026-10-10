# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: eye-joint-assessment.spec.mjs >> red eye with photophobia shows emergency assessment and 120 exit
- Location: e2e\eye-joint-assessment.spec.mjs:3:1

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByTestId('care-result')
Expected substring: "红眼"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" getByTestId('care-result') with timeout 5000ms
  - waiting for getByTestId('care-result')

```

```yaml
- link "跳转到主要内容":
  - /url: "#main-content"
- banner:
  - button "返回常医智导首页":
    - strong: 常医智导
    - text: Care Intelligence
  - navigation "主导航":
    - button "智能就医"
    - button "医疗资源"
    - button "就医地图"
    - button "可信 AI"
    - button "开始智能分诊"
  - text: 常州 · 320400
  - button "打开本地偏好"
- main:
  - button "返回首页"
  - list "分诊进度":
    - listitem: ✓ 描述症状
    - listitem: ✓ 补充信息
    - listitem: 3 安全方向
    - listitem: 4 资源路径
  - text: 你的描述
  - paragraph: “左眼发红疼痛，非常怕光”
  - button "修改"
  - list "分析进度":
    - listitem:
      - strong: 已读取描述
    - listitem:
      - strong: Safety Gate 完成
      - text: 高风险优先处理
    - listitem:
      - strong: 急诊出口
      - text: 不再推荐普通就医路径
  - alert "需要优先进行紧急医疗评估":
    - text: 需要优先评估 高风险 · 安全优先，普通资源推荐已停止
    - heading "需要优先进行紧急医疗评估" [level=2]
    - paragraph: 不要继续等待在线推荐结果。如果当前情况紧急、持续加重或有人意识、呼吸异常，请立即联系当地急救服务。
    - link "拨打 120":
      - /url: tel:120
    - button "查看急诊资源"
    - paragraph: 当前红眼合并怕光或视力变化，需要优先急诊专业评估，不能等待普通预约；本系统不诊断眼病。
    - paragraph: 目录存在急诊字段 ≠ 当前可接诊。真实急救以 120 调度为准。
    - paragraph: 系统只提供辅助分流信息，不替代急救指令、医生诊断或处方。
  - complementary "当前上下文":
    - region "就近急诊资源":
      - heading "就近急诊资源" [level=3]
      - text: 公开字段标记，非实时可用性
      - list:
        - listitem:
          - strong: 常州市第一人民医院
          - text: 三级甲等 · 综合医院 天宁区局前街185号
          - link "高德导航":
            - /url: https://uri.amap.com/navigation?to=119.958%2C31.7768%2C%E5%B8%B8%E5%B7%9E%E5%B8%82%E7%AC%AC%E4%B8%80%E4%BA%BA%E6%B0%91%E5%8C%BB%E9%99%A2&mode=car&policy=1&callnative=0
        - listitem:
          - strong: 常州市第二人民医院
          - text: 三级甲等 · 综合医院 天宁区兴隆巷29号
          - link "高德导航":
            - /url: https://uri.amap.com/navigation?to=119.965%2C31.77%2C%E5%B8%B8%E5%B7%9E%E5%B8%82%E7%AC%AC%E4%BA%8C%E4%BA%BA%E6%B0%91%E5%8C%BB%E9%99%A2&mode=car&policy=1&callnative=0
        - listitem:
          - strong: 常州市中医医院
          - text: 三级甲等 · 中医医院 天宁区和平北路25号
          - link "高德导航":
            - /url: https://uri.amap.com/navigation?to=119.962%2C31.78%2C%E5%B8%B8%E5%B7%9E%E5%B8%82%E4%B8%AD%E5%8C%BB%E5%8C%BB%E9%99%A2&mode=car&policy=1&callnative=0
        - listitem:
          - strong: 常州市第三人民医院
          - text: 三级乙等 · 综合医院 天宁区兰陵北路300号
          - link "高德导航":
            - /url: https://uri.amap.com/navigation?to=119.955%2C31.76%2C%E5%B8%B8%E5%B7%9E%E5%B8%82%E7%AC%AC%E4%B8%89%E4%BA%BA%E6%B0%91%E5%8C%BB%E9%99%A2&mode=car&policy=1&callnative=0
        - listitem:
          - strong: 常州市肿瘤医院
          - text: 三级乙等 · 专科医院 钟楼区怀德北路1号
          - link "高德导航":
            - /url: https://uri.amap.com/navigation?to=119.948%2C31.785%2C%E5%B8%B8%E5%B7%9E%E5%B8%82%E8%82%BF%E7%98%A4%E5%8C%BB%E9%99%A2&mode=car&policy=1&callnative=0
      - paragraph: 这些标记说明目录中记录了急诊科室，不代表当前可以接诊。真实急救请以 120 调度为准。
      - button "在地图上查看急诊分布"
    - region "到院位置":
      - text: 到院位置
      - paragraph: 未提供位置
      - button "使用本次精确定位"
      - text: 选择所在区域
      - combobox "选择所在区域":
        - option "选择所在区域" [selected]
        - option "天宁区（参考点估算）"
        - option "钟楼区（参考点估算）"
        - option "武进区（参考点估算）"
        - option "新北区（参考点估算）"
        - option "金坛区（参考点估算）"
        - option "溧阳市（参考点估算）"
        - option "经开区（参考点估算）"
      - paragraph: 未使用用户位置；距离和交通可达性不会影响推荐排序。
- contentinfo:
  - text: 常医智导
  - button "可信 AI"
  - button "医疗资源"
  - button "就医地图"
  - text: 面向常州示范区的就医方向与资源信息参考，不替代医生诊断、急救或处方。
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test("red eye with photophobia shows emergency assessment and 120 exit", async ({ page }) => {
  4  |   await page.goto("/triage");
  5  |   await page.locator("#triage-condition").fill("左眼发红疼痛，非常怕光");
  6  |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/triage") && r.request().method() === "POST");
  7  |   await page.getByRole("button", { name: "查看安全状态" }).click();
  8  |   const d = (await (await response).json()).data;
  9  |   expect(d.triage_status).toBe("EMERGENCY");
> 10 |   await expect(page.getByTestId("care-result")).toContainText("红眼");
     |                                                 ^ Error: expect(locator).toContainText(expected) failed
  11 |   await expect(page.getByRole("link", { name: /120/ })).toBeVisible();
  12 | });
  13 | 
  14 | test("current joint swelling pain and restricted movement bypass ordinary booking", async ({ page }) => {
  15 |   await page.goto("/triage");
  16 |   await page.locator("#triage-condition").fill("右膝肿胀疼痛，不能弯曲");
  17 |   await page.getByRole("button", { name: "查看安全状态" }).click();
  18 |   await expect(page.getByTestId("care-result")).toContainText("关节肿痛");
  19 |   const response = page.waitForResponse(r => r.url().endsWith("/api/v1/recommendations") && r.request().method() === "POST");
  20 |   await page.getByRole("button", { name: "暂时跳过，查看当前就医方向" }).click();
  21 |   const d = (await (await response).json()).data;
  22 |   expect(d.resource_strategy.code).toBe("urgent_assessment");
  23 |   expect(d.recommended_doctors).toEqual([]);
  24 |   expect(d.weights_used).toEqual({});
  25 | });
  26 | 
```