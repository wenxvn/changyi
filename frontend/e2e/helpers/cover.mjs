import { expect } from "@playwright/test";

/**
 * The big-screen cover is shown on the first paint of "/" (and on reload).
 * Specs that drive the home page dismiss it the same way a person does:
 * one click anywhere on the cover surface.
 */
export async function enterHomeFromCover(page) {
  const cover = page.getByTestId("cover-screen");
  await cover.waitFor({ state: "visible" });
  await cover.click({ position: { x: 12, y: 12 } });
  await expect(cover).toHaveCount(0);
}
