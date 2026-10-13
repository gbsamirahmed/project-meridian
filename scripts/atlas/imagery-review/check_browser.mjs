import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import assert from 'node:assert/strict';
const output = process.env.MERIDIAN_BROWSER_OUTPUT;
if (!output) throw Error('Set an output directory outside Git');
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage(), external = [], errors = [];
await context.route('**/*', route => {
  const origin = new URL(route.request().url()).origin;
  if (origin !== 'http://127.0.0.1:5182') { external.push(origin); return route.abort(); }
  return route.continue();
});
page.on('pageerror', error => errors.push(error.message));
const settle = () => page.waitForFunction(() => window.imageryReview?.map.loaded());
try {
  await page.goto('http://127.0.0.1:5182/'); await settle();
  await page.screenshot({ path: join(output, 'overview-contours.png') });
  await page.locator('#contours').uncheck(); await page.screenshot({ path: join(output, 'overview-photo.png') });
  assert.equal(await page.evaluate(() => window.imageryReview.map.getLayoutProperty('swiss-smoothed', 'visibility')), 'none');
  await page.locator('#contours').check(); await page.locator('#shade').check(); await settle();
  await page.screenshot({ path: join(output, 'overview-shade.png') });
  await page.locator('#shade').uncheck(); await page.locator('#close').click(); await settle();
  await page.screenshot({ path: join(output, 'close.png') });
  const canvas = page.locator('canvas').first(); const box = await canvas.boundingBox();
  const before = await page.evaluate(() => window.imageryReview.map.getCenter().toArray());
  await page.mouse.move(box.x + 800, box.y + 500); await page.mouse.down();
  await page.mouse.move(box.x + 850, box.y + 520, { steps: 5 }); await page.mouse.up(); await settle();
  assert.notDeepEqual(await page.evaluate(() => window.imageryReview.map.getCenter().toArray()), before);
  await page.setViewportSize({ width: 384, height: 832 }); await settle();
  await page.screenshot({ path: join(output, 'mobile.png') });
  const state = await page.evaluate(() => ({ pitch: window.imageryReview.map.getPitch(), terrain: window.imageryReview.map.getTerrain() ?? null,
    errors: window.imageryReview.errors, contourFragments: window.imageryReview.map.queryRenderedFeatures({ layers: ['swiss-native'] }).length }));
  assert.equal(state.pitch, 0); assert.equal(state.terrain, null); assert.ok(state.contourFragments > 0);
  assert.deepEqual(state.errors, []); assert.deepEqual(errors, []); assert.deepEqual(external, []);
  const stats = await fetch('http://127.0.0.1:5182/stats').then(response => response.json());
  await writeFile(join(output, 'receipt.json'), JSON.stringify({ state, stats, external, errors,
    renderer: 'Chromium / SwiftShader; reference viewport is not Android validation' }, null, 2));
  console.log(JSON.stringify({ state, stats, external, errors }));
} finally { await browser.close(); }
