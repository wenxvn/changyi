import { test, expect } from "@playwright/test";

test("late catalog data does not re-open or reset the doctor detail", async ({ page }) => {
  let releaseHospitals;
  const hospitalsGate = new Promise(resolve => { releaseHospitals = resolve; });
  let detailRequests = 0;
  await page.route("**/api/v1/hospitals", async route => {
    await hospitalsGate;
    await route.continue();
  });
  await page.route("**/api/v1/doctors/2000", async route => {
    detailRequests += 1;
    const response = await route.fetch();
    await route.fulfill({ response });
  });

  await page.goto("/resources?doctor=2000");
  const identity = page.locator(".resource-detail__identity");
  await expect(identity).toBeVisible({ timeout: 20_000 });
  const requestsAfterOpen = detailRequests;

  const hospitalsResponse = page.waitForResponse(response => response.url().includes("/api/v1/hospitals"));
  releaseHospitals();
  await hospitalsResponse;
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));

  await expect(identity).toBeVisible({ timeout: 2_000 });
  expect(detailRequests).toBe(requestsAfterOpen);
});

test("switching from a hospital deep link to doctors closes the sheet and stays there", async ({ page }) => {
  await page.goto("/resources?from=triage&direction=%E7%A5%9E%E7%BB%8F%E5%86%85%E7%A7%91&safety=ROUTINE&type=hospital&hospital=1");
  await expect(page.locator(".resource-detail__identity")).toBeVisible({ timeout: 20_000 });
  await page.getByTestId("resource-detail-overlay").click({ position: { x: 12, y: 12 } });
  await expect(page.getByTestId("resource-detail-overlay")).toHaveCount(0);

  await page.getByRole("tab", { name: "医生" }).click();
  await expect(page.getByTestId("resource-detail-overlay")).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "医生" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByTestId("filter-doctor-hospital")).toBeVisible({ timeout: 20_000 });

  // Give the doctors list time to resolve; the hospital deep link must not
  // reopen its sheet once the user has switched tabs.
  await page.waitForTimeout(1_500);
  await expect(page.getByTestId("resource-detail-overlay")).toHaveCount(0);
  expect(new URL(page.url()).searchParams.get("hospital")).toBeNull();
});
