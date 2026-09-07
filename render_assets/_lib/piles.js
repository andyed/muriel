// muriel.spatial — piles.
//
// After Mander, Salomon & Wong, "A 'Pile' Metaphor for Supporting Casual
// Organization of Information" (CHI 1992). Their observation was that people
// do not file; they pile. A folder demands you name a category and commit to
// it before you have one, and the cost of that decision is why the desktop
// silts up with things nobody classified. A pile costs nothing to make, is
// legible at a glance from its size and its top item, and can be browsed by
// riffling without being opened.
//
// Piling maps onto an instanced field almost for free, which is the reason to
// do it here rather than in a consumer: a pile, a spread pile, and a
// re-sorted field are all the same operation — some subset of instances move
// to new matrices. Nothing enters or leaves the scene graph, so a pile of
// 400 costs the same as a pile of 4 to draw.
//
// What a pile is NOT, here: a container. Membership is supplied by the
// consumer as index lists, so a facet-derived grouping (every clip tagged
// `govee`) and a hand-made pile are the same object to this module, and an
// item may sit in several piles — which is the normal case for tags, and which
// a folder tree cannot represent at all.
//
// Exports:
//   PileLayout — place piles on a surface; collapse, spread, and riffle them

import * as THREE from 'three';

/** Pile display states. */
export const PILED = 'piled';
export const SPREAD = 'spread';

export class PileLayout {
  /**
   * @param {object} opts
   * @param {import('./instanced.js').TileField} opts.field
   * @param {import('./spatial.js').Mountain} [opts.surface] supplies
   *   planeToWorld; omit for a flat field in world space.
   * @param {(i:number) => number} opts.aspectOf
   * @param {number} [opts.stackOffset] world units each card in a pile is
   *   nudged, so the stack reads as depth rather than one card.
   * @param {number} [opts.faceCount] members shown as a contact sheet on the
   *   face of a collapsed pile: a square grid (4 or 9), so cells share the
   *   footprint's proportions and members that match the pile's average
   *   aspect tile it without gaps (0 = a single cover, the pre-2026-09 look)
   * @param {number} [opts.maxVisibleInPile] cards drawn proud of the stack
   *   before the rest are hidden behind the top of it.
   */
  constructor({
    field, surface = null, aspectOf,
    stackOffset = 3.2,
    maxVisibleInPile = 24,
    faceCount = 9,
  }) {
    this.field = field;
    this.surface = surface;
    this.aspectOf = aspectOf;
    this.stackOffset = stackOffset;
    this.maxVisibleInPile = maxVisibleInPile;
    this.faceCount = faceCount;

    /** @type {Array<{label:string, indices:number[], u:number, v:number, w:number, h:number, state:string}>} */
    this.piles = [];
    this.spreadPile = -1;
    this._q = new THREE.Quaternion();
  }

  /**
   * Lay groups out as piles across the surface.
   *
   * Pile footprint scales with the square root of its member count, not
   * linearly: a pile of 400 is deeper than a pile of 40, but it is not ten
   * times wider — the whole point of a pile is that it holds a lot in roughly
   * the space of one thing. Size still has to be readable at a glance, which
   * is what the original paper's "you can tell how big a pile is by looking at
   * it" claim rests on, so the growth is real, just sublinear.
   *
   * @param {Array<{label:string, indices:number[]}>} groups
   * @param {object} [opts]
   */
  arrange(groups, {
    width = 2400, depth = 2600,
    cardH = 150, gap = 330, rowGap = 300,
  } = {}) {
    this.piles = [];
    const halfW = width / 2;
    let u = -halfW;
    let v = 0;
    let rowTall = 0;

    for (const g of groups) {
      // Sublinear growth, floored so a one-item pile is still a card.
      const scale = Math.min(2.4, 0.75 + Math.sqrt(g.indices.length) * 0.11);
      const h = cardH * scale;
      const w = h * this._avgAspect(g.indices);

      if (u > -halfW && u + w > halfW) {       // wrap to the next shelf
        v -= rowTall + rowGap;
        rowTall = 0;
        u = -halfW;
      }
      this.piles.push({
        label: g.label, indices: g.indices,
        u: u + w / 2, v, w, h, state: PILED,
      });
      rowTall = Math.max(rowTall, h);
      u += w + gap;
    }

    // The surface was sized for a corpus; piles are far sparser, so report the
    // depth actually used rather than pretending to fill it.
    this.usedDepth = -v + rowTall;
    for (let i = 0; i < this.piles.length; i++) this.collapse(i, true);
    return this.piles;
  }

  _avgAspect(indices) {
    if (!indices.length) return 4 / 3;
    let sum = 0;
    for (const i of indices) sum += this.aspectOf(i);
    return Math.min(2.4, Math.max(0.6, sum / indices.length));
  }

  /** Plane (u,v) → world, via the surface when there is one. */
  _world(u, v, cardH) {
    if (this.surface) return this.surface.planeToWorld(u, v, cardH);
    return new THREE.Vector3(u, cardH / 2, v);
  }

  /**
   * Stack a pile's members. Cards are nudged along the pile's normal and
   * jittered slightly so the stack reads as a physical heap rather than one
   * card — Mander et al. drew the same cue, and it is doing real work: an
   * unjittered stack of identical rectangles is indistinguishable from a
   * single item, which loses the "how big is this pile" glance.
   */
  /**
   * The members shown on a collapsed pile's face: up to faceCount, sampled
   * evenly through the pile's order (positions 0, n/K, 2n/K …). Samples, not
   * centroids: a pile that is mostly one thing shows that, a mixed pile shows
   * the mix. One cover told you nothing about 134 others.
   */
  faceOf(pileIndex) {
    const pile = this.piles[pileIndex];
    const n = pile?.indices.length || 0;
    if (!n || !this.faceCount) return []; // an empty pile (filtered to nothing) has no face
    // Only a full square grid tiles the footprint: 1, 4 or 9 members; 3×3 once
    // a pile is large enough (24+) for nine samples to say more than four.
    const k = n >= 24 && this.faceCount >= 9 ? 9 : n >= 4 && this.faceCount >= 4 ? 4 : 1;
    return Array.from({ length: k }, (_, j) => pile.indices[Math.floor(j * n / k)]);
  }

  /** Cell geometry of the face grid inside the pile's footprint: [cols, rows], square. */
  _faceGrid(count) {
    const cols = Math.max(1, Math.ceil(Math.sqrt(count)));
    return [cols, Math.max(1, Math.ceil(count / cols))];
  }

  collapse(pileIndex, immediate = false) {
    const pile = this.piles[pileIndex];
    if (!pile) return;
    pile.state = PILED;
    if (this.spreadPile === pileIndex) this.spreadPile = -1;

    // The face: a contact sheet of sampled members laid in cells over the
    // footprint, nearest the camera, each contained in its cell with its own
    // proportions. Everything else stacks behind as before.
    const face = this.faceOf(pileIndex), faceSet = new Set(face);
    const [cols, rows] = this._faceGrid(face.length);
    const cellW = pile.w / cols, cellH = pile.h / rows, inset = 0.94;
    const faceZ = (this.maxVisibleInPile + 1) * this.stackOffset;
    face.forEach((i, j) => {
      const col = j % cols, row = Math.floor(j / cols);
      const aspect = this.aspectOf(i);
      const h = Math.min(cellH * inset, (cellW * inset) / aspect), w = h * aspect;
      const u = pile.u - pile.w / 2 + cellW * (col + 0.5);
      // A card stands on its plane point (the surface lifts it by h/2), so the
      // cell's bottom line places the card at the cell's centre; row 0 on top.
      const v = pile.v + (rows - 1 - row) * cellH + (cellH - h) / 2;
      const p = this._world(u, v, h);
      this._q.identity();
      // Distinct depth per cell so no two face cards are coplanar.
      const z = p.z + faceZ + j * 0.2;
      if (immediate) this.field.place(i, p.x, p.y, z, w, h, this._q);
      else this.field.moveTo(i, p.x, p.y, z, w, h, this._q);
    });

    const n = pile.indices.length;
    for (let k = 0; k < n; k++) {
      const i = pile.indices[k];
      if (faceSet.has(i)) continue;
      // Deepest card first, so the LAST member drawn is the top of the pile.
      const depth = n - 1 - k;
      const shown = Math.min(depth, this.maxVisibleInPile);
      const jitter = this._jitter(i);

      const w = pile.h * this.aspectOf(i);
      const p = this._world(
        pile.u + jitter.x * 7,
        pile.v + shown * 1.6,
        pile.h,
      );
      // Push each card proud of the one beneath along +Z so the depth buffer
      // orders the stack correctly whatever the instance order happens to be.
      // Cap the visible fan, not depth ordering. Putting every overflow card
      // on the same plane makes overlapping textures fight in the depth
      // buffer. One world unit keeps the tail distinct at ordinary camera
      // distances without extending its footprint across the surface.
      const overflow = Math.max(0, depth - this.maxVisibleInPile);
      const z = p.z + (this.maxVisibleInPile - shown) * this.stackOffset - overflow;
      this._q.setFromAxisAngle(UP_Z, jitter.r * 0.05);

      if (immediate) this.field.place(i, p.x, p.y, z, w, pile.h, this._q);
      else this.field.moveTo(i, p.x, p.y, z, w, pile.h, this._q);
    }
    if (immediate) this.field.layout();
  }

  /**
   * Open a pile into a browsable local cluster.
   *
   * Spreading in place rather than flying the pile to a viewer is deliberate:
   * the pile's position on the surface is the only thing telling you WHICH
   * pile you opened, and a pile that leaves home to be read takes its own
   * label with it.
   */
  spread(pileIndex, { columns = null, gap = 14 } = {}) {
    const pile = this.piles[pileIndex];
    if (!pile) return;
    if (this.spreadPile >= 0 && this.spreadPile !== pileIndex) {
      this.collapse(this.spreadPile);
    }
    pile.state = SPREAD;
    this.spreadPile = pileIndex;

    const n = pile.indices.length;
    const cols = columns || Math.max(1, Math.ceil(Math.sqrt(n * 1.6)));
    const cardH = pile.h * 0.62;

    // Centre the spread on the pile so it opens where it sits.
    const rows = Math.ceil(n / cols);
    // Mixed-aspect imagery needs each column's actual widest card. A fixed
    // 1.5-aspect cell makes even ordinary 16:9 screenshots overlap.
    const columnWidths = new Array(cols).fill(0);
    for (let k = 0; k < n; k++) {
      columnWidths[k % cols] = Math.max(columnWidths[k % cols], cardH * this.aspectOf(pile.indices[k]));
    }
    const totalWidth = columnWidths.reduce((sum, w) => sum + w, 0) + Math.max(0, cols - 1) * gap;
    let left = pile.u - totalWidth / 2;
    const columnCentres = columnWidths.map((w) => {
      const centre = left + w / 2;
      left += w + gap;
      return centre;
    });
    const originV = pile.v + (rows - 1) * (cardH + gap) / 2;

    for (let k = 0; k < n; k++) {
      const i = pile.indices[k];
      const col = k % cols;
      const row = Math.floor(k / cols);
      const w = cardH * this.aspectOf(i);
      const p = this._world(columnCentres[col], originV - row * (cardH + gap), cardH);
      this._q.identity();
      this.field.moveTo(i, p.x, p.y, p.z, w, cardH, this._q);
    }
  }

  /** Toggle. Returns the resulting state. */
  toggle(pileIndex) {
    const pile = this.piles[pileIndex];
    if (!pile) return null;
    if (pile.state === SPREAD) { this.collapse(pileIndex); return PILED; }
    this.spread(pileIndex);
    return SPREAD;
  }

  /**
   * World anchors for pile labels.
   *
   * A pile is identified by two things and needs both: its position, which is
   * what spatial memory indexes on, and its name. Mander et al. leaned on the
   * top item as a visual proxy, which works for a desk of documents you wrote
   * and not at all for a facet value like `firmware` — so the label is not
   * decoration here, it is the only thing distinguishing one heap of coloured
   * rectangles from another.
   *
   * One element per pile, so keep pile counts in the dozens. A facet with 200
   * values wants a different treatment than piling.
   */
  labelAnchors(yOffset = 0.62) {
    return this.piles.map((pile, i) => {
      const p = this._world(pile.u, pile.v, pile.h);
      return {
        index: i,
        label: pile.label,
        count: pile.indices.length,
        state: pile.state,
        x: p.x, y: p.y + pile.h * yOffset, z: p.z + 6,
        width: pile.w,
      };
    });
  }

  /**
   * Create an empty pile. Returns its index.
   *
   * Piling is casual organization: you make the heap first and name it later,
   * or never. So a pile with no members and no label is a legal, expected
   * state, not an error to guard against.
   */
  createPile(label = '', { u = 0, v = 0, w = 220, h = 150 } = {}) {
    this.piles.push({ label, indices: [], u, v, w, h, state: PILED });
    return this.piles.length - 1;
  }

  /**
   * Move an item into a pile. `exclusive` false leaves existing memberships
   * alone, which is what tags want; true is the desk metaphor, where a thing
   * is in one heap because it is a physical object.
   */
  assign(itemIndex, pileIndex, { exclusive = true } = {}) {
    if (exclusive) {
      for (const pile of this.piles) {
        const at = pile.indices.indexOf(itemIndex);
        if (at >= 0) pile.indices.splice(at, 1);
      }
    }
    const target = this.piles[pileIndex];
    if (!target || target.indices.includes(itemIndex)) return;
    target.indices.push(itemIndex);
  }

  /** Remove an item from a pile. */
  unassign(itemIndex, pileIndex) {
    const pile = this.piles[pileIndex];
    if (!pile) return;
    const at = pile.indices.indexOf(itemIndex);
    if (at >= 0) pile.indices.splice(at, 1);
  }

  /**
   * Capture pile membership as portable view state.
   *
   * Keyed by a caller-supplied stable key, NEVER by instance index. Indices are
   * positions in whatever array the field was built from this session — they
   * change when the corpus is filtered, re-sorted, or grows by one clip, so
   * index-keyed state silently reassigns every pile the next time it loads.
   *
   * Choose the key carefully: it has to survive whatever the underlying store
   * lets a user do. A filename or a title is usually the WRONG choice, because
   * renaming is exactly the thing people do to notes.
   *
   * This is view state, not data — an annotation over the corpus rather than a
   * property of any item in it. That is what lets several views hold different
   * piles over the same items, which a per-item field cannot express.
   *
   * @param {(index:number) => string} keyOf
   */
  serialize(keyOf) {
    return {
      version: 1,
      piles: this.piles.map((pile) => ({
        label: pile.label,
        u: +pile.u.toFixed(1),
        v: +pile.v.toFixed(1),
        keys: pile.indices.map(keyOf).filter(Boolean),
      })),
    };
  }

  /**
   * Rebuild piles from view state.
   *
   * Keys that no longer resolve are dropped and REPORTED rather than silently
   * skipped — a pile quietly losing members as notes get renamed looks like
   * nothing at all until the pile is empty.
   *
   * @param {object} state from serialize()
   * @param {(key:string) => number} indexOf  -1 when the key is unknown
   * @returns {{restored:number, orphaned:string[]}}
   */
  restore(state, indexOf) {
    if (!state || state.version !== 1 || !Array.isArray(state.piles)) {
      return { restored: 0, orphaned: [] };
    }
    const orphaned = [];
    let restored = 0;
    this.piles = state.piles.map((p) => {
      const indices = [];
      for (const key of p.keys || []) {
        const i = indexOf(key);
        if (i >= 0) { indices.push(i); restored++; }
        else orphaned.push(key);
      }
      return {
        label: p.label || '', indices,
        u: p.u || 0, v: p.v || 0,
        w: 220, h: 150, state: PILED,
      };
    });
    return { restored, orphaned };
  }

  /** Which pile an item index belongs to, or -1. First match wins. */
  pileOf(itemIndex) {
    for (let p = 0; p < this.piles.length; p++) {
      if (this.piles[p].indices.includes(itemIndex)) return p;
    }
    return -1;
  }

  /**
   * Deterministic per-item jitter. Deliberately NOT random: a pile that
   * reshuffles its own cards every time it collapses destroys the spatial
   * memory the whole metaphor runs on — you found this thing last time by
   * remembering it stuck out on the left.
   */
  _jitter(i) {
    const a = Math.sin(i * 78.233) * 43758.5453;
    const b = Math.sin(i * 12.9898) * 24634.6345;
    return { x: (a - Math.floor(a)) - 0.5, r: (b - Math.floor(b)) - 0.5 };
  }
}

const UP_Z = new THREE.Vector3(0, 0, 1);
