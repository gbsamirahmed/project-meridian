import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { createHash } from 'node:crypto';

const code = readFileSync(new URL('./viewer.js', import.meta.url), 'utf8');
const pure = {}; vm.runInNewContext(code, pure);
const model = pure.MeridianContourMath;

test('four provisional bands and deterministic threshold boundaries', () => {
  assert.deepEqual([4, 2, 1, 0.75, 0.5, 0.25, 0.2].map(value => model.bandFor(value)), [0, 0, 1, 1, 2, 2, 3]);
  assert.deepEqual(Array.from(model.bands, band => [band.variant, band.interval]), [[2, 20], [1, 20], [1, 10], [0, 10]]);
  assert.equal(model.policy.settleMs, 180);
});
test('hysteresis resists small reversals and accepts larger scale changes', () => {
  assert.equal(model.bandFor(1.9, 0), 0); assert.equal(model.bandFor(1.75, 0), 1);
  assert.equal(model.bandFor(2.1, 1), 1); assert.equal(model.bandFor(2.25, 1), 0);
  assert.equal(model.bandFor(0.24, 2), 2); assert.equal(model.bandFor(0.21, 2), 3);
  assert.equal(model.bandFor(0.2, 0), 3); assert.equal(model.bandFor(4, 3), 0);
});
test('north-up affine raster registration and zoom anchor are reversible', () => {
  for (const size of [[384, 600], [1280, 700]]) {
    for (const scale of [0.01, 0.5, 8]) {
      const view = { x: 2625000, y: 1092000, scale };
      for (const [col, row] of [[0, 0], [1999, 2000], [3999, 3999]]) {
        const point = [2624000 + (col + 0.5) * 0.5, 1093000 - (row + 0.5) * 0.5];
        const screen = model.worldToScreen(point, view, ...size);
        assert.deepEqual(Array.from(model.screenToWorld(screen, view, ...size)), point);
        const origin = model.worldToScreen([2624000, 1093000], view, ...size);
        assert.ok(Math.abs(screen[0] - origin[0] - (col + 0.5) * 0.5 * scale) < 1e-8);
        assert.ok(Math.abs(screen[1] - origin[1] - (row + 0.5) * 0.5 * scale) < 1e-8);
      }
      const fixed = model.screenToWorld([90, 170], view, ...size);
      const changed = model.zoom(view, 1.5, [90, 170], ...size);
      assert.deepEqual(Array.from(model.screenToWorld([90, 170], changed, ...size)), Array.from(fixed));
    }
  }
});
test('20 m subset and nearest-line distance preserve height semantics', () => {
  assert.equal(model.accepts({ twentyMetreSubset: false }, 20), false);
  assert.equal(model.accepts({ twentyMetreSubset: false }, 10), true);
  assert.equal(model.segmentDistance([5, 4], [0, 0], [10, 0]), 4);
});

function harness() {
  const elements = new Map(), timers = new Map(), frames = new Map(); let nextId = 1;
  const calls = [];
  const context = new Proxy({}, { get: (object, key) => key in object ? object[key] : (...args) => calls.push([key, ...args]) });
  const get = id => {
    if (!elements.has(id)) elements.set(id, { value: '', checked: true, style: {}, textContent: '', listeners: {},
      addEventListener(type, callback) { this.listeners[type] = callback; },
      getBoundingClientRect: () => ({ left: 0, top: 0, width: 384, height: 600 }),
      getContext: () => context, focus() {}, setPointerCapture() {},
      getAttribute: () => 'data:image/png;base64,fixture' });
    return elements.get(id);
  };
  get('mode').value = 'auto'; get('variant').value = '2'; get('interval').value = '20';
  const line = { level: 2500, index: true, twentyMetreSubset: true, line: 0,
    coordinates: [[2624900, 1092000], [2625100, 1092000]] };
  get('contour-data').textContent = JSON.stringify({ variants: ['Native', 'Strict', 'Smoothed'].map(label => ({
    label, lines: [line], counts: { '10': { lines: 1, vertices: 2 }, '20': { lines: 1, vertices: 2 } },
  })) });
  let image;
  const sandbox = { document: { getElementById: get }, window: { devicePixelRatio: 2 },
    Image: class { constructor() { image = this; this.naturalWidth = this.naturalHeight = 4000; } },
    Path2D: class { moveTo() {} lineTo() {} }, ResizeObserver: class { observe() {} },
    requestAnimationFrame: callback => { const id = nextId++; frames.set(id, callback); return id; },
    setTimeout: callback => { const id = nextId++; timers.set(id, callback); return id; },
    clearTimeout: id => timers.delete(id),
  };
  vm.runInNewContext(code, sandbox);
  const flushFrames = () => { for (const [id, callback] of [...frames]) { frames.delete(id); callback(); } };
  const settle = () => { for (const [id, callback] of [...timers]) { timers.delete(id); callback(); } flushFrames(); };
  const send = (id, type, values = {}) => get(id).listeners[type]({ type, button: 0, pointerId: 1,
    clientX: 192, clientY: 300, preventDefault() {}, ...values });
  flushFrames();
  return { get, send, settle, flushFrames, image, calls };
}

test('mock controls: manual overrides keep camera and retained elevation picking', () => {
  const h = harness();
  h.get('mode').value = 'manual'; h.send('mode', 'change');
  const before = h.get('scale-label').textContent;
  h.get('variant').value = '0'; h.send('variant', 'change');
  h.get('interval').value = '10'; h.send('interval', 'change'); h.flushFrames();
  assert.equal(h.get('scale-label').textContent, before);
  assert.match(h.get('statistics').textContent, /Manual · Native · 10 m/);
  h.send('map', 'pointerdown'); h.send('map', 'pointerup'); h.flushFrames();
  assert.match(h.get('selection').textContent, /2500 m LN02 · Native/);
  h.send('map', 'keydown', { key: 'ArrowRight' }); h.flushFrames();
  assert.match(h.get('selection').textContent, /2500 m LN02/);
});
test('mock gestures: automatic source swap waits for release and uses CSS scale', () => {
  const h = harness();
  h.send('map', 'pointerdown');
  for (let i = 0; i < 11; i++) h.send('in', 'click');
  h.flushFrames(); h.settle();
  assert.equal(h.get('variant').value, '2');
  h.send('map', 'pointercancel'); h.settle();
  assert.equal(h.get('variant').value, '0'); assert.equal(h.get('interval').value, '10');
  assert.match(h.get('statistics').textContent, /Native detail/);
  h.send('fit', 'click'); h.settle();
  assert.equal(h.get('variant').value, '2'); assert.equal(h.get('interval').value, '20');
});
test('mock background decoding, alignment rectangle, toggle and failure notice', () => {
  const h = harness(); h.image.onload(); h.flushFrames();
  assert.ok(h.calls.some(([name, ...args]) => name === 'drawImage' && args.slice(1).join(',') === '0,0,2000,2000'));
  const before = h.calls.filter(([name]) => name === 'drawImage').length;
  h.get('background').checked = false; h.send('background', 'change'); h.flushFrames();
  assert.equal(h.calls.filter(([name]) => name === 'drawImage').length, before);
  const bad = harness(); bad.image.onerror();
  assert.match(bad.get('background-state').textContent, /could not be decoded/);
});
test('bundle is sealed and self-contained; all genuine coordinates remain reversible', () => {
  assert.ok(process.env.MERIDIAN_MULTISCALE_HTML, 'Supply the generated bundle; no skipped genuine payload validation');
  const html = readFileSync(process.env.MERIDIAN_MULTISCALE_HTML, 'utf8');
  const executable = html.split('<script>')[1].split('</script>')[0];
  assert.equal(executable, code);
  assert.ok(html.includes(`script-src 'sha256-${createHash('sha256').update(code).digest('base64')}'`));
  assert.ok(html.includes("connect-src 'none'")); assert.ok(html.includes('img-src data:'));
  assert.equal(/\b(fetch|XMLHttpRequest|WebSocket)\b/.test(code), false);
  assert.equal(/(?:src|href)=["']https?:/i.test(html), false);
  const payload = JSON.parse(html.split('<script type="application/json" id="contour-data">')[1].split('</script>')[0]);
  let count = 0, maxError = 0;
  payload.variants.forEach((variant, index) => {
    let vertices = 0;
    for (const line of variant.lines) {
      assert.equal(line.index, line.level % 100 === 0); assert.equal(line.twentyMetreSubset, line.level % 20 === 0);
      for (const point of line.coordinates) {
        vertices++;
        for (const scale of [0.1, 0.5, 8]) {
          const view = { x: 2625000, y: 1092000, scale };
          const back = model.screenToWorld(model.worldToScreen(point, view, 384, 600), view, 384, 600);
          maxError = Math.max(maxError, Math.hypot(back[0]-point[0], back[1]-point[1]));
        }
      }
    }
    assert.equal(vertices, [662196, 150389, 140562][index]); count += vertices;
  });
  assert.ok(maxError <= 1e-8);
  console.log(JSON.stringify({ vertices: count, maximumRoundtripMetres: maxError, currentRssBytes: process.memoryUsage().rss }));
});
