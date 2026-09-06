// muriel.spatial — one InstancedMesh carrying an entire image field.
//
// The whole corpus draws in ONE draw call. Per-instance attributes carry which
// atlas slot to sample, which tier that slot lives in, and an opacity — so tier
// promotion, dimming, and the hole punched for a DOM-promoted card are all
// attribute writes, not scene-graph churn.
//
// Tier assignment is a CPU loop over every instance, once per frame. That reads
// alarming and isn't: it is flat arithmetic over typed arrays with no
// allocation and no DOM contact, ~2,500 iterations of a distance compare. The
// thing that actually costs at this count is touching the DOM, which is why the
// DOM tier is a pool of a dozen (see hybrid.js) rather than one node per item.
//
// Exports:
//   TileField — instanced quads + tier management + picking

import * as THREE from 'three';
import { AtlasPair } from './atlas.js';

const VERT = /* glsl */`
attribute float aSlot;
attribute float aTier;
attribute float aOpacity;
attribute vec2  aFit;

varying vec2  vUv;
varying float vSlot;
varying float vTier;
varying float vOpacity;
varying vec2  vFit;

void main() {
  vUv = uv;
  vSlot = aSlot;
  vTier = aTier;
  vOpacity = aOpacity;
  vFit = aFit;
  gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0);
}
`;

const FRAG = /* glsl */`
uniform sampler2D farAtlas;
uniform sampler2D nearAtlas;
uniform vec2 farGrid;
uniform vec2 nearGrid;
uniform vec3 emptyColor;

varying vec2  vUv;
varying float vSlot;
varying float vTier;
varying float vOpacity;
varying vec2  vFit;

void main() {
  if (vOpacity < 0.004) discard;          // DOM twin owns this one

  // Sample the letterboxed sub-rect the atlas actually drew into, centred in
  // the slot, so a slot whose image is a different aspect than the quad shows
  // the picture uncropped rather than stretched.
  vec2 inner = (vec2(1.0) - vFit) * 0.5 + vUv * vFit;

  bool near = vTier > 0.5;
  vec2 grid = near ? nearGrid : farGrid;
  float col = mod(vSlot, grid.x);
  float row = floor(vSlot / grid.x);

  // CanvasTexture uploads with flipY, so canvas row 0 (top) is the HIGH v end.
  vec2 uv = vec2(
    (col + inner.x) / grid.x,
    1.0 - (row + 1.0 - inner.y) / grid.y
  );

  vec4 c = near ? texture2D(nearAtlas, uv) : texture2D(farAtlas, uv);

  // A slot that has not loaded yet is transparent. Painting a flat placeholder
  // rather than discarding keeps the field's shape legible while it streams —
  // a wall that pops into existence tile by tile reads as broken.
  if (c.a < 0.02) c = vec4(emptyColor, 0.55);

  gl_FragColor = vec4(c.rgb, c.a * vOpacity);
}
`;

export class TileField {
  /**
   * @param {object} opts
   * @param {THREE.Scene} opts.scene
   * @param {number} opts.count
   * @param {(index:number, tier:'far'|'near') => (string|null)} opts.resolve
   * @param {number} [opts.nearDistance] world distance inside which an instance
   *   is promoted to the near atlas
   * @param {number} [opts.nearSlots]
   * @param {number} [opts.farPx]
   * @param {number} [opts.nearPx]
   * @param {number|string} [opts.emptyColor] placeholder for unloaded slots
   */
  constructor({
    scene, count, resolve,
    nearDistance = 1400,
    nearSlots = 256, farPx = 64, nearPx = 256,
    emptyColor = 0x1b2430,
  }) {
    this.count = count;
    this.nearDistance = nearDistance;

    this.atlases = new AtlasPair({ count, farPx, nearPx, nearSlots, resolve });

    const geo = new THREE.PlaneGeometry(1, 1);
    this.aSlot = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    this.aTier = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    this.aOpacity = new THREE.InstancedBufferAttribute(new Float32Array(count).fill(1), 1);
    this.aFit = new THREE.InstancedBufferAttribute(new Float32Array(count * 2).fill(1), 2);
    geo.setAttribute('aSlot', this.aSlot);
    geo.setAttribute('aTier', this.aTier);
    geo.setAttribute('aOpacity', this.aOpacity);
    geo.setAttribute('aFit', this.aFit);

    this.material = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      transparent: true,
      // Written but not tested against: the field is drawn back-to-front by
      // the camera-distance sort, and depth-writing transparent quads punch
      // holes in whatever draws after them.
      depthWrite: false,
      uniforms: {
        farAtlas:   { value: this.atlases.far.texture },
        nearAtlas:  { value: this.atlases.near.texture },
        farGrid:    { value: new THREE.Vector2(this.atlases.far.cols, this.atlases.far.rows) },
        nearGrid:   { value: new THREE.Vector2(this.atlases.near.cols, this.atlases.near.rows) },
        emptyColor: { value: new THREE.Color(emptyColor) },
      },
    });

    this.mesh = new THREE.InstancedMesh(geo, this.material, count);
    this.mesh.frustumCulled = false;   // bounds are set by layout(), not geometry
    this.mesh.renderOrder = 0;
    scene.add(this.mesh);

    this._m = new THREE.Matrix4();
    this._q = new THREE.Quaternion();
    this._p = new THREE.Vector3();
    this._s = new THREE.Vector3(1, 1, 1);
    // Instance centres in world space, kept CPU-side so the per-frame tier pass
    // never has to decompose a matrix. Sizes and orientations are kept for the
    // same reason plus one more: a DOM twin has to land exactly where its quad
    // was, and decomposing an instance matrix per promotion to find out is
    // wasted work when placement already knew.
    this.centres = new Float32Array(count * 3);
    this.sizes = new Float32Array(count * 2);
    this.rotations = new Float32Array(count * 4);
    this._tierDirty = false;
    this._suppressed = new Uint8Array(count);   // 1 = a DOM twin owns it

    this.atlases.onTileReady = (index, tier) => this._onTileReady(index, tier);
  }

  /**
   * Place one instance. `rotation` is optional and takes a Quaternion.
   * Call layout() when the whole field has been placed.
   */
  place(index, x, y, z, width, height, rotation = null) {
    this._p.set(x, y, z);
    this._q.identity();
    if (rotation) this._q.copy(rotation);
    this._s.set(width, height, 1);
    this._m.compose(this._p, this._q, this._s);
    this.mesh.setMatrixAt(index, this._m);
    this.centres[index * 3] = x;
    this.centres[index * 3 + 1] = y;
    this.centres[index * 3 + 2] = z;
    this.sizes[index * 2] = width;
    this.sizes[index * 2 + 1] = height;
    this.rotations[index * 4] = this._q.x;
    this.rotations[index * 4 + 1] = this._q.y;
    this.rotations[index * 4 + 2] = this._q.z;
    this.rotations[index * 4 + 3] = this._q.w;
  }

  /** World width of an instance — how wide its DOM twin must be scaled. */
  widthOf(index) { return this.sizes[index * 2]; }

  /** Width/height of an instance, so a DOM twin can match its shape. */
  aspectOf(index) {
    const h = this.sizes[index * 2 + 1];
    return h > 0 ? this.sizes[index * 2] / h : 1;
  }

  /** Copy an instance's orientation into `out`. */
  orientationOf(index, out) {
    return out.set(
      this.rotations[index * 4],
      this.rotations[index * 4 + 1],
      this.rotations[index * 4 + 2],
      this.rotations[index * 4 + 3],
    );
  }

  /** Commit placements and recompute bounds for raycasting. */
  layout() {
    this.mesh.instanceMatrix.needsUpdate = true;
    this.mesh.computeBoundingSphere();
  }

  /**
   * Hide an instance because a DOM element is standing in for it. The instance
   * keeps its slot — demotion is then instant, with no reload.
   */
  suppress(index, on) {
    const v = on ? 1 : 0;
    if (this._suppressed[index] === v) return;
    this._suppressed[index] = v;
    this.aOpacity.array[index] = on ? 0 : 1;
    this.aOpacity.needsUpdate = true;
  }

  /**
   * Per-frame tier pass: promote what is near the camera to the big atlas,
   * demote what has left. Returns the number of near-tier residents.
   */
  update(camera, now = performance.now()) {
    const cx = camera.position.x, cy = camera.position.y, cz = camera.position.z;
    const near2 = this.nearDistance * this.nearDistance;
    const c = this.centres;
    const tier = this.aTier.array;
    const slots = this.aSlot.array;
    let resident = 0;

    for (let i = 0; i < this.count; i++) {
      if (this._suppressed[i]) continue;
      const dx = c[i * 3] - cx, dy = c[i * 3 + 1] - cy, dz = c[i * 3 + 2] - cz;
      const d2 = dx * dx + dy * dy + dz * dz;

      if (d2 <= near2) {
        resident++;
        const slot = this.atlases.request(i, 'near', now);
        if (slot >= 0) {
          if (tier[i] !== 1 || slots[i] !== slot) {
            tier[i] = 1; slots[i] = slot; this._tierDirty = true;
            this._copyFit(i, 'near', slot);
          }
          continue;
        }
        // Pool exhausted — fall through to the far tier rather than blanking.
      } else if (this.atlases.nearSlot[i] >= 0) {
        this.atlases.releaseNear(i);
      }

      const farSlot = this.atlases.request(i, 'far', now);
      if (tier[i] !== 0 || slots[i] !== farSlot) {
        tier[i] = 0;
        slots[i] = Math.max(0, farSlot);
        this._tierDirty = true;
        this._copyFit(i, 'far', farSlot);
      }
    }

    if (this._tierDirty) {
      this.aTier.needsUpdate = true;
      this.aSlot.needsUpdate = true;
      this._tierDirty = false;
    }
    this.atlases.flush(now);
    return resident;
  }

  _copyFit(index, tier, slot) {
    if (slot < 0) return;
    const atlas = tier === 'near' ? this.atlases.near : this.atlases.far;
    this.aFit.array[index * 2] = atlas.fits[slot * 2];
    this.aFit.array[index * 2 + 1] = atlas.fits[slot * 2 + 1];
    this.aFit.needsUpdate = true;
  }

  _onTileReady(index, tier) {
    const slot = tier === 'near' ? this.atlases.nearSlot[index] : this.atlases.farSlot[index];
    const isNear = tier === 'near';
    // Only adopt the tile if the instance is currently showing that tier —
    // a far tile arriving after promotion must not clobber the near slot.
    if ((this.aTier.array[index] > 0.5) === isNear) this._copyFit(index, tier, slot);
  }

  /**
   * Which instance is under a normalized-device-coords pointer, or -1.
   * O(count) triangle tests — fine on click, throttle it on hover.
   */
  pick(raycaster) {
    const hits = raycaster.intersectObject(this.mesh, false);
    for (const hit of hits) {
      if (hit.instanceId === undefined) continue;
      if (this._suppressed[hit.instanceId]) continue;   // DOM twin takes the click
      return hit.instanceId;
    }
    return -1;
  }

  /** VRAM held by the atlases. Flat in `count` above the far tier. */
  get bytes() { return this.atlases.bytes; }

  dispose() {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.mesh.removeFromParent();
    this.atlases.dispose();
  }
}
