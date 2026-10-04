import { test, expect } from "@playwright/test";

test("missing thumbnail falls back to the original doctor photo", async ({ page }) => {
  await page.route("**/static/images/doctor-variants/**", route => route.abort());
  await page.goto("/resources?doctor=2000");
  const identity = page.locator(".resource-detail__identity");
  await expect(identity).toBeVisible({ timeout: 20_000 });
  await identity.scrollIntoViewIfNeeded();
  const image = identity.locator(".doctor-index-avatar img");
  await expect(image).toHaveAttribute("src", /\/static\/images\/doctors\//);
  await expect.poll(() => image.evaluate(node => node.complete && node.naturalWidth > 0)).toBe(true);
});

test("unavailable photo leaves a readable identity instead of a broken image", async ({ page }) => {
  await page.route("**/static/images/doctor-variants/**", route => route.abort());
  await page.route("**/static/images/doctors/**", route => route.abort());
  await page.goto("/resources?doctor=2000");
  const identity = page.locator(".resource-detail__identity");
  await expect(identity).toBeVisible({ timeout: 20_000 });
  await identity.scrollIntoViewIfNeeded();
  await expect(identity.locator(".doctor-index-avatar img")).toHaveCount(0);
  await expect(identity.locator(".doctor-index-avatar")).not.toBeEmpty();
  await expect(page.locator("#resource-detail-title")).toBeVisible();
});
