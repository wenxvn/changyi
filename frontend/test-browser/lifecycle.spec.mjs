import { test, expect } from "@playwright/test";

function reply(route, condition) {
  return route.fulfill({ json: { data: { condition, recommended_hospitals: [], recommended_doctors: [] }, meta: {}, error: null } });
}

async function complete(page, route, condition) {
  const response = page.waitForResponse(value => value.url().endsWith("/api/v1/recommendations") && value.request().postDataJSON()?.condition === condition);
  await reply(route, condition);
  await (await response).finished();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
}

async function controlled(page) {
  const requests = new Map();
  await page.route("**/api/v1/recommendations", route => {
    requests.set(route.request().postDataJSON().condition, route);
  });
  await page.goto("/test-browser/fixture.html");
  await expect.poll(() => requests.has("A")).toBe(true);
  return requests;
}

test("StrictMode effect replay still publishes the recommendation", async ({ page }) => {
  await page.route("**/api/v1/recommendations", route => reply(route, "A"));
  await page.goto("/test-browser/fixture.html?strict");
  await expect(page.getByTestId("data")).toHaveText("A");
  await expect(page.getByTestId("loading")).toHaveText("false");
});

test("superseded A cannot clear B loading or replace B data", async ({ page }) => {
  const requests = await controlled(page);
  await page.getByRole("button", { name: "Switch B" }).click();
  await expect.poll(() => requests.has("B")).toBe(true);
  await complete(page, requests.get("A"), "A");
  await expect(page.getByTestId("data")).toHaveText("empty");
  await expect(page.getByTestId("loading")).toHaveText("true");
  await reply(requests.get("B"), "B");
  await expect(page.getByTestId("data")).toHaveText("B");
  await expect(page.getByTestId("loading")).toHaveText("false");
});

test("disabled routing discards the old response and can restart", async ({ page }) => {
  const requests = await controlled(page);
  await page.getByRole("button", { name: "Disable", exact: true }).click();
  await complete(page, requests.get("A"), "A");
  await expect(page.getByTestId("data")).toHaveText("empty");
  await expect(page.getByTestId("loading")).toHaveText("false");
  requests.delete("A");
  await page.getByRole("button", { name: "Enable", exact: true }).click();
  await expect.poll(() => requests.has("A")).toBe(true);
  await reply(requests.get("A"), "A");
  await expect(page.getByTestId("data")).toHaveText("A");
});

test("returning to A cannot confuse the first A with the new attempt", async ({ page }) => {
  const requests = await controlled(page);
  const oldA = requests.get("A");
  await page.getByRole("button", { name: "Switch B" }).click();
  await expect.poll(() => requests.has("B")).toBe(true);
  requests.delete("A");
  await page.getByRole("button", { name: "Switch A" }).click();
  await expect.poll(() => requests.has("A")).toBe(true);
  await complete(page, oldA, "A");
  await expect(page.getByTestId("data")).toHaveText("empty");
  await expect(page.getByTestId("loading")).toHaveText("true");
  await complete(page, requests.get("B"), "B");
  await expect(page.getByTestId("loading")).toHaveText("true");
  await complete(page, requests.get("A"), "A");
  await expect(page.getByTestId("data")).toHaveText("A");
  await expect(page.getByTestId("loading")).toHaveText("false");
});
