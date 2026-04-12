# Interactive JS — Live Demo Channel

The biggest win over Photoshop: **parameters the reader can move**. Static images can't be explored; interactive demos let the reader develop intuition by playing with the underlying model.

Part of the [Render](../render.md) skill — see the top-level index for mission, universal rules, and channel map.

## When to use
- Blog post explainers (Adventures in AI Coding, Inside the Math style)
- Paper figures with sliders (CHI / ETTAC / CIKM submissions can include live demo URLs)
- Worked examples and teaching artifacts
- Audio-reactive visualizers (Psychodeli lineage)
- Eye-tracking replays with timeline scrubber
- Anything where "watching it move" matters more than "seeing one frame"

## Constraints (from `~/CLAUDE.md`)
- **ES6 modules direct.** No bundlers, no build step.
- **WebGL is the primary graphics stack.** Canvas2D for non-shader 2D, D3 for data binding to DOM/SVG, Three.js when 3D scene management beats raw WebGL.
- **Defensive numerics:** `isFinite()` guards, NaN traps, clamp before passing to GLSL.
- **Small focused functions** over mega-files.
- **Inline comments explain "why."**

## Default scaffold — single-file HTML

```html
<!DOCTYPE html>
<html data-mg-theme="dark">
<head>
  <meta charset="utf-8">
  <title>Demo</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/marginalia@latest/marginalia.css">
  <style>
    :root { color-scheme: dark; }
    body { max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
    canvas { width: 100%; aspect-ratio: 16/9; display: block; background: #0a0a0f; }
    .controls { display: flex; gap: 1rem; padding: 1rem 0; }
  </style>
</head>
<body>
  <main>
    <h1>Title</h1>
    <p>One-paragraph context.</p>
    <canvas id="stage" width="1280" height="720"></canvas>
    <div class="controls">
      <label>Param <input type="range" id="p1" min="0" max="1" step="0.01" value="0.5"></label>
    </div>
  </main>
  <script type="module">
    'use strict';
    const cvs = document.getElementById('stage');
    const ctx = cvs.getContext('2d'); // or 'webgl2'
    const p1 = document.getElementById('p1');
    function frame() {
      const v = parseFloat(p1.value);
      if (!isFinite(v)) return requestAnimationFrame(frame);
      // ... draw using v ...
      requestAnimationFrame(frame);
    }
    frame();
  </script>
</body>
</html>
```

One file. No build. Marginalia handles editorial chrome. Demo lives at `<project>/demos/<name>.html` and can be linked from a blog post or paper.

## Library choices

| Need | Library | Why |
|---|---|---|
| Shaders / 3D / perf | WebGL2 raw + Three.js for scenes | Andy's primary stack |
| Data binding to DOM/SVG | D3 v7 | Reactive scales, no virtual DOM |
| 2D sketches / teaching | p5.js | Lowest activation energy |
| Audio-reactive | Web Audio API + AnalyserNode | Native, zero deps |
| Eye-tracking replay | Custom Canvas2D + rAF | Fixation timing matters; no abstraction |
| Reactive UI controls | Vanilla `<input type="range">` | No framework needed for sliders |

## Permalink convention
Demos with shareable state should follow the **PermalinkManager** pattern from Scrutinizer/Psychodeli: URL hash encodes parameters, parsed on load, rewritten on change. Read the existing manager class first — don't reinvent it.

## Marginalia integration
Wrap demos in marginalia callouts for editorial context:
```html
<aside class="mg-callout" data-type="tip">
  <h3>Try it</h3>
  <iframe src="demos/foveation.html" loading="lazy" style="width:100%;border:0;aspect-ratio:16/9"></iframe>
  <p>Drag the slider to see how cortical magnification compresses peripheral vision.</p>
</aside>
```

## Reference exemplars (don't rewrite)
- **Inside the Math** — shipped WebGL explainer for foveation/cortical magnification. Reference it; don't rebuild it.
- **Scrutinizer demos** — PermalinkManager pattern for shareable WebGL state.
- **Psychodeli** — audio-reactive shader pipeline (owned by psychodeli-brand-guide for assets).

## Distribution & hosting

Once a demo exists as a single-file HTML, the next decision is where it lives. Different hosts have sharply different strengths — choose based on audience (private vs public), forkability, and build friction.

| Host | Best for | Trade |
|---|---|---|
| **GitHub Pages** | Repo-hosted demos (Scrutinizer, Psychodeli, marginalia, Inside the Math) — canonical, diffable, co-located with source. | Build/push latency; doesn't surface demos for browsing discovery. |
| **CodePen** | Single-file shareable demos; sci-fi / FUI experiments; "paste this into a Pen" teaching artifacts; fork-to-iterate. | Free Pens are public — don't paste unreleased client or research code. |
| **Observable** | D3 data-viz figures with reactive cells — the right host for CHI / ETTAC / CIKM paper figures where the reader can move parameters. | Cell-based, not a normal HTML file — different mental model. |
| **gist** | Minimum-friction single-file distribution; linkable from notes and papers. | No live preview without a third-party renderer (bl.ocks.org went read-only). |
| **CodeSandbox / StackBlitz** | Full-project demos with npm dependencies; SDK examples. | Overkill for single-file work; heavier iteration loop. |
| **Local `file://`** | Private iteration, screenshot capture, ffmpeg recording of interactive demos. | Doesn't share without promoting to a host. |

### CodePen — the Prefill API

CodePen's highest-leverage feature: `POST` a JSON payload of HTML/CSS/JS to `codepen.io/pen/define` and open a new Pen with the code pre-populated, ready for the reader to run or fork. Perfect for "Try this in a Pen" buttons inside blog posts — one click and the reader is in a live editor with your code.

```html
<form action="https://codepen.io/pen/define" method="POST" target="_blank">
  <input type="hidden" name="data" value='{
    "title": "FUI scan overlay",
    "html": "<canvas id=c></canvas>",
    "css":  "body{background:#000}",
    "js":   "/* demo code here */",
    "tags": ["fui","canvas","webgl"]
  }'>
  <button type="submit">Open in CodePen</button>
</form>
```

Full docs: [blog.codepen.io/documentation/prefill](https://blog.codepen.io/documentation/prefill/). Tags, titles, descriptions, and external resources (including marginalia CDN) can all be set in the payload. For educational content this is the highest-leverage single feature in the whole skill — don't reach for screenshots when you can reach for a live fork.

### CodePen — embeds

Two modes, both work inside marginalia pages:

```html
<!-- Result only -->
<p class="codepen" data-height="400" data-default-tab="result"
   data-slug-hash="abcDEF" data-user="andyed">
  See the Pen on CodePen.
</p>
<script src="https://cpwebassets.codepen.io/assets/embed/ei.js" async></script>

<!-- Full editor (html + css + js tabs) -->
<p class="codepen" data-height="600" data-default-tab="html,result"
   data-slug-hash="abcDEF" data-user="andyed">...</p>
```

Wrap the embed in a marginalia callout for editorial framing inside a blog post:

```html
<aside class="mg-callout" data-type="tip">
  <h3>Try it</h3>
  <p class="codepen" data-height="500" data-slug-hash="..." data-user="andyed"></p>
</aside>
```

### Observable — for paper figures

Observable notebooks (`observablehq.com`) are the right host for reactive D3 figures embedded in research papers. Cells are reactive — change one slider and every downstream cell recomputes. The embed runtime (`@observablehq/runtime`) lets you pull specific cells into a marginalia page, so the notebook becomes the source of truth and the blog post is a curated view into it. Ideal for CHI / ETTAC / CIKM figure supplements where the reader should be able to explore parameters.

### Tag conventions

On CodePen specifically: tag each experiment with both a **technical** tag (`webgl`, `canvas`, `svg`, `d3`) and a **genre** tag (`fui`, `hud`, `generative`, `typography`, `scrollytelling`) so your work surfaces to the right community and theirs surfaces to yours.

### Privacy caveat

Free CodePen Pens are public. Free Observable notebooks are public. Free gists can be "secret" but are still URL-accessible. Don't paste unreleased Scrutinizer shaders, unpublished research data, or client work into any free tier — use GitHub Pages (private repo + gh-pages) or local files for anything sensitive. When in doubt, ask before pasting.

## Lessons from past projects
- **No bare `console.log` in Psychodeli.** Use `window.debugManager`.
- **Don't dim/fade SERP cards on hover or brush.**
- **WebGL variable names: read the source, don't guess.**
- **Shader changes need verification.** Run tests or capture a screenshot before claiming a fix is working.
