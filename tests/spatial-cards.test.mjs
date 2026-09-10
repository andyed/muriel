// Test the drawable-card tile path separately from the browser API it wraps.
// Run with: node --test tests/spatial-cards.test.mjs
//
// These are policy tests: queueing, the per-pump budget, slot ownership and the
// failure contract. Whether Chrome actually paints an element is Phase 0's
// question, answered in render_assets/html-in-canvas-probe/RESULTS.md.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const dataModule = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const three = dataModule(`
  export class CanvasTexture { constructor() { this.needsUpdate = false; } dispose() {} }
  export const SRGBColorSpace = 'srgb';
  export const LinearFilter = 1006;
`);

// A canvas stub with just the 2D surface TileAtlas touches. drawElementImage is
// present so the real drawElement() path runs; the recorder lets a test assert
// on the clip, which is the part that keeps tiles out of their neighbours.
const calls = [];
globalThis.document = {
  createElement() {
    return {
      width: 0, height: 0,
      getContext() {
        return {
          clearRect(...a) { calls.push(['clearRect', ...a]); },
          save() { calls.push(['save']); },
          restore() { calls.push(['restore']); },
          translate(...a) { calls.push(['translate', ...a]); },
          scale(...a) { calls.push(['scale', ...a]); },
          beginPath() { calls.push(['beginPath']); },
          rect(...a) { calls.push(['rect', ...a]); },
          clip() { calls.push(['clip']); },
          drawImage() { calls.push(['drawImage']); },
          drawElementImage(...a) { calls.push(['drawElementImage', ...a]); },
          // Opaque by default: the fixture stands for a browser that PAINTS.
          // The blank-canary test swaps in a transparent one, because "the
          // draw reported success and the pixels are absent" is the specific
          // failure being asserted there, not the normal case.
          getImageData(x, y, w, h) {
            const data = new Uint8ClampedArray(w * h * 4);
            for (let i = 3; i < data.length; i += 4) data[i] = 255;
            return { data };
          },
        };
      },
    };
  },
};
globalThis.performance ??= { now: () => 0 };
// The image path is exercised only as the fallback these tests assert on, so
// this Image never loads — _inflight going up is the whole signal.
globalThis.Image = class { addEventListener() {} set src(_v) {} };

const source = await readFile(new URL('../render_assets/_lib/atlas.js', import.meta.url), 'utf8');
const { AtlasPair, TileAtlas, RETRY } = await import(dataModule(source.replace("from 'three'", `from '${three}'`)));

// What CardHost.capture() hands back: one reused card-sized bitmap.
const staging = () => ({ width: 340, height: 255 });

function pair(overrides = {}) {
  calls.length = 0;
  return new AtlasPair({
    count: 64,
    nearSlots: 32,
    resolve: () => 'http://example.invalid/never-loaded.png',
    resolveSource: () => staging(),
    ...overrides,
  });
}

test('a source job draws synchronously, never enters _inflight, and reports ready once', () => {
  const ready = [];
  const p = pair();
  p.onTileReady = (index, tier) => ready.push([index, tier]);

  const slot = p.request(3, 'near');

  assert.ok(slot >= 0, 'a slot was allocated');
  assert.equal(p._inflight, 0, 'a synchronous draw must not consume the image concurrency window');
  assert.deepEqual(ready, [[3, 'near']]);
  assert.equal(p.nearSlot[3], slot, 'the item still owns its slot');
  assert.equal(p._nearOwner[slot], 3);
  assert.ok(calls.some(([m]) => m === 'drawImage'), 'the tile was blitted from the source, not loaded');
  assert.equal(p.sourcePathBlank, false);
});

test('the per-pump budget caps synchronous draws and flush() drains the rest', () => {
  const ready = [];
  const p = pair({ sourceDrawsPerPump: 4 });
  p.onTileReady = (index) => ready.push(index);

  // Queue directly so one _pump() sees all ten at once, rather than the one
  // pump-per-request that request() would give.
  for (let i = 0; i < 10; i++) {
    const slot = p.near.alloc();
    p.nearSlot[i] = slot;
    p._nearOwner[slot] = i;
    p._nearQueue.push({ index: i, tier: 'near', slot });
  }
  p._pump();
  assert.equal(ready.length, 4, 'one pump draws exactly the budget');
  assert.equal(p._nearQueue.length, 6, 'the rest stay queued');

  p.flush(1e6);
  assert.equal(ready.length, 8, 'a frame flush draws the next batch');
  p.flush(2e6);
  assert.equal(ready.length, 10, 'and the queue drains across frames');
  assert.equal(p._nearQueue.length, 0);
});

test('a job whose slot was reassigned while queued is skipped, exactly like the image path', () => {
  const ready = [];
  const p = pair();
  p.onTileReady = (index) => ready.push(index);
  const slot = p.near.alloc();
  p._nearQueue.push({ index: 9, tier: 'near', slot });
  p.nearSlot[9] = slot + 1;          // someone else took over in the meantime
  p._pump();
  assert.deepEqual(ready, [], 'a stale job draws nothing');
});

test('a blank canary retires the source path instead of shipping an empty field', () => {
  // The first draw "succeeds" and paints nothing — exactly what an unpainted
  // host does, with no exception anywhere to notice it by.
  const p = pair();
  p.near.ctx.getImageData = (x, y, w, h) => ({ data: new Uint8ClampedArray(w * h * 4) });
  p.request(4, 'near');
  assert.equal(p.sourcePathBlank, true, 'the path is retired after one blank draw');
  assert.equal(p._inflight, 1, 'and the tile is re-requested down the image path');
  assert.equal(p._sourceFor({ index: 4, tier: 'near' }), null, 'later jobs skip the element path');
});

test('resolveSource returning null falls through to the image path per tier', () => {
  const p = pair({ resolveSource: (index, tier) => (tier === 'near' ? staging() : null) });
  p.request(11, 'far');
  assert.equal(p._inflight, 1, 'the far tier loaded an image');
  assert.ok(!calls.some(([m]) => m === 'drawImage'), 'nothing was blitted; the far tier is on images');
});

test('with no resolveSource the pair behaves exactly as before', () => {
  const p = pair({ resolveSource: null });
  p.request(1, 'near');
  assert.equal(p._inflight, 1, 'the image path is the only path');
  assert.equal(p._sourceFor({ index: 1, tier: 'near' }), null);
});


test('RETRY is a startup race, not a failure: the job is requeued and draws once ready', () => {
  const ready = [];
  let painted = false;
  const p = pair({ resolveSource: () => (painted ? staging() : RETRY) });
  p.onTileReady = (index) => ready.push(index);

  const slot = p.request(6, 'near');
  assert.deepEqual(ready, [], 'nothing drew on the first attempt');
  assert.ok(!p._failed.has('near:6'), 'a startup race is NOT a permanent failure');
  assert.equal(p.nearSlot[6], slot, 'the item keeps its slot while it waits');
  assert.equal(p._nearQueue.length, 1, 'the job is queued for the next frame');

  painted = true;                    // the compositor catches up
  p.flush(1e6);
  assert.deepEqual(ready, [6], 'and the tile draws once the source is ready');
});

test('a source that never becomes ready falls back to an image rather than a hole', () => {
  const p = pair({ resolveSource: () => RETRY, sourceRetries: 3 });
  p.request(8, 'near');
  for (let f = 0; f < 6; f++) p.flush(1e6 * (f + 1));
  assert.equal(p._inflight, 1, 'the tile went down the image path');
  assert.equal(p._nearQueue.length, 0, 'and stopped requeueing forever');
  assert.ok(!p._failed.has('near:8'), 'it is not a failure — it is a different source');
});

test('a source that cannot draw fails the tile exactly like a failed image load', () => {
  const p = pair();
  p.near.draw = () => false;
  const slot = p.request(7, 'near');
  assert.equal(p.nearSlot[7], -1, 'the slot is released');
  assert.equal(p._nearOwner[slot], -1, 'and its owner is reset');
  assert.ok(p._failed.has('near:7'), 'and the failure is recorded so it is not retried forever');
});
