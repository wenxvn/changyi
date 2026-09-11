import { test, expect } from "@playwright/test";

test.describe("mobile product smoke", () => {
  test("home keeps primary composer and navigation usable", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /把症状/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "开始分析" })).toBeVisible();
    // Unsupported browsers show an explicit fallback; supported ones show the control.
    await expect(page.getByText(/语音输入|当前浏览器不支持语音输入/).first()).toBeVisible();
    await page.screenshot({ path: test.info().outputPath("mobile-home.png"), fullPage: true });
  });

  test("triage keeps the primary action and navigation usable", async ({ page }) => {
    await page.goto("/triage");
    await expect(page.getByRole("heading", { name: /现在有什么不舒服/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "查看安全状态" })).toBeVisible();
    await page.screenshot({ path: test.info().outputPath("mobile-triage-initial.png"), fullPage: true });

    await page.getByRole("button", { name: "打开导航" }).click();
    await expect(page.getByRole("navigation", { name: "主导航" })).toBeVisible();
    await expect(page.getByRole("button", { name: "开始智能分诊" })).toBeVisible();
    await page.screenshot({ path: test.info().outputPath("mobile-navigation.png"), fullPage: true });
  });

  test("emergency path stays actionable without horizontal overflow", async ({ page }) => {
    await page.goto("/triage");
    await page.getByLabel("你的描述").fill("突然胸口压榨样疼痛，出冷汗，呼吸困难");
    await page.getByRole("button", { name: "查看安全状态" }).click();
    await expect(page.getByRole("heading", { name: /需要优先进行紧急医疗评估|建议尽快/ })).toBeVisible({ timeout: 20_000 });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    expect(overflow).toBe(false);
    await page.screenshot({ path: test.info().outputPath("mobile-emergency.png"), fullPage: true });
  });

  test("resources filters and doctor list stay usable", async ({ page }) => {
    await page.goto("/resources?type=doctor");
    await expect(page.getByRole("heading", { name: /把城市资源/ })).toBeVisible();
    await expect(page.getByTestId("filter-doctor-hospital")).toBeVisible();
    await expect(page.getByTestId("filter-doctor-department")).toBeVisible();
    await expect(page.getByTestId("filter-doctor-title")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    expect(overflow).toBe(false);
    await page.screenshot({ path: test.info().outputPath("mobile-resources.png"), fullPage: true });
  });

  test("map, trust, hospital and doctor detail stay readable", async ({ page }) => {
    for (const path of ["/map", "/trust", "/resources?hospital=1", "/resources?doctor=1"]) {
      await page.goto(path);
      await expect(page.locator("main, section").first()).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
      expect(overflow, `horizontal overflow on ${path}`).toBe(false);
      await page.screenshot({ path: test.info().outputPath(`mobile-${path.replace(/\W+/g, "-")}.png`), fullPage: true });
    }
  });
});
