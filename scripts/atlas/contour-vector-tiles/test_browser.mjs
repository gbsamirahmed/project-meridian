/* Bounded local Chromium verification; software WebGL is not an Android benchmark. */
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';
const root = process.env.MERIDIAN_TILE_ROOT;
if (!root) throw new Error('Explicit external product required');
const output = process.env.MERIDIAN_BROWSER_OUTPUT || join(root, 'browser-review-final'); mkdirSync(output);
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage(), consoleErrors = [], external = [], snapshots = [];
const countersBefore = await fetch('http://127.0.0.1:5180/stats').then(response => response.json());
await context.route('**/*', route => {
  const url = new URL(route.request().url());
  if (url.protocol.startsWith('http') && url.origin !== 'http://127.0.0.1:5180') {
    external.push(url.origin); route.abort();
  } else route.continue();
});
page.on('pageerror', error => consoleErrors.push(error.message));
page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
try {
  await page.goto('http://127.0.0.1:5180/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.meridianTiles?.metrics.firstIdleMs !== null && window.meridianTiles?.map.loaded());
  const initialFirstIdleMs = await page.evaluate(() => window.meridianTiles.metrics.firstIdleMs);
  const camera = await page.evaluate(() => ({ pitch: window.meridianTiles.map.getPitch(), terrain: window.meridianTiles.map.getTerrain() || null }));
  assert.equal(camera.pitch, 0); assert.equal(camera.terrain, null);
  for (const zoom of [9.5, 11.5, 12.5, 14, 15.9, 17.5, 18.5]) {
    const start = performance.now();
    await page.evaluate(zoom => window.meridianTiles.map.jumpTo({ zoom }), zoom);
    await page.waitForFunction(() => window.meridianTiles.map.loaded());
    await page.waitForTimeout(150);
    const record = await page.evaluate(() => {
      const { map } = window.meridianTiles;
        return { zoom: map.getZoom(), pitch: map.getPitch(), queriedFragmentsIncludingZeroOpacity: map.queryRenderedFeatures().length,
        visibleProperties: map.queryRenderedFeatures().slice(0, 3).map(feature => feature.properties),
        status: document.getElementById('status').textContent };
    });
    if (zoom === 9.5) assert.equal(record.queriedFragmentsIncludingZeroOpacity, 0); else assert.ok(record.queriedFragmentsIncludingZeroOpacity > 0);
    record.settleMs = performance.now() - start; snapshots.push(record);
    if ([14, 18.5].includes(zoom)) await page.screenshot({ path: join(output, `desktop-z${zoom}.png`) });
  }
  for (const product of ['swiss-smoothed', 'swiss-2m', 'swiss-native']) {
    await page.selectOption('#mode', product); await page.selectOption('#interval', '20');
    await page.waitForFunction(() => window.meridianTiles.map.loaded());
    assert.ok(await page.evaluate(() => window.meridianTiles.map.queryRenderedFeatures().length > 0));
  }
  await page.selectOption('#mode', 'swiss-native'); await page.selectOption('#interval', '10');
  await page.evaluate(() => window.meridianTiles.map.jumpTo({ zoom: 17, center: window.meridianTiles.metadata.centre }));
  await page.waitForFunction(() => window.meridianTiles.map.loaded());
  const before = await page.evaluate(() => window.meridianTiles.map.getCenter().toArray());
  const canvas = page.locator('canvas').first(), box = await canvas.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 80, box.y + box.height / 2 + 30, { steps: 8 }); await page.mouse.up();
  await page.waitForFunction(() => window.meridianTiles.map.loaded());
  const after = await page.evaluate(() => window.meridianTiles.map.getCenter().toArray());
  assert.notDeepEqual(after, before);
  await page.mouse.wheel(0, -150); await page.waitForTimeout(500);
  assert.ok(await page.evaluate(() => window.meridianTiles.map.getZoom() > 17));
  const pick = await page.evaluate(() => {
    const { map } = window.meridianTiles;
    for (const feature of map.queryRenderedFeatures()) {
      const coordinates = feature.geometry.type === 'LineString' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
      for (const line of coordinates) for (const point of line) {
        const pixel = map.project(point);
        if (pixel.x > 10 && pixel.y > 10 && pixel.x < map.getCanvas().clientWidth - 10 && pixel.y < map.getCanvas().clientHeight - 10)
          return { x: pixel.x, y: pixel.y };
      }
    }
  });
  assert.ok(pick); await page.mouse.click(box.x + pick.x, box.y + pick.y);
  await page.waitForFunction(() => document.getElementById('picked').textContent.includes('m LN02'));
  await page.setViewportSize({ width: 384, height: 832 });
  await page.click('#fit'); await page.selectOption('#mode', 'auto');
  await page.waitForFunction(() => window.meridianTiles.map.loaded());
  await page.screenshot({ path: join(output, 'mobile-reference.png') });
  const originalErrors = await page.evaluate(() => window.meridianTiles.metrics.errors);
  assert.deepEqual(originalErrors, []); assert.deepEqual(external, []); assert.deepEqual(consoleErrors, []);
  const normalConsoleErrors = consoleErrors.length;
  // One controlled failed local tile request, without mutating any product files.
  await context.route('**/tiles/**', route => route.abort());
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Local map error:'));
  const errorNotice = await page.locator('#status').textContent();
  await context.unroute('**/tiles/**');
  await page.reload({ waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.meridianTiles?.map.loaded());
  const result = { engine: 'installed headless Chromium; software WebGL/SwiftShader', snapshots,
    gesturePan: true, wheelZoom: true, manualVariants: true, elevationClick: true, mobileViewportRendered: true,
    externalPageRequests: external.length, normalConsoleErrors,
    controlledErrorNotice: errorNotice, recoveryAfterReload: true,
    initialFirstIdleMs, recoveryFirstIdleMs: await page.evaluate(() => window.meridianTiles.metrics.firstIdleMs),
    countersBefore, serverCountersAfter: await page.evaluate(() => fetch('/stats').then(response => response.json())) };
  writeFileSync(join(output, 'browser-receipt.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
} finally { await browser.close(); }
