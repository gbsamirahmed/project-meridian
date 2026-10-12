import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { createHash } from 'node:crypto';

const code = readFileSync(new URL('./viewer.js', import.meta.url), 'utf8');
const sandbox = {}; vm.runInNewContext(code, sandbox);
const model = sandbox.MeridianContourMath;
test('metre display is north-up, uniformly scaled and reversible', () => {
  for (const [width,height] of [[384,600],[1280,700],[832,384]]) {
    for (const scale of [0.01,0.4,15]) {
      const view = {x:2625000,y:1092000,scale};
      for (const point of [[2624000,1091000],[2626000,1093000],[2624500.123456789,1092100.234567891]]) {
        const screen = model.worldToScreen(point,view,width,height);
        const back = model.screenToWorld(screen,view,width,height);
        assert.ok(Math.hypot(back[0]-point[0],back[1]-point[1])<=1e-8);
      }
      assert.ok(model.worldToScreen([view.x,view.y+10],view,width,height)[1]<height/2);
    }
  }
});
test('zoom anchors preserve alignment, limits and input camera', () => {
  const view = model.fit(384,600), before = JSON.stringify(view), anchor = [70,190];
  const fixed = model.screenToWorld(anchor,view,384,600);
  const changed = model.zoom(view,1.5,anchor,384,600);
  const back = model.screenToWorld(anchor,changed,384,600);
  assert.ok(Math.hypot(back[0]-fixed[0],back[1]-fixed[1])<=1e-8);
  assert.equal(JSON.stringify(view),before);
  assert.equal(model.zoom(view,1e9,anchor,384,600).scale,15);
});
test('20 m is a filter, never a derived or rounded elevation', () => {
  assert.equal(model.accepts({level:2510,twentyMetreSubset:false},10),true);
  assert.equal(model.accepts({level:2510,twentyMetreSubset:false},20),false);
  assert.equal(model.accepts({level:2500,twentyMetreSubset:true},20),true);
});
test('elevation picking follows nearest retained line segments', () => {
  assert.equal(model.segmentDistance([5,4],[0,0],[10,0]),4);
  assert.equal(model.segmentDistance([0,0],[0,0],[0,0]),0);
  assert.equal(model.segmentDistance([13,4],[0,0],[10,0]),5);
});
test('offline bundle declares no network dependencies and exact executable CSP hash', () => {
  const template=readFileSync(new URL('./viewer.html',import.meta.url),'utf8');
  assert.ok(template.includes("connect-src 'none'"));
  assert.ok(template.includes("default-src 'none'"));
  assert.equal(/\b(fetch|XMLHttpRequest|WebSocket)\b/.test(code),false);
  assert.equal(/<(script|link|img)[^>]+(src|href)=/i.test(template),false);
  if (process.env.MERIDIAN_CONTOUR_HTML) {
    const html=readFileSync(process.env.MERIDIAN_CONTOUR_HTML,'utf8');
    const executable=html.split('<script>')[1].split('</script>')[0];
    const hash=createHash('sha256').update(executable).digest('base64');
    assert.ok(html.includes(`script-src 'sha256-${hash}'`));
    assert.equal(executable,code);
  }
});
test('all genuine display coordinates round-trip without changing contour heights', {skip:!process.env.MERIDIAN_CONTOUR_HTML}, () => {
  const html=readFileSync(process.env.MERIDIAN_CONTOUR_HTML,'utf8');
  const payload=JSON.parse(html.split('<script type="application/json" id="contour-data">')[1].split('</script>')[0]);
  const expected=[662196,150389,140562];let maxError=0;
  payload.variants.forEach((variant,index) => {
    let count=0;
    for (const line of variant.lines) {
      assert.equal(line.index,line.level%100===0);assert.equal(line.twentyMetreSubset,line.level%20===0);
      for (const point of line.coordinates) {
        count++;
        for (const scale of [0.1,0.5,8]) {
          const view={x:2625000,y:1092000,scale};
          const back=model.screenToWorld(model.worldToScreen(point,view,384,600),view,384,600);
          maxError=Math.max(maxError,Math.hypot(back[0]-point[0],back[1]-point[1]));
        }
      }
    }
    assert.equal(count,expected[index]);
  });
  assert.ok(maxError<=1e-8);
  console.log(JSON.stringify({vertices:953147,maximumRoundtripMetres:maxError,currentRssBytes:process.memoryUsage().rss}));
});
