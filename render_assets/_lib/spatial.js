// muriel.spatial — shared JS helpers for the 3D-typography demos.
//
// Each consumer page sets up its own importmap pointing 'three' at a
// CDN; this module's `import * as THREE from 'three'` resolves through
// that map. The lib has no other build dependency.
//
// Exports:
//   createScene({...})           — scene + camera + dual renderers + resize
//   Mountain                     — tilted plane group + grid + zones + planeToWorld
//   addFloorGrid(scene, {...})   — flat X-Z grid at given y
//   addHorizon(scene, {...})     — single horizon line segment
//   makePlane(html, {...})       — CSS3DObject wrapper for any DIV
//   FocusController              — click-to-focus animation (mountain demos)
//   startRenderLoop({...})       — parallax + auto-orbit + render
//   THREE, CSS3DObject           — re-exports
//
// For fields of more than a few hundred items, one CSS3DObject per item is the
// wrong shape — see instanced.js (GPU quads) and hybrid.js (a small DOM pool
// lent to whatever is close enough to read). This module stays the scene,
// camera, geometry and camera-motion layer for both.

import * as THREE from 'three';
import {
  CSS3DRenderer, CSS3DObject,
} from 'three/addons/renderers/CSS3DRenderer.js';

// ─── Scene boilerplate ──────────────────────────────────────────────

export function createScene({
  webglMount = '#webgl',
  cssMount   = '#css3d',
  fov        = 48,
  cameraPos  = [0, 170, 780],
  lookAt     = [0, 130, -300],
  near       = 1,
  far        = 8000,
  // Size to this element instead of the window. A full-page demo wants the
  // window; a scene embedded in an app pane needs the pane, or it renders at
  // viewport size behind a smaller container and every pointer coordinate is
  // wrong. Accepts an element or a selector.
  container  = null,
} = {}) {
  const box = typeof container === 'string'
    ? document.querySelector(container)
    : container;
  const measure = () => (box
    ? { w: box.clientWidth || 1, h: box.clientHeight || 1 }
    : { w: window.innerWidth, h: window.innerHeight });

  const scene = new THREE.Scene();
  scene.background = null;

  let { w, h } = measure();
  const camera = new THREE.PerspectiveCamera(fov, w / h, near, far);
  camera.position.set(...cameraPos);
  camera.lookAt(...lookAt);

  const webglRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  webglRenderer.setPixelRatio(window.devicePixelRatio || 1);
  webglRenderer.setSize(w, h);
  webglRenderer.setClearColor(0x000000, 0);
  document.querySelector(webglMount).appendChild(webglRenderer.domElement);

  const cssRenderer = new CSS3DRenderer();
  cssRenderer.setSize(w, h);
  document.querySelector(cssMount).appendChild(cssRenderer.domElement);

  const resize = () => {
    ({ w, h } = measure());
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    webglRenderer.setSize(w, h);
    cssRenderer.setSize(w, h);
  };
  window.addEventListener('resize', resize);
  // A container can change size without the window doing so — a collapsing
  // sidebar, a detail panel opening. ResizeObserver catches what resize misses.
  if (box && typeof ResizeObserver !== 'undefined') {
    new ResizeObserver(resize).observe(box);
  }

  return { scene, camera, webglRenderer, cssRenderer, resize, measure };
}

// ─── Mountain — tilted grid plane + zones ───────────────────────────

export class Mountain {
  constructor({
    scene, tilt = Math.PI * 0.115, y = 60,
    width = 1900, depth = 1700,
    cols = 30, rows = 26,
    color = 0x7fdfff, opacity = 0.32,
  } = {}) {
    this.tilt = tilt;
    this.sinT = Math.sin(tilt);
    this.cosT = Math.cos(tilt);
    this.group = new THREE.Group();
    this.group.rotation.x = tilt;
    this.group.position.y = y;
    scene.add(this.group);
    this.group.add(this._makeGrid({ width, depth, cols, rows, color, opacity }));
  }

  _makeGrid({ width, depth, cols, rows, color, opacity }) {
    const halfW = width / 2;
    const positions = [];
    const stepZ = depth / rows;
    for (let i = 0; i <= rows; i++) {
      const z = -i * stepZ;
      positions.push(-halfW, 0, z,  halfW, 0, z);
    }
    const stepX = width / cols;
    for (let i = 0; i <= cols; i++) {
      const x = -halfW + i * stepX;
      positions.push(x, 0, 0,  x, 0, -depth);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position',
      new THREE.Float32BufferAttribute(positions, 3));
    const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
    return new THREE.LineSegments(geo, mat);
  }

  // Coloured elliptical region painted on the mountain — the original
  // Data Mountain (Robertson/Dumais 1998) used carpet zones for
  // sub-clustering. Pass plane coords (u, v); rx/ry are the radii.
  zone({ u, v, rx = 280, ry = 200, color = 0x7fdfff, opacity = 0.08 } = {}) {
    const segments = 48;
    const shape = new THREE.Shape();
    for (let i = 0; i <= segments; i++) {
      const a = (i / segments) * Math.PI * 2;
      const x = u + Math.cos(a) * rx;
      const z = v + Math.sin(a) * ry;
      if (i === 0) shape.moveTo(x, z);
      else         shape.lineTo(x, z);
    }
    const geo = new THREE.ShapeGeometry(shape);
    const mat = new THREE.MeshBasicMaterial({
      color, transparent: true, opacity,
      depthWrite: false, side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.rotation.x = -Math.PI / 2;
    this.group.add(mesh);
    return mesh;
  }

  // Project a (u, v) plane coord into world space. Cards stand upright
  // on the plane: world Y is offset by half the card height so the
  // bottom edge sits on the tilted surface.
  planeToWorld(u, v, cardHeight = 0) {
    return new THREE.Vector3(
      u,
      this.group.position.y + (-v) * this.sinT + cardHeight / 2,
      v * this.cosT,
    );
  }

  /**
   * Lay out a whole corpus on the slope, front to back.
   *
   * The original Data Mountain (Robertson / Czerwinski / Larson / Robbins /
   * Thiel / van Dantzich, UIST 1998) had the *user* place ~100 pages by hand —
   * the spatial memory being tested was theirs. A corpus of thousands cannot be
   * hand-placed, so the slope has to earn its depth some other way: order
   * carries the meaning, and depth carries the ordering.
   *
   * Rows are justified — each row filled to the plane's width — with the target
   * height shrinking toward the back. That is the same rule a flat justified
   * wall uses, with one addition: because far rows are smaller AND further up
   * the tilted plane, they foreshorten twice, so a back row costs very little
   * screen area while staying present as context. That double falloff is the
   * whole reason to put a wall on a slope rather than leave it flat.
   *
   * @param {number} count
   * @param {(i:number) => number} aspectOf  width/height of item i
   * @returns {Array<{u:number, v:number, w:number, h:number, row:number, depth:number}>}
   *   `depth` is 0 at the front edge and 1 at the back, for consumers that want
   *   to dim, thin, or drop detail with distance.
   */
  arrange(count, aspectOf, {
    width = 1900, depth = 1700,
    frontH = 210, backH = 64,
    gap = 16, rowGap = 26,
    fit = true,
    overlap = 0,
  } = {}) {
    // Negative gap shingles the tiles like roof slates or a fanned deck. It is
    // a real information channel and not only a look: overlap orders the row,
    // because what covers what is unambiguous, where a gapped row is just
    // adjacency. It needs the depth buffer to be correct, which is why the
    // field stopped alpha-blending.
    if (overlap) gap = -Math.abs(overlap);
    if (!fit) return this._pack(count, aspectOf, { width, depth, frontH, backH, gap, rowGap }, 1).out;

    // Fit every item inside `depth`. Without this the row profile clamps at the
    // back and rows simply keep marching past the plane: at 2,500 items a
    // 2,600-deep slope ran to 7,242 and stranded 36% of the corpus off the end,
    // while the surviving ramp was so long the tilt read as a flat floor.
    //
    // Shrinking the height profile puts more items per row AND makes each row
    // shallower, so depth used falls monotonically as scale falls — which is
    // what makes a binary search valid here.
    let lo = 0.04, hi = 1;
    let best = this._pack(count, aspectOf, { width, depth, frontH, backH, gap, rowGap }, lo);
    if (this._pack(count, aspectOf, { width, depth, frontH, backH, gap, rowGap }, hi).usedDepth <= depth) {
      best = this._pack(count, aspectOf, { width, depth, frontH, backH, gap, rowGap }, hi);
    } else {
      for (let i = 0; i < 18; i++) {
        const mid = (lo + hi) / 2;
        const trial = this._pack(count, aspectOf, { width, depth, frontH, backH, gap, rowGap }, mid);
        if (trial.usedDepth <= depth) { best = trial; lo = mid; } else { hi = mid; }
      }
    }
    return best.out;
  }

  /**
   * One packing pass at a given height scale.
   * @returns {{out: Array, usedDepth: number}} every item placed, and how deep
   *   the slope had to be to hold them.
   */
  _pack(count, aspectOf, o, scale) {
    const { width, depth, gap, rowGap } = o;
    const frontH = o.frontH * scale;
    const backH = o.backH * scale;
    const out = [];
    const halfW = width / 2;
    let v = 0;
    let i = 0;
    let row = 0;

    while (i < count) {
      const t = Math.min(1, -v / depth);
      const targetH = frontH + (backH - frontH) * t;

      const start = i;
      let sumAspect = 0;
      while (i < count) {
        sumAspect += aspectOf(i);
        i++;
        if (sumAspect * targetH + gap * (i - start - 1) >= width) break;
      }
      const n = i - start;
      const h = (width - gap * (n - 1)) / sumAspect;
      const rowH = (i >= count && h > targetH * 1.45) ? targetH : h;

      let u = -halfW;
      for (let k = start; k < i; k++) {
        const w = aspectOf(k) * rowH;
        out.push({ u: u + w / 2, v, w, h: rowH, row, depth: Math.min(1, -v / depth) });
        u += w + gap;
      }

      v -= rowH + rowGap;
      row++;
    }
    return { out, usedDepth: -v };
  }
}

// ─── Standalone grid + horizon helpers ──────────────────────────────

export function addFloorGrid(scene, {
  halfWidth = 2000, divisions = 32, y = 0,
  color = 0x7fdfff, opacity = 0.10,
} = {}) {
  const step = (halfWidth * 2) / divisions;
  const positions = [];
  for (let i = 0; i <= divisions; i++) {
    const z = -halfWidth + i * step;
    positions.push(-halfWidth, y, z,  halfWidth, y, z);
  }
  for (let i = 0; i <= divisions; i++) {
    const x = -halfWidth + i * step;
    positions.push(x, y, -halfWidth,  x, y, halfWidth);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position',
    new THREE.Float32BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
  const lines = new THREE.LineSegments(geo, mat);
  scene.add(lines);
  return lines;
}

export function addHorizon(scene, {
  y = 920, z = -1200, halfWidth = 3000,
  color = 0xff5fa2, opacity = 0.45,
} = {}) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(
    [-halfWidth, y, z,  halfWidth, y, z], 3));
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity });
  const line = new THREE.Line(geo, mat);
  scene.add(line);
  return line;
}

// ─── CSS3D wrapper ──────────────────────────────────────────────────

/**
 * Wrap markup or a node in a CSS3DObject.
 *
 * Pass a string for authored markup you control. Pass a Node — or an array of
 * them — for anything derived from data you did not write: the string path
 * goes through innerHTML, and a consumer rendering scraped third-party titles
 * must not have an innerHTML path available to it at all.
 */
export function makePlane(content, {
  x = 0, y = 0, z = 0,
  rotX = 0, rotY = 0, rotZ = 0,
  className = 'plane',
  width = null,
} = {}) {
  const el = document.createElement('div');
  el.className = className;
  if (width) el.style.width = width + 'px';
  if (typeof content === 'string') el.innerHTML = content;
  else if (Array.isArray(content)) el.append(...content);
  else if (content) el.append(content);
  const obj = new CSS3DObject(el);
  obj.position.set(x, y, z);
  if (rotX) obj.rotation.x = rotX;
  if (rotY) obj.rotation.y = rotY;
  if (rotZ) obj.rotation.z = rotZ;
  return obj;
}

// ─── Click-to-focus animation (mountain-style) ──────────────────────

export class FocusController {
  constructor({
    focusPos = new THREE.Vector3(0, 160, 420),
    duration = 600,
    featureClass = 'featured',
  } = {}) {
    this.focusPos = focusPos;
    this.duration = duration;
    this.featureClass = featureClass;
    this.focused = null;
  }

  // Attach click handlers to a list of CSS3DObjects. Each card's
  // base position is captured so unfocus can return it home.
  bind(cards) {
    for (const card of cards) {
      card.userData.basePos = card.position.clone();
      card.element.addEventListener('click', (e) => {
        // Debug aid — if clicks aren't reaching here, something above
        // (HUD, legend, sibling card) is intercepting in screen space.
        console.log('[focus] click on', card.userData.title || card.userData.name || '?',
                    'at world', card.position.toArray().map(v => v.toFixed(0)));
        this.toggle(card);
      });
    }
  }

  toggle(card) {
    if (this.focused && this.focused !== card) this.unfocus(this.focused);
    if (this.focused === card) { this.unfocus(card); return; }
    this.focused = card;
    card.element.classList.add(this.featureClass);
    this._animate(card, this.focusPos);
  }

  unfocus(card) {
    // Keep the featured flag on cards that were authored as featured.
    if (!card.userData.featured) {
      card.element.classList.remove(this.featureClass);
    }
    this._animate(card, card.userData.basePos);
    if (this.focused === card) this.focused = null;
  }

  _animate(obj, target) {
    const start = obj.position.clone();
    const t0 = performance.now();
    const dur = this.duration;
    function step(now) {
      const t = Math.min(1, (now - t0) / dur);
      // ease-out cubic
      const e = 1 - Math.pow(1 - t, 3);
      obj.position.lerpVectors(start, target, e);
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
}

// ─── Render loop with parallax + auto-orbit ─────────────────────────

export function startRenderLoop({
  scene, camera, webglRenderer, cssRenderer,
  basePos    = new THREE.Vector3(0, 170, 780),
  lookTarget = new THREE.Vector3(0, 130, -300),
  fovParallax     = { x: 180, y: 90 },
  idleMs          = 6000,
  autoOrbit       = { radius: 260, yAmp: 38, speed: 0.0010 },
  dollyRange      = [-300, 700],
  cameraLerp      = 0.06,
  lookXAmount     = 60,
  lookYAmount     = 40,
  beforeRender    = null,      // hook for per-card lerps etc.
  onKeydown       = null,      // hook for app-specific key handling
  // Depth-order the CSS3D cards. The default walks the scene and writes a
  // zIndex for every visible card, every frame — correct and cheap for the
  // dozen-card demos, and quadratically wrong past a few hundred, where it
  // becomes thousands of style writes per frame. A high-count consumer passes
  // its own (see HybridField.sort, which is bounded by the DOM pool).
  sortDom         = null,
} = {}) {
  const cam = {
    mx: 0, my: 0, dolly: 0,
    lastInput: performance.now(),
    autoOrbit: false,
    orbitAngle: 0,
  };
  window.addEventListener('mousemove', (e) => {
    cam.mx = (e.clientX / window.innerWidth) * 2 - 1;
    cam.my = (e.clientY / window.innerHeight) * 2 - 1;
    cam.lastInput = performance.now();
    cam.autoOrbit = false;
  });
  window.addEventListener('wheel', (e) => {
    cam.dolly = Math.max(dollyRange[0], Math.min(dollyRange[1],
      cam.dolly + e.deltaY * 0.5));
    cam.lastInput = performance.now();
    e.preventDefault();
  }, { passive: false });
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
      cam.autoOrbit = !cam.autoOrbit;
      e.preventDefault();
    }
    if (onKeydown) onKeydown(e, cam);
  });
  const tmpPos = new THREE.Vector3();
  const tmpLook = new THREE.Vector3();
  const _zTmp = new THREE.Vector3();
  function tick(now) {
    if (beforeRender) beforeRender(now);
    const idle = (now - cam.lastInput) > idleMs;
    if (idle && !cam.autoOrbit) cam.autoOrbit = true;
    let tx = cam.mx * fovParallax.x;
    let ty = basePos.y - cam.my * fovParallax.y;
    let tz = basePos.z + cam.dolly;
    if (cam.autoOrbit) {
      cam.orbitAngle += autoOrbit.speed;
      tx = Math.sin(cam.orbitAngle) * autoOrbit.radius;
      ty = basePos.y + Math.sin(cam.orbitAngle * 0.7) * autoOrbit.yAmp;
    }
    tmpPos.set(tx, ty, tz);
    camera.position.lerp(tmpPos, cameraLerp);
    tmpLook.set(
      cam.mx * lookXAmount,
      lookTarget.y + (-cam.my * lookYAmount),
      lookTarget.z,
    );
    camera.lookAt(tmpLook);
    // CSS3DRenderer does NOT depth-sort. Assign zIndex by camera distance so the
    // nearest card always paints on top. Without this, cards flattened by
    // opacity/filter (e.g. the distance-dimming .dim-* classes) stack in DOM
    // order and a far card can sit above the focused one. Harmless for
    // non-flattened cards (3D position still wins).
    if (sortDom) {
      sortDom(camera);
    } else {
      scene.traverse((o) => {
        if (o.element && o.visible) {
          o.element.style.zIndex =
            String(Math.round(1e6 - camera.position.distanceTo(o.getWorldPosition(_zTmp))));
        }
      });
    }
    webglRenderer.render(scene, camera);
    cssRenderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  return cam;  // consumers can read/poke this
}

export { THREE, CSS3DObject };
