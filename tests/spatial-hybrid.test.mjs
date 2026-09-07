// Test promotion policy separately from the DOM/WebGL renderers.
// Run with: node --test tests/spatial-hybrid.test.mjs
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const dataModule = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;
const three = dataModule('export class Vector3 {}');
const css = dataModule('export class CSS3DObject {}');
const source = await readFile(process.env.HYBRID_FIELD_SOURCE || new URL('../render_assets/_lib/hybrid.js', import.meta.url), 'utf8');
const { HybridField } = await import(dataModule(source
  .replace("from 'three'", `from '${three}'`)
  .replace("from 'three/addons/renderers/CSS3DRenderer.js'", `from '${css}'`)));

const camera = { position: { x: 0, y: 0, z: 0 } };
function fixture(options = {}) {
  // Items 0 and 1 are near; item 2 is well beyond promotion distance.
  const field = { count: 3, nearDistance: 100, centres: [1, 0, 0, 2, 0, 0, 1000, 0, 0] };
  const hybrid = new HybridField({ scene: {}, field, build() {}, poolSize: 0, ...options });
  // Keep the real candidate, incumbent, focus and diff policy; replace only
  // the rendering side effects with a small pool and a promotion ledger.
  hybrid.pool = [{}, {}];
  hybrid._promote = (index) => hybrid.live.set(index, { index, el: { setAttribute() {} } });
  hybrid._demote = ({ index }) => hybrid.live.delete(index);
  hybrid._position = () => {};
  return hybrid;
}

test('default eligibility preserves automatic near-card promotion', () => {
  const hybrid = fixture();
  hybrid.update(camera);
  assert.deepEqual([...hybrid.live.keys()], [0, 1]);
});

test('eligibility excludes buried cards and demotes incumbents that become buried', () => {
  const visible = new Set([1]);
  const hybrid = fixture({ eligible: (i) => visible.has(i) });
  hybrid.update(camera);
  assert.deepEqual([...hybrid.live.keys()], [1], 'the nearer buried item cannot become a DOM overlay');
  visible.delete(1);
  visible.add(0);
  hybrid.update(camera);
  assert.deepEqual([...hybrid.live.keys()], [0], 'an incumbent loses its DOM element when no longer eligible');
});

test('explicit focus overrides both eligibility and promotion distance', () => {
  const hybrid = fixture({ eligible: () => false });
  hybrid.setFocus(2);
  hybrid.update(camera);
  assert.deepEqual([...hybrid.live.keys()], [2]);
  hybrid.setFocus(-1);
  hybrid.update(camera);
  assert.equal(hybrid.live.size, 0, 'clearing focus reapplies the automatic eligibility policy');
});
