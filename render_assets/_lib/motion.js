// muriel.spatial — continuous row motion for a tile field.
//
// Sliding rows and sweeping tile angles are not decoration. A static field of
// 2,500 rectangles reads as texture; the same field with rows drifting at
// different rates reads as depth, because relative motion is the strongest
// depth cue the visual system has after occlusion — nearer rows sweep further
// per unit time, and you get parallax for free from a layout that already
// varies scale with distance.
//
// Two rules the implementation is built around:
//
// 1. OSCILLATE, DON'T MARQUEE. "Slide right and left" is a bounded sweep, and
//    that is lucky: a wrapping marquee has to move a quad's CENTRE across the
//    seam atomically, or the vertices on either side of it wrap on different
//    frames and the quad tears across the screen. A bounded sweep has no seam.
//
// 2. ONE SOURCE OF TRUTH. The displacement is computed here, in JS, once per
//    frame, into a small per-ROW array — then handed to the shader as a
//    uniform. The obvious alternative, computing the wave in the vertex shader
//    from a time uniform, means the CPU does not know where anything actually
//    is: picking, DOM promotion and keyboard navigation would all address the
//    static layout while the viewer sees the moving one. Every click would miss
//    by however far the row had drifted. A per-row array is ~64 floats, so
//    there is nothing to gain by duplicating the maths into GLSL and quite a
//    lot to lose.
//
// Exports:
//   RowMotion — per-row slide + angle sweep, shared by shader and CPU

/** Uniform array size. Rows beyond this reuse the last slot rather than break. */
export const MAX_ROWS = 64;

export class RowMotion {
  /**
   * @param {object} [opts]
   * @param {number} [opts.slide]      lateral amplitude, world units
   * @param {number} [opts.slideRate]  radians/second of the sweep
   * @param {number} [opts.slidePhase] phase shift per row — what turns a
   *   uniform slide into a travelling wave. At 0 the whole field moves as one
   *   slab, which reads as a camera pan rather than as rows.
   * @param {number} [opts.sweep]      angle amplitude, radians
   * @param {number} [opts.sweepRate]
   * @param {number} [opts.sweepPhase]
   * @param {boolean} [opts.alternate] flip direction on odd rows
   */
  constructor({
    slide = 26, slideRate = 0.22, slidePhase = 0.55,
    sweep = 0.10, sweepRate = 0.17, sweepPhase = 0.8,
    alternate = true,
  } = {}) {
    Object.assign(this, {
      slide, slideRate, slidePhase, sweep, sweepRate, sweepPhase, alternate,
    });
    this.offsets = new Float32Array(MAX_ROWS);
    this.angles = new Float32Array(MAX_ROWS);
    this.enabled = true;
    this.time = 0;
  }

  /** Advance the wave. `dt` in ms. */
  update(dt) {
    if (!this.enabled) {
      this.offsets.fill(0);
      this.angles.fill(0);
      return;
    }
    this.time += dt / 1000;
    for (let r = 0; r < MAX_ROWS; r++) {
      // Sublinear row scaling keeps far rows from swinging as far as near ones
      // in world units — they already foreshorten, so an equal world-space
      // amplitude reads as the back of the field barely moving.
      const dir = this.alternate && (r & 1) ? -1 : 1;
      this.offsets[r] = dir * this.slide *
        Math.sin(this.time * this.slideRate * Math.PI * 2 + r * this.slidePhase);
      this.angles[r] = dir * this.sweep *
        Math.sin(this.time * this.sweepRate * Math.PI * 2 + r * this.sweepPhase);
    }
  }

  /** Clamp a row index into the uniform array. */
  static slot(row) {
    return Math.max(0, Math.min(MAX_ROWS - 1, row | 0));
  }

  offsetFor(row) { return this.offsets[RowMotion.slot(row)]; }
  angleFor(row) { return this.angles[RowMotion.slot(row)]; }

  /** Fade the motion out — for a screenshot, a test, or reduced-motion. */
  setEnabled(on) {
    this.enabled = on;
    if (!on) { this.offsets.fill(0); this.angles.fill(0); }
  }
}

/**
 * Honour the user's motion preference.
 *
 * A field that slides and sweeps continuously is exactly the thing
 * prefers-reduced-motion exists for — vestibular triggers are large-area
 * parallax, which is precisely what this module produces. Off is a legitimate
 * final state here, not a degraded one: the layout carries the information, the
 * motion only makes the depth easier to read.
 */
export function respectReducedMotion(motion, win = window) {
  if (!win.matchMedia) return () => {};
  const mq = win.matchMedia('(prefers-reduced-motion: reduce)');
  const apply = () => motion.setEnabled(!mq.matches);
  apply();
  mq.addEventListener('change', apply);
  return () => mq.removeEventListener('change', apply);
}
