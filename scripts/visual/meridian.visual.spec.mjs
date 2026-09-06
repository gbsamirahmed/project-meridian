import { expect, test } from "@playwright/test";
import { mkdir, readFile, writeFile } from "node:fs/promises";
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
  const diagnostics = { console: [], pageErrors: [], failedRequests: [], errorResponses: [] };
  page.on("console", (message) => {
    if (diagnostics.console.length >= 300) return;
    diagnostics.console.push({ type: message.type(), text: message.text(), location: message.location() });
  });
  page.on("pageerror", (error) => {
    diagnostics.pageErrors.push({ name: error.name, message: error.message, stack: error.stack ?? null });
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
    diagnostics.errorResponses.push({ status: response.status(), url: response.url() });
  });
  return diagnostics;
}

async function saveDiagnostics(name, diagnostics, testInfo) {
  await mkdir(generatedVisualDirectory, { recursive: true });
  const outputPath = path.join(generatedVisualDirectory, `diagnostics-${name}.json`);
  await writeFile(outputPath, JSON.stringify(diagnostics, null, 2) + "\n", "utf8");
  await testInfo.attach("browser diagnostics", { path: outputPath, contentType: "application/json" });
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

test("desktop shell keeps the timeline in Location and the layer rail persistent", async ({ page }, testInfo) => {
  const size = viewportName(testInfo);
  const diagnostics = observeBrowser(page);

  try {
    await openMeridian(page);
    await expect(page.getByRole("region", { name: "Forecast timeline" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Analysis" })).toHaveCount(0);
    await capture(page, `location-${size}`);

    const navigationGroup = page.locator(".maplibregl-ctrl-top-right .maplibregl-ctrl-group").first();
    const layerRail = page.locator(".map-tool-strip");
    const navigationBounds = await navigationGroup.boundingBox();
    const layerBounds = await layerRail.boundingBox();
    expect(navigationBounds).not.toBeNull();
    expect(layerBounds).not.toBeNull();
    if (!navigationBounds || !layerBounds) throw new Error("Map control rail did not render");
    const viewport = page.viewportSize();
    if (!viewport) throw new Error("Desktop project has no viewport");
    expect(Math.abs(navigationBounds.width - layerBounds.width)).toBeLessThanOrEqual(1);
    expect(Math.abs(navigationBounds.x + navigationBounds.width / 2 - layerBounds.x - layerBounds.width / 2)).toBeLessThanOrEqual(1);
    expect(Math.abs(viewport.width - navigationBounds.x - navigationBounds.width - 12)).toBeLessThanOrEqual(1);
    expect(Math.abs(viewport.width - layerBounds.x - layerBounds.width - 12)).toBeLessThanOrEqual(1);
    expect(Math.abs(navigationBounds.y - 12)).toBeLessThanOrEqual(1);
    expect(Math.abs(layerBounds.y - navigationBounds.y - navigationBounds.height - 10)).toBeLessThanOrEqual(1);
    await expect(page.getByRole("button", { name: "Hide map controls" })).toHaveCount(0);

    const forecastRange = page.getByRole("slider", { name: "Forecast hour" });
    await expect(forecastRange).toBeVisible();
    await page.getByRole("button", { name: "Play forecast" }).click();
    await expect(page.getByRole("button", { name: "Pause forecast" })).toBeVisible();

    const journeyTab = page.getByRole("tab", { name: "Journey" });
    await journeyTab.click();
    await expect(journeyTab).toHaveAttribute("aria-selected", "true");
    await expect(page.getByRole("region", { name: "Forecast timeline" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Plan with a route" })).toBeVisible();
    await expect(page.getByText("Processed locally in your browser.")).toBeVisible();
    await capture(page, `journey-empty-${size}`);

    const locationTab = page.getByRole("tab", { name: "Location" });
    await locationTab.click();
    await expect(page.getByRole("button", { name: "Pause forecast" })).toBeVisible();
    await page.getByRole("button", { name: "Pause forecast" }).click();

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
    await expect(layerRail).toBeVisible();

    await capture(page, `post-interaction-${size}`);
  } finally {
    await saveDiagnostics(`shell-${size}`, diagnostics, testInfo);
  }

  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});

test("safe GPX route exposes Journey, in-panel Tune, and interactive Analysis", async ({ page }, testInfo) => {
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
    const longRouteName = "Snowdonia ridge traverse with an intentionally long route name for workspace overflow validation";
    const fixtureXml = (await readFile(gpxFixture, "utf8")).replaceAll("Snowdonia smoke route", longRouteName);
    await page.locator('input[type="file"]').setInputFiles({
      name: "meridian-public-long-name-smoke.gpx",
      mimeType: "application/gpx+xml",
      buffer: Buffer.from(fixtureXml),
    });

    const routeTitle = page.locator(".journey-route-title h2");
    await expect(routeTitle).toHaveText(longRouteName);
    await expect(page.getByRole("tab", { name: "Analysis" })).toBeVisible({ timeout: 30_000 });
    await expect(page.locator(".journey-profile-card .route-profile-summary")).toBeVisible();

    const titleLayout = await routeTitle.evaluate((element) => {
      const style = getComputedStyle(element);
      return {
        clientWidth: element.clientWidth,
        scrollWidth: element.scrollWidth,
        overflow: style.overflow,
        textOverflow: style.textOverflow,
        whiteSpace: style.whiteSpace,
      };
    });
    expect(titleLayout.scrollWidth).toBeGreaterThan(titleLayout.clientWidth);
    expect(titleLayout.overflow).toBe("hidden");
    expect(titleLayout.textOverflow).toBe("ellipsis");
    expect(titleLayout.whiteSpace).toBe("nowrap");
    const workspaceLayout = await page.locator(".desktop-workspace-content").evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
      overflowX: getComputedStyle(element).overflowX,
    }));
    expect(workspaceLayout.scrollWidth).toBeLessThanOrEqual(workspaceLayout.clientWidth);
    expect(workspaceLayout.overflowX).toBe("hidden");
    const clearRouteLayout = await page.getByRole("button", { name: "Clear route" }).evaluate((element) => ({
      flexShrink: getComputedStyle(element).flexShrink,
      whiteSpace: getComputedStyle(element).whiteSpace,
    }));
    expect(clearRouteLayout.flexShrink).toBe("0");
    expect(clearRouteLayout.whiteSpace).toBe("nowrap");
    await expect(page.getByText("Environmental details")).toHaveCount(0);
    await capture(page, "journey-loaded-1440x900");

    await page.getByRole("button", { name: "Tune" }).click();
    await expect(page.getByRole("heading", { name: "Journey settings" })).toBeVisible();
    await expect(page.locator(".journey-settings-view")).toBeVisible();
    await expect(page.locator(".workspace-popover")).toHaveCount(0);
    await capture(page, "journey-settings-1440x900");
    await page.locator(".journey-back-button").click();
    await expect(page.getByRole("heading", { name: "Journey settings" })).toHaveCount(0);

    const mapFurniture = page.locator(".maplibregl-ctrl-bottom-right");
    const beforeAnalysis = await mapFurniture.boundingBox();
    await page.getByRole("button", { name: "Analyse", exact: true }).click();
    const analysis = page.getByRole("region", { name: "Route analysis" });
    await expect(analysis).toBeVisible();
    await expect(page.getByRole("tab", { name: "Analysis" })).toHaveAttribute("aria-selected", "true");
    await expect(page.locator(".route-analysis.desktop-surface")).toHaveCount(0);
    await expect(page.getByRole("region", { name: "Forecast timeline" })).toHaveCount(0);
    const afterAnalysis = await mapFurniture.boundingBox();
    expect(beforeAnalysis).not.toBeNull();
    expect(afterAnalysis).not.toBeNull();
    if (beforeAnalysis && afterAnalysis) {
      expect(Math.abs(beforeAnalysis.x - afterAnalysis.x)).toBeLessThanOrEqual(1);
      expect(Math.abs(beforeAnalysis.y - afterAnalysis.y)).toBeLessThanOrEqual(1);
    }

    for (const name of ["Temperature analysis", "Rain analysis", "Wind analysis", "Gradient analysis", "Elevation analysis"]) {
      const button = analysis.getByRole("button", { name });
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
    }

    const profile = analysis.getByRole("slider", { name: "Route elevation and expected journey profile" });
    const bounds = await profile.boundingBox();
    expect(bounds).not.toBeNull();
    if (!bounds) throw new Error("Route profile has no rendered bounds");
    await page.mouse.move(bounds.x + bounds.width * 0.25, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText(/km ·/).first()).toBeVisible();
    await page.mouse.click(bounds.x + bounds.width * 0.5, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText("Pinned journey point")).toBeVisible();
    await page.mouse.click(bounds.x + bounds.width * 0.75, bounds.y + bounds.height * 0.5);
    await expect(analysis.getByText("Pinned journey point")).toBeVisible();
    await capture(page, "analysis-pinned-1440x900");
    await analysis.getByRole("button", { name: "Unpin" }).click();
    await expect(analysis.getByText(/Hover to preview/)).toBeVisible();
  } finally {
    await saveDiagnostics("route-1440x900", diagnostics, testInfo);
  }

  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});
