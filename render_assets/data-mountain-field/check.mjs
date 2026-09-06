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
    nearDistinctSlots: new Set(Array.from(field.atlases.nearSlot).filter((s) => s >= 0)).size,
    farDistinctSlots: new Set(Array.from(field.atlases.farSlot).filter((s) => s >= 0)).size,
    farResidentRaw: Array.from(field.atlases.farSlot).filter((s) => s >= 0).length,
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
// Two items sharing one slot sample the same pixels and BOTH look plausible on
// screen, so nothing but a count catches it. Eviction leaked exactly one
// duplicate per evict until the free-list/detach split.
ok(stats.nearResident === stats.nearDistinctSlots, 'no two items share a near slot', `${stats.nearResident} holders / ${stats.nearDistinctSlots} slots`);
ok(stats.farResidentRaw === stats.farDistinctSlots, 'no two items share a far slot', `${stats.farResidentRaw} holders / ${stats.farDistinctSlots} slots`);
ok(stats.nearResident > 0, 'near tier promoted something', `${stats.nearResident} resident`);
ok(stats.farResident > stats.nearResident, 'far tier carries the bulk', `${stats.farResident} far vs ${stats.nearResident} near`);
ok(stats.suppressed === stats.domCards, 'each DOM card suppresses exactly its quad', `${stats.suppressed} vs ${stats.domCards}`);
ok(stats.vramMB < 130, 'atlas VRAM within budget', `${stats.vramMB} MB`);

// Screenshot last and best-effort: SwiftShader needs a long time to compose a
// 2,500-instance frame, and a capture timeout must not discard the numbers.
try {
  // ── keyboard ──────────────────────────────────────────────────────────────
// The point of the DOM tier is that the selection is a REAL element. These
// assert the whole chain: container is a listbox, focus lands, arrows move,
// and aria-activedescendant actually resolves to a live option — a nav that
// merely tracks an integer would pass a screenshot and fail every one of these.
const rowOf = (t) => { const m = /row (\d+)/.exec(t || ''); return m ? +m[1] : -1; };
const liveText = () => page.evaluate(() => document.querySelector('[aria-live]')?.textContent || '');
const press = async (k, n = 1) => {
  for (let i = 0; i < n; i++) { await page.keyboard.press(k); await page.waitForTimeout(160); }
};

await page.evaluate(() => document.getElementById('css3d').focus());
await page.waitForTimeout(400);
const kbShape = await page.evaluate(() => {
  const c = document.getElementById('css3d');
  const ad = c.getAttribute('aria-activedescendant');
  const el = ad ? document.getElementById(ad) : null;
  return {
    role: c.getAttribute('role'),
    focusable: c.getAttribute('tabindex') === '0',
    focusIsContainer: document.activeElement === c,
    selection: window.__field.nav.selection,
    adResolves: !!el,
    adRole: el ? el.getAttribute('role') : null,
    adSelected: el ? el.getAttribute('aria-selected') : null,
    liveRegions: document.querySelectorAll('[aria-live]').length,
  };
});
ok(kbShape.role === 'listbox', 'field is a listbox, not 2500 tab stops', kbShape.role);
ok(kbShape.focusable && kbShape.focusIsContainer, 'the field takes keyboard focus');
ok(kbShape.selection >= 0, 'focusing the field selects an item', `#${kbShape.selection}`);
ok(kbShape.adResolves && kbShape.adRole === 'option' && kbShape.adSelected === 'true',
   'aria-activedescendant resolves to a live, selected option',
   `${kbShape.adRole}/${kbShape.adSelected}`);
ok(kbShape.liveRegions === 1, 'exactly one live region announces movement', String(kbShape.liveRegions));

const kbStart = await liveText();
await press('ArrowRight');
const kbMoved = await liveText();
ok(kbMoved !== kbStart, 'an arrow key moves the selection and announces it');

// A directional sweep must stay on its own row. It did not, when the cone test
// divided instead of multiplying: "right" reached two rows nearer the camera.
await press('ArrowDown');
const beforeSweep = await liveText();
await press('End');
const afterEnd = await liveText();
await press('Home');
const afterHome = await liveText();
ok(rowOf(beforeSweep) >= 0 && rowOf(afterEnd) === rowOf(beforeSweep)
     && rowOf(afterHome) === rowOf(beforeSweep),
   'Home/End sweep stays on its own row',
   `row ${rowOf(beforeSweep)} → End ${rowOf(afterEnd)} → Home ${rowOf(afterHome)}`);

// ── view state ────────────────────────────────────────────────────────────
// Piles are an annotation over the corpus, not a property of any item in it,
// so they have to survive a round trip through a stable key. Index-keyed state
// would pass a naive round-trip and silently reassign every pile the moment the
// corpus is filtered or grows by one — so the assertions below check the KEYS,
// not just that the counts match.
const vs = await page.evaluate(() => {
  const { piles, groups } = window.__field;
  piles.arrange(groups, { width: 2400, depth: 2600 });
  const keyOf = (i) => `https://example.test/item/${i}`;
  const indexOf = (k) => { const m = /\/item\/(\d+)$/.exec(k); return m ? +m[1] : -1; };

  const np = piles.createPile('hand-made');
  piles.assign(5, np);
  const before = piles.piles.map((q) => [q.label, q.indices.length]);
  const state = piles.serialize(keyOf);
  const rt = piles.restore(state, indexOf);
  const after = piles.piles.map((q) => [q.label, q.indices.length]);

  const broken = JSON.parse(JSON.stringify(state));
  broken.piles[0].keys[0] = 'https://example.test/item/renamed-away';
  const rt2 = piles.restore(broken, indexOf);

  return {
    roundTripped: JSON.stringify(before) === JSON.stringify(after),
    restored: rt.restored,
    keysAreStable: state.piles.every((q) => q.keys.every((k) => typeof k === 'string' && !/^\d+$/.test(k))),
    handMade: piles.piles.some((q) => q.label === 'hand-made'),
    inExactlyOnePile: piles.piles.filter((q) => q.indices.includes(5)).length,
    orphansReported: rt2.orphaned.length,
  };
});

ok(vs.roundTripped, 'pile view state survives a serialize/restore round trip');
ok(vs.keysAreStable, 'view state keys are stable ids, not instance indices');
ok(vs.handMade, 'a hand-made pile can be created and persisted');
ok(vs.inExactlyOnePile === 1, 'exclusive assign leaves an item in one pile', `${vs.inExactlyOnePile} piles`);
ok(vs.orphansReported === 1, 'an unresolvable key is reported, not silently dropped', `${vs.orphansReported} orphan(s)`);

await page.screenshot({ path: process.argv[3] || '/tmp/field.png', timeout: 120000 });
  console.log(`\nshot: ${process.argv[3]}`);
} catch (e) {
  console.log(`\nshot skipped: ${String(e).split('\n')[0]}`);
}
await browser.close();

console.log(fails.length ? `\n${fails.length} FAILED` : '\nall checks passed');
process.exit(fails.length ? 1 : 0);
