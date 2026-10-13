/* Same-camera local browser samples; screenshots outside Git, no terrain generation. */
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import assert from 'node:assert/strict';
const output = process.env.MERIDIAN_OPACITY_OUTPUT;
if (!output) throw new Error('Fresh external MERIDIAN_OPACITY_OUTPUT required');
mkdirSync(output);
const browser = await chromium.launch({ headless: true, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await context.newPage(), errors = [], external = [], samples = [];
await context.route('**/*', route => {
  if (new URL(route.request().url()).origin !== 'http://127.0.0.1:5180') { external.push(route.request().url()); route.abort(); }
  else route.continue();
});
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
try {
  await page.goto('http://127.0.0.1:5180/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => window.meridianTiles?.map.loaded());
  for (const zoom of [10.99, 11, 11.05, 11.25, 11.5, 12, 13, 13.9, 14, 14.1, 16, 18.5]) {
    await page.evaluate(zoom => window.meridianTiles.map.jumpTo({ zoom }), zoom);
    await page.waitForFunction(() => window.meridianTiles.map.loaded());
    await page.waitForTimeout(150);
    const sample = await page.evaluate(() => {
      const { map } = window.meridianTiles;
      return { zoom: map.getZoom(), pitch: map.getPitch(), terrain: map.getTerrain() || null,
        status: document.getElementById('status').textContent,
        expressions: ['swiss-smoothed', 'swiss-2m', 'swiss-native'].map(id => map.getPaintProperty(id, 'line-opacity')) };
    });
    assert.equal(sample.pitch, 0); assert.equal(sample.terrain, null); samples.push(sample);
    if ([10.99, 11.25, 12, 14, 18.5].includes(zoom))
      await page.screenshot({ path: join(output, `z${zoom}.png`) });
  }
  assert.deepEqual(external, []); assert.deepEqual(errors, []);
  writeFileSync(join(output, 'opacity-browser-receipt.json'), JSON.stringify({
    engine: 'installed headless Chromium / SwiftShader', samples, consoleErrors: errors, externalRequests: external,
    scope: 'fractional-zoom rendered comparisons only; no Android/touch claim',
  }, null, 2) + '\n');
  console.log(`Passed ${samples.length} fractional-zoom browser samples; no console or external-request errors.`);
} finally { await browser.close(); }
