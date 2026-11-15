// An image that would taint the atlas canvas must not reach it.
//
// A canvas that has had a non-origin-clean image drawn into it is tainted for
// good: every later readback and every WebGL upload from it throws
// SecurityError. For an atlas that is the whole field, not one tile, and the
// throw lands in the consumer's frame loop.
//
// The case that reaches a same-origin wall is an SVG holding a
// `<foreignObject>` (Mermaid and draw.io exports do). Chrome and Safari treat
// such an image as not origin-clean wherever it was loaded from, with or
// without `crossOrigin`, so the loader's CORS request does not help.
//
// The loader checks each image element on a throwaway canvas first, with a
// draw aimed off that canvas so nothing is decoded for it. If an engine stops
// marking a canvas for a draw that lands nowhere, the atlases below come back
// unreadable and these tests fail, which is the point of reading them back.
//
// Run with: node --test tests/spatial-atlas-taint.test.mjs
// Needs playwright resolvable from this repository and network access for
// three from jsDelivr, like tests/spatial-tile-pixels.test.mjs.
// MURIEL_SPATIAL_LIB points the page at another copy of render_assets/_lib.
// MURIEL_TEST_CHROME names a Chrome binary to run in instead of Playwright's.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { test, before, after } from 'node:test';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const LIB = path.resolve(process.env.MURIEL_SPATIAL_LIB || path.join(HERE, '../render_assets/_lib'));

let chromium = null;
try { ({ chromium } = await import('playwright')); } catch { /* reported as the skip reason below */ }
const skip = chromium ? false : 'playwright is not resolvable from this repository (see the header comment)';

const CLEAN = fill => `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="100%" height="100%" fill="${fill}"/></svg>`;
const TAINTING = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="100%" height="100%" fill="#2a9d8f"/><foreignObject x="10" y="10" width="200" height="60"><div xmlns="http://www.w3.org/1999/xhtml">label</div></foreignObject></svg>`;
const FILLS = ['#d70009', '#1a2a6c', null, '#f3e5ab', '#6c5ce7'];   // null: the tainting one
const BAD = FILLS.indexOf(null);

const PAGE = `<!doctype html>
<meta charset="utf-8">
<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js" } }
</script>
<script type="module">
import { AtlasPair, TileAtlas, taintsCanvas } from '/_lib/atlas.js';

const readable = (canvas) => {
  try { canvas.getContext('2d').getImageData(0, 0, 1, 1); return true; } catch (e) { return e.name; }
};
const load = (url) => new Promise((resolve, reject) => {
  const img = new Image(); img.crossOrigin = 'anonymous';
  img.onload = () => resolve(img); img.onerror = () => reject(new Error('load failed: ' + url));
  img.src = url;
});

// Does this browser treat the fixture as tainting at all? Without this the
// tests below would pass on an engine that draws it clean.
window.fixtureTaints = async () => {
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 8;
  canvas.getContext('2d').drawImage(await load('/img/bad.svg'), 0, 0, 8, 8);
  return readable(canvas) !== true;
};

// The image path: every tile requested in both tiers, one of them tainting.
window.loadAll = async (count) => {
  const ready = [];
  const pair = new AtlasPair({
    count, farPx: 64, nearPx: 128, nearSlots: count,
    resolve: (i) => '/img/' + i + '.svg',
  });
  pair.onTileReady = (i, tier) => ready.push(tier + ':' + i);
  for (let i = 0; i < count; i++) { pair.request(i, 'far'); pair.request(i, 'near'); }
  const until = performance.now() + 8000;
  while ((pair._inflight || pair._nearQueue.length || pair._farQueue.length) && performance.now() < until) {
    await new Promise(r => setTimeout(r, 30));
  }
  const coverage = (atlas, slots) => Array.from(slots, s => (s < 0 ? null : atlas.slotCoverage(s)));
  return {
    settled: !pair._inflight,
    near: readable(pair.near.canvas), far: readable(pair.far.canvas),
    nearSlots: Array.from(pair.nearSlot), farSlots: Array.from(pair.farSlot),
    nearCoverage: coverage(pair.near, pair.nearSlot), farCoverage: coverage(pair.far, pair.farSlot),
    failed: [...pair._failed].sort(), ready: ready.sort(),
  };
};

// The source path: a consumer hands draw() an image element directly.
window.drawDirect = async () => {
  const atlas = new TileAtlas({ tilePx: 64, capacity: 4 });
  const bad = await load('/img/bad.svg'), good = await load('/img/0.svg');
  const out = {};
  out.asked = [taintsCanvas(bad), taintsCanvas(good), taintsCanvas(document.createElement('canvas'))];
  out.bad = atlas.draw(0, bad);
  out.afterBad = readable(atlas.canvas);
  out.badAgain = atlas.draw(0, bad);        // the answer is remembered, not re-derived wrongly
  out.good = atlas.draw(1, good);           // and one bad image does not poison the check
  out.goodAgain = atlas.draw(2, good);
  out.afterGood = readable(atlas.canvas);
  out.coverage = [0, 1, 2].map(s => atlas.slotCoverage(s));
  // One element given another picture, as a card's <img> is when its cover
  // changes: the earlier answer belongs to the earlier URL.
  const swap = (img, url) => new Promise((resolve) => { img.onload = resolve; img.src = url; });
  await swap(bad, '/img/1.svg');
  out.badNowClean = atlas.draw(0, bad);
  await swap(good, '/img/bad.svg');
  out.goodNowBad = atlas.draw(1, good);
  out.afterSwap = readable(atlas.canvas);
  // A canvas source is the drawable-card path, and takes no check.
  const tile = document.createElement('canvas'); tile.width = tile.height = 64;
  const g = tile.getContext('2d'); g.fillStyle = '#808000'; g.fillRect(0, 0, 64, 64);
  out.canvas = atlas.draw(3, tile);
  out.canvasCoverage = atlas.slotCoverage(3);
  return out;
};
window.ready = true;
</script>`;

let browser, server, origin;
before(async () => {
  if (skip) return;
  server = createServer(async (req, res) => {
    const { pathname } = new URL(req.url, 'http://fixture');
    if (pathname === '/') { res.setHeader('content-type', 'text/html'); res.end(PAGE); return; }
    const img = /^\/img\/(\d+|bad)\.svg$/.exec(pathname);
    if (img) {
      const fill = img[1] === 'bad' ? null : FILLS[Number(img[1])];
      res.setHeader('content-type', 'image/svg+xml');
      res.end(fill ? CLEAN(fill) : TAINTING);
      return;
    }
    const lib = /^\/_lib\/([\w-]+\.js)$/.exec(pathname);
    if (lib) {
      try { res.setHeader('content-type', 'text/javascript'); res.end(await readFile(path.join(LIB, lib[1]))); return; } catch { /* 404 below */ }
    }
    res.writeHead(404); res.end();
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  origin = `http://127.0.0.1:${server.address().port}`;
  const executablePath = process.env.MURIEL_TEST_CHROME || undefined;
  browser = await chromium.launch(executablePath ? { executablePath } : {});
});
after(async () => { await browser?.close(); await new Promise(r => (server ? server.close(r) : r())); });

async function run(fn, arg) {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  try {
    await page.goto(origin);
    await page.waitForFunction(() => window.ready === true, null, { timeout: 20000 });
    assert.equal(await page.evaluate(() => window.fixtureTaints()), true,
      'the fixture SVG taints a canvas in this browser, so the checks below mean something');
    const result = await page.evaluate(([name, a]) => window[name](a), [fn, arg]);
    assert.deepEqual(errors, [], 'no page errors');
    return result;
  } finally { await page.close(); }
}

test('a tainting image fails its own tile and leaves both atlases readable', { skip }, async () => {
  const r = await run('loadAll', FILLS.length);
  assert.equal(r.settled, true, 'every load finished');
  assert.equal(r.near, true, 'the near atlas is still readable');
  assert.equal(r.far, true, 'the far atlas is still readable');
  assert.deepEqual(r.failed, [`far:${BAD}`, `near:${BAD}`], 'only the tainting item failed, in both tiers');
  const others = FILLS.map((_, i) => i).filter(i => i !== BAD);
  assert.deepEqual(r.ready, [...others.map(i => `far:${i}`), ...others.map(i => `near:${i}`)].sort(), 'every other tile was announced');
  assert.equal(r.nearSlots[BAD], -1, 'the tainting item holds no near slot');
  assert.equal(r.farSlots[BAD], -1, 'the tainting item holds no far slot');
  for (const i of others) {
    assert.ok(r.nearCoverage[i] > 0.5, `near tile ${i} has its picture (${r.nearCoverage[i]})`);
    assert.ok(r.farCoverage[i] > 0.5, `far tile ${i} has its picture (${r.farCoverage[i]})`);
  }
});

test('draw() refuses a tainting image element and goes on accepting clean ones', { skip }, async () => {
  const r = await run('drawDirect');
  assert.deepEqual(r.asked, [true, false, false], 'taintsCanvas answers for an image element, and passes a canvas');
  assert.equal(r.bad, false, 'the tainting image is refused');
  assert.equal(r.afterBad, true, 'the atlas is readable after the refusal');
  assert.equal(r.badAgain, false, 'and refused again');
  assert.equal(r.good, true, 'a clean image draws after a tainting one was refused');
  assert.equal(r.goodAgain, true, 'and draws again');
  assert.equal(r.afterGood, true, 'the atlas is still readable');
  assert.equal(r.coverage[0], 0, 'the refused slot holds nothing');
  assert.ok(r.coverage[1] > 0.5 && r.coverage[2] > 0.5, `the clean slots hold their picture (${r.coverage})`);
  assert.equal(r.badNowClean, true, 'an element that now holds a clean picture draws');
  assert.equal(r.goodNowBad, false, 'an element that now holds the tainting picture is refused');
  assert.equal(r.afterSwap, true, 'the atlas is readable after both');
  assert.equal(r.canvas, true, 'a canvas source still draws');
  assert.ok(r.canvasCoverage > 0.9, `and fills its slot (${r.canvasCoverage})`);
});
