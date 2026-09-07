// Geometry checks need only the vector/quaternion value containers, not a
// WebGL renderer. Run with: node --test tests/spatial-piles.test.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const dataModule = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const values = dataModule(`
  export class Vector3 { constructor(x=0,y=0,z=0) { Object.assign(this,{x,y,z}); } }
  export class Quaternion { setFromAxisAngle() { return this; } identity() { return this; } }
`);
const source = await readFile(process.env.PILE_LAYOUT_SOURCE || new URL('../render_assets/_lib/piles.js', import.meta.url), 'utf8');
const { PileLayout } = await import(dataModule(source.replace("from 'three'", `from '${values}'`)));

function fixture(aspects, { tilted = false } = {}) {
  const positions = new Map();
  const record = (i, x, y, z, w, h) => positions.set(i, { x, y, z, w, h });
  const field = { place: record, moveTo: record, layout() {} };
  // Cards stand on their plane point: the surface lifts them by half their height.
  const surface = { planeToWorld: (x, y, h) => ({ x, y: tilted ? -y * .6 + h / 2 : y + h / 2, z: tilted ? y * .8 : 0 }) };
  const piles = new PileLayout({ field, surface, aspectOf: (i) => aspects[i] });
  piles.arrange([{ label: 'screenshots', indices: aspects.map((_, i) => i) }]);
  return { piles, positions };
}

test('a large collapsed pile has no coplanar tail, on upright or tilted surfaces', () => {
  for (const tilted of [false, true]) {
    const { piles, positions } = fixture(new Array(406).fill(16 / 9), { tilted });
    const face = new Set(piles.faceOf(0));
    const cards = [...positions.entries()].filter(([i]) => !face.has(i)).map(([, p]) => p);
    assert.equal(new Set([...positions.values()].map((card) => card.z)).size, positions.size, 'no two cards share a depth');
    for (let i = 1; i < cards.length; i++) {
      assert.ok(cards[i].z > cards[i - 1].z, 'later pile members remain nearer the camera');
    }
    assert.ok(Math.max(...cards.map((p) => p.x)) - Math.min(...cards.map((p) => p.x)) < 14, 'tail retains the compact fan footprint');
    const top = cards.at(-1);
    const pile = piles.piles[0];
    assert.equal(top.z, piles.maxVisibleInPile * piles.stackOffset, 'front stacked card depth is unchanged');
    assert.equal(top.h, pile.h);
    const before = [...positions.values()];
    piles.collapse(0, false);
    assert.deepEqual([...positions.values()], before, 'animated and immediate collapse share stable targets');
  }
});

test('a collapsed pile wears a contact sheet: sampled members in cells over the footprint, nearest the camera', () => {
  const aspects = new Array(134).fill(0).map((_, i) => (i % 3 === 0 ? 0.7 : 16 / 9));
  const { piles, positions } = fixture(aspects);
  const pile = piles.piles[0], face = piles.faceOf(0);
  assert.equal(face.length, 9, 'a large pile shows a 3×3 sheet');
  assert.deepEqual(face, [0, 14, 29, 44, 59, 74, 89, 104, 119], 'samples are spread evenly through the pile order');
  const cover = { y: pile.v + pile.h / 2 }; // the footprint's centre in world y (cards stand on v)
  const stackedZ = Math.max(...[...positions.entries()].filter(([i]) => !face.includes(i)).map(([, p]) => p.z));
  const cells = face.map((i) => positions.get(i));
  for (const c of cells) {
    assert.ok(c.z > stackedZ, 'face cards are nearest the camera');
    assert.ok(c.x - c.w / 2 >= pile.u - pile.w / 2 - 1e-6 && c.x + c.w / 2 <= pile.u + pile.w / 2 + 1e-6, 'inside the footprint horizontally');
    assert.ok(c.y - c.h / 2 >= cover.y - pile.h / 2 - 1e-6 && c.y + c.h / 2 <= cover.y + pile.h / 2 + 1e-6, 'inside the footprint vertically');
  }
  for (let a = 0; a < cells.length; a++) for (let b = a + 1; b < cells.length; b++) {
    const p = cells[a], q = cells[b];
    const apart = p.x + p.w / 2 <= q.x - q.w / 2 + 1e-6 || q.x + q.w / 2 <= p.x - p.w / 2 + 1e-6 || p.y + p.h / 2 <= q.y - q.h / 2 + 1e-6 || q.y + q.h / 2 <= p.y - p.h / 2 + 1e-6;
    assert.ok(apart, 'face cards never overlap');
  }
  assert.ok(Math.abs(positions.get(0).w / positions.get(0).h - 0.7) < 1e-6, 'a portrait member keeps its proportions in its cell');
  assert.ok(Math.abs(positions.get(14).w / positions.get(14).h - 16 / 9) < 1e-6);
  // Members matching the pile's average aspect fill their cells: a square sheet of 16:9 covers in a 16:9 footprint.
  const wide = fixture(new Array(40).fill(16 / 9)); const wf = wide.piles.faceOf(0); assert.equal(wf.length, 9);
  const cellArea = (wide.piles.piles[0].w / 3) * (wide.piles.piles[0].h / 3);
  for (const i of wf) { const c = wide.positions.get(i); assert.ok(c.w * c.h > cellArea * 0.85, 'a matching member fills most of its cell'); }
  const one = fixture([1.5]); assert.deepEqual(one.piles.faceOf(0), [0]);
  const empty = fixture([1.5]); empty.piles.piles[0].indices = []; assert.deepEqual(empty.piles.faceOf(0), [], 'a pile filtered to nothing has no face');
  empty.piles.collapse(0, true); // and collapsing it is harmless
  const five = fixture(new Array(5).fill(1)); assert.equal(five.piles.faceOf(0).length, 4, 'four to eight members show a 2×2 sheet');
  const bare = new (piles.constructor)({ field: { place() {}, moveTo() {}, layout() {} }, aspectOf: () => 1, faceCount: 0 });
  bare.arrange([{ label: 'x', indices: [0, 1, 2] }]); assert.deepEqual(bare.faceOf(0), [], 'faceCount 0 restores the single-cover look');
  // Spreading and collapsing again yields the same face.
  piles.spread(0); piles.collapse(0, true);
  assert.deepEqual(piles.faceOf(0), face);
});

test('mixed wide and portrait cards spread without overlap and remain centred', () => {
  const aspects = [4, .6, 16 / 9, .8, 3, 1];
  const { piles, positions } = fixture(aspects);
  const gap = 14;
  piles.spread(0, { columns: 3, gap });
  const cards = aspects.map((_, i) => positions.get(i)); // by member index, not insertion order
  for (let row = 0; row < 2; row++) {
    for (let col = 1; col < 3; col++) {
      const prev = cards[row * 3 + col - 1], next = cards[row * 3 + col];
      assert.ok(next.x - next.w / 2 - (prev.x + prev.w / 2) >= gap - 1e-8, 'adjacent image edges retain the requested gap');
    }
  }
  const left = Math.min(...cards.map((p) => p.x - p.w / 2));
  const right = Math.max(...cards.map((p) => p.x + p.w / 2));
  assert.ok(Math.abs((left + right) / 2 - piles.piles[0].u) < 1e-8, 'spread remains anchored at the pile');
});
