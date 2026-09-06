// Structural checks for the hybrid tile field. Frame time under headless
// Chromium is SwiftShader (software raster), so it is a floor, not a number
// to quote — the claims under test here are structural: one draw call for the
// whole corpus, a DOM budget that does not grow with it, flat VRAM.
import { chromium } from 'playwright';

// Usage:  node check.mjs <url> [screenshot.png]
//   cd render_assets && python3 -m http.server 8731
//   node data-mountain-field/check.mjs http://127.0.0.1:8731/data-mountain-field/
//
// Exits non-zero when any check fails, so it is usable as a gate. It asserts
// the DOM budget is BOUNDED rather than merely small: a regression that put one
// element per item back would still render, still screenshot correctly, and
// fail here.
/** Absolute ceiling on live DOM cards, whatever the corpus size. */
const DOM_CEILING = 64;

const url = process.argv[2];
if (!url) {
  console.error('usage: node check.mjs <url> [screenshot.png]');
  process.exit(2);
}
const browser = await chromium.launch({
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', (e) => errors.push(String(e)));

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForFunction(() => window.__field !== undefined, { timeout: 20000 });
await page.waitForTimeout(4000);   // let tiers settle and atlases stream

const stats = await page.evaluate(() => {
  const { field, hybrid, renderer, count } = window.__field;
  const css3d = document.getElementById('css3d');
  return {
    count,
    drawCalls: renderer.info.render.calls,
    triangles: renderer.info.render.triangles,
    instances: field.mesh.count,
    domCards: hybrid.live.size,
    domNodesInScene: css3d.querySelectorAll('.hybrid-card').length,
    poolSize: hybrid.pool.length,
    vramMB: +(field.bytes / 1048576).toFixed(1),
    farCols: field.atlases.far.cols,
    farCapacity: field.atlases.far.capacity,
    nearCapacity: field.atlases.near.capacity,
    farResident: Array.from(field.atlases.farSlot).filter((s) => s >= 0).length,
    nearResident: Array.from(field.atlases.nearSlot).filter((s) => s >= 0).length,
    suppressed: Array.from(field._suppressed).filter(Boolean).length,
  };
});

console.log(JSON.stringify(stats, null, 2));
console.log('');

const fails = [];
const ok = (cond, label, detail) => {
  (cond ? 0 : fails.push(label));
  console.log(`${cond ? ' ok ' : 'FAIL'}  ${label}${detail ? `  — ${detail}` : ''}`);
};

ok(errors.length === 0, 'no console/page errors', errors.slice(0, 3).join(' | '));
ok(stats.instances === stats.count, 'every item is an instance', `${stats.instances}/${stats.count}`);
ok(stats.drawCalls <= 6, 'whole corpus in a handful of draw calls', `${stats.drawCalls} calls`);
// Two bounds, and the absolute one is the load-bearing half. Checking only
// "within the configured pool" is vacuous against the exact regression this
// exists to catch — a consumer that sets poolSize to the corpus size has
// thrown the design away, and a relative bound still passes it.
ok(stats.domNodesInScene <= DOM_CEILING, 'DOM budget is a constant, not a function of corpus size', `${stats.domNodesInScene} ≤ ${DOM_CEILING} with ${stats.count} items`);
ok(stats.domNodesInScene <= stats.poolSize, 'DOM cards within the configured pool', `${stats.domNodesInScene} ≤ ${stats.poolSize}`);
ok(stats.domCards > 0, 'the DOM tier is actually populated', `${stats.domCards} live`);
ok(stats.nearResident <= stats.nearCapacity, 'near tier respects its pool', `${stats.nearResident} ≤ ${stats.nearCapacity}`);
ok(stats.nearResident > 0, 'near tier promoted something', `${stats.nearResident} resident`);
ok(stats.farResident > stats.nearResident, 'far tier carries the bulk', `${stats.farResident} far vs ${stats.nearResident} near`);
ok(stats.suppressed === stats.domCards, 'each DOM card suppresses exactly its quad', `${stats.suppressed} vs ${stats.domCards}`);
ok(stats.vramMB < 130, 'atlas VRAM within budget', `${stats.vramMB} MB`);

// Screenshot last and best-effort: SwiftShader needs a long time to compose a
// 2,500-instance frame, and a capture timeout must not discard the numbers.
try {
  await page.screenshot({ path: process.argv[3] || '/tmp/field.png', timeout: 120000 });
  console.log(`\nshot: ${process.argv[3]}`);
} catch (e) {
  console.log(`\nshot skipped: ${String(e).split('\n')[0]}`);
}
await browser.close();

console.log(fails.length ? `\n${fails.length} FAILED` : '\nall checks passed');
process.exit(fails.length ? 1 : 0);
