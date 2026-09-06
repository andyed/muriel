// muriel.spatial — keyboard navigation for a tile field.
//
// A GPU quad cannot be focused, described, or tabbed to. That is the standing
// objection to rendering an interface as pixels, and the hybrid answers it: the
// selected item is always promoted to a real DOM element, so keyboard focus
// lands on something a screen reader can read and a focus ring can outline.
// Navigation drives promotion rather than the other way round.
//
// The accessibility model is a listbox with a roving active descendant, not
// 2,500 tab stops. One Tab lands you in the field; arrows move within it; Tab
// leaves. This is the same contract a virtualized list uses, and for the same
// reason — the elements are transient, so focus lives on the container and
// `aria-activedescendant` names the current one.
//
// Movement is computed in SCREEN space, not in the layout's own coordinates.
// Arrow keys have to follow what the viewer sees: the same corpus is a slope in
// one layout and a grid of piles in another, "right" means different things on
// each, and after an orbit it means something different again. Projecting to
// the camera and picking the nearest candidate in the pressed direction gets
// all of that for free, and needs no layout to describe its own topology.
//
// Exports:
//   FieldNavigator

import * as THREE from 'three';

/**
 * Tangent of the half-angle a candidate must fall inside. 0.55 is ~29°.
 *
 * This is a ratio of perpendicular offset to distance travelled, and it must
 * MULTIPLY: `perp <= along * CONE`. Dividing instead widens the cone to ~61°,
 * which on a receding slope is enough for "right" to find something two rows
 * nearer the camera, so a Home/End sweep curves off its own row.
 */
const CONE = 0.55;
/** Perpendicular offset is penalised this much harder than distance travelled. */
const PERP_WEIGHT = 2.4;

export class FieldNavigator {
  /**
   * @param {object} opts
   * @param {import('./instanced.js').TileField} opts.field
   * @param {import('./hybrid.js').HybridField} opts.hybrid
   * @param {THREE.Camera} opts.camera
   * @param {HTMLElement} opts.container element that holds keyboard focus
   * @param {(index:number) => string} [opts.labelOf] spoken/announced name
   * @param {(index:number, centre:THREE.Vector3) => void} [opts.onSelect]
   *   Move the camera. Left to the consumer because the camera rig belongs to
   *   the scene, not to navigation.
   * @param {(index:number) => void} [opts.onActivate] Enter / Space
   * @param {() => void} [opts.onEscape]
   * @param {(dir:number) => void} [opts.onGroupStep] Tab-level jump between
   *   groups or piles; +1 / -1.
   * @param {(letter:string) => (number|null)} [opts.onTypeAhead] jump to a
   *   group whose label starts with a typed prefix.
   */
  constructor({
    field, hybrid, camera, container,
    labelOf = null, onSelect = null, onActivate = null,
    onEscape = null, onGroupStep = null, onTypeAhead = null,
  }) {
    this.field = field;
    this.hybrid = hybrid;
    this.camera = camera;
    this.container = container;
    this.labelOf = labelOf;
    this.onSelect = onSelect;
    this.onActivate = onActivate;
    this.onEscape = onEscape;
    this.onGroupStep = onGroupStep;
    this.onTypeAhead = onTypeAhead;

    this.selection = -1;
    this._v = new THREE.Vector3();
    this._sel = new THREE.Vector3();
    this._typed = '';
    this._typedAt = 0;
    this._sweeping = false;

    container.setAttribute('role', 'listbox');
    container.setAttribute('aria-label',
      'Spatial field. Arrow keys move between items, Enter opens, Escape releases.');
    if (!container.hasAttribute('tabindex')) container.tabIndex = 0;

    // A polite live region, because the visual cue for "the selection moved"
    // is a camera move, which conveys nothing to a screen reader.
    this.live = document.createElement('div');
    this.live.setAttribute('aria-live', 'polite');
    this.live.setAttribute('aria-atomic', 'true');
    // Clipped rather than display:none — a hidden live region is not announced.
    this.live.style.cssText =
      'position:absolute;width:1px;height:1px;overflow:hidden;' +
      'clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap';
    container.appendChild(this.live);

    this._onKey = (e) => this.handleKey(e);
    container.addEventListener('keydown', this._onKey);
    container.addEventListener('focus', () => {
      if (this.selection < 0) this.selectFirstVisible();
    });
  }

  /**
   * Project an instance centre to normalized device coords.
   * Uses the DISPLACED centre — arrow keys have to move between the tiles the
   * viewer can see, not the ones the static layout says are there.
   */
  _project(index, out) {
    this.field.worldCentre(index, out);
    out.project(this.camera);
    return out;
  }

  /**
   * Nearest item in a screen-space direction.
   * @param {number} dx -1 | 0 | 1
   * @param {number} dy -1 | 0 | 1  (positive is up the screen)
   */
  step(dx, dy) {
    if (this.selection < 0) return this.selectFirstVisible();
    this._project(this.selection, this._sel);

    // Horizontal movement stays in its own row.
    //
    // Screen-space alone was enough while rows sat in tidy columns. Once rows
    // PAN at independent rates they no longer line up, so "left" can land on a
    // neighbouring row that happens to have drifted into the gap — and Home/End
    // then walk diagonally across the field. The row tag is the ground truth
    // about what a row is; screen space only decides the order within it.
    const rows = this.field.rows;
    const lockRow = dx !== 0 && dy === 0 && rows ? rows[this.selection] : null;

    let best = -1;
    let bestScore = Infinity;
    for (let i = 0; i < this.field.count; i++) {
      if (i === this.selection) continue;
      if (lockRow !== null && rows[i] !== lockRow) continue;
      this._project(i, this._v);
      // Behind the camera, or outside the frustum in depth.
      if (this._v.z < -1 || this._v.z > 1) continue;

      const ox = this._v.x - this._sel.x;
      const oy = this._v.y - this._sel.y;
      const along = ox * dx + oy * dy;
      if (along <= 1e-4) continue;                 // wrong side entirely
      const perp = Math.abs(ox * -dy + oy * dx);
      if (perp > Math.abs(along) * CONE + 0.02) continue;   // outside the cone

      const score = along + perp * PERP_WEIGHT;
      if (score < bestScore) { bestScore = score; best = i; }
    }
    if (best >= 0) this.select(best);
    return best;
  }

  /** The item nearest the centre of the screen. */
  selectFirstVisible() {
    let best = -1;
    let bestScore = Infinity;
    for (let i = 0; i < this.field.count; i++) {
      this._project(i, this._v);
      if (this._v.z < -1 || this._v.z > 1) continue;
      const score = this._v.x * this._v.x + this._v.y * this._v.y;
      if (score < bestScore) { bestScore = score; best = i; }
    }
    if (best >= 0) this.select(best);
    return best;
  }

  select(index) {
    if (index < 0 || index >= this.field.count) return;
    this.selection = index;
    // Pin it to the DOM tier: this is what makes the selection a real element
    // rather than a rectangle, and it is why the hybrid exists.
    this.hybrid.setFocus(index);
    this.hybrid.update(this.camera);

    this.field.worldCentre(index, this._sel);
    // Suppressed mid-run: moving the camera between the steps of a Home/End
    // sweep changes what "right" means in screen space partway through, and the
    // sweep curves off its own row. Fired once, at the end.
    if (this.onSelect && !this._sweeping) this.onSelect(index, this._sel);

    const el = this.hybrid.elementFor(index);
    if (el) {
      this.container.setAttribute('aria-activedescendant', el.id);
      el.setAttribute('aria-selected', 'true');
    } else {
      // Promotion can lose to a full pool. Say so rather than pointing
      // aria-activedescendant at an element that is not there.
      this.container.removeAttribute('aria-activedescendant');
    }
    this.announce(this.labelOf ? this.labelOf(index) : `Item ${index}`);
  }

  announce(text) {
    if (!text) return;
    // Re-announce an identical string by breaking the text node: a live region
    // whose content did not change is not re-read, and moving between two items
    // with the same label would then be silent.
    this.live.textContent = '';
    this.live.textContent = text;
  }

  handleKey(e) {
    const k = e.key;
    let handled = true;

    switch (k) {
      case 'ArrowLeft':  this.step(-1, 0); break;
      case 'ArrowRight': this.step(1, 0); break;
      case 'ArrowUp':    this.step(0, 1); break;
      case 'ArrowDown':  this.step(0, -1); break;

      // Run to the end of the current row / column rather than paging blindly:
      // repeated steps stop where the field stops, which is what Home/End mean.
      case 'Home': this._run(-1, 0); break;
      case 'End':  this._run(1, 0); break;
      case 'PageUp':   this._runN(0, 1, 6); break;
      case 'PageDown': this._runN(0, -1, 6); break;

      case 'Enter':
      case ' ':
        if (this.onActivate && this.selection >= 0) this.onActivate(this.selection);
        break;

      case 'Escape':
        if (this.onEscape) this.onEscape();
        break;

      case 'Tab':
        // Shift+Tab / Tab step between GROUPS while inside the field, and only
        // fall through to the browser's own focus order when there are none —
        // otherwise leaving a 2,500-item field means 2,500 tab presses.
        if (this.onGroupStep) this.onGroupStep(e.shiftKey ? -1 : 1);
        else handled = false;
        break;

      default:
        if (k.length === 1 && /\S/.test(k) && this.onTypeAhead) {
          const now = performance.now();
          if (now - this._typedAt > 900) this._typed = '';
          this._typedAt = now;
          this._typed += k.toLowerCase();
          const hit = this.onTypeAhead(this._typed);
          if (hit === null || hit === undefined) handled = false;
        } else {
          handled = false;
        }
    }

    if (handled) { e.preventDefault(); e.stopPropagation(); }
  }

  /** Step in a direction until it stops moving. */
  _run(dx, dy) { this._sweep(dx, dy, 500); }

  _runN(dx, dy, n) { this._sweep(dx, dy, n); }

  /**
   * Repeated steps against a FROZEN camera, so the direction means the same
   * thing for the whole sweep.
   */
  _sweep(dx, dy, limit) {
    this._sweeping = true;
    try {
      for (let i = 0; i < limit; i++) if (this.step(dx, dy) < 0) break;
    } finally {
      this._sweeping = false;
    }
    if (this.onSelect && this.selection >= 0) {
      this.field.worldCentre(this.selection, this._sel);
      this.onSelect(this.selection, this._sel);
    }
  }

  dispose() {
    this.container.removeEventListener('keydown', this._onKey);
    this.live.remove();
  }
}
