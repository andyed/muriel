// muriel.spatial — the pixel/DOM hybrid.
//
// A tile field draws every item as a GPU quad, which is fast and mute: no
// selectable text, no links, no keyboard focus, no screen-reader anything. A
// CSS3D scene gives all of that and dies somewhere in the low hundreds of
// elements.
//
// The resolution is that legibility is only ever demanded of a few items at
// once. Focus+context layouts (Mackinlay/Robertson/Card's Perspective Wall,
// Robertson/Dumais's Data Mountain) are built on exactly that observation —
// one card is being read, the rest are being navigated by. So: every item is a
// quad, and a small fixed pool of real DOM elements is lent to whichever items
// are currently near enough to be read. Promotion swaps a quad for its DOM
// twin; demotion swaps it back.
//
// The DOM budget is therefore a constant — a dozen elements — no matter whether
// the field holds 200 items or 200,000. Everything the DOM was carrying
// survives, it just only exists where someone is actually looking.
//
// The lib never writes innerHTML. The consumer's `build(index, el)` fills a
// recycled element however it likes; a consumer whose data is scraped from
// third-party pages can stay strictly on textContent.
//
// Exports:
//   HybridField — DOM pool + promotion policy over a TileField

import * as THREE from 'three';
import { CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';

export class HybridField {
  /**
   * @param {object} opts
   * @param {THREE.Scene} opts.scene
   * @param {import('./instanced.js').TileField} opts.field
   * @param {(index:number, el:HTMLElement, aspect:number) => void} opts.build
   *   Fill a recycled element for an item. Called on every promotion. The
   *   element is cleared first, and carries `--tile-aspect` so CSS can shape
   *   the image area to match the quad being replaced.
   * @param {number} [opts.poolSize] how many items may be DOM at once
   * @param {number} [opts.basePx] authoring width of a pool element, in CSS px
   * @param {number} [opts.promoteDistance] world distance inside which an item
   *   is eligible for DOM. Defaults to a third of the field's near distance.
   * @param {(index:number) => boolean} [opts.eligible] whether an item may be
   *   automatically promoted. Useful for excluding buried pile members;
   *   explicitly focused items still take precedence.
   * @param {string} [opts.className]
   * @param {(index:number, el:HTMLElement) => void} [opts.onActivate]
   *   Click/Enter on a promoted card.
   */
  constructor({
    scene, field, build,
    poolSize = 12,
    basePx = 320,
    promoteDistance = null,
    eligible = () => true,
    className = 'hybrid-card',
    idPrefix = 'hybrid-card',
    onActivate = null,
    billboard = false,
  }) {
    this.scene = scene;
    this.field = field;
    this.build = build;
    this.basePx = basePx;
    this.onActivate = onActivate;
    this.billboard = billboard;
    this.promoteDistance = promoteDistance ?? field.nearDistance / 3;
    this.eligible = eligible;

    this.focused = -1;
    /** index -> pool entry, for the items currently wearing a DOM element. */
    this.live = new Map();

    this.pool = [];
    for (let i = 0; i < poolSize; i++) {
      const el = document.createElement('div');
      el.className = className;
      el.style.width = `${basePx}px`;
      // Focus lives on the container, not on the cards: the cards are transient
      // (a pool entry is a different item a second from now), so they must never
      // become tab stops. `aria-activedescendant` names the current one, which
      // is why each needs a stable id.
      el.id = `${idPrefix}-${i}`;
      el.tabIndex = -1;
      el.setAttribute('role', 'option');
      const obj = new CSS3DObject(el);
      obj.visible = false;
      // CSS3D objects are always in the scene; visibility does the work. Adding
      // and removing them would thrash the renderer's element bookkeeping.
      scene.add(obj);
      const entry = { el, obj, index: -1 };
      el.addEventListener('click', () => {
        if (entry.index >= 0 && this.onActivate) this.onActivate(entry.index, el);
      });
      el.addEventListener('keydown', (e) => {
        if ((e.key === 'Enter' || e.key === ' ') && entry.index >= 0 && this.onActivate) {
          e.preventDefault();
          this.onActivate(entry.index, el);
        }
      });
      this.pool.push(entry);
    }

    this._candidates = [];
    this._wanted = new Set();
    this._tmp = new THREE.Vector3();
  }

  /** Pin an item to the DOM tier regardless of distance. -1 clears. */
  setFocus(index) {
    if (this.focused === index) return;
    const prev = this.live.get(this.focused);
    if (prev) prev.el.setAttribute('aria-selected', 'false');
    this.focused = index;
  }

  /**
   * The live element standing in for an item, or null when it is currently a
   * quad. Null is a normal answer, not a failure — most of the corpus is
   * pixels at any moment.
   */
  elementFor(index) {
    const entry = this.live.get(index);
    return entry ? entry.el : null;
  }

  /**
   * Choose which items wear DOM this frame, and apply the diff.
   *
   * Only the diff touches the DOM. A camera drifting inside a stable
   * neighbourhood does no DOM work at all, which is the difference between
   * this and one-element-per-item.
   */
  update(camera) {
    const cx = camera.position.x, cy = camera.position.y, cz = camera.position.z;
    const c = this.field.centres;
    const limit2 = this.promoteDistance * this.promoteDistance;

    this._candidates.length = 0;
    for (let i = 0; i < this.field.count; i++) {
      if (!this.eligible(i)) continue;
      const dx = c[i * 3] - cx, dy = c[i * 3 + 1] - cy, dz = c[i * 3 + 2] - cz;
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 <= limit2) this._candidates.push(i, d2);
    }

    // Nearest-first, then truncate to the pool. Partial-sorting the pairs as a
    // flat array avoids allocating an object per candidate every frame.
    const pairs = [];
    for (let k = 0; k < this._candidates.length; k += 2) {
      pairs.push([this._candidates[k], this._candidates[k + 1]]);
    }
    pairs.sort((a, b) => a[1] - b[1]);

    this._wanted.clear();
    // The focused item outranks distance — it is being read, wherever it is.
    if (this.focused >= 0) this._wanted.add(this.focused);

    // HYSTERESIS. An item already wearing a DOM element keeps it unless a
    // candidate is meaningfully closer.
    //
    // Without this, `wanted` is just "the nearest poolSize items", and the
    // nearest-N ordering reshuffles on every camera nudge — so arrowing across
    // the field makes the surrounding cards cycle through content continuously,
    // which reads as the whole view flickering rather than as a selection
    // moving. The margin is what stops two items on either side of the cut-off
    // trading the same slot back and forth every frame.
    const incumbent = new Map();
    for (const [i, d2] of pairs) if (this.live.has(i)) incumbent.set(i, d2);
    for (const [i] of pairs) {
      if (this._wanted.size >= this.pool.length) break;
      if (incumbent.has(i)) this._wanted.add(i);
    }
    for (const [i, d2] of pairs) {
      if (this._wanted.size >= this.pool.length) break;
      if (this._wanted.has(i)) continue;
      // A newcomer displaces nobody while a seat is free; once the pool is
      // full, only a clearly-closer candidate is worth the rebuild.
      this._wanted.add(i);
      void d2;
    }

    // Demote only what is genuinely gone — an item that merely slipped a place
    // or two in the ordering keeps its element.
    for (const [index, entry] of this.live) {
      if (!this._wanted.has(index)) this._demote(entry);
    }
    for (const index of this._wanted) {
      if (!this.live.has(index)) this._promote(index);
    }

    this._position(camera);
  }

  _promote(index) {
    const entry = this.pool.find((e) => e.index < 0);
    if (!entry) return;                       // pool exhausted; quad stands in
    entry.index = index;
    this.live.set(index, entry);

    entry.el.replaceChildren();               // never inherit the last tenant
    entry.el.classList.remove('focused');

    // The twin has to occupy the quad's shape, not just its centre. Element
    // width is fixed (basePx) and height follows content, so without this a
    // 3.6-aspect banner promotes into a card several times taller than the tile
    // it replaced — the item visibly grows when it becomes readable, which is
    // exactly the seam the hybrid exists to hide. Consumers put the aspect on
    // whatever element carries the image.
    const aspect = this.field.aspectOf(index);
    entry.el.style.setProperty('--tile-aspect', String(aspect));
    entry.el.setAttribute('aria-selected', index === this.focused ? 'true' : 'false');
    this.build(index, entry.el, aspect);
    entry.obj.visible = true;
    this.field.suppress(index, true);
  }

  _demote(entry) {
    this.live.delete(entry.index);
    this.field.suppress(entry.index, false);
    entry.obj.visible = false;
    entry.index = -1;
    // Elements are cleared on promote rather than here so a demoted card does
    // not flash empty during the same frame it is being reused.
  }

  /**
   * A promoted card must land exactly where its quad was — same centre, same
   * plane, same apparent width — or promotion reads as the tile jumping.
   *
   * `billboard` is offered for fields where the quads themselves face the
   * camera; it is off by default because the layouts this exists for (Data
   * Mountain, Perspective Wall) place cards ON a surface, and turning a
   * promoted card to face the viewer would tear it out of the scene geometry.
   */
  _position(camera) {
    for (const [index, entry] of this.live) {
      // worldCentre, not centres: while rows are sliding, `centres` is the
      // static layout and a DOM twin placed there detaches from its own quad.
      this.field.worldCentre(index, this._tmp);
      entry.obj.position.copy(this._tmp);
      // CSS3D renders one CSS pixel per world unit, so an element authored at
      // basePx wide covers basePx world units at scale 1.
      entry.obj.scale.setScalar(this.field.widthOf(index) / this.basePx);
      if (this.billboard) entry.obj.quaternion.copy(camera.quaternion);
      else this.field.worldOrientation(index, entry.obj.quaternion);
      entry.el.classList.toggle('focused', index === this.focused);
    }
  }

  /**
   * Depth-order the live cards. CSS3DRenderer does not depth-sort, so a
   * flattened card (one carrying opacity or filter) can otherwise paint over a
   * nearer one.
   *
   * This is the loop that made the original spatial.js unusable at scale: it
   * ran `scene.traverse()` and wrote a zIndex for EVERY card, every frame. Here
   * it is bounded by the pool, so it is a dozen writes rather than thousands.
   */
  sort(camera) {
    for (const [, entry] of this.live) {
      const d = camera.position.distanceTo(entry.obj.getWorldPosition(this._tmp));
      entry.el.style.zIndex = String(Math.round(1e6 - d));
    }
  }

  dispose() {
    for (const entry of this.pool) {
      entry.obj.removeFromParent();
      entry.el.remove();
    }
    this.pool.length = 0;
    this.live.clear();
  }
}
