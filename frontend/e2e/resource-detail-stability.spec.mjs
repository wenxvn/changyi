import { test, expect } from "@playwright/test";

test("late catalog data does not reset an already loaded same-resource detail", async ({ page }) => {
  let releaseHospitals, releaseDoctors, releaseExtraDetail;
  const hospitalsGate = new Promise(resolve => { releaseHospitals = resolve; });
  const doctorsGate = new Promise(resolve => { releaseDoctors = resolve; });
  const extraGate = new Promise(resolve => { releaseExtraDetail = resolve; });
  let hospitalReleased = false;
  let readyRequests = 0;
  let detailRequests = 0;
  let thirdDelivered;
  const lateReselection = new Promise(resolve => { thirdDelivered = resolve; });
  await page.route("**/api/v1/hospitals", async route => {
    await hospitalsGate;
    await route.continue();
  });
  await page.route(/\/api\/v1\/doctors(?:\?|$)/, async route => {
    await doctorsGate;
    await route.continue();
  });
  await page.route("**/api/v1/doctors/2000", async route => {
    detailRequests += 1;
    const late = hospitalReleased;
    if (late && detailRequests > readyRequests + 1) await extraGate;
    const response = await route.fetch();
    await route.fulfill({ response });
    if (late) thirdDelivered();
  });
  try {
    await page.goto("/resources?doctor=2000");
    const identity = page.locator(".resource-detail__identity");
    await expect(identity).toBeVisible({ timeout: 20_000 });
    readyRequests = detailRequests;
    hospitalReleased = true;
    releaseHospitals();
    await lateReselection;
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await expect(identity).toBeVisible({ timeout: 2_000 });
    expect(detailRequests).toBe(readyRequests + 1);
    await expect(page.locator("#resource-detail-title")).toBeVisible();
  } finally {
    releaseHospitals();
    releaseDoctors();
    releaseExtraDetail();
  }
});
