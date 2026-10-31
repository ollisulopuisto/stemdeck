// The What's New panel (#whatsNewDialog): after an upgrade it shows the
// changelog entries newer than the acknowledged version, once; the full
// release history lives behind the About dialog's What's New button and
// never touches the seen-marker.
import { expect, test } from "@playwright/test";

const stubHealth = (page, version) =>
  page.route("**/api/health**", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ name: "StemDeck", status: "ok", version, ffmpeg_configured: true }),
    }));

const seenMarker = (page) => page.evaluate(() => JSON.parse(localStorage.getItem("stemdeck.whatsNewSeen") || "null"));

test.describe("What's New panel", () => {
  test("opens after an upgrade with the versions since the acknowledged one, and explicit close records the marker", async ({ page }) => {
    await stubHealth(page, "0.19.1");
    await page.addInitScript(() => localStorage.setItem("stemdeck.whatsNewSeen", JSON.stringify("0.19.0")));
    await page.goto("/", { waitUntil: "domcontentloaded" });

    const dialog = page.locator("#whatsNewDialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.locator("h2")).toHaveText("What's new since 0.19.0");
    await expect(dialog.locator(".wn-ver").first()).toHaveText("v0.19.1");
    await expect(dialog.locator(".wn-ver")).toHaveCount(1); // 0.19.1 only: seen was 0.19.0

    await page.locator("#whatsNewDone").click();
    await expect(dialog).toBeHidden();
    await expect.poll(() => seenMarker(page)).toBe("0.19.1");
  });

  test("first run of the feature shows the current version only, and Escape records nothing", async ({ page }) => {
    await stubHealth(page, "0.19.1");
    await page.goto("/", { waitUntil: "domcontentloaded" });

    const dialog = page.locator("#whatsNewDialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.locator("h2")).toHaveText("What's new in 0.19.1");
    await expect(dialog.locator(".wn-ver")).toHaveCount(1); // not the whole history

    await dialog.press("Escape");
    await expect(dialog).toBeHidden();
    expect(await seenMarker(page)).toBeNull(); // Escape leaves it for the next launch
  });

  test("nothing opens when the install is up to date or older than the marker", async ({ page }) => {
    await stubHealth(page, "0.19.1");
    await page.addInitScript(() => localStorage.setItem("stemdeck.whatsNewSeen", JSON.stringify("0.20.0")));
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500); // the panel is async; give it the chance to appear
    await expect(page.locator("#whatsNewDialog")).toBeHidden();
  });

  test("the About dialog's What's New button shows the full history without touching the marker", async ({ page }) => {
    await stubHealth(page, "0.19.1");
    await page.addInitScript(() => localStorage.setItem("stemdeck.whatsNewSeen", JSON.stringify("0.19.1")));
    await page.goto("/", { waitUntil: "domcontentloaded" });

    await page.locator("#aboutBtn").click();
    await page.locator("#aboutWhatsNew").click();

    const dialog = page.locator("#whatsNewDialog");
    await expect(dialog).toBeVisible();
    await expect(dialog.locator("h2")).toHaveText("Release history");
    expect(await dialog.locator(".wn-ver").count()).toBeGreaterThan(10); // the full log
    await page.locator("#whatsNewDone").click();
    await expect.poll(() => seenMarker(page)).toBe("0.19.1"); // unchanged
  });
});
