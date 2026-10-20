// TileField's fragment shader, checked on the pixels it draws. Every other
// spatial test stubs three, so none of them can see what a tile looks like;
// these render a real field in headless Chromium (SwiftShader) and read the
// frame back.
//
// Run with: node --test tests/spatial-tile-pixels.test.mjs
// Needs playwright resolvable from this repository (muriel has no package.json:
// `npm i --no-save playwright` here, or a node_modules link to a checkout that
// has it) and network access for three from jsDelivr, as the demo pages use.
// MURIEL_SPATIAL_LIB points the page at another copy of render_assets/_lib,
// such as a consumer's vendored one.
//
// Two defects these caught, both invisible to the stubbed tests:
// - Output encoding. The atlases are sRGB-tagged, so sampling decodes them to
//   linear; written without re-encoding, every tile drew about 2.2 gamma dark
//   (167,170,176 reached the frame as 99,103,111) and dark covers went black.
//   With only this defect, 475 of 650 samples failed per tier.
// - Slot lookup. The slot index is an interpolated float, and at an exact
//   multiple of the atlas column count it can arrive just under the integer,
//   so part of the tile sampled the previous slot: here slot 5 drew slot 4's
//   green in one corner, and slot 15 drew slot 14's grey over half its face.
//
// And one in three itself, caught by the per-slot upload test: through r183,
// WebGLRenderer.copyTextureToTexture bound the destination to unit 0 without
// making unit 0 active when it was already bound there (mrdoob/three.js#33153).
// The far atlas sits on unit 0, and a render leaves the near atlas's unit
// active, so a far tile copied in on its own went into the near atlas, or into
// no texture once an earlier copy had unbound the active unit. On r169 both
// recoloured tiles kept their old colour, all 50 samples.
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

// 25 tiles make a 5 x 5 atlas, so slots 5, 10, 15 and 20 sit at exact
// multiples of the column count, and each differs sharply from the slot
// before it. Mid and dark tones are there because gamma error is largest on
// them. Tile 12 is a transparent canvas: a slot that holds no picture.
const COLOURS = [
  'd70009', 'a7aab0', '1a2a6c', 'ffffff', '00ff00',
  'ff00ff', '808080', '2a9d8f', '000000', 'ffff00',
  '0000ff', 'fa8072', null, '8b4513', 'cccccc',
  '333333', '00ffff', '800080', 'ff8000', '32cd32',
  'f3e5ab', '445566', '808000', 'c0392b', '6c5ce7',
];
const EMPTY = 0x1b2430;   // TileField's default emptyColor
const TRANSPARENT = COLOURS.indexOf(null);
const SLOTLESS = 3;       // forced to slot -1 after the first frame
const TOLERANCE = 3;      // per channel, out of 255: 8-bit sRGB decode and re-encode

// Far tiles redrawn after the atlas is on the GPU, few enough that flush()
// copies each slot in with copyTextureToTexture rather than re-uploading the
// canvas. Two, so the second copy runs after the first one's trailing unbind.
const RECOLOUR = { 6: 'ff2200', 13: '00aaff' };

const rgb = hex => [0, 2, 4].map(k => parseInt(hex.slice(k, k + 2), 16));
const EMPTY_RGB = rgb(EMPTY.toString(16).padStart(6, '0'));

const PAGE = `<!doctype html>
<meta charset="utf-8">
<style>html, body { margin: 0; background: #000; }</style>
<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js" } }
</script>
<script type="module">
import * as THREE from 'three';
import { TileField } from '/_lib/instanced.js';

const COLOURS = ${JSON.stringify(COLOURS)};
const SIZE = 640, EDGE = 100, PITCH = 130;

function tile(hex) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 64;
  if (hex) { const g = canvas.getContext('2d'); g.fillStyle = '#' + hex; g.fillRect(0, 0, 64, 64); }
  return canvas;
}

// One field, drawn once, read back at a 5 x 5 grid of points inside each
// tile's face (70% of its extent, clear of the slot edges, like a consumer's
// isolatedSamples probe). Tiles are turned about Y so depth varies across
// each quad, which is what perspective-correct interpolation of the slot
// varying is sensitive to.
window.renderField = (tier, recolour = null) => {
  const renderer = new THREE.WebGLRenderer({ antialias: false });
  renderer.setPixelRatio(1); renderer.setSize(SIZE, SIZE);
  document.body.replaceChildren(renderer.domElement);
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x000000);
  const camera = new THREE.PerspectiveCamera(40, 1, 1, 10000);
  camera.position.set(0, 0, 1000); camera.lookAt(0, 0, 0); camera.updateMatrixWorld();

  const count = COLOURS.length;
  const field = new TileField({
    scene, count, farPx: 64, nearPx: 64, nearSlots: count,
    nearDistance: tier === 'near' ? 1e6 : 0,
    resolve: () => null,
    resolveSource: i => tile(COLOURS[i]),
  });
  const turn = new THREE.Quaternion(), placed = [];
  for (let i = 0; i < count; i++) {
    const col = i % 5, row = Math.floor(i / 5);
    const x = (col - 2) * PITCH, y = (2 - row) * PITCH;
    turn.setFromAxisAngle(new THREE.Vector3(0, 1, 0), (col % 2 ? -1 : 1) * 0.45);
    field.place(i, x, y, 0, EDGE, EDGE, turn);
    placed.push({ centre: new THREE.Vector3(x, y, 0), turn: turn.clone() });
  }
  field.layout();
  field.update(camera);
  field.flush(performance.now() + 1e6);
  field.update(camera);

  const gl = renderer.getContext(), px = new Uint8Array(4), p = new THREE.Vector3();
  const sample = i => {
    const out = [];
    for (let r = 0; r < 5; r++) for (let c = 0; c < 5; c++) {
      p.set((c / 4 - 0.5) * 0.7 * EDGE, (r / 4 - 0.5) * 0.7 * EDGE, 0)
        .applyQuaternion(placed[i].turn).add(placed[i].centre).project(camera);
      gl.readPixels(Math.round((p.x + 1) / 2 * gl.drawingBufferWidth),
        Math.round((p.y + 1) / 2 * gl.drawingBufferHeight), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
      out.push([px[0], px[1], px[2]]);
    }
    return out;
  };

  renderer.render(scene, camera);
  const tiles = COLOURS.map((_, i) => sample(i));

  // The slotless path is the shader's other output. Nothing in a settled
  // field produces it on demand, so write the attribute directly.
  field.aSlot.array[${SLOTLESS}] = -1; field.aSlot.needsUpdate = true;
  renderer.render(scene, camera);
  const slotless = sample(${SLOTLESS});

  // The per-slot upload path, which needs a renderer attached and the atlas
  // already on the GPU. The unit state is read without disturbing three's
  // cache of it: save the active unit, look at unit 0, put the active unit back.
  let copied = null;
  if (recolour) {
    field.atlases.setRenderer(renderer);
    const far = field.atlases.far;
    const active = gl.getParameter(gl.ACTIVE_TEXTURE);
    gl.activeTexture(gl.TEXTURE0);
    const unit0 = gl.getParameter(gl.TEXTURE_BINDING_2D);
    gl.activeTexture(active);
    const units = { farOnUnit0: unit0 === renderer.properties.get(far.texture).__webglTexture, activeIsUnit0: active === gl.TEXTURE0 };
    for (const [i, hex] of Object.entries(recolour)) far.draw(field.atlases.farSlot[i], tile(hex));
    field.flush(performance.now() + 3e6);
    renderer.render(scene, camera);
    copied = { units, uploadedBytes: far.uploadedBytes, tileBytes: far.tilePx * far.tilePx * 4,
      tiles: Object.fromEntries(Object.keys(recolour).map(i => [i, sample(Number(i))])) };
  }

  const atlas = tier === 'near' ? field.atlases.near : field.atlases.far;
  const slots = Array.from(tier === 'near' ? field.atlases.nearSlot : field.atlases.farSlot);
  const tiers = Array.from(field.aTier.array);
  renderer.dispose();
  return { cols: atlas.cols, slots, tiers, tiles, slotless, copied };
};
window.ready = true;
</script>`;

let browser, server, origin;
before(async () => {
  if (skip) return;
  server = createServer(async (req, res) => {
    const { pathname } = new URL(req.url, 'http://fixture');
    if (pathname === '/') { res.setHeader('content-type', 'text/html'); res.end(PAGE); return; }
    const lib = /^\/_lib\/([\w-]+\.js)$/.exec(pathname);
    if (lib) {
      try { res.setHeader('content-type', 'text/javascript'); res.end(await readFile(path.join(LIB, lib[1]))); return; } catch { /* 404 below */ }
    }
    res.writeHead(404); res.end();
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  origin = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch();
});
after(async () => { await browser?.close(); await new Promise(r => (server ? server.close(r) : r())); });

async function render(tier, recolour = null) {
  const page = await browser.newPage({ viewport: { width: 640, height: 640 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  try {
    await page.goto(origin);
    await page.waitForFunction(() => window.ready === true, null, { timeout: 20000 });
    const result = await page.evaluate(([t, r]) => window.renderField(t, r), [tier, recolour]);
    // A shader that fails to compile draws nothing and throws nothing; three
    // reports it on the console, so a console error fails the test.
    assert.deepEqual(errors, [], 'no page or console errors');
    return result;
  } finally { await page.close(); }
}

const within = (pixel, want) => pixel.every((v, k) => Math.abs(v - want[k]) <= TOLERANCE);

function assertTiles({ cols, slots, tiers, tiles, slotless }, tier) {
  // Guard the fixture itself: if the atlas stopped being 5 wide, or slots
  // stopped following index order, the multiple-of-columns case would no
  // longer be exercised and the slot checks would pass vacuously.
  assert.equal(cols, 5, `${tier} atlas is 5 columns wide`);
  assert.deepEqual(slots, COLOURS.map((_, i) => i), `${tier} slot i holds tile i`);
  assert.ok(tiers.every(t => t === (tier === 'near' ? 1 : 0)), `every tile drew from the ${tier} atlas`);
  const wrong = [];
  for (const [i, hex] of COLOURS.entries()) {
    const want = hex ? rgb(hex) : EMPTY_RGB;
    tiles[i].forEach((pixel, k) => { if (!within(pixel, want)) wrong.push(`tile ${i} (slot ${slots[i]}) sample ${k}: ${pixel} vs ${want}`); });
  }
  slotless.forEach((pixel, k) => { if (!within(pixel, EMPTY_RGB)) wrong.push(`slotless tile ${SLOTLESS} sample ${k}: ${pixel} vs ${EMPTY_RGB}`); });
  assert.deepEqual(wrong, [], `${wrong.length} ${tier}-tier samples off their atlas colour`);
}

test('far-tier tiles draw their atlas colour as sRGB across the whole face, empty slots included', { skip }, async () => {
  assertTiles(await render('far'), 'far');
});

test('near-tier tiles draw their atlas colour as sRGB across the whole face, empty slots included', { skip }, async () => {
  assertTiles(await render('near'), 'near');
});

test('far tiles copied in one slot at a time reach the far atlas', { skip }, async () => {
  const { copied } = await render('far', RECOLOUR);
  // Guard the fixture: the copies must run with the far atlas on unit 0 and
  // another unit active, and flush() must take the per-slot path. If three
  // assigned units differently or the atlas re-uploaded the canvas, the loss
  // could not happen and this would pass vacuously.
  assert.deepEqual(copied.units, { farOnUnit0: true, activeIsUnit0: false }, 'far atlas on unit 0, another unit active');
  assert.equal(copied.uploadedBytes, Object.keys(RECOLOUR).length * copied.tileBytes, 'flush copied each slot instead of the canvas');
  const wrong = [];
  for (const [i, hex] of Object.entries(RECOLOUR)) {
    copied.tiles[i].forEach((pixel, k) => { if (!within(pixel, rgb(hex))) wrong.push(`tile ${i} sample ${k}: ${pixel} vs ${rgb(hex)}`); });
  }
  assert.deepEqual(wrong, [], `${wrong.length} samples kept the colour from before the copy`);
});

test('the transparent and slotless fixtures really are the two empty paths', { skip }, () => {
  // Tile 12 samples a slot whose pixels are transparent (the second output);
  // tile 3 is forced to slot -1 (the first). If either index changed, one of
  // the shader's two outputs would go untested.
  assert.equal(COLOURS[TRANSPARENT], null);
  assert.ok(TRANSPARENT !== SLOTLESS && COLOURS[SLOTLESS] !== null);
  assert.ok(COLOURS[0] !== null, 'tile 0 is drawn first and must be opaque, or the atlas blank-source canary trips');
});
