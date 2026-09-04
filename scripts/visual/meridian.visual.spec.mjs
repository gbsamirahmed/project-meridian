import { expect, test } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(here, "..", "..");
const generatedVisualDirectory = path.join(repositoryRoot, "test-results", "visual");
const terrainFixture = path.join(here, "fixtures", "terrain-256.png");
const gpxFixture = path.join(repositoryRoot, "scripts", "route", "fixtures", "snowdonia-smoke.gpx");

function viewportName(testInfo) {
  const viewport = testInfo.project.use.viewport;
  return viewport ? `${viewport.width}x${viewport.height}` : testInfo.project.name;
}

function observeBrowser(page) {
  const diagnostics = {
    console: [],
    pageErrors: [],
    failedRequests: [],
    errorResponses: [],
  };

  page.on("console", (message) => {
    if (diagnostics.console.length >= 300) return;
    diagnostics.console.push({
      type: message.type(),
      text: message.text(),
      location: message.location(),
    });
  });
  page.on("pageerror", (error) => {
    diagnostics.pageErrors.push({
      name: error.name,
      message: error.message,
      stack: error.stack ?? null,
    });
  });
  page.on("requestfailed", (request) => {
    if (diagnostics.failedRequests.length >= 300) return;
    diagnostics.failedRequests.push({
      method: request.method(),
      resourceType: request.resourceType(),
      url: request.url(),
      error: request.failure()?.errorText ?? "unknown",
    });
  });
  page.on("response", (response) => {
    if (response.status() < 400 || diagnostics.errorResponses.length >= 300) return;
    diagnostics.errorResponses.push({
      status: response.status(),
      url: response.url(),
    });
  });

  return diagnostics;
}

async function saveDiagnostics(name, diagnostics, testInfo) {
  await mkdir(generatedVisualDirectory, { recursive: true });
  const outputPath = path.join(generatedVisualDirectory, `diagnostics-${name}.json`);
  await writeFile(outputPath, JSON.stringify(diagnostics, null, 2) + "\n", "utf8");
  await testInfo.attach("browser diagnostics", {
    path: outputPath,
    contentType: "application/json",
  });
}

async function openMeridian(page) {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator("main.app-shell.desktop-shell-active")).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Meridian workspace" })).toBeVisible();
  await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
}

async function capture(page, name) {
  await mkdir(generatedVisualDirectory, { recursive: true });
  await page.screenshot({
    path: path.join(generatedVisualDirectory, `${name}.png`),
    animations: "disabled",
    fullPage: false,
  });
}

test.describe.configure({ mode: "serial" });

test("desktop shell renders, interacts, and captures screenshots", async ({ page }, testInfo) => {
  const size = viewportName(testInfo);
  const diagnostics = observeBrowser(page);

  try {
    await openMeridian(page);
    await capture(page, `initial-${size}`);

    const journeyTab = page.getByRole("tab", { name: "Journey" });
    await journeyTab.click();
    await expect(journeyTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("heading", { name: "Plan with a route" })).toBeVisible();

    const locationTab = page.getByRole("tab", { name: "Location" });
    await locationTab.click();
    await expect(locationTab).toHaveAttribute("aria-selected", "true");

    await page.getByRole("button", { name: "Global settings" }).click();
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await page.getByRole("button", { name: "Close settings" }).click();
    await expect(page.getByRole("dialog", { name: "Settings" })).toHaveCount(0);

    const elevation = page.locator('button[title="Elevation"]');
    await expect(elevation).toHaveAttribute("aria-pressed", "false");
    await elevation.click();
    await expect(elevation).toHaveAttribute("aria-pressed", "true");
    await elevation.click();
    await expect(elevation).toHaveAttribute("aria-pressed", "false");

    const play = page.getByRole("button", { name: "Play forecast" });
    await play.click();
    await expect(page.getByRole("button", { name: "Pause forecast" })).toBeVisible();
    await page.getByRole("button", { name: "Pause forecast" }).click();

    await page.getByRole("button", { name: "Hide map controls" }).click();
    await expect(page.getByRole("button", { name: "Map controls" })).toBeVisible();
    await page.getByRole("button", { name: "Map controls" }).click();
    await expect(page.locator(".map-tool-strip")).toBeVisible();

    await capture(page, `post-interaction-${size}`);
  } finally {
    await saveDiagnostics(`shell-${size}`, diagnostics, testInfo);
  }

  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});

test("safe GPX route loads and profile preview/pin remains interactive", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-1440x900", "Route proof runs once at the representative desktop viewport.");
  const diagnostics = observeBrowser(page);

  await page.route("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/**", async (route) => {
    await route.fulfill({
      path: terrainFixture,
      contentType: "image/png",
      headers: { "Cache-Control": "public, max-age=3600" },
    });
  });

  try {
    await openMeridian(page);
    await page.getByRole("tab", { name: "Journey" }).click();
    await page.locator('input[type="file"]').setInputFiles(gpxFixture);

    await expect(page.getByText("Snowdonia smoke route", { exact: true }).first()).toBeVisible();
    const analysis = page.getByRole("region", { name: "Route analysis" });
    await expect(analysis).toBeVisible({ timeout: 30_000 });

    const profile = page.getByRole("slider", {
      name: "Route elevation and expected journey profile",
    });
    const bounds = await profile.boundingBox();
    expect(bounds).not.toBeNull();
    if (!bounds) throw new Error("Route profile has no rendered bounds");

    await page.mouse.move(bounds.x + bounds.width * 0.25, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText(/km ·/).first()).toBeVisible();

    await page.mouse.click(bounds.x + bounds.width * 0.5, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText("Pinned journey point")).toBeVisible();

    await page.mouse.click(bounds.x + bounds.width * 0.75, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText("Pinned journey point")).toBeVisible();

    await analysis.getByRole("button", { name: "Unpin" }).click();
    await expect(analysis.getByText(/Hover to preview/)).toBeVisible();

    await capture(page, "route-analysis-1440x900");
  } finally {
    await saveDiagnostics("route-1440x900", diagnostics, testInfo);
  }

  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});
