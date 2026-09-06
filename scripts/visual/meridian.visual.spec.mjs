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

function makeGpx(name, coordinates) {
  const points = coordinates.map(([longitude, latitude]) =>
    `<trkpt lat="${latitude}" lon="${longitude}"><ele>100</ele></trkpt>`
  ).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="Meridian visual test"><trk><name>${name}</name><trkseg>${points}</trkseg></trk></gpx>`;
}

async function mockMapNetwork(page) {
  await page.route("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/**", async (route) => {
    await route.fulfill({ path: terrainFixture, contentType: "image/png" });
  });
  await page.route("https://api.maptiler.com/resources/logo.svg", async (route) => {
    await route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="28" viewBox="0 0 120 28"><rect width="120" height="28" fill="white"/><text x="60" y="19" text-anchor="middle" font-family="Arial" font-size="16" fill="#111">MapTiler</text></svg>',
    });
  });
  await page.route("https://api.maptiler.com/tiles/satellite-v2/tiles.json?**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        tiles: ["https://visual.meridian.test/satellite/{z}/{x}/{y}.png"],
        attribution: "© MapTiler",
        minzoom: 0,
        maxzoom: 20,
      }),
    });
  });
  await page.route("https://visual.meridian.test/satellite/**", async (route) => {
    await route.fulfill({ path: terrainFixture, contentType: "image/png" });
  });
}

function locationForecastFixture() {
  const start = new Date("2026-09-06T00:00:00Z");
  const time = Array.from({ length: 168 }, (_, index) => new Date(start.getTime() + index * 3_600_000).toISOString().slice(0, 16));
  const wave = (index, period, low, high) => low + (Math.sin(index / period * Math.PI * 2) + 1) / 2 * (high - low);
  const dailyTime = Array.from({ length: 7 }, (_, index) => new Date(start.getTime() + index * 86_400_000).toISOString().slice(0, 10));
  return {
    utc_offset_seconds: 3600,
    current: {
      temperature_2m: 11.8, relative_humidity_2m: 84, precipitation: 0.3,
      cloud_cover: 72, pressure_msl: 1008, wind_speed_10m: 21,
      wind_gusts_10m: 36, visibility: 6800, dew_point_2m: 8.7,
    },
    hourly: {
      time,
      temperature_2m: time.map((_, index) => Number(wave(index - 7, 24, 5, 16).toFixed(1))),
      precipitation: time.map((_, index) => index % 29 > 23 ? null : Number(Math.max(0, wave(index, 15, -0.8, 2.4)).toFixed(1))),
      cloud_cover: time.map((_, index) => Math.round(wave(index, 19, 18, 98))),
      wind_speed_10m: time.map((_, index) => Math.round(wave(index, 28, 8, 34))),
      wind_direction_10m: time.map((_, index) => (205 + index * 7) % 360),
      wind_gusts_10m: time.map((_, index) => Math.round(wave(index, 23, 18, 52))),
      visibility: time.map((_, index) => index % 41 === 18 ? null : Math.round(wave(index, 31, 2500, 18000))),
      freezing_level_height: time.map((_, index) => Math.round(wave(index, 35, 1250, 2700))),
    },
    daily: {
      time: dailyTime,
      temperature_2m_max: dailyTime.map((_, index) => 16 - index * 0.4),
      temperature_2m_min: dailyTime.map((_, index) => 5 + index * 0.2),
    },
  };
}

async function mockLocationForecast(page) {
  await page.route("https://nominatim.openstreetmap.org/search?**", route => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify([{ lat: "56.7969", lon: "-5.0036" }]),
  }));
  await page.route("https://nominatim.openstreetmap.org/reverse?**", route => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ display_name: "Ben Nevis, Highland" }),
  }));
  await page.route("https://api.open-meteo.com/v1/forecast?**", route => {
    if (route.request().url().includes("hourly=pressure_msl")) {
      const time = Array.from({ length: 25 }, (_, index) => new Date(Date.UTC(2026, 8, 6, index)).toISOString().slice(0, 16));
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(Array.from({ length: 81 }, (_, point) => ({
          hourly: { time, pressure_msl: time.map((_, hour) => 1004 + point * 0.08 + hour * 0.12) },
        }))),
      });
    }
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(locationForecastFixture()),
    });
  });
}

async function importRoute(page, name, coordinates) {
  await page.getByRole("tab", { name: "Journey" }).click();
  await page.locator('input[type="file"]').setInputFiles({
    name: `${name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}.gpx`,
    mimeType: "application/gpx+xml",
    buffer: Buffer.from(makeGpx(name, coordinates)),
  });
  await expect(page.locator(".journey-route-title h2")).toHaveText(name, { timeout: 30_000 });
  await expect(page.getByRole("tab", { name: "Analysis" })).toBeVisible({ timeout: 30_000 });
  // MapView uses a 750 ms app-driven fit transition; inspect only the settled camera.
  await page.waitForTimeout(800);
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
    await mockMapNetwork(page);
    await openMeridian(page);
    await expect(page.getByRole("region", { name: "Forecast timeline" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Analysis" })).toHaveCount(0);
    await capture(page, `location-${size}`);

    await expect(page.getByRole("button", { name: "Enter focus mode" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Focus map" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Hide workspace" })).toHaveCount(0);
    await expect(page.locator('.desktop-brand img[src="/favicon.svg"]')).toBeVisible();

    const viewport = page.viewportSize();
    if (!viewport) throw new Error("Desktop project has no viewport");
    const infoButton = page.locator(".maplibregl-ctrl-attrib-button");
    const infoBounds = await infoButton.boundingBox();
    expect(infoBounds).not.toBeNull();
    if (!infoBounds) throw new Error("Map information control did not render");
    expect(Math.abs(viewport.width - infoBounds.x - infoBounds.width - 12)).toBeLessThanOrEqual(1);
    expect(Math.abs(viewport.height - infoBounds.y - infoBounds.height - 12)).toBeLessThanOrEqual(1);
    await expect(page.locator(".maptiler-logo")).toHaveCount(0);

    // MapLibre does not expose style readiness in the DOM; let its initial load
    // callback settle before requesting an optional basemap source.
    await page.waitForTimeout(1_000);
    await page.getByRole("button", { name: "Satellite basemap" }).click();
    const mapTilerLogo = page.locator(".maptiler-logo");
    const mapTilerImage = mapTilerLogo.locator("img");
    await expect(mapTilerImage).toBeVisible({ timeout: 20_000 });
    expect(await mapTilerImage.getAttribute("src")).toBe("https://api.maptiler.com/resources/logo.svg");
    const mapTilerBounds = await mapTilerLogo.boundingBox();
    expect(mapTilerBounds).not.toBeNull();
    if (mapTilerBounds) {
      const overlapsInfo = !(
        mapTilerBounds.x + mapTilerBounds.width <= infoBounds.x ||
        infoBounds.x + infoBounds.width <= mapTilerBounds.x ||
        mapTilerBounds.y + mapTilerBounds.height <= infoBounds.y ||
        infoBounds.y + infoBounds.height <= mapTilerBounds.y
      );
      expect(overlapsInfo).toBe(false);
    }
    await capture(page, `satellite-location-${size}`);
    await page.getByRole("button", { name: "Terrain basemap" }).click();
    await expect(page.locator(".maptiler-logo")).toHaveCount(0);

    const navigationGroup = page.locator(".maplibregl-ctrl-top-right .maplibregl-ctrl-group").first();
    const layerRail = page.locator(".map-tool-strip");
    const navigationBounds = await navigationGroup.boundingBox();
    const layerBounds = await layerRail.boundingBox();
    expect(navigationBounds).not.toBeNull();
    expect(layerBounds).not.toBeNull();
    if (!navigationBounds || !layerBounds) throw new Error("Map control rail did not render");
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

    await page.getByRole("button", { name: "Enter focus mode" }).click();
    await expect(page.getByRole("complementary", { name: "Meridian workspace" })).toHaveCount(0);
    await expect(page.locator(".map-tool-strip")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Restore Meridian interface" })).toBeVisible();
    await capture(page, `focus-${size}`);
    await page.getByRole("button", { name: "Restore Meridian interface" }).click();
    await expect(page.getByRole("complementary", { name: "Meridian workspace" })).toBeVisible();
    await expect(page.locator(".map-tool-strip")).toBeVisible();
    await capture(page, `restored-${size}`);
  } finally {
    await saveDiagnostics(`shell-${size}`, diagnostics, testInfo);
  }

  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});

test("Forecast Workspace is a shared temporal instrument beside Location", async ({ page }, testInfo) => {
  const size = viewportName(testInfo);
  const diagnostics = observeBrowser(page);
  try {
    await mockMapNetwork(page);
    await mockLocationForecast(page);
    await openMeridian(page);
    await page.getByRole("searchbox", { name: "Search location" }).fill("Ben Nevis");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.getByRole("heading", { name: "Ben Nevis, Highland" })).toBeVisible({ timeout: 15_000 });
    const openButton = page.getByRole("button", { name: "Detailed forecast" });
    await expect(openButton).toBeVisible();
    await capture(page, `forecast-location-closed-${size}`);
    await openButton.click();

    const workspace = page.getByRole("complementary", { name: "Forecast workspace" });
    await expect(workspace).toBeVisible();
    const primaryBounds = await page.getByRole("complementary", { name: "Meridian workspace" }).boundingBox();
    const workspaceBounds = await workspace.boundingBox();
    const railBounds = await page.locator(".map-tool-strip").boundingBox();
    const viewport = page.viewportSize();
    expect(primaryBounds && workspaceBounds && railBounds && viewport).toBeTruthy();
    if (primaryBounds && workspaceBounds && railBounds && viewport) {
      expect(Math.abs(workspaceBounds.x - primaryBounds.x - primaryBounds.width - 12)).toBeLessThanOrEqual(1);
      expect(Math.abs(workspaceBounds.y - 12)).toBeLessThanOrEqual(1);
      expect(Math.abs(viewport.height - workspaceBounds.y - workspaceBounds.height - 12)).toBeLessThanOrEqual(1);
      expect(railBounds.x - workspaceBounds.x - workspaceBounds.width).toBeGreaterThanOrEqual(11);
    }
    await capture(page, `forecast-open-${size}`);

    const timeline = page.getByRole("slider", { name: "Forecast hour" });
    const originalTimelineValue = await timeline.inputValue();
    const plot = page.getByRole("slider", { name: "Forecast time" });
    const plotBounds = await plot.boundingBox();
    if (!plotBounds) throw new Error("Forecast plot has no bounds");
    await page.mouse.move(plotBounds.x + plotBounds.width * 0.62, plotBounds.y + plotBounds.height * 0.35);
    expect(await timeline.inputValue()).toBe(originalTimelineValue);
    if (testInfo.project.name === "desktop-1440x900") await capture(page, "forecast-hover-1440x900");

    await page.mouse.click(plotBounds.x + plotBounds.width * 0.62, plotBounds.y + plotBounds.height * 0.35);
    await expect(workspace.getByRole("button", { name: "Unpin" })).toBeVisible();
    expect(await timeline.inputValue()).not.toBe(originalTimelineValue);
    if (testInfo.project.name === "desktop-1440x900") await capture(page, "forecast-pinned-1440x900");
    await page.mouse.click(plotBounds.x + plotBounds.width * 0.62, plotBounds.y + plotBounds.height * 0.35);
    await expect(workspace.getByRole("button", { name: "Unpin" })).toHaveCount(0);
    await plot.focus();
    await plot.press("ArrowRight");
    await plot.press("Enter");
    await expect(workspace.getByRole("button", { name: "Unpin" })).toBeVisible();
    await workspace.getByRole("button", { name: "Unpin" }).click();

    const dayButtons = workspace.getByRole("button").filter({ has: page.locator("small") });
    await dayButtons.nth(2).click();
    await expect(dayButtons.nth(2)).toHaveAttribute("aria-pressed", "true");
    if (testInfo.project.name === "desktop-1440x900") await capture(page, "forecast-another-day-1440x900");

    await page.getByRole("tab", { name: "Journey" }).click();
    await expect(workspace).toHaveCount(0);
    await page.getByRole("tab", { name: "Location" }).click();
    await expect(page.getByRole("heading", { name: "Ben Nevis, Highland" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Detailed forecast" })).toBeVisible();
  } finally {
    await saveDiagnostics(`forecast-${size}`, diagnostics, testInfo);
  }
  expect(diagnostics.pageErrors, "Unhandled browser page errors; see generated diagnostics").toEqual([]);
});

test("imported route fitting respects the visible map beside the primary workspace", async ({ page }, testInfo) => {
  const size = viewportName(testInfo);
  const diagnostics = observeBrowser(page);

  await page.route("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/**", async (route) => {
    await route.fulfill({
      path: terrainFixture,
      contentType: "image/png",
      headers: { "Cache-Control": "public, max-age=3600" },
    });
  });

  try {
    await mockMapNetwork(page);
    await openMeridian(page);
    await importRoute(page, "Ben Nevis Mountain Track", [
      [-5.0776, 56.8107], [-5.066, 56.807], [-5.058, 56.802],
      [-5.049, 56.797], [-5.039, 56.795], [-5.027, 56.798],
      [-5.015, 56.799], [-5.0036, 56.7969],
    ]);
    await capture(page, `route-fit-ben-nevis-${size}`);

    const workspaceLayout = await page.locator(".desktop-workspace-content").evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
    expect(workspaceLayout.scrollWidth).toBeLessThanOrEqual(workspaceLayout.clientWidth);

    await page.getByRole("button", { name: "Enter focus mode" }).click();
    await expect(page.getByRole("button", { name: "Restore Meridian interface" })).toBeVisible();
    await page.getByRole("button", { name: "Restore Meridian interface" }).click();
    await expect(page.locator(".journey-route-title h2")).toHaveText("Ben Nevis Mountain Track");

    if (testInfo.project.name === "desktop-1440x900") {
      await page.getByRole("button", { name: "Clear route" }).click();
      await importRoute(page, "West Highland Way", [
        [-4.316, 55.942], [-4.452, 56.064], [-4.586, 56.252],
        [-4.67, 56.471], [-4.706, 56.645], [-4.837, 56.78],
        [-5.105, 56.819],
      ]);
      await capture(page, "route-fit-west-highland-way-1440x900");

      await page.getByRole("button", { name: "Clear route" }).click();
      await importRoute(page, "Box Hill short route", [
        [-0.313, 51.25], [-0.306, 51.254], [-0.298, 51.251],
        [-0.305, 51.247], [-0.313, 51.25],
      ]);
      await capture(page, "route-fit-box-hill-1440x900");
    }
  } finally {
    await saveDiagnostics(`route-fit-${size}`, diagnostics, testInfo);
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
    await mockMapNetwork(page);
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
    // MapView uses a 750 ms app-driven fit transition; inspect only the settled camera.
    await page.waitForTimeout(800);
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
