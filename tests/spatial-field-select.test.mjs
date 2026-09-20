// The near-tier budget: from an overview every instance can sit inside the
// near band, and the field must hand the fixed pool to the nearest ones only,
// asking the atlas for nothing else. Run with: node --test tests/spatial-field-select.test.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const dataModule = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
// Stub three: only the constructors the field touches at construction and in
// the tier pass; geometry, materials and the mesh are inert objects.
const three = dataModule(`
  export class Vector3 { constructor(x=0,y=0,z=0){this.x=x;this.y=y;this.z=z;} set(x,y,z){this.x=x;this.y=y;this.z=z;return this;} }
  export class Quaternion { constructor(){this.x=0;this.y=0;this.z=0;this.w=1;} identity(){return this;} copy(){return this;} set(){return this;} }
  export class Matrix4 { compose(){return this;} }
  export class Vector2 { constructor(x,y){this.x=x;this.y=y;} }
  export class Color { constructor(){} }
  export class PlaneGeometry { setAttribute(){} dispose(){} }
  export class InstancedBufferAttribute { constructor(array){this.array=array;} }
  export class ShaderMaterial { constructor(o){this.uniforms=o.uniforms;} dispose(){} }
  export class InstancedMesh { constructor(g,m,n){this.count=n;this.instanceMatrix={};} setMatrixAt(){} computeBoundingSphere(){} removeFromParent(){} }
  export class CanvasTexture { constructor(){} dispose(){} }
  export const SRGBColorSpace = 1, LinearFilter = 1;
`);
const atlasSource = (await readFile(new URL('../render_assets/_lib/atlas.js', import.meta.url), 'utf8')).replace("from 'three'", `from '${three}'`);
const motion = dataModule('export const MAX_ROWS = 8;');
const source = (await readFile(new URL('../render_assets/_lib/instanced.js', import.meta.url), 'utf8'))
  .replace("from 'three'", `from '${three}'`)
  .replace("from './atlas.js'", `from '${dataModule(atlasSource)}'`)
  .replace("from './motion.js'", `from '${motion}'`);
// atlas.js needs a document for its canvases; a minimal one suffices.
globalThis.document = { createElement: () => ({ getContext: () => ({ clearRect() {}, drawImage() {} }), width: 0, height: 0 }) };
const { TileField } = await import(dataModule(source));

function field(count, nearSlots) {
  const requested = [];
  const f = new TileField({ scene: { add() {} }, count, nearSlots, nearDistance: 1e9, resolve: () => null });
  const request = f.atlases.request.bind(f.atlases);
  f.atlases.request = (i, tier, now) => { requested.push([i, tier]); return request(i, tier, now); };
  return { f, requested };
}

test('the near pool goes to the nearest instances and nothing else is asked for', () => {
  const { f, requested } = field(100, 8);
  // The atlas is square, so a pool of 8 rounds up to 3×3 = 9 real slots; the
  // budget is the atlas's capacity, not the number asked for.
  const budget = f.atlases.near.capacity;
  assert.equal(budget, 9);
  // Instance i sits at x = i, so the nearest nine to a camera at the origin are 0..8.
  for (let i = 0; i < 100; i++) f.place(i, i, 0, 0, 1, 1);
  const resident = f.update({ position: { x: 0, y: 0, z: 0 } }, 1000);
  assert.equal(resident, budget);
  const near = requested.filter(([, t]) => t === 'near').map(([i]) => i).sort((a, b) => a - b);
  assert.deepEqual(near, [0, 1, 2, 3, 4, 5, 6, 7, 8], 'only the budgeted nearest ask for a near slot');
  const far = requested.filter(([, t]) => t === 'far').length;
  assert.equal(far, 100, 'everyone holds a far tile, the near residents included: far is the corpus, near is a cache');
  assert.ok([0, 1, 2].every(i => f.atlases.farSlot[i] >= 0 && f.atlases.nearSlot[i] >= 0));
});

test('a camera move re-spends the budget and releases what left the nearest set', () => {
  const { f } = field(50, 4);
  for (let i = 0; i < 50; i++) f.place(i, i * 10, 0, 0, 1, 1);
  f.update({ position: { x: 0, y: 0, z: 0 } }, 1000);
  assert.deepEqual([0, 1, 2, 3].map(i => f.atlases.nearSlot[i] >= 0), [true, true, true, true]);
  // Far enough along that nothing already resident is still nearest, and late
  // enough that the LRU is allowed to evict what the first frame touched.
  f.update({ position: { x: 490, y: 0, z: 0 } }, 2000);
  assert.deepEqual([46, 47, 48, 49].map(i => f.atlases.nearSlot[i] >= 0), [true, true, true, true], 'the new nearest four hold the pool');
  assert.deepEqual([0, 1, 2, 3].map(i => f.atlases.nearSlot[i] >= 0), [false, false, false, false], 'the old ones were released');
});

test('quickselect leaves the k smallest in front for sorted, reversed and duplicate keys', () => {
  const { f } = field(1, 1);
  for (const keys of [[5, 4, 3, 2, 1, 0], [0, 1, 2, 3, 4, 5], [3, 3, 3, 1, 1, 9, 0, 3], [7]]) {
    for (let k = 1; k <= keys.length; k++) {
      const idx = Int32Array.from(keys.keys());
      f._selectNearest(idx, keys.length, k, Float32Array.from(keys));
      const front = [...idx.subarray(0, k)].map(i => keys[i]).sort((a, b) => a - b);
      const want = [...keys].sort((a, b) => a - b).slice(0, k);
      assert.deepEqual(front, want, `keys ${keys} k=${k}`);
    }
  }
});

test('takeDirty reports a change once and a quiet field not at all', () => {
  const { f } = field(3, 2);
  assert.equal(f.takeDirty(), true, 'a fresh field has never been drawn');
  assert.equal(f.takeDirty(), false);
  f.place(0, 1, 2, 3, 4, 5); f.layout();
  assert.equal(f.takeDirty(), true);
  f.update({ position: { x: 0, y: 0, z: 0 } }, 1000);
  f.takeDirty();
  f.update({ position: { x: 0, y: 0, z: 0 } }, 1017);
  assert.equal(f.takeDirty(), false, 'a stationary camera over a settled field changes nothing');
});

test('an inactive instance keeps its placement and both slots, is the coldest in the pool, and is neither drawn nor picked', () => {
  // No pressure: a pool of nine over six instances. Hiding keeps everything.
  { const { f } = field(6, 9);
    for (let i = 0; i < 6; i++) f.place(i, i * 10, 0, 0, 8, 8);
    f.update({ position: { x: 0, y: 0, z: 0 } }, 1000);
    assert.ok(f.atlases.nearSlot[0] >= 0, 'near-resident');
    f.setActive(0, false); f.setActive(5, false);
    assert.equal(f.activeCount, 4);
    assert.ok(f.atlases.nearSlot[0] >= 0, 'hiding is not eviction: the near slot stays');
    assert.equal(f.aOpacity.array[0], 0, 'not drawn');
    assert.equal(f.centres[0], 0, 'placement untouched');
    f.update({ position: { x: 0, y: 0, z: 0 } }, 2000);
    assert.ok(f.atlases.nearSlot[0] >= 0, 'still resident while nothing shown needs the space');
    f.setActive(0, true);
    assert.equal(f.aOpacity.array[0], 1, 'drawn again without a reload');
    // A suppressed (DOM-twinned) instance stays hidden when reactivated, and a
    // hidden one stays hidden when its twin leaves.
    f.suppress(1, true); f.setActive(1, false); f.suppress(1, false);
    assert.equal(f.aOpacity.array[1], 0);
    f.setActive(1, true);
    assert.equal(f.aOpacity.array[1], 1);
  }
  // Pressure: a pool of four, five shown instances want it. The hidden one is
  // the coldest and goes first; the four shown nearest hold the pool.
  { const { f } = field(6, 4);
    for (let i = 0; i < 6; i++) f.place(i, i * 10, 0, 0, 8, 8);
    f.update({ position: { x: 0, y: 0, z: 0 } }, 1000);
    const far5 = f.atlases.farSlot[5];
    f.setActive(0, false);
    f.update({ position: { x: 0, y: 0, z: 0 } }, 2000);
    assert.equal(f.atlases.nearSlot[0], -1, 'the LRU reclaims the hidden instance first');
    assert.ok([1, 2, 3, 4].every(i => f.atlases.nearSlot[i] >= 0), 'the four shown nearest hold the pool');
    assert.equal(f.atlases.farSlot[5], far5, 'far residency is untouched throughout');
  }
});
