import { expect, test } from "@playwright/test";
import { enterHomeFromCover } from "./helpers/cover.mjs";

test("the big-screen cover enters the existing home page from anywhere", async ({ page }, testInfo) => {
  await page.goto("/");

  const cover = page.getByTestId("cover-screen");
  await expect(cover).toBeVisible();
  await expect(page.getByRole("heading", { name: "常医智导", level: 1 })).toBeVisible();
  await expect(page.getByRole("button", { name: /点击任意处进入/ })).toBeVisible();
  await expect(page.getByTestId("cover-screen").getByText("安全优先", { exact: true })).toBeVisible();
  await expect(page.getByTestId("cover-screen").getByText(/不替代医生诊断、急救或处方/)).toBeVisible();
  // The product UI stays mounted underneath but is not reachable while the cover is up.
  await expect(page.locator(".app-shell")).toHaveAttribute("inert", /.*/);
  await page.screenshot({ path: testInfo.outputPath("cover-desktop.png") });

  // Empty cover space is a valid target: no dedicated control is required.
  await page.mouse.click(40, 40);
  await expect(cover).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /哪里不舒服/ })).toBeVisible();
  await expect(page.getByTestId("symptom-composer").first()).toBeVisible();
  await expect(page.locator(".app-shell")).not.toHaveAttribute("inert", /.*/);
  await page.screenshot({ path: testInfo.outputPath("cover-entered-home.png") });
});

test("the visible enter control and the keyboard both dismiss the cover", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /点击任意处进入/ }).click();
  await expect(page.getByTestId("cover-screen")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /哪里不舒服/ })).toBeVisible();

  await page.goto("/");
  await expect(page.getByTestId("cover-screen")).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("cover-screen")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /哪里不舒服/ })).toBeVisible();
});

test("the cover is shown once per page load and never on other routes", async ({ page }) => {
  await page.goto("/triage");
  await expect(page.getByRole("heading", { name: /现在有什么不舒服/ })).toBeVisible();
  await expect(page.getByTestId("cover-screen")).toHaveCount(0);

  await page.goto("/");
  await enterHomeFromCover(page);
  await page.getByRole("navigation", { name: "主导航" }).getByRole("button", { name: "医疗资源" }).click();
  await page.getByRole("heading", { name: /找到适合当前情况/ }).waitFor();
  await page.getByRole("button", { name: "返回常医智导首页" }).click();
  await expect(page.getByRole("heading", { name: /哪里不舒服/ })).toBeVisible();
  await expect(page.getByTestId("cover-screen")).toHaveCount(0);

  await page.reload();
  await expect(page.getByTestId("cover-screen")).toBeVisible();
});

