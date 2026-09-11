import { test, expect } from "@playwright/test";

test("location permission denied keeps regional fallback usable", async ({ page }) => {
  await page.addInitScript(() => {
    navigator.geolocation.getCurrentPosition = (_success, error) => {
      if (typeof error === "function") {
        error({ code: 1, message: "User denied Geolocation" });
      }
    };
  });

  await page.goto("/triage");
  await expect(page.getByRole("heading", { name: /现在有什么不舒服/ })).toBeVisible();
  const locateButton = page.getByRole("button", { name: "使用本次精确定位" });
  if (await locateButton.count()) {
    await locateButton.click();
  }
  await expect(page.getByLabel("选择所在区域")).toBeVisible();
  await page.getByLabel("你的描述").fill("最近总是头晕");
  await page.getByRole("button", { name: "查看安全状态" }).click();
  await expect(page.getByRole("heading", { name: /可以继续了解|建议尽快|还需要一点信息|需要优先/ })).toBeVisible({ timeout: 20_000 });
});

test("speech input unsupported fallback is explicit", async ({ page }) => {
  await page.addInitScript(() => {
    delete window.SpeechRecognition;
    delete window.webkitSpeechRecognition;
  });
  await page.goto("/triage");
  await expect(page.getByText("当前浏览器不支持语音输入")).toBeVisible();
});
