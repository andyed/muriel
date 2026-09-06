// muriel.spatial — canvas-backed texture atlases for high-count tile fields.
//
// A spatial scene that carries thousands of images cannot give each one its own
// texture (thousands of draw calls) or its own DOM node (thousands of composited
// layers). It packs them into a handful of atlases and draws the lot as one
// instanced mesh — see instanced.js for the consumer.
//
// Two tiers, because a single tier forces an impossible tradeoff:
//
//   far   every item, small (64px). Sized so the WHOLE corpus is resident:
//         2,500 tiles at 64px is ~41 MB of VRAM. This is what you see when
//         zoomed out, where a tile is a few pixels of colour and shape.
//   near  a fixed pool of large slots (256px), handed out by camera distance
//         and recycled LRU. ~256 slots is ~67 MB, and that budget is FLAT —
//         it does not grow with the corpus.
//
// So VRAM is bounded by the tier sizes, not by item count. A 25,000-item field
// costs the same near-tier as a 250-item one; only the far atlas grows, and it
// grows at 16 KB per item.
//
// Uploads are batched. Writing to the backing canvas is cheap; pushing it to
// the GPU is not, so draws accumulate and flush at most once per `uploadMs`.
//
// Exports:
//   TileAtlas    — one canvas-backed atlas with slot allocation
//   AtlasPair    — the far/near pair plus the LRU that moves items between them

import * as THREE from 'three';

/** Atlas dimension cap. 4096 is universally supported; 8192 is not. */
const MAX_ATLAS_PX = 4096;

/**
 * One canvas-backed texture atlas holding fixed-size square slots.
 *
 * Slots are addressed by index, laid out row-major. The consumer shader turns
 * a slot index into UVs, so nothing here needs to know about geometry.
 */
export class TileAtlas {
  /**
   * @param {object} opts
   * @param {number} opts.tilePx    edge length of one slot, in texels
   * @param {number} opts.capacity  slots required; the atlas sizes itself to fit
   * @param {number} [opts.uploadMs] minimum ms between GPU uploads
   */
  constructor({ tilePx, capacity, uploadMs = 120 }) {
    this.tilePx = tilePx;
    this.uploadMs = uploadMs;

    // Square-ish atlas big enough for `capacity` slots, capped at MAX_ATLAS_PX.
    // Sized to the exact need rather than rounded up to a power of two: NPOT
    // textures are unconditional in WebGL2, and there are no mipmaps and no
    // wrapping here to want POT for. Rounding 2,500 64px tiles up to 4096²
    // costs 26 MB of VRAM to hold 1,596 slots that can never be allocated.
    const perSide = Math.ceil(Math.sqrt(capacity));
    const px = Math.min(MAX_ATLAS_PX, perSide * tilePx);
    this.cols = Math.max(1, Math.floor(px / tilePx));
    this.rows = Math.max(1, Math.floor(px / tilePx));
    this.capacity = this.cols * this.rows;

    this.canvas = document.createElement('canvas');
    this.canvas.width = px;
    this.canvas.height = px;
    this.ctx = this.canvas.getContext('2d', { willReadFrequently: false });
    // Transparent, not black: an unfilled slot must read as absent, not as a
    // black tile. The instanced shader also discards on zero alpha.
    this.ctx.clearRect(0, 0, px, px);

    this.texture = new THREE.CanvasTexture(this.canvas);
    this.texture.colorSpace = THREE.SRGBColorSpace;
    this.texture.minFilter = THREE.LinearFilter;   // no mips: slots would bleed
    this.texture.magFilter = THREE.LinearFilter;
    this.texture.generateMipmaps = false;

    this._dirty = false;
    this._lastUpload = 0;
    this._free = [];
    for (let i = this.capacity - 1; i >= 0; i--) this._free.push(i);

    // Fraction of the slot each drawn image actually covers, from the image's
    // OWN aspect rather than the item's declared one. The shader samples this
    // sub-rect, so a wrong or missing `dims` costs a slightly wrong quad shape
    // instead of a stretched picture.
    this.fits = new Float32Array(this.capacity * 2).fill(1);
  }

  /** @returns {number} a free slot index, or -1 when the atlas is full. */
  alloc() {
    return this._free.length ? this._free.pop() : -1;
  }

  /**
   * Wipe a slot's pixels without returning it to the pool.
   *
   * Split from free() because eviction hands the slot straight to its next
   * owner: doing that via free() puts the slot on the free list AND in the new
   * owner's hands, so the next alloc() hands the same slot to a second item and
   * two tiles sample the same pixels. Every eviction leaked one duplicate.
   */
  clear(slot) {
    if (slot < 0 || slot >= this.capacity) return;
    const { x, y } = this.slotRect(slot);
    this.ctx.clearRect(x, y, this.tilePx, this.tilePx);
    this.fits[slot * 2] = 1;
    this.fits[slot * 2 + 1] = 1;
    this._dirty = true;
  }

  /** Return a slot to the pool and clear it so a stale image cannot show. */
  free(slot) {
    if (slot < 0 || slot >= this.capacity) return;
    this.clear(slot);
    this._free.push(slot);
  }

  /** Pixel rect of a slot in the backing canvas. */
  slotRect(slot) {
    return {
      x: (slot % this.cols) * this.tilePx,
      y: Math.floor(slot / this.cols) * this.tilePx,
      w: this.tilePx,
      h: this.tilePx,
    };
  }

  /**
   * Draw an image into a slot, letterboxed to preserve aspect ratio.
   *
   * Aspect is preserved rather than stretched because these are photographic
   * excerpts — a squashed 3:1 banner is unrecognizable, which defeats the
   * entire point of showing it. The instanced quad is separately scaled to the
   * item's real aspect, so the letterbox padding lands outside the visible
   * quad rather than as visible bars.
   */
  draw(slot, image) {
    if (slot < 0 || slot >= this.capacity) return false;
    const { x, y, w, h } = this.slotRect(slot);
    const iw = image.naturalWidth || image.width;
    const ih = image.naturalHeight || image.height;
    if (!iw || !ih) return false;

    const scale = Math.min(w / iw, h / ih);
    const dw = Math.max(1, Math.round(iw * scale));
    const dh = Math.max(1, Math.round(ih * scale));

    this.ctx.clearRect(x, y, w, h);
    try {
      this.ctx.drawImage(image, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
      this.fits[slot * 2] = dw / w;
      this.fits[slot * 2 + 1] = dh / h;
    } catch {
      // A cross-origin image without CORS headers taints the canvas on draw in
      // some engines and throws in others. Either way the slot is unusable —
      // report failure so the caller can fall back rather than silently
      // shipping a blank tile.
      return false;
    }
    this._dirty = true;
    return true;
  }

  /**
   * Push pending canvas writes to the GPU, at most once per `uploadMs`.
   * Call once per frame; it self-throttles.
   */
  flush(now = performance.now()) {
    if (!this._dirty || now - this._lastUpload < this.uploadMs) return false;
    this.texture.needsUpdate = true;
    this._dirty = false;
    this._lastUpload = now;
    return true;
  }

  /** Bytes of VRAM this atlas occupies, for budget reporting. */
  get bytes() {
    return this.canvas.width * this.canvas.height * 4;
  }

  dispose() {
    this.texture.dispose();
    this.canvas.width = this.canvas.height = 0;
  }
}

/**
 * The far/near pair, plus the promotion logic that moves an item between them.
 *
 * The caller supplies a `resolve(item, tier)` returning a URL (or null) for a
 * given tier, so a consumer with a real thumbnail ladder can serve a 64px
 * thumb to `far` and a 256px one to `near` instead of downscaling the same
 * large file twice.
 */
export class AtlasPair {
  /**
   * @param {object} opts
   * @param {number} opts.count          number of items in the field
   * @param {number} [opts.farPx]        far-tier slot size
   * @param {number} [opts.nearPx]       near-tier slot size
   * @param {number} [opts.nearSlots]    near-tier pool size (flat VRAM budget)
   * @param {(item:any, tier:'far'|'near') => (string|null)} opts.resolve
   * @param {number} [opts.concurrency]  simultaneous image loads
   */
  constructor({
    count, farPx = 64, nearPx = 256, nearSlots = 256,
    resolve, concurrency = 8,
  }) {
    this.resolve = resolve;
    this.far = new TileAtlas({ tilePx: farPx, capacity: count });
    this.near = new TileAtlas({ tilePx: nearPx, capacity: nearSlots });

    // item index -> slot in each tier; -1 means "not resident".
    this.farSlot = new Int32Array(count).fill(-1);
    this.nearSlot = new Int32Array(count).fill(-1);
    // Monotonic touch counter per item, for LRU eviction of near slots.
    this.lastSeen = new Float64Array(count);
    this._nearOwner = new Int32Array(this.near.capacity).fill(-1);

    // Two queues, near drained first. One LIFO queue looks right — the most
    // recent request is nearest what the user is looking at — and is exactly
    // wrong on the initial load, where every request arrives in one burst in
    // index order. LIFO then serves the BACK of the field first and the front
    // last: measured on a 727-clip corpus, 0 of the 39 front-of-field tiles had
    // loaded after 20 seconds while the back was fully resident.
    this._nearQueue = [];
    this._farQueue = [];
    this._inflight = 0;
    this._concurrency = concurrency;
    this._failed = new Set();
    this.onTileReady = null;   // (index, tier) => void
  }

  /**
   * Ask for an item at a tier. Returns immediately; the tile appears when the
   * image loads. Repeated calls are cheap and refresh the LRU timestamp.
   */
  request(index, tier, now = performance.now()) {
    if (tier === 'near') this.lastSeen[index] = now;
    const slots = tier === 'far' ? this.farSlot : this.nearSlot;
    if (slots[index] >= 0) return slots[index];
    if (this._failed.has(`${tier}:${index}`)) return -1;

    const atlas = tier === 'far' ? this.far : this.near;
    let slot = atlas.alloc();
    if (slot < 0) {
      if (tier === 'far') return -1;      // far is sized to fit; full means a bug
      slot = this._evictNear(now);
      if (slot < 0) return -1;            // everything in the pool is hot
    }
    slots[index] = slot;
    if (tier === 'near') this._nearOwner[slot] = index;

    this._enqueue(index, tier, slot);
    return slot;
  }

  /** Drop an item's near-tier slot — it has left the near band. */
  releaseNear(index) {
    const slot = this.nearSlot[index];
    if (slot < 0) return;
    this.near.free(slot);
    this.nearSlot[index] = -1;
    this._nearOwner[slot] = -1;
  }

  /**
   * Detach the coldest resident near slot and hand it straight to the caller.
   *
   * The slot deliberately does NOT go back on the free list — it is being
   * reassigned, not released. See TileAtlas.clear().
   *
   * @returns {number} the detached slot, or -1 when everything is hot
   */
  _evictNear(now) {
    let coldest = -1;
    let coldestAt = Infinity;
    for (let slot = 0; slot < this._nearOwner.length; slot++) {
      const owner = this._nearOwner[slot];
      // An unowned slot belongs to the free list, and alloc() would already
      // have handed it out; taking it here would hand out the same slot twice.
      if (owner < 0) continue;
      const seen = this.lastSeen[owner];
      // Never evict something touched this frame — that thrashes under a pan.
      if (now - seen < 16) continue;
      if (seen < coldestAt) { coldestAt = seen; coldest = slot; }
    }
    if (coldest < 0) return -1;
    const owner = this._nearOwner[coldest];
    this.near.clear(coldest);
    this.nearSlot[owner] = -1;
    this._nearOwner[coldest] = -1;
    return coldest;
  }

  _enqueue(index, tier, slot) {
    (tier === 'near' ? this._nearQueue : this._farQueue).push({ index, tier, slot });
    this._pump();
  }

  _pump() {
    while (this._inflight < this._concurrency) {
      // Near before far: the near tier IS the set the camera is close to, so
      // this serves what is on screen rather than whatever was requested last.
      // Within a tier, LIFO — a fresh request during a pan beats a stale one.
      const q = this._nearQueue.length ? this._nearQueue : this._farQueue;
      if (!q.length) return;
      const job = q.pop();
      const slots = job.tier === 'far' ? this.farSlot : this.nearSlot;
      // The slot may have been reassigned while queued.
      if (slots[job.index] !== job.slot) continue;
      this._load(job);
    }
  }

  _load({ index, tier, slot }) {
    const url = this.resolve(index, tier);
    if (!url) { this._failed.add(`${tier}:${index}`); return; }

    this._inflight++;
    const img = new Image();
    // Same-origin attachments need no CORS; a remote hero does, or drawImage
    // taints the canvas. Requesting it costs nothing when the server ignores it.
    img.crossOrigin = 'anonymous';
    img.decoding = 'async';
    const done = (ok) => {
      this._inflight--;
      const slots = tier === 'far' ? this.farSlot : this.nearSlot;
      if (ok && slots[index] === slot) {
        const atlas = tier === 'far' ? this.far : this.near;
        if (atlas.draw(slot, img) && this.onTileReady) this.onTileReady(index, tier);
      } else if (!ok) {
        this._failed.add(`${tier}:${index}`);
        if (slots[index] === slot) {
          (tier === 'far' ? this.far : this.near).free(slot);
          slots[index] = -1;
          if (tier === 'near') this._nearOwner[slot] = -1;
        }
      }
      this._pump();
    };
    img.addEventListener('load', () => done(true), { once: true });
    img.addEventListener('error', () => done(false), { once: true });
    img.src = url;
  }

  /** Flush both atlases. Call once per frame. */
  flush(now = performance.now()) {
    const a = this.far.flush(now);
    const b = this.near.flush(now);
    return a || b;
  }

  /** VRAM budget, for the HUD and for tests that assert the budget is flat. */
  get bytes() {
    return this.far.bytes + this.near.bytes;
  }

  dispose() {
    this.far.dispose();
    this.near.dispose();
    this._nearQueue.length = 0;
    this._farQueue.length = 0;
  }
}
