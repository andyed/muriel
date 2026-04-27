# Kinetic typography — letters that move with intent

**When to reach for it.** When the message is *emotional* or *temporal* and the typography is doing the expressive work — protest signs, announcements, reveals, warnings, agent-to-human communication with character. Static text can't time itself; kinetic typography is type designed to be played, not just read.

Use it for:

- **Agent-to-human flourish** — when a response deserves more than plain markdown (greetings, completions, alerts, dramatic reveals).
- **Protest and broadcast graphics** — slogan-scale typography where impact + legibility at a glance matters more than information density.
- **Editorial punctuation inside longer pieces** — a single animated pull-quote or scene title inside an otherwise static blog post.
- **Scene titles / kickers for video** — muriel's [`channels/video.md`](../channels/video.md) captures these once and burns them into the final MP4.

Don't reach for it when:

- The message is informational and needs to be scannable — regular typography serves readers better. Motion *costs* attention.
- The target surface is print or email. Motion vanishes; fall back to raster.
- Ambient-noise motion is the only reason you're considering it. Kinetic typography should *deliver* meaning, not fill airspace.

## Lineage and grammar

The tradition runs from Saul Bass's title sequences through Kyle Cooper / Imaginary Forces into Territory Studio's motion-forward UI work (the same lineage that feeds [FUI](fui.md) — they overlap on sci-fi title cards). The grammar is narrow and strict:

- **Max contrast.** Cream or white on near-black, or inverse. No muddy middle tones. muriel's 8:1 rule is the floor; kinetic typography often goes higher (~15:1) because motion-blurred glyphs lose apparent contrast during transitions.
- **Strategic motion.** Every keyframe communicates. If a letter moves without reason, cut the animation.
- **No ambient noise.** No floaters, no drift, no decorative wiggle. The type is the message; nothing else is on screen doing busy work.
- **Emotional vocabulary.** A small named set of expressive modes (excited, playful, question, warning, reveal, etc.) — rehearsed, not improvised per shot. Consistency is how the audience learns to read the motion.
- **SDF text alpha rule.** When using SDF/MSDF text renderers (Troika, BMFont), never modulate alpha for fade effects — it breaks the distance-field antialiasing. Use RGB animation or scale/position tweens instead.
- **Debug-logging discipline.** Animated demos multiply log spam. Route through a project-level `debugManager` or a conditional logger; never ship bare `console.log`.

## Substrate choices

| Substrate | When | Notes |
|---|---|---|
| **[pretext](https://chenglou.me/pretext/)** | Typographic layout + animated Canvas2D at 60fps | Measures text outside the DOM reflow path, so per-frame re-layout is cheap. Good when the animation needs precise control over line breaks, rich inline weight/color, or text-in-shape flow. See [`channels/interactive.md`](../channels/interactive.md#typographic-canvas-with-pretext) for the API walkthrough. |
| **[iblipper](https://github.com/andyed/iblipper2025)** | Full animation-as-a-language pipeline with a rehearsed emotion vocabulary — *and* single-frame social-media graphic composer | muriel's dedicated kinetic-typography substrate. Built on pretext; exposes the emotional vocabulary as a UI. Invoke `/iblipper` when (a) the deliverable is an animated artifact, or (b) the deliverable is a single-frame social-media graphic where slogan-scale rhetorical typography is the work. Edit Message → export PNG covers the still case without IAP. Additional programmatic controls likely to be feature-requested upstream as muriel's call-pattern stabilizes. |
| **Troika three.js SDF text** | 3D scenes with kinetic type inside | Respect the SDF alpha rule. Scale / position animations are safe; alpha fades are not. |
| **Raw Canvas2D + rAF** | Simple single-line kinetic type with custom easing | Lowest activation energy. Use when pretext's rich-inline API is overkill. |
| **CSS animations** | Editorial-scale kinetic type on the web | Fine for subtle motion; hits limits when the animation needs per-character timing or non-DOM layout. |

## Calling iblipper headlessly for stills

iblipper exposes a `/render.html` route that mounts its renderer with no app shell — no Landing, FAQ, composer, gestures, IAP, splash. The page reads a JSON config from `?config=<encoded JSON>`, renders to canvas, and sets `window.__renderReady = true` after a configurable hold so a screenshot driver can capture the "held moment" of the entry animation. Pixel-identical to the in-app iBlipper output because it *is* the same renderer.

**Minimum config:**

```json
{ "text": "Maximum signal", "emotion": "emphatic", "fgColor": "#ffeb3b", "bgColor": "#0a0a0f", "wpm": 250, "width": 1200, "height": 630, "density": 100, "holdMs": 700 }
```

**Capture pattern (raw chrome, no automation library):**

```bash
ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$CONFIG")
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --hide-scrollbars --window-size=1200,630 \
  --virtual-time-budget=1500 --screenshot=out.png \
  "http://localhost:5173/render.html?config=$ENCODED"
```

`--virtual-time-budget` lets Chrome run a fast clock for the page so the entry animation runs to `holdMs` quickly; ~1500ms is plenty of headroom for `holdMs ≤ 1100`.

**Key knobs.**

| Knob | Effect |
|---|---|
| `text` | Plain text. **Embed `\n` for explicit phrase breaks** — see below. |
| `emotion` | Named recipe. `emphatic`, `hurry`, `idyllic`, `question`, `excited`, `playful`, `electric`, `urgent` (`response_required`), `casual`, `wobbly`, `glitch`, `fuzzy`, `decrypted`, `neutral`. Each picks font, animation, trail, and timing. |
| `density` | Words per frame, 1–10 normally. **Pass `100` (or any value > 50) for "All" mode** — every word on one frame, no chunking. |
| `holdMs` | Wait this many ms after mount before flagging `__renderReady`. Default 600. Bump to 800–1100 if the recipe has a long entry animation (`emphatic`, `glitch_reveal`-restart). |
| `fgColor` / `bgColor` | Hex strings. Verify 8:1 contrast — see [`channels/style-guides.md`](../channels/style-guides.md). |
| `width` / `height` | CSS pixels. Match your target dimension exactly; no need to oversample, the renderer is vector-faithful at any size. See [`channels/dimensions.md`](../channels/dimensions.md) for the canonical IG / OG / video / paper presets. |

### Controlling word splitting with explicit `\n`

iBlipper's break-finder picks a balanced line arrangement automatically, with a built-in disparity cap that prevents function-word amplification (so "AT THE" can't be larger than "QUESTION"). For most stills the default is fine — let it choose.

When you need *specific* phrase boundaries, **embed `\n` directly in `text`**. Density-100 mode preserves them as hard line breaks; the renderer treats each `\n`-separated paragraph independently and the cross-paragraph cap keeps sizes consistent. This is the documented escape hatch:

```jsonc
// Auto-balance — break-finder decides:
{ "text": "AI is fast at the wrong question.", "density": 100, ... }
// Renders as: AI IS / FAST AT / THE WRONG / QUESTION.

// Explicit phrase boundary at the comma:
{ "text": "AI is fast,\nat the wrong question.", "density": 100, ... }
// Forces: AI IS FAST / AT THE WRONG QUESTION.
```

**Heuristics for where to put `\n`:**

- **At sentence breaks** (periods, semicolons) when the chunk has multiple sentences and you want each on its own group of lines.
- **At natural rhetorical breaks** (commas before a contrasting clause, conjunctions starting a payoff line). Mirrors how a poster designer would read the line aloud and hit a beat.
- **Between attribution and quote** — `"The medium is the message.\n— McLuhan"`.

**Heuristics for where NOT to:**

- Don't split on every word — you reintroduce the disparity bug, and the per-paragraph independent sizing makes single-word lines size to fill width regardless of word length.
- Don't split a phrase that has stopwords-only on one side: `"AI is fast at the\nwrong question"` strands "AT THE" alone, which the cap then forces small. Group them: `"AI is fast\nat the wrong question"`.

### Recipe selection cheatsheet for stills

| Vibe | Emotion | Notes |
|---|---|---|
| Bold declarative, slogan, "I have a take" | `emphatic` | Rubik Mono One; very wide, **avoid for >5 words** at IG-square — letters crop |
| Forward-motion observation, fast take | `hurry` | Roboto Condensed Italic; italic skew enacts motion; tightest fit for long lines |
| Tech / AI / monitor aesthetic | `electric` | Share Tech Mono + RGB-split fringe; on-theme for AI subjects |
| Loud / urgent / "stop and read this" | `response_required` | Anton bold; pair with bright accent (verify 8:1) |
| Bouncy, joyful, casual | `playful` | Chewy; round letterforms; pink/warm palette |
| Calm, editorial, breathing | `idyllic` | Lora Italic; reflection trail under text; airy spacing |
| Inquisitive, soft alarm | `question` | Quicksand; subtle echo trail drifting up-left |

## Reference exemplars

- **iblipper** — canonical in this workspace. Emotional-expression vocabulary, Pretext-based renderer, protest-sign mode, URL-shareable animations. The `/iblipper` skill is how you invoke it; read its SKILL.md for the supported emotion set.
- **pretext-coachella** — public pretext exemplar at [andyed/pretext-coachella](https://github.com/andyed/pretext-coachella). Not primarily animated, but demonstrates the typographic canvas substrate that animated work builds on.
- **Saul Bass title sequences** — foundational. *Psycho*, *Vertigo*, *North by Northwest*. The best pre-CGI argument for motion as meaning.
- **Kyle Cooper / Imaginary Forces** — *Se7en*, *The Mummy*, *Dawn of the Dead*. Type as scene-setting; the lineage into Territory and Perception.
- **Type in Motion** (Woolman, Bellantoni — Thames & Hudson) — the reference book on the grammar. Worth reading in print.

## Integration with other muriel channels

- **[`channels/video.md`](../channels/video.md)** — capture a kinetic-typography piece (from iblipper, pretext, or custom) as MP4, then burn tooltips / trim / concat with ffmpeg.
- **[`channels/raster.md`](../channels/raster.md)** — pull a single frame as a static hero image for social cards or paper figures.
- **[`channels/interactive.md`](../channels/interactive.md)** — embed the live animation inline in a marginalia blog post.
- **[`vocabularies/fui.md`](fui.md)** — the overlap surface: sci-fi title cards are kinetic typography in the FUI idiom.

## Rules that always apply

Muriel's universal rules aren't suspended because the text is moving:

- **8:1 contrast minimum** on all text, including mid-animation states. If a tween dips below 8:1 for more than a frame, fix it — usually by interpolating RGB rather than alpha.
- **Label every number.** Animated stats dashboards still need units.
- **Measure before drawing.** Pretext makes this literal — it measures outside the DOM reflow path.
- **No false profundity.** If a letter moves and you can't state the reason in one sentence, it shouldn't move.
