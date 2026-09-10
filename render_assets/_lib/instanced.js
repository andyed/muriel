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
import { MAX_ROWS } from './motion.js';

const VERT = /* glsl */`
attribute float aSlot;
attribute float aTier;
attribute float aOpacity;
attribute vec2  aFit;
attribute float aRow;

uniform float uRowOffset[MAX_ROWS];
uniform float uRowAngle[MAX_ROWS];
uniform float uWrapSpan;

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

  int row = int(clamp(aRow, 0.0, float(MAX_ROWS - 1)));

  // Displace the instance CENTRE, then rebuild the quad around it. Applying the
  // offset to each vertex independently would be identical here, but rotating
  // is not: a per-vertex angle shears the quad instead of turning it.
  vec3 centre = instanceMatrix[3].xyz;
  vec3 local  = (instanceMatrix * vec4(position, 1.0)).xyz - centre;

  float a = uRowAngle[row];
  float ca = cos(a), sa = sin(a);
  // Turn about Y — the tiles pivot like slats, which is the axis that reads as
  // foreshortening. About Z they would spin in place and read as broken.
  local = vec3(ca * local.x + sa * local.z, local.y, -sa * local.x + ca * local.z);

  centre.x += uRowOffset[row];
  // Wrap the CENTRE, never the vertices: the quad has already been rebuilt
  // around it, so the whole tile crosses the seam in one step instead of
  // tearing in half.
  if (uWrapSpan > 0.0) {
    // Do not name this "half" -- that is a reserved word in GLSL ES, and the
    // shader then silently fails to compile, leaving every CPU-side assertion
    // passing over a field that is not being drawn at all.
    // (No backticks in here either: this comment lives inside a JS template
    // literal, and one would end the string.)
    float halfSpan = uWrapSpan * 0.5;
    centre.x = mod(centre.x + halfSpan, uWrapSpan) - halfSpan;
  }

  gl_Position = projectionMatrix * modelViewMatrix * vec4(centre + local, 1.0);
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

  // No slot: this tile has no image — the load failed, or it has not been
  // requested yet. It must render as ABSENT. Clamping a missing slot to 0
  // instead makes every such tile display slot 0's picture, so a corpus with
  // failures renders as hundreds of copies of one image and looks like a
  // shader bug rather than missing data.
  if (vSlot < 0.0) {
    gl_FragColor = vec4(emptyColor, 1.0);
    return;
  }

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
  if (c.a < 0.02) c = vec4(emptyColor, 1.0);

  gl_FragColor = vec4(c.rgb, c.a * vOpacity);
}
`;

const AXIS_Y = new THREE.Vector3(0, 1, 0);

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
   * @param {(index:number, tier:'far'|'near') => (CanvasImageSource|null)} [opts.resolveSource]
   *   Optional synchronous tile source tried before `resolve`; see AtlasPair
   *   and cards.js.
   * @param {number} [opts.sourceDrawsPerPump]
   */
  constructor({
    scene, count, resolve,
    nearDistance = 1400,
    nearSlots = 256, farPx = 64, nearPx = 256,
    emptyColor = 0x1b2430,
    blend = false,
    resolveSource = null, sourceDrawsPerPump = 16,
  }) {
    this.count = count;
    this.nearDistance = nearDistance;

    this.atlases = new AtlasPair({
      count, farPx, nearPx, nearSlots, resolve, resolveSource, sourceDrawsPerPump,
    });

    const geo = new THREE.PlaneGeometry(1, 1);
    this.aSlot = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    this.aTier = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    this.aOpacity = new THREE.InstancedBufferAttribute(new Float32Array(count).fill(1), 1);
    this.aFit = new THREE.InstancedBufferAttribute(new Float32Array(count * 2).fill(1), 2);
    this.aRow = new THREE.InstancedBufferAttribute(new Float32Array(count), 1);
    geo.setAttribute('aSlot', this.aSlot);
    geo.setAttribute('aTier', this.aTier);
    geo.setAttribute('aOpacity', this.aOpacity);
    geo.setAttribute('aFit', this.aFit);
    geo.setAttribute('aRow', this.aRow);

    // Tiles are photographs: effectively opaque, with the only non-opaque
    // fragments being suppressed instances and unloaded slots, both of which
    // discard outright. So they get the depth buffer rather than blending —
    // an InstancedMesh cannot sort its instances, and instance order here runs
    // FRONT to BACK, meaning a blended field paints far tiles over near ones.
    // Invisible while rows barely overlap; fatal for a pile, which is nothing
    // but overlap.
    //
    // `blend: true` restores the old alpha-blended path for consumers that want
    // smooth per-instance fades and can accept the ordering artifacts.
    this.material = new THREE.ShaderMaterial({
      vertexShader: VERT,
      fragmentShader: FRAG,
      defines: { MAX_ROWS },
      transparent: blend,
      depthWrite: !blend,
      depthTest: true,
      alphaTest: blend ? 0 : 0.5,
      uniforms: {
        farAtlas:   { value: this.atlases.far.texture },
        nearAtlas:  { value: this.atlases.near.texture },
        farGrid:    { value: new THREE.Vector2(this.atlases.far.cols, this.atlases.far.rows) },
        nearGrid:   { value: new THREE.Vector2(this.atlases.near.cols, this.atlases.near.rows) },
        emptyColor: { value: new THREE.Color(emptyColor) },
        uRowOffset: { value: new Float32Array(MAX_ROWS) },
        uRowAngle:  { value: new Float32Array(MAX_ROWS) },
        uWrapSpan:  { value: 0 },
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
    // Animation targets, and the set of instances actually in flight. The set
    // is the point: piles spread, filters re-lay the field, and none of that
    // should cost anything for the instances holding still.
    this.rows = new Float32Array(count);
    this.motion = null;
    this._targets = new Float32Array(count * 6);
    this.targetRot = new Float32Array(count * 4);
    this._moving = new Set();
    this._qa = new THREE.Quaternion();
    this._qb = new THREE.Quaternion();
    this._qRow = new THREE.Quaternion();
    this._qw = new THREE.Quaternion();
    this._pc = new THREE.Vector3();
    this._corner = [
      new THREE.Vector3(), new THREE.Vector3(),
      new THREE.Vector3(), new THREE.Vector3(),
    ];
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

    // Targets mirror the placement unless moveTo() overrides them. Without
    // this, an instance that was only ever placed directly has an all-zero
    // target, and settle() teleports it to the origin at zero size — invisible,
    // silent, and indistinguishable from a failed load.
    if (!this._moving.has(index)) {
      const t = this._targets;
      t[index * 6] = x; t[index * 6 + 1] = y; t[index * 6 + 2] = z;
      t[index * 6 + 3] = width; t[index * 6 + 4] = height;
      this.targetRot[index * 4] = this._q.x;
      this.targetRot[index * 4 + 1] = this._q.y;
      this.targetRot[index * 4 + 2] = this._q.z;
      this.targetRot[index * 4 + 3] = this._q.w;
    }
  }

  /** Tag an instance with the row it belongs to, for row-wise motion. */
  setRow(index, row) {
    this.aRow.array[index] = row;
    this.rows[index] = row;
    this.aRow.needsUpdate = true;
  }

  /** Attach a RowMotion. Pass null to stop animating. */
  setMotion(motion) {
    this.motion = motion;
  }

  /**
   * Push the current row displacement to the GPU. Call once per frame, before
   * anything reads worldCentre().
   */
  applyMotion(dt = 16.7) {
    if (!this.motion) return;
    this.motion.update(dt);
    this.material.uniforms.uRowOffset.value.set(this.motion.offsets);
    this.material.uniforms.uRowAngle.value.set(this.motion.angles);
    this.material.uniforms.uWrapSpan.value = this.motion.wrapSpan || 0;
  }

  /**
   * Where an instance actually IS on screen, base layout plus row motion.
   *
   * Everything that addresses items by position must go through this rather
   * than reading `centres` directly — picking, DOM promotion, keyboard
   * navigation. `centres` is the static layout, and while the field is moving
   * that is a place nothing is.
   */
  worldCentre(index, out) {
    const c = this.centres;
    const x = this.motion
      ? this.motion.wrapX(c[index * 3], this.rows[index])
      : c[index * 3];
    return out.set(x, c[index * 3 + 1], c[index * 3 + 2]);
  }

  /** World width of an instance — how wide its DOM twin must be scaled. */
  widthOf(index) { return this.sizes[index * 2]; }

  /** Width/height of an instance, so a DOM twin can match its shape. */
  aspectOf(index) {
    const h = this.sizes[index * 2 + 1];
    return h > 0 ? this.sizes[index * 2] / h : 1;
  }

  /** Copy an instance's placed orientation into `out`. */
  orientationOf(index, out) {
    return out.set(
      this.rotations[index * 4],
      this.rotations[index * 4 + 1],
      this.rotations[index * 4 + 2],
      this.rotations[index * 4 + 3],
    );
  }

  /**
   * Orientation including the row's angle sweep — what the quad is ACTUALLY
   * showing. A DOM twin using orientationOf() instead sits flat while the
   * quads around it turn, which is more conspicuous than no animation at all.
   */
  worldOrientation(index, out) {
    this.orientationOf(index, out);
    if (!this.motion) return out;
    const a = this.motion.angleFor(this.rows[index]);
    if (!a) return out;
    this._qRow.setFromAxisAngle(AXIS_Y, a);
    return out.premultiply(this._qRow);
  }

  /**
   * Which instance is under a point in normalized device coords, or -1.
   *
   * CPU-side rather than three.js raycasting, because raycasting tests the
   * INSTANCE MATRIX and the instance matrix is the static layout — the row
   * displacement lives in the vertex shader. Raycasting a moving field misses
   * by however far the row has drifted, silently and only while it moves.
   *
   * Projects the four corners of each quad and does a point-in-quad test, so it
   * respects the row angle as well as the offset. ~4 projections per instance
   * on a click, which is nothing at this count.
   */
  pickAt(ndcX, ndcY, camera) {
    let best = -1;
    let bestDepth = Infinity;

    for (let i = 0; i < this.count; i++) {
      if (this._suppressed[i]) continue;      // DOM twin takes the click
      this.worldCentre(i, this._pc);
      this.worldOrientation(i, this._qw);
      const hw = this.sizes[i * 2] / 2;
      const hh = this.sizes[i * 2 + 1] / 2;

      let inside = true;
      let depth = 0;
      for (let k = 0; k < 4; k++) {
        const sx = (k === 0 || k === 3) ? -hw : hw;
        const sy = (k < 2) ? hh : -hh;
        this._corner[k].set(sx, sy, 0).applyQuaternion(this._qw).add(this._pc).project(camera);
        depth += this._corner[k].z;
      }
      depth /= 4;
      if (depth < -1 || depth > 1) continue;

      // Convex point-in-quad: the point must be on the same side of all edges.
      let sign = 0;
      for (let k = 0; k < 4 && inside; k++) {
        const a = this._corner[k];
        const b = this._corner[(k + 1) % 4];
        const cross = (b.x - a.x) * (ndcY - a.y) - (b.y - a.y) * (ndcX - a.x);
        if (cross === 0) continue;
        const s = cross > 0 ? 1 : -1;
        if (sign === 0) sign = s;
        else if (s !== sign) inside = false;
      }
      if (inside && depth < bestDepth) { bestDepth = depth; best = i; }
    }
    return best;
  }

  /** Commit placements and recompute bounds for raycasting. */
  layout() {
    this.mesh.instanceMatrix.needsUpdate = true;
    this.mesh.computeBoundingSphere();
  }

  /**
   * Animate an instance toward a new placement.
   *
   * Piles spread and collapse, groups re-sort, a facet filter re-lays the
   * field — all of which are the same operation: some subset of instances move
   * to new places while everything else holds still. Only moving instances are
   * written, so a settled field costs nothing per frame, and a spreading pile
   * costs its own member count rather than the corpus.
   */
  moveTo(index, x, y, z, width, height, rotation = null) {
    const t = this._targets;
    t[index * 6] = x; t[index * 6 + 1] = y; t[index * 6 + 2] = z;
    t[index * 6 + 3] = width; t[index * 6 + 4] = height;
    if (rotation) {
      this.targetRot[index * 4] = rotation.x;
      this.targetRot[index * 4 + 1] = rotation.y;
      this.targetRot[index * 4 + 2] = rotation.z;
      this.targetRot[index * 4 + 3] = rotation.w;
    } else {
      this.targetRot[index * 4] = this.rotations[index * 4];
      this.targetRot[index * 4 + 1] = this.rotations[index * 4 + 1];
      this.targetRot[index * 4 + 2] = this.rotations[index * 4 + 2];
      this.targetRot[index * 4 + 3] = this.rotations[index * 4 + 3];
    }
    this._moving.add(index);
  }

  /** Snap an instance to its target immediately, cancelling any motion. */
  settle(index) {
    const t = this._targets;
    this._qa.set(this.targetRot[index * 4], this.targetRot[index * 4 + 1],
                 this.targetRot[index * 4 + 2], this.targetRot[index * 4 + 3]);
    this.place(index, t[index * 6], t[index * 6 + 1], t[index * 6 + 2],
               t[index * 6 + 3], t[index * 6 + 4], this._qa);
    this._moving.delete(index);
  }

  /**
   * Advance in-flight placements. `ease` is the fraction of the remaining
   * distance covered this frame — frame-rate corrected so the motion does not
   * change speed with the refresh rate.
   *
   * @returns {number} instances still moving
   */
  tick(dt = 16.7, ease = 0.14) {
    if (!this._moving.size) return 0;
    const k = 1 - Math.pow(1 - ease, dt / 16.7);
    const t = this._targets;
    const c = this.centres;
    const s = this.sizes;

    for (const i of this._moving) {
      const dx = t[i * 6] - c[i * 3];
      const dy = t[i * 6 + 1] - c[i * 3 + 1];
      const dz = t[i * 6 + 2] - c[i * 3 + 2];
      const dw = t[i * 6 + 3] - s[i * 2];
      const dh = t[i * 6 + 4] - s[i * 2 + 1];

      // Settle on a threshold in world units rather than never quite arriving.
      // Without it every animated instance stays in the moving set forever and
      // rewrites its matrix on every frame for the life of the page.
      if (Math.abs(dx) + Math.abs(dy) + Math.abs(dz) + Math.abs(dw) + Math.abs(dh) < 0.5) {
        this.settle(i);
        continue;
      }
      this._qa.set(this.rotations[i * 4], this.rotations[i * 4 + 1],
                   this.rotations[i * 4 + 2], this.rotations[i * 4 + 3]);
      this._qb.set(this.targetRot[i * 4], this.targetRot[i * 4 + 1],
                   this.targetRot[i * 4 + 2], this.targetRot[i * 4 + 3]);
      this._qa.slerp(this._qb, k);
      this.place(i,
        c[i * 3] + dx * k, c[i * 3 + 1] + dy * k, c[i * 3 + 2] + dz * k,
        s[i * 2] + dw * k, s[i * 2 + 1] + dh * k, this._qa);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    return this._moving.size;
  }

  get moving() { return this._moving.size; }

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
        // -1 propagates to the shader as "no image". It must NOT be clamped to
        // 0: slot 0 is a real tile, and aliasing every slotless instance onto
        // it renders the corpus as many copies of whichever image landed there.
        slots[i] = farSlot;
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
   * Raycast pick. Correct only for a field with no row motion — see pickAt(),
   * which is what a moving field must use.
   */
  pick(raycaster) {
    if (this.motion && this.motion.enabled) {
      console.warn('[TileField] pick() ignores row motion; use pickAt(ndcX, ndcY, camera)');
    }
    const hits = raycaster.intersectObject(this.mesh, false);
    for (const hit of hits) {
      if (hit.instanceId === undefined) continue;
      if (this._suppressed[hit.instanceId]) continue;
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
