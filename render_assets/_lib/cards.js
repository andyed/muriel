// muriel.spatial — persistent DOM cards as a tile source.
//
// A `<canvas layoutsubtree>` can paint real DOM descendants into its own bitmap
// (Chrome's HTML-in-Canvas API). That lets a tile field source its atlas from
// live cards instead of raster thumbnails, which buys three things a texture
// cannot: the text stays in find-in-page, in text selection, and in the
// accessibility tree. A find match can then fly the camera to the tile.
//
// This module owns the host and its cards, and CAPTURES a card into a
// card-sized bitmap that AtlasPair can treat as an ordinary image source; see
// `resolveSource` in atlas.js.
//
// The capture step is not an optimisation, it is the only thing that works.
// `drawElementImage` does not place an element into a sub-rect the way
// `drawImage` does: whatever scale sits on the context, the paint covers the
// WHOLE canvas — measured, a 1024px canvas at scale 1 gets 1024px of coverage,
// at 0.5 gets 512, at 0.25 gets 256 — and the DOMMatrix it returns centres the
// element in its own box rather than honouring the destination. So the host
// canvas is sized to exactly one card, the card is drawn into it at scale 1,
// and the resulting canvas is letterboxed into an atlas slot by the ordinary
// `TileAtlas.draw()` path. The atlas stays a plain canvas and the
// nearest-ancestor rule never touches it.
//
// THE TWO RULES THIS FILE EXISTS TO ENFORCE, both measured, both counter-
// intuitive, and both silent when broken:
//
//   1. The host must be PAINTED. `drawElementImage` on an element the
//      compositor has not painted returns a DOMMatrix and draws nothing, with
//      no exception thrown. `opacity: 0`, `visibility: hidden`,
//      `clip-path: inset(100%)` and `left: -100vw` all produce blank tiles.
//      `opacity: 0.01` paints in full, including underneath an opaque
//      full-viewport canvas — the compositor does not cull an occluded layer
//      the way it culls a fully transparent one.
//
//   2. Cards must be STACKED, not laid out. A host taller than the viewport
//      loses paint records for its WHOLE subtree, not just the offscreen part.
//      So every card is absolutely positioned at the host's origin and the host
//      stays exactly one card in size at any count. Verified to 2,500 cards.
//      Stacking costs nothing on the find side: find reaches a card buried at
//      index 317 of 500 and the paint event names it.
//
// Chrome-only, behind `chrome://flags/#canvas-draw-element` or
// `--enable-blink-features=CanvasDrawElement`. `CardHost.supported()` is the
// feature check; everything here is opt-in and nothing else in _lib changes
// behaviour when it is off.

import { RETRY } from './atlas.js';

/** True when this browser can draw DOM elements into a canvas. */
export function supported() {
  return typeof CanvasRenderingContext2D !== 'undefined'
    && typeof CanvasRenderingContext2D.prototype.drawElementImage === 'function';
}

/** Re-exported so a consumer wiring `resolveSource` needs one import. */
export { RETRY };

export class CardHost {
  /**
   * @param {object} opts
   * @param {HTMLElement} opts.container  where the host canvas is appended
   * @param {number} opts.count           one card per item
   * @param {(index:number, el:HTMLElement) => void} opts.build
   *   Fills the card. MUST use textContent / createElement — card content is
   *   third-party scraped text and innerHTML is banned for it.
   * @param {string} [opts.className]     class on each card
   * @param {number} [opts.width]         card width in CSS px
   * @param {number} [opts.height]        card height in CSS px
   * @param {number} [opts.captureScale] bitmap pixels per CSS pixel in the
   *   capture. 1 is the card at its own size, which is what the 256px near tier
   *   wants; there is no reason to go higher unless a tier is larger than the
   *   card.
   */
  constructor({ container, count, build, className = 'drawable-card', width = 340, height = 255, captureScale = 1 }) {
    this.count = count;
    this.width = width;
    this.height = height;
    this._byElement = new WeakMap();
    this._cards = new Array(count);
    this._paintHandlers = new Set();
    this._disposed = false;

    const canvas = document.createElement('canvas');
    canvas.setAttribute('layoutsubtree', '');
    canvas.className = 'card-host';
    // Bitmap == one card, so a scale-1 drawElementImage fills it exactly and
    // nothing is cropped. This canvas holds ONE captured card at a time.
    canvas.width = Math.round(width * captureScale);
    canvas.height = Math.round(height * captureScale);
    // Rule 2: one card's worth of layout, whatever `count` is.
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    this.canvas = canvas;
    this.captureScale = captureScale;
    this.ctx = canvas.getContext('2d', { willReadFrequently: false });

    for (let i = 0; i < count; i++) {
      const el = document.createElement('div');
      el.className = className;
      el.setAttribute('drawable', '');
      el.dataset.index = String(i);
      // Rule 2 again. Set here rather than in CSS so a consumer stylesheet
      // cannot quietly un-stack the pile and blank the field.
      el.style.position = 'absolute';
      el.style.top = '0';
      el.style.left = '0';
      el.style.width = `${width}px`;
      el.style.height = `${height}px`;
      build(i, el);
      canvas.appendChild(el);
      this._cards[i] = el;
      this._byElement.set(el, i);
    }

    container.appendChild(canvas);

    this._onPaint = (e) => {
      if (this._disposed) return;
      const indices = [];
      for (const el of e.changedElements ?? []) {
        const i = this._byElement.get(el);
        if (i !== undefined) indices.push(i);
      }
      if (!indices.length) return;
      for (const fn of this._paintHandlers) fn(indices, e);
    };
    canvas.addEventListener('paint', this._onPaint);
  }

  /**
   * Draw one card into the host bitmap and hand back the bitmap.
   *
   * The returned canvas is REUSED for every capture, so a caller must consume
   * it before the next call — which AtlasPair does, drawing it into a slot
   * synchronously. Returning the canvas rather than a copy is the point: a
   * per-card copy would put 2,500 card-sized bitmaps on the heap.
   *
   * @returns {HTMLCanvasElement|RETRY|null} the bitmap; RETRY while the
   *   compositor has not painted the host yet; null if this card cannot be
   *   captured at all.
   */
  capture(index) {
    const el = this._cards[index];
    if (!el || this._disposed) return null;
    if (!el.offsetWidth || !el.offsetHeight) return RETRY;   // hidden host

    const { width: w, height: h } = this.canvas;
    this.ctx.clearRect(0, 0, w, h);
    this.ctx.save();
    try {
      if (this.captureScale !== 1) this.ctx.scale(this.captureScale, this.captureScale);
      this.ctx.drawElementImage(el, 0, 0);
    } catch (err) {
      // The compositor has not painted this host yet. Temporary, and the only
      // temporary failure — everything else here is permanent for this card.
      return /No cached paint record/i.test(err?.message ?? '') ? RETRY : null;
    } finally {
      this.ctx.restore();
    }
    return this.canvas;
  }

  /** The card for an index, or null. */
  elementFor(index) {
    return this._cards[index] ?? null;
  }

  /** The index a card belongs to, or undefined. */
  indexOf(el) {
    return this._byElement.get(el);
  }

  /**
   * Subscribe to the canvas `paint` event, mapped to card indices.
   *
   * The browser fires this when it changes a drawable itself — which is how a
   * find-in-page match announces itself, since nothing in our own code touches
   * a card after build(). Returns an unsubscribe function.
   */
  onPaint(fn) {
    this._paintHandlers.add(fn);
    return () => this._paintHandlers.delete(fn);
  }

  /**
   * Resolve once the cards have paint records, so the first draw does not throw
   * `No cached paint record`.
   *
   * `requestPaint()` plus the paint event is the explicit signal; two rendering
   * updates is the portable fallback, and measured enough on its own. The
   * timeout exists so a host that never paints resolves anyway — the caller
   * finds out from the blank-canary path in AtlasPair rather than by hanging.
   */
  ready(timeoutMs = 500) {
    if (typeof this.canvas.requestPaint !== 'function') return this._frames(2);
    return new Promise((resolve) => {
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      this.canvas.addEventListener('paint', finish, { once: true });
      this.canvas.requestPaint();
      setTimeout(finish, timeoutMs);
    }).then(() => this._frames(1));
  }

  /**
   * Resolve once the cards are not going to repaint themselves any more:
   * `ready()`, plus every hero image inside the host decoded.
   *
   * This matters because the `paint` event is how a find-in-page match
   * announces itself, and an `<img>` finishing load repaints its card exactly
   * the same way. A consumer that arms its find handler before the images
   * settle gets a burst of phantom "matches" at startup. There is no flag on
   * the event to tell the two apart, so the only honest discriminator is time:
   * wait until we know WE are done changing the cards.
   */
  async settled(timeoutMs = 4000) {
    await this.ready();
    const images = [...this.canvas.querySelectorAll('img')].filter((img) => !img.complete);
    if (!images.length) return this._frames(1);
    await Promise.race([
      Promise.all(images.map((img) => new Promise((resolve) => {
        img.addEventListener('load', resolve, { once: true });
        img.addEventListener('error', resolve, { once: true });
      }))),
      new Promise((resolve) => setTimeout(resolve, timeoutMs)),
    ]);
    return this._frames(2);
  }

  _frames(n) {
    return new Promise((resolve) => {
      let left = n;
      const step = () => (--left <= 0 ? resolve() : requestAnimationFrame(step));
      requestAnimationFrame(step);
    });
  }

  dispose() {
    if (this._disposed) return;
    this._disposed = true;
    this.canvas.removeEventListener('paint', this._onPaint);
    this._paintHandlers.clear();
    this._cards.length = 0;
    this.canvas.remove();
  }
}
