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
// 1. PAN WRAPS, AND THE WRAP MUST BE ATOMIC. Rows scroll continuously rather
//    than sweeping back and forth. A quad's CENTRE has to cross the seam in one
//    step — wrap the vertices independently and the quad tears in half across
//    the screen. The field shader displaces the centre and rebuilds the quad
//    around it, so this holds by construction.
//
//    The real constraint of a marquee is the other one: the row's content must
//    be WIDER than the visible frame, or the viewer watches tiles vanish at one
//    edge and reappear at the other. `wrapSpan` is the loop length; frame the
//    camera inside it. `oscillate` is kept for fields that cannot afford the
//    off-screen margin.
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
    mode = 'pan',
    speed = 34, speedVariance = 0.45, wrapSpan = 0,
    slide = 26, slideRate = 0.22, slidePhase = 0.55,
    sweep = 0.10, sweepRate = 0.17, sweepPhase = 0.8,
    alternate = true,
  } = {}) {
    Object.assign(this, {
      mode, speed, speedVariance, wrapSpan,
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
    const span = this.wrapSpan;

    for (let r = 0; r < MAX_ROWS; r++) {
      const dir = this.alternate && (r & 1) ? -1 : 1;

      if (this.mode === 'pan') {
        // Each row scrolls at its own rate. Uniform speed reads as one sliding
        // slab — a camera pan — and the whole point is that rows are separate.
        const rate = this.speed * (1 + this.speedVariance * hash01(r));
        let x = dir * this.time * rate;
        // Kept inside one span rather than growing without bound: an offset in
        // the millions loses float precision, and a float32 uniform loses it
        // sooner than the JS double that computed it, so the two halves would
        // drift apart after a few minutes of idling.
        if (span > 0) x = ((x % span) + span) % span;
        this.offsets[r] = x;
      } else {
        this.offsets[r] = dir * this.slide *
          Math.sin(this.time * this.slideRate * Math.PI * 2 + r * this.slidePhase);
      }

      this.angles[r] = dir * this.sweep *
        Math.sin(this.time * this.sweepRate * Math.PI * 2 + r * this.sweepPhase);
    }
  }

  /** Clamp a row index into the uniform array. */
  static slot(row) {
    return Math.max(0, Math.min(MAX_ROWS - 1, row | 0));
  }

  offsetFor(row) { return this.offsets[RowMotion.slot(row)]; }

  /**
   * Apply this row's offset to a base x, wrapping into the loop.
   *
   * The CPU mirror of the shader's wrap. Everything positional on the CPU side
   * goes through here, so a click during a pan lands on the tile that is drawn
   * rather than the one the static layout claims.
   */
  wrapX(baseX, row) {
    const x = baseX + this.offsetFor(row);
    const span = this.wrapSpan;
    if (!span) return x;
    const half = span / 2;
    return ((((x + half) % span) + span) % span) - half;
  }
  angleFor(row) { return this.angles[RowMotion.slot(row)]; }

  /** Fade the motion out — for a screenshot, a test, or reduced-motion. */
  setEnabled(on) {
    this.enabled = on;
    if (!on) { this.offsets.fill(0); this.angles.fill(0); }
  }
}

/** Stable per-row jitter so a row keeps its own speed across reloads. */
function hash01(r) {
  const v = Math.sin((r + 1) * 127.1) * 43758.5453;
  return v - Math.floor(v);
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
