# PixiJS — 2D WebGL/WebGPU substrate

> **Credit up front:** this vocabulary is a curated subset of the upstream [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) documentation (MIT). We didn't write it — we picked the patterns relevant to muriel and pointed at the source. The hard work of documenting v8's API lives there; this file is a thin on-ramp and a reminder of when to reach for the library at all. When in doubt, read upstream.

**When to reach for it.** PixiJS is the right tool when vanilla Canvas / D3 / SVG runs out of headroom and Three.js is overkill. It's a fast 2D renderer with a batched scene graph on WebGL 1/2, WebGPU, and Canvas fallback. No 3D scene graph, no physics, no camera rig — just high-performance 2D.

Use it for:

- **Particle-dense gaze visualizations** — `ParticleContainer` renders 10k+ fixations in one draw call.
- **Shader-driven heatmaps and foveation demos** — `Filter.from({ gl, resources })` accepts GLSL ES 3.0 fragments with `uBackTexture` for back-buffer sampling.
- **Audio-reactive interactive demos** — ticker-driven uniform updates, blend modes, and particle pools without dropping frames on 60Hz.
- **Sprite-dense editorial pieces** — where `<canvas>` + raw draw calls would batch poorly and `<svg>` with thousands of nodes would freeze the DOM.

Don't reach for it when:

- The output is a static raster. Use Pillow (`channels/raster.md`) — PixiJS adds GPU setup cost for zero benefit on still images.
- The piece is information-dense typography with linked selection. Use D3 + SVG (`channels/svg.md`, `channels/interactive.md`) — the DOM is your friend for brushing and accessibility.
- You need 3D. Use Three.js; PixiJS is explicitly 2D.

## Version and licensing

- Pin to **PixiJS `^8.18`**. v8 is the current stable line (v8.18.1 shipped 2026-04-14); no v9 on the horizon.
- PixiJS is MIT. The [pixijs-skills](https://github.com/pixijs/pixijs-skills) repo is also MIT. Safe to vendor curated excerpts here; upstream is the source of truth.

## Quick start (v8)

```ts
import { Application } from "pixi.js";

const app = new Application();
await app.init({ width: 800, height: 600, background: "#0a0a0f" });
document.body.appendChild(app.canvas);
```

Three non-obvious v8 traps:

1. **Constructor takes no arguments.** All options go through the async `app.init()` call. Passing options to `new Application(...)` silently logs a deprecation warning and ignores them.
2. **`app.canvas`, not `app.view`.** The v7 name is gone.
3. **`app.destroy({ releaseGlobalResources: true })`** on teardown, or stale textures persist across re-inits (common in HMR/demo loops).

## Primitives worth knowing

Pull the upstream skill file from [pixijs-skills](https://github.com/pixijs/pixijs-skills/tree/main/skills) when you need depth. The render-relevant subset:

| Upstream skill | When to read |
|---|---|
| `pixijs-application` | Init, resize, lifecycle, `app.destroy()` |
| `pixijs-core-concepts` | Scene graph mental model |
| `pixijs-scene-sprite` | Image + animated sprites |
| `pixijs-scene-graphics` | Vector drawing, shapes, stroke/fill |
| `pixijs-scene-text` | Bitmap + SDF text rendering |
| `pixijs-scene-particle-container` | 10k+ sprites in one draw call — see below |
| `pixijs-scene-mesh` | Custom geometry, quads with custom attributes |
| `pixijs-filters` | Built-in effects (blur, color-matrix, displacement, noise) |
| `pixijs-blend-modes` | Screen, multiply, add — audio-reactive grammar |
| `pixijs-custom-rendering` | Writing GLSL/WGSL shaders — see below |

Skip for muriel's purposes: `pixijs-migration-v8`, `pixijs-environments`, `pixijs-accessibility`, `pixijs-events`, `pixijs-ticker`, `pixijs-create`, `pixijs-math`, `pixijs-color`, `pixijs-assets` (nice-to-know, not load-bearing).

## Pattern: particle gaze overlay

For 10k-fixation visualizations where SVG freezes and Canvas batches poorly.

```ts
import { Application, Assets, Particle, ParticleContainer, Rectangle } from "pixi.js";

const app = new Application();
await app.init({ width: 1920, height: 1080, background: "#0a0a0f" });
document.body.appendChild(app.canvas);

const texture = await Assets.load("dot.png");  // single shared atlas

const particles = new ParticleContainer({
  texture,
  boundsArea: new Rectangle(0, 0, app.screen.width, app.screen.height),
  dynamicProperties: { position: true, color: true },  // mark only what animates
});

for (const fixation of fixations) {
  particles.addParticle(new Particle({
    texture,
    x: fixation.x,
    y: fixation.y,
    anchorX: 0.5,
    anchorY: 0.5,
    scaleX: Math.log(fixation.duration_ms) / 4,
    scaleY: Math.log(fixation.duration_ms) / 4,
    tint: 0xe6e4d2,     // OLED cream
    alpha: 0.4,
  }));
}

app.stage.addChild(particles);
```

Traps:

- **Must set `boundsArea`** or the container is culled as invisible and `containsPoint` always misses.
- **Use `addParticle`, not `addChild`.** `ParticleContainer` rejects `Sprite` children in v8 (hard break from v7).
- **All particles share one base texture source.** Atlases work; unrelated textures do not.
- **Mark only animated properties as `dynamicProperties: true`.** Static properties are cheaper. If you mutate a static property at runtime, call `container.update()` once.
- For bulk mutation, push directly to `container.particleChildren` and call `update()` once, rather than calling `addParticle` per item.

## Pattern: shader-driven filter with back-buffer sampling

For foveation demos where the filter needs to read already-rendered pixels behind it.

```ts
import { Filter } from "pixi.js";

const foveationFragment = `
  in vec2 vTextureCoord;
  out vec4 finalColor;
  uniform sampler2D uTexture;
  uniform sampler2D uBackTexture;
  uniform vec2 uFovea;
  uniform float uRadius;

  void main(void) {
    vec4 src = texture(uTexture, vTextureCoord);
    vec4 back = texture(uBackTexture, vTextureCoord);
    float d = distance(vTextureCoord, uFovea);
    float blur = smoothstep(uRadius, uRadius * 2.0, d);
    finalColor = mix(src, back, blur);
  }
`;

const foveation = Filter.from({
  gl: { fragment: foveationFragment },
  resources: {
    uniforms: {
      uFovea:  { value: new Float32Array([0.5, 0.5]), type: "vec2<f32>" },
      uRadius: { value: 0.15, type: "f32" },
    },
  },
  blendRequired: true,  // populates uBackTexture each frame
});

sprite.filters = [foveation];

app.ticker.add(() => {
  foveation.resources.uniforms.uniforms.uFovea[0] = mouseXNormalized;
  foveation.resources.uniforms.uniforms.uFovea[1] = mouseYNormalized;
});
```

v8 shader traps:

- **GLSL ES 3.0 conventions.** `in`/`out` (not `varying`/`attribute`), `texture()` (not `texture2D()`), `out vec4 finalColor` (not `gl_FragColor`).
- **Every uniform needs `{ value, type }`.** `{ uTime: 1 }` throws; must be `{ uTime: { value: 1, type: "f32" } }`.
- **Textures are resources, not uniforms.** Pass `texture.source` and `texture.source.style` as top-level resource entries, not inside a `UniformGroup`.
- **`blendRequired: true`** forces an extra GPU copy per frame to populate `uBackTexture`. Only enable when the effect actually needs it.
- **Strict CSP:** import `pixi.js/unsafe-eval` once at startup if your page blocks `unsafe-eval`, or UBO-backed shaders (and WebGPU) throw on first use.

## Integration with render channels

- **`channels/interactive.md`** — PixiJS is a substrate option alongside vanilla WebGL, Canvas, and D3. Use the single-file scaffold + PermalinkManager pattern; `app.init()` fits into the same mount-point hook.
- **`channels/gaze.md`** — particle container for scanpath and fixation density when fixation counts exceed ~2k.
- **`channels/heatmaps.md`** — Gaussian kernel via fragment shader is faster than Pillow for interactive exploration; keep Pillow for static paper figures.
- **`channels/science.md`** — rarely. Paper figures should be matplotlib or SVG. PixiJS only if the figure is genuinely interactive and lives on the web.

## Upstream

- [pixijs/pixijs-skills](https://github.com/pixijs/pixijs-skills) — full skill set (22 modules), MIT.
- [pixijs/pixijs](https://github.com/pixijs/pixijs) — library source, MIT.
- [pixijs docs](https://pixijs.download/release/docs/index.html) — API reference.
- [pixijs examples](https://pixijs.com/8.x/examples) — canonical demos.
