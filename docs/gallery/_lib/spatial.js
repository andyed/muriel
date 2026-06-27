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
} = {}) {
  const scene = new THREE.Scene();
  scene.background = null;

  const camera = new THREE.PerspectiveCamera(
    fov, window.innerWidth / window.innerHeight, near, far,
  );
  camera.position.set(...cameraPos);
  camera.lookAt(...lookAt);

  const webglRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  webglRenderer.setPixelRatio(window.devicePixelRatio || 1);
  webglRenderer.setSize(window.innerWidth, window.innerHeight);
  webglRenderer.setClearColor(0x000000, 0);
  document.querySelector(webglMount).appendChild(webglRenderer.domElement);

  const cssRenderer = new CSS3DRenderer();
  cssRenderer.setSize(window.innerWidth, window.innerHeight);
  document.querySelector(cssMount).appendChild(cssRenderer.domElement);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    webglRenderer.setSize(window.innerWidth, window.innerHeight);
    cssRenderer.setSize(window.innerWidth, window.innerHeight);
  });

  return { scene, camera, webglRenderer, cssRenderer };
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

export function makePlane(html, {
  x = 0, y = 0, z = 0,
  rotX = 0, rotY = 0, rotZ = 0,
  className = 'plane',
  width = null,
} = {}) {
  const el = document.createElement('div');
  el.className = className;
  if (width) el.style.width = width + 'px';
  el.innerHTML = html;
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
    scene.traverse((o) => {
      if (o.element && o.visible) {
        o.element.style.zIndex =
          String(Math.round(1e6 - camera.position.distanceTo(o.getWorldPosition(_zTmp))));
      }
    });
    webglRenderer.render(scene, camera);
    cssRenderer.render(scene, camera);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
  return cam;  // consumers can read/poke this
}

export { THREE, CSS3DObject };
