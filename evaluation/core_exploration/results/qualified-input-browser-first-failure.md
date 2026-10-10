# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: qualified-symptom-input.spec.mjs >> qualified symptom denial publishes a review notice rather than disease predictions
- Location: e2e\qualified-symptom-input.spec.mjs:3:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。', { exact: true })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。', { exact: true }) with timeout 5000ms
  - waiting for getByText('描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。', { exact: true })

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
    - listitem: 2 补充信息
    - listitem: 3 安全方向
    - listitem: 4 资源路径
  - text: 你的描述
  - paragraph: “没有严重头痛”
  - button "修改"
  - list "分析进度":
    - listitem:
      - strong: 已读取描述
    - listitem:
      - strong: Safety Gate 完成
    - listitem:
      - strong: 选择性拒答
      - text: 暂不强行给出确定科室方向
    - listitem:
      - strong: 自适应追问
      - text: 补充关键信息后重新计算
    - listitem:
      - strong: 多目标资源路由
  - article "可以继续了解合适的就医路径":
    - text: 可继续了解路径 当前描述未提示需要立即急诊；这不是诊断结论。
    - heading "可以继续了解合适的就医路径" [level=2]
    - paragraph: 可以按下面的方向先去了解科室与常州资源；最终判断以医生面诊为准。
    - text: 建议先了解
    - strong: 全科医学科
    - text: 为什么这样判断
    - list:
      - listitem: 更适合按科室匹配、距离和可及门诊资源综合推荐。
      - listitem: 还需补充：主要症状信息不足、缺少持续时间
    - paragraph: 描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。 此说明仅针对辅助疾病分析，不能用于判断就医是否安全。
    - list "就医路径进度":
      - listitem:
        - strong: 安全门
        - text: 未提示立即急诊
      - listitem:
        - strong: 就医方向
        - text: 科室方向已给出
      - listitem:
        - strong: 城市资源
        - text: 医院、医生与导航
  - region "是否伴有胸痛、呼吸困难、意识异常、大出血、一侧肢体无力等危险信号？":
    - text: 自适应追问 · 需要补充信息 第 1 问 / 共 8 问
    - paragraph: 为什么现在问：当前信息不足以稳定给出科室方向，补充后路径会重新计算。
    - heading "是否伴有胸痛、呼吸困难、意识异常、大出血、一侧肢体无力等危险信号？" [level=2]
    - paragraph: 补充急诊红旗规则
    - group "追问选项":
      - button "没有"
      - button "有其中一种"
      - button "不确定"
    - button "暂时跳过，查看当前就医方向"
    - paragraph: 回答后会重新计算路径；跳过则保留当前一般性方向。
  - region "资源路径":
    - heading "资源路径" [level=3]
    - text: 等待匹配 补充信息后会自动匹配资源；也可以先跳过追问查看当前方向。
  - complementary "当前上下文":
    - complementary "当前理解":
      - text: 当前理解 可继续了解路径
      - paragraph: “没有严重头痛”
      - term: 安全门
      - definition: 可继续了解路径
      - term: 就医方向
      - definition: 全科医学科
      - term: 待补充
      - definition: 主要症状信息不足、缺少持续时间
      - paragraph: 系统对当前输入的辅助整理，不是诊断结论。
    - region "下一步":
      - heading "下一步" [level=3]
      - text: 按顺序完成即可
      - list:
        - listitem:
          - strong: 匹配常州医院与医生
          - text: 点击后读取公开资源，页面会保留来源与推荐依据。
      - button "查看当前资源路径"
      - button "调整到院偏好"
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
    - group: 资源偏好 只影响匹配，不改变安全分诊
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
  3  | test("qualified symptom denial publishes a review notice rather than disease predictions", async ({ page }) => {
  4  |   await page.goto("/triage");
  5  |   await page.locator("#triage-condition").fill("没有严重头痛");
  6  |   const response = page.waitForResponse(value => value.url().endsWith("/api/v1/triage") && value.request().method() === "POST");
  7  |   await page.getByRole("button", { name: "查看安全状态" }).click();
  8  |   const data = (await (await response).json()).data;
  9  |   expect(data.disease_prediction.abstained).toBe(true);
  10 |   expect(data.disease_prediction.predictions).toEqual([]);
  11 |   expect(data.disease_prediction.input_assertions.unknown).toEqual(["headache"]);
> 12 |   await expect(page.getByText("描述包含对症状程度的否认，辅助疾病分析暂需复核，请结合完整症状进行专业评估。", { exact: true })).toBeVisible();
     |                                                                                           ^ Error: expect(locator).toBeVisible() failed
  13 | });
  14 | 
```