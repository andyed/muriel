// Browser checks are separate from pure model tests. Install Playwright and its
// Chromium in the test environment, not in the reference lab.
//   node tests/multiscale-browser.mjs
// PLAYWRIGHT_MODULE may name an existing module directory; BASE_URL may point
// to the lab index. Otherwise this script serves the checkout on loopback.
// SCREENSHOT_DIR opt-in captures support a separate human render inspection.
import assert from 'node:assert/strict';
import test from 'node:test';
import { createRequire } from 'node:module';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { records } from '../plugins/muriel/skills/compose/examples/linked-atlas/data.mjs';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const labPath = '/plugins/muriel/skills/compose/examples/linked-atlas/index.html';
const mime = { '.html': 'text/html', '.mjs': 'text/javascript', '.js': 'text/javascript', '.css': 'text/css', '.md': 'text/plain' };

async function serve() {
  const server = createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
      const path = resolve(root, `.${pathname}`);
      if (!path.startsWith(root + sep)) { response.writeHead(403).end(); return; }
      const body = await readFile(path);
      response.writeHead(200, { 'Content-Type': `${mime[extname(path)] || 'application/octet-stream'}; charset=utf-8` });
      response.end(body);
    } catch { response.writeHead(404).end('Not found'); }
  });
  await new Promise((accept, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', accept); });
  return { url: `http://127.0.0.1:${server.address().port}${labPath}`, close: () => new Promise(done => server.close(done)) };
}

const sorted = values => [...values].sort();
function expected(x, y = [0, 100], habitat = 'All') {
  return records.filter(r => r.x >= x[0] && r.x <= x[1] && r.detections >= y[0] && r.detections <= y[1] && (habitat === 'All' || r.habitat === habitat)).map(r => r.id).sort();
}
const snapshot = page => page.evaluate(() => window.linkedAtlas.snapshot());
async function selectionIs(page, ids) {
  const snap = await snapshot(page);
  assert.deepEqual(snap.state.selection === null ? null : sorted(snap.state.selection), ids === null ? null : sorted(ids));
  assert.deepEqual(sorted(snap.derived.selectedIds), sorted(ids ?? []));
  const countText = await page.locator('#selection-count').innerText();
  assert.match(countText, ids === null ? /inactive|no selection/i : new RegExp(`\\b${ids.length}\\b`));
  return snap;
}
async function exactSelection(page, x, y = [0, 100]) {
  for (const [id, value] of [['range-start', x[0]], ['range-end', x[1]], ['value-start', y[0]], ['value-end', y[1]]]) {
    await page.locator(`#${id}`).fill(String(value));
  }
  const submit = page.getByRole('button', { name: 'Apply selection', exact: true });
  await submit.focus();
  await page.keyboard.press('Enter');
  assert.equal(await submit.evaluate(el => el === document.activeElement), true, 'applying selection retains keyboard focus');
}

// Use the browser's actual SVG transform only to locate the input target. The
// expected IDs come from the independent data predicate above, not the reducer.
async function clientPoint(page, view, x, y = 50) {
  return page.evaluate(({ view, x, y }) => {
    const svg = document.getElementById(view);
    const snap = window.linkedAtlas.snapshot();
    const plot = snap.plots[view];
    const domain = view === 'overview' ? [0, 32] : snap.derived.viewport;
    const logical = svg.createSVGPoint();
    logical.x = plot.left + (x - domain[0]) / (domain[1] - domain[0]) * (plot.right - plot.left);
    logical.y = plot.bottom - y / 100 * (plot.bottom - plot.top);
    const client = logical.matrixTransform(svg.getScreenCTM());
    return { x: client.x, y: client.y };
  }, { view, x, y });
}
async function drag(page, view, x, y = [0, 100]) {
  await page.locator(`#${view}`).scrollIntoViewIfNeeded();
  const from = await clientPoint(page, view, x[0], y[0]);
  const to = await clientPoint(page, view, x[1], y[1]);
  await page.mouse.move(from.x, from.y);
  await page.mouse.down();
  await page.mouse.move(to.x, to.y, { steps: 8 });
  await page.mouse.up();
}

const contrastReceipts = [];
async function auditRenderedText(page, name) {
  // This audit is scoped to the lab's solid-color text. Capture the actual
  // background underneath each glyph by making only glyph fills transparent.
  // SVG backplates and stroke-under-fill halos remain painted. No browser
  // default background, ancestor color, or hardcoded SVG fill is assumed.
  const targets = await page.evaluate(() => {
    const targets = [];
    const numberColor = value => {
      const match = value.match(/^rgba?\(([^)]+)\)$/);
      if (!match) throw new Error(`Unsupported text paint: ${value}`);
      const values = match[1].split(/[\s,/]+/).filter(Boolean).map(Number);
      return [...values.slice(0, 3), values[3] ?? 1];
    };
    function add(element, rects, label) {
      if (element.closest('script,style,.sr-only,option') || !rects.length) return;
      const css = getComputedStyle(element);
      if (css.visibility !== 'visible' || css.display === 'none') return;
      let alpha = 1;
      let clip = { left: 0, top: 0, right: document.documentElement.scrollWidth, bottom: document.documentElement.scrollHeight };
      for (let ancestor = element; ancestor; ancestor = ancestor.parentElement) {
        const style = getComputedStyle(ancestor);
        alpha *= Number(style.opacity);
        if (style.backgroundImage !== 'none' && style.backgroundImage.includes('currentcolor')) throw new Error('Text audit does not support currentColor-dependent backgrounds');
        if (ancestor === document.body || ancestor === document.documentElement) continue;
        const box = ancestor.getBoundingClientRect();
        if (/hidden|auto|scroll|clip/.test(style.overflowX)) {
          clip.left = Math.max(clip.left, box.left + scrollX); clip.right = Math.min(clip.right, box.right + scrollX);
        }
        if (/hidden|auto|scroll|clip/.test(style.overflowY)) {
          clip.top = Math.max(clip.top, box.top + scrollY); clip.bottom = Math.min(clip.bottom, box.bottom + scrollY);
        }
      }
      if (alpha === 0) return;
      const svgText = element instanceof SVGElement;
      const foreground = numberColor(svgText ? css.fill : css.color);
      foreground[3] *= alpha * (svgText ? Number(css.fillOpacity) : 1);
      const boxes = rects.map(r => ({
        left: Math.max(clip.left, r.left + scrollX), right: Math.min(clip.right, r.right + scrollX),
        top: Math.max(clip.top, r.top + scrollY), bottom: Math.min(clip.bottom, r.bottom + scrollY),
      })).filter(r => r.right - r.left > 2 && r.bottom - r.top > 2);
      if (boxes.length) targets.push({ label, foreground, boxes, svg: svgText });
    }
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let node; (node = walk.nextNode());) {
      if (!node.data.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(node);
      add(node.parentElement, [...range.getClientRects()], node.data.trim().slice(0, 80));
    }
    for (const element of document.querySelectorAll('input[type=number],select')) {
      add(element, [element.getBoundingClientRect()], `${element.id}: ${element.value}`);
    }
    return targets;
  });
  const foreground = await page.screenshot({ fullPage: true, scale: 'css' });
  let background;
  const style = await page.addStyleTag({ content: '* { color:transparent!important; text-shadow:none!important; } svg text, svg tspan { fill:transparent!important; }' });
  try { background = await page.screenshot({ fullPage: true, scale: 'css' }); }
  finally { await style.evaluate(el => el.remove()); }
  const result = await page.evaluate(async ({ foreground, background, targets }) => {
    async function pixels(base64) {
      const image = new Image(); image.src = `data:image/png;base64,${base64}`;
      await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
      const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
      return { width: image.width, height: image.height, data: context.getImageData(0, 0, image.width, image.height).data };
    }
    const [before, beneath] = await Promise.all([pixels(foreground), pixels(background)]);
    if (before.width !== beneath.width || before.height !== beneath.height) throw new Error('Text suppression changed screenshot geometry');
    function luminance(rgb) {
      const linear = rgb.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
      return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722;
    }
    let minimum = Infinity, html = 0, svg = 0;
    const failures = [];
    for (const target of targets) {
      let samples = 0, lowest = Infinity;
      for (const box of target.boxes) {
        for (let y = Math.max(0, Math.floor(box.top)); y < Math.min(before.height, Math.ceil(box.bottom)); y++) {
          for (let x = Math.max(0, Math.floor(box.left)); x < Math.min(before.width, Math.ceil(box.right)); x++) {
            const at = (y * before.width + x) * 4;
            if (Math.max(...[0, 1, 2].map(c => Math.abs(before.data[at + c] - beneath.data[at + c]))) < 8) continue;
            const bg = [beneath.data[at], beneath.data[at + 1], beneath.data[at + 2]];
            const fg = bg.map((v, c) => target.foreground[c] * target.foreground[3] + v * (1 - target.foreground[3]));
            const a = luminance(fg), b = luminance(bg);
            lowest = Math.min(lowest, (Math.max(a, b) + .05) / (Math.min(a, b) + .05)); samples++;
          }
        }
      }
      if (!samples) failures.push({ text: target.label, kind: target.svg ? 'svg' : 'html', reason: 'No perceptible glyph fill in visible text bounds' });
      else {
        if (target.svg) svg++; else html++;
        minimum = Math.min(minimum, lowest);
        if (lowest < 8) failures.push({ text: target.label, kind: target.svg ? 'svg' : 'html', contrast: Number(lowest.toFixed(3)), paint: target.foreground });
      }
    }
    return { html, svg, minimum: Number(minimum.toFixed(3)), failures };
  }, { foreground: foreground.toString('base64'), background: background.toString('base64'), targets });
  assert.ok(result.html > 20 && result.svg > 5, `${name}: audit must see both HTML and SVG text`);
  assert.deepEqual(result.failures, [], `${name}: rendered text must maintain 8:1 against the painted background`);
  contrastReceipts.push({ state: name, html: result.html, svg: result.svg, minimum: result.minimum });
  return result;
}
async function capture(page, name) {
  await auditRenderedText(page, name);
  if (!process.env.SCREENSHOT_DIR) return;
  await mkdir(process.env.SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({ path: resolve(process.env.SCREENSHOT_DIR, `${name}.png`), fullPage: true });
}

await test('linked atlas browser interactions', async t => {
  const server = process.env.BASE_URL ? null : await serve();
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
    const url = process.env.BASE_URL || server.url;
    async function withPage(run, options = {}) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', ...options });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      try {
        await page.goto(url);
        await page.waitForFunction(() => Boolean(window.linkedAtlas?.snapshot));
        await run(page, context);
        assert.deepEqual(errors, [], 'no browser script errors');
      } finally { await context.close(); }
    }

    await t.test('keyboard exact range, linked counts, empty selection and clear', async () => withPage(async page => {
      await selectionIs(page, null);
      await exactSelection(page, [12, 22], [60, 100]);
      const ids = expected([12, 22], [60, 100]);
      await selectionIs(page, ids);
      const selectedRows = await page.locator('#records tr.selected').count();
      assert.equal(selectedRows, ids.length, 'table reflects the same selected identities');
      await page.locator('#filter').selectOption('Upland');
      const snap = await selectionIs(page, ids);
      const visibleIds = ids.filter(id => records.find(r => r.id === id).habitat === 'Upland');
      assert.deepEqual(sorted(snap.derived.selectedVisibleIds), visibleIds);
      assert.equal(snap.derived.selectedHidden, ids.length - visibleIds.length);
      assert.equal(await page.locator('#records tr.selected').count(), visibleIds.length);
      await exactSelection(page, [0, 32], [99, 100]);
      await selectionIs(page, []);
      await page.locator('#clear-selection').focus();
      await page.keyboard.press('Enter');
      await selectionIs(page, null);
    }));

    await t.test('pointer brush survives CSS scaling, nonzero page origin and page scroll', async () => withPage(async page => {
      await page.locator('#detail').evaluate(svg => { svg.style.transformOrigin = '37px 23px'; svg.style.transform = 'translate(19px, 11px) scale(.82)'; });
      await drag(page, 'detail', [8.03, 13.97], [20.5, 85.5]);
      await selectionIs(page, expected([8.03, 13.97], [20.5, 85.5]));
      await drag(page, 'detail', [13.97, 8.03], [85.5, 20.5]);
      await selectionIs(page, expected([8.03, 13.97], [20.5, 85.5]));
      assert.ok(await page.evaluate(() => scrollY) > 0, 'gesture occurred with a scrolled document');
      await capture(page, 'desktop-scaled-brush');
    }));

    await t.test('unfinished pointer gesture cancels and pointer capture completes outside plot', async () => withPage(async page => {
      await exactSelection(page, [12, 22], [60, 100]);
      const before = expected([12, 22], [60, 100]);
      await page.locator('#detail').scrollIntoViewIfNeeded();
      const start = await clientPoint(page, 'detail', 7, 25);
      const move = await clientPoint(page, 'detail', 17, 75);
      await page.mouse.move(start.x, start.y); await page.mouse.down();
      await page.mouse.move(move.x, move.y, { steps: 4 });
      assert.ok((await snapshot(page)).state.pending, 'gesture is pending before Escape');
      await page.keyboard.press('Escape'); await page.mouse.up();
      const snap = await selectionIs(page, before);
      assert.equal(snap.state.pending, null);
      assert.equal(await page.locator('#detail .brush').count(), 0, 'cancel removes unfinished rectangle');
      const from = await clientPoint(page, 'detail', 8.03, 20.5);
      const outside = await clientPoint(page, 'detail', 36, 85.5);
      await page.mouse.move(from.x, from.y); await page.mouse.down();
      await page.mouse.move(outside.x, outside.y, { steps: 5 }); await page.mouse.up();
      await selectionIs(page, expected([8.03, 32], [20.5, 85.5]));
      assert.equal((await snapshot(page)).state.pending, null, 'capture release cannot leave pending state');
    }));

    await t.test('zoom changes representation, preserves selection and keeps overview domain', async () => withPage(async page => {
      await exactSelection(page, [12, 22], [60, 100]);
      const ids = expected([12, 22], [60, 100]);
      const initial = await snapshot(page);
      assert.equal(initial.level, 'aggregate');
      const zoom = page.locator('#zoom-in');
      await zoom.focus();
      for (let i = 0; i < 4; i++) await page.keyboard.press('Enter');
      let snap = await selectionIs(page, ids);
      assert.notEqual(snap.level, 'aggregate', 'the rendered representation changes with projected space');
      assert.equal(await zoom.evaluate(el => el === document.activeElement), true);
      assert.ok(snap.state.viewport[1] - snap.state.viewport[0] < 32);
      await capture(page, 'desktop-zoomed-selection');
      await drag(page, 'overview', [1.03, 3.97], [10, 90]);
      await selectionIs(page, expected([1.03, 3.97]));
      await page.locator('#full-extent').click();
      snap = await selectionIs(page, expected([1.03, 3.97]));
      assert.deepEqual(snap.state.viewport, [0, 32]);
      await capture(page, 'desktop-overview');
    }));

    await t.test('pin remains distinct from hover, selection, filtering and zoom', async () => withPage(async page => {
      await page.getByRole('button', { name: 'Pin F001', exact: true }).click();
      let snap = await snapshot(page);
      assert.equal(snap.state.pin, 'F001');
      await selectionIs(page, null);
      await page.locator('#filter').selectOption('Upland');
      snap = await snapshot(page);
      assert.equal(snap.state.pin, 'F001');
      assert.equal(snap.derived.inspectorId, 'F001');
      assert.match(await page.locator('#inspector-body').innerText(), /F001/);
      await page.locator('#filter').selectOption('All');
      for (let i = 0; i < 4; i++) await page.locator('#zoom-in').click();
      const point = page.locator('#detail [data-record]').first();
      const previewId = await point.getAttribute('data-record');
      await point.hover();
      snap = await snapshot(page);
      assert.equal(snap.state.preview, previewId);
      assert.equal(snap.derived.inspectorId, previewId);
      await page.locator('#detail-title').hover();
      snap = await snapshot(page);
      assert.equal(snap.state.preview, null);
      assert.equal(snap.state.pin, 'F001');
      assert.equal(snap.derived.inspectorId, 'F001');
    }));

    await t.test('selection set operators are available through keyboard controls', async () => withPage(async page => {
      await exactSelection(page, [8, 16]);
      const a = expected([8, 16]), b = expected([12, 20]);
      await page.locator('#operation').selectOption('add');
      await exactSelection(page, [12, 20]);
      await selectionIs(page, sorted(new Set([...a, ...b])));
      await page.locator('#operation').selectOption('subtract');
      await exactSelection(page, [12, 20]);
      await selectionIs(page, a.filter(id => !b.includes(id)));
      await page.locator('#undo').focus(); await page.keyboard.press('Enter');
      await selectionIs(page, sorted(new Set([...a, ...b])));
      await page.locator('#operation').selectOption('intersect');
      await exactSelection(page, [12, 20]);
      await selectionIs(page, b);
    }));

    await t.test('a click and sub-threshold motion preserve the committed cohort', async () => withPage(async page => {
      await exactSelection(page, [12, 22], [60, 100]);
      const ids = expected([12, 22], [60, 100]);
      await page.locator('#detail').scrollIntoViewIfNeeded();
      const point = await clientPoint(page, 'detail', 7, 97);
      await page.mouse.click(point.x, point.y);
      await selectionIs(page, ids);
      await page.mouse.move(point.x, point.y); await page.mouse.down();
      await page.mouse.move(point.x + 1, point.y + 1); await page.mouse.up();
      await selectionIs(page, ids);
      assert.equal((await snapshot(page)).state.pending, null);
    }));

    await t.test('wheel anchoring, pan and focus recovery use the navigation path', async () => withPage(async page => {
      await exactSelection(page, [12, 22], [60, 100]);
      const ids = expected([12, 22], [60, 100]);
      await page.locator('input[name=mode][value=navigate]').check();
      await page.getByRole('button', { name: 'Pin F001', exact: true }).focus();
      await page.locator('#detail').scrollIntoViewIfNeeded();
      const anchorX = 16;
      const anchor = await clientPoint(page, 'detail', anchorX, 50);
      await page.mouse.move(anchor.x, anchor.y);
      await page.mouse.wheel(0, -240);
      await page.waitForFunction(() => window.linkedAtlas.snapshot().state.viewport[0] > 0);
      let snap = await selectionIs(page, ids);
      assert.ok(Math.abs((snap.state.viewport[0] + snap.state.viewport[1]) / 2 - anchorX) < .0001, 'the data beneath the wheel anchor stays fixed');
      assert.equal(await page.evaluate(() => document.activeElement?.tagName === 'BODY'), false, 'a disappearing focused row transfers focus to a useful control');
      assert.equal(await page.locator('#overview').getAttribute('data-domain'), '0,32');
      const before = [...snap.state.viewport];
      await drag(page, 'detail', [15, 13], [50, 50]);
      snap = await selectionIs(page, ids);
      assert.ok(Math.abs(snap.state.viewport[0] - (before[0] + 2)) < .01);
      assert.ok(Math.abs(snap.state.viewport[1] - (before[1] + 2)) < .01);
    }));

    await t.test('responsive aggregate labels fit while IDs and selected counts survive resize', async () => withPage(async page => {
      const ids = expected([12, 22], [60, 100]);
      await exactSelection(page, [12, 22], [60, 100]);
      async function inspectBins() {
        const bins = await page.locator('#detail [data-bin]').evaluateAll(elements => elements.map(bin => {
          const label = bin.querySelector('.aggregate-label'), cell = bin.querySelector('rect');
          const text = label?.getBBox(), box = cell.getBBox();
          return { ids: bin.dataset.members.split(','), selected: Number(bin.dataset.selected), label: label?.textContent,
            fits: Boolean(text && text.x >= box.x && text.x + text.width <= box.x + box.width && text.y >= box.y && text.y + text.height <= box.y + box.height) };
        }));
        assert.deepEqual(sorted(bins.flatMap(bin => bin.ids)), sorted(records.map(r => r.id)), 'the aggregate partition contains each observation exactly once');
        assert.equal(bins.reduce((sum, bin) => sum + bin.selected, 0), ids.length);
        assert.ok(bins.every(bin => bin.fits && /\d+\s*\/\s*\d+/.test(bin.label)), 'every aggregate has a complete selected/total label that fits inside its cell');
      }
      await inspectBins();
      await page.setViewportSize({ width: 390, height: 844 });
      await page.waitForFunction(() => window.linkedAtlas.snapshot().plots.detail.width < 400);
      await selectionIs(page, ids);
      await inspectBins();
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.match(await page.locator('#mobile-selection-count').innerText(), new RegExp(`\\b${ids.length}\\b`));
      await capture(page, 'phone-selected-aggregates');
    }));

    await t.test('contrast audit detects low-contrast SVG fills and changed HTML backgrounds', async () => withPage(async page => {
      const badFill = await page.addStyleTag({ content: 'svg text { fill:#5f6065!important; }' });
      await assert.rejects(() => auditRenderedText(page, 'planted-svg-fill'), error => error.actual?.some(failure => failure.kind === 'svg' && failure.contrast < 8));
      await badFill.evaluate(el => el.remove());
      await page.locator('.lead .muted').evaluate(el => { el.style.backgroundColor = '#ffffff'; });
      await assert.rejects(() => auditRenderedText(page, 'planted-html-background'), error => error.actual?.some(failure => failure.kind === 'html' && failure.contrast < 8));
    }));

    await t.test('phone layout, real browser touch dispatch and cancelled touch preserve intent', async () => withPage(async (page, context) => {
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'page fits phone width');
      const overflow = await page.locator('.table-scroll').evaluate(el => getComputedStyle(el).overflowX);
      assert.match(overflow, /auto|scroll/, 'wide table has its own scroll region');
      await page.locator('#detail').scrollIntoViewIfNeeded();
      const cdp = await context.newCDPSession(page);
      const from = await clientPoint(page, 'detail', 5.03, 20.5);
      const to = await clientPoint(page, 'detail', 15.97, 85.5);
      const touch = (type, points) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: points.map(p => ({ ...p, id: 1, radiusX: 1, radiusY: 1, force: 1 })) });
      await touch('touchStart', [from]);
      await touch('touchMove', [to]);
      await touch('touchEnd', []);
      const ids = expected([5.03, 15.97], [20.5, 85.5]);
      await selectionIs(page, ids);
      await touch('touchStart', [from]);
      await touch('touchMove', [await clientPoint(page, 'detail', 25, 95)]);
      assert.ok((await snapshot(page)).state.pending);
      await touch('touchCancel', []);
      await selectionIs(page, ids);
      assert.equal((await snapshot(page)).state.pending, null);
      await touch('touchStart', [from]);
      await touch('touchMove', [to]);
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [
        { ...to, id: 1, radiusX: 1, radiusY: 1, force: 1 },
        { x: to.x + 25, y: to.y + 20, id: 2, radiusX: 1, radiusY: 1, force: 1 },
      ] });
      assert.equal((await snapshot(page)).state.pending, null, 'a second touch cancels a one-pointer brush');
      await touch('touchEnd', []);
      await selectionIs(page, ids);
      await page.locator('#clear-selection').tap();
      await selectionIs(page, null);
      await capture(page, 'phone-selection-controls');
      await cdp.detach();
    }, { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }));
    for (const receipt of contrastReceipts) t.diagnostic(`Rendered text contrast ${JSON.stringify(receipt)}`);
  } finally {
    if (browser) await browser.close();
    if (server) await server.close();
  }
});
