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
   * @param {number} [opts.maxVisibleInPile] cards drawn proud of the stack
   *   before the rest are hidden behind the top of it.
   */
  constructor({
    field, surface = null, aspectOf,
    stackOffset = 3.2,
    maxVisibleInPile = 24,
  }) {
    this.field = field;
    this.surface = surface;
    this.aspectOf = aspectOf;
    this.stackOffset = stackOffset;
    this.maxVisibleInPile = maxVisibleInPile;

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
  collapse(pileIndex, immediate = false) {
    const pile = this.piles[pileIndex];
    if (!pile) return;
    pile.state = PILED;
    if (this.spreadPile === pileIndex) this.spreadPile = -1;

    const n = pile.indices.length;
    for (let k = 0; k < n; k++) {
      const i = pile.indices[k];
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
      const z = p.z + (this.maxVisibleInPile - shown) * this.stackOffset;
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
    const cellW = cardH * 1.5 + gap;
    const originU = pile.u - (cols - 1) * cellW / 2;
    const originV = pile.v + (rows - 1) * (cardH + gap) / 2;

    for (let k = 0; k < n; k++) {
      const i = pile.indices[k];
      const col = k % cols;
      const row = Math.floor(k / cols);
      const w = cardH * this.aspectOf(i);
      const p = this._world(originU + col * cellW, originV - row * (cardH + gap), cardH);
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
