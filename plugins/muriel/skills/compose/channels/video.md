# Video — Product Demos, GIFs, Recorded Talks

Scripted screen recordings with tooltip overlays for YouTube/social. ffmpeg for trim/concat/burn. `desktop-control` MCP for mouse choreography. AppleScript for menu automation.

Part of the [muriel](../SKILL.md) skill — see the top-level index for mission, universal rules, and channel map.

## Tools available

| Tool | What it does | How to invoke |
|------|-------------|---------------|
| `desktop-control` MCP | Move mouse, click, key combos, screenshots | `mcp__desktop-control__move_mouse`, `__click`, `__key_combo` |
| App-specific skill | Switch modes or toggle features in the app being demoed via AppleScript menus | `/<app> mode <name>` (project-specific) |
| AppleScript (direct) | Any macOS UI automation — menu clicks, window focus, keystrokes | `osascript -e '...'` |
| [**Recordly**](https://github.com/webadderall/Recordly) | Capture + auto-zoom + cursor polish + motion blur + styled frames (the "product-demo video" app) | AGPL-3.0 desktop app; record → export MP4 → hand off to muriel's post-processing |
| macOS built-in screen recording | Zero-setup capture, no polish | `Cmd+Shift+5` — use when Recordly is overkill or unavailable |
| ffmpeg (homebrew-ffmpeg tap) | Trim, burn captions, add music, encode | Hard-burn via `subtitles` filter (libass) |

## Workflow

### With Recordly (recommended for polished product/walkthrough videos)

1. **Record in Recordly** — auto-zoom follows the cursor, cursor polish + motion blur applied in-editor, webcam overlay optional, styled frame around the final composition. Export MP4.
2. **(Optional) Burn captions via muriel** — if you have a tooltip manifest with precise timecodes, run `burn-tooltips.sh manifest.json recordly-out.mp4 final.mp4` to add hard-burned captions.
3. **(Optional) Further ffmpeg passes** — trim, concat, encode for YouTube using the recipes below.

### Without Recordly (zero-setup path)

1. **Write a tooltip manifest** — JSON array of `{start, end, text}` objects
2. **Script the choreography** — `desktop-control` moves the mouse on timed coordinates; AppleScript switches modes
3. **User records** with `Cmd+Shift+5` while agent drives the app
4. **Post-process**: `burn-tooltips.sh manifest.json raw.mov output.mp4`
   - Generates SRT from manifest
   - Burns captions via ffmpeg `subtitles` filter (Helvetica 24px, white, black outline)
   - Trims with `-ss` / `-t` flags
   - Drops audio with `-an` when needed
   - H.264 CRF 22, faststart for YouTube

## ffmpeg setup

The default `brew install ffmpeg` lacks `drawtext`/`subtitles` filters. Install the full version:
```bash
brew uninstall ffmpeg
brew tap homebrew-ffmpeg/ffmpeg
brew install homebrew-ffmpeg/ffmpeg/ffmpeg
```
This includes freetype, libass, fontconfig — enables `drawtext`, `subtitles`, and `ass` filters.

## Tooltip burn script

A `burn-tooltips.sh` script (see your app repo or [`muriel/tools/`](../tools/)) — two modes:
```bash
# SRT only (no ffmpeg needed)
burn-tooltips.sh tooltips.json output.srt

# Full pipeline: trim + burn + optional music
burn-tooltips.sh tooltips.json raw.mov output.mp4 [music.mp3]
```

Uses `subtitles` filter (libass) for hard-burn. Falls back to soft-sub mux if drawtext unavailable. Music mixed at 15% volume.

## Lessons learned

- **Trim first, caption second** — tooltip timecodes are relative to the trimmed video, not the raw recording. Use `-ss` to skip dead intro before the filter chain.
- **Drop audio with `-an`** — screen recordings capture system audio, dogs barking, etc.
- **macOS filenames have Unicode spaces** — `PM` in screen recording filenames uses a narrow no-break space (U+202F). Use glob matching, not exact strings.
- **Excalidraw: skip hand-drawn** — use `roughness: 0`, `fontFamily: 2` (Helvetica), `fillStyle: "solid"`. The hand-drawn aesthetic reads as fake, not charming.
- **SRT for YouTube** — even with hard-burned captions, upload the SRT too. YouTube auto-translates it.

## ffmpeg editing recipes

Standalone operations for cutting, joining, and splitting video outside the tooltip pipeline.

```bash
# Cut segment (fast, keyframe-aligned)
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy output.mp4

# Cut segment (precise, re-encodes)
ffmpeg -ss 00:00:10 -i input.mp4 -t 20 -c:v libx264 -c:a aac output.mp4

# Last N seconds
ffmpeg -sseof -30 -i input.mp4 -c copy output.mp4

# Concatenate via file list (recommended — works across codecs)
# list.txt contains: file 'clip1.mp4'\nfile 'clip2.mp4'\nfile 'clip3.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Concatenate with re-encode (when codecs differ)
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac output.mp4

# Split into fixed-length segments
ffmpeg -i input.mp4 -c copy -f segment -segment_time 60 -reset_timestamps 1 output_%03d.mp4
```

**`-c copy` vs re-encode:** `-c copy` is instant but cuts on keyframes (may be off by a few frames). Add `-c:v libx264 -c:a aac` for frame-accurate cuts at the cost of speed. `-ss` before `-i` is faster; after `-i` is more precise.

## Design doc

See [`docs/PERMUTE.md`](https://github.com/andyed/muriel/blob/main/docs/PERMUTE.md) for the infographic aspiration: Tufte, Bertin, Gestalt, CRAP, semantic zoom, small multiples, linked displays.

## HTML → MP4 via hyperframes

For videos whose source of truth is HTML (release announcements, feature explainers, animated data viz, kinetic-typography compositions, website-to-video), use [**hyperframes**](https://github.com/heygen-com/hyperframes) (HeyGen, Apache 2.0). Puppeteer + FFmpeg + GSAP rendering; deterministic (same input → same output). Explicitly built for agent-driven authoring.

Installed globally via `npx skills add heygen-com/hyperframes -y -g`. Registers five Claude Code slash commands:

| Skill | What it does |
|---|---|
| `/hyperframes` | HTML composition authoring — captions, TTS, audio-reactive animation, transitions |
| `/hyperframes-cli` | CLI commands — `init`, `lint`, `preview`, `render`, `transcribe`, `tts`, `doctor` |
| `/hyperframes-registry` | Block and component installation via `hyperframes add <block>` |
| `/website-to-hyperframes` | Capture a URL → turn it into a video (Scrutinizer.app promo candidate) |
| `/gsap` | GSAP timelines, easing, ScrollTrigger, framework integration, performance |

### When to pick what

| If the source of truth is… | Use |
|---|---|
| A running macOS app (Scrutinizer mode sweeps, Psychodeli visualizer playback) | **Recordly** |
| An HTML composition (release demo, explainer, animated chart) | **hyperframes** |
| A scripted walkthrough driving a real app via the mouse | **desktop-control + ffmpeg** |
| A static screenshot pipeline that needs motion frosting (zoom-pan, fade-in caption) | **ffmpeg filters directly** |

### Quickstart

```bash
npx hyperframes init my-video      # scaffolds HTML composition
cd my-video
npx hyperframes preview            # live-reload in browser
npx hyperframes render             # MP4 out
```

Compose in HTML with data attributes:

```html
<div id="stage" data-composition-id="release" data-start="0" data-width="1920" data-height="1080">
  <video src="scrutinizer-demo.mp4" data-start="0" data-duration="8" data-track-index="0" muted playsinline></video>
  <div class="caption" data-start="1" data-duration="4" data-track-index="1">
    Only 2° of your vision is sharp.
  </div>
  <audio src="music.wav" data-start="0" data-duration="8" data-track-index="2" data-volume="0.5"></audio>
</div>
```

### Catalog blocks worth knowing

50+ prebuilt blocks at [hyperframes.heygen.com/catalog](https://hyperframes.heygen.com/catalog/blocks/data-chart):

- **Social overlays** — `instagram-follow`, lower thirds, subscribe animations
- **Shader transitions** — `flash-through-white`, WebGL dissolves
- **Data viz** — `data-chart` (animated bar/line), counters
- **Captions + TTS** — synced text over video, auto-narration
- **Audio-reactive** — shaders or CSS animations driven by waveform analysis

Install blocks via `npx hyperframes add <block-name>`.

### Frame Adapter pattern

Bring your own animation runtime (GSAP, Lottie, CSS, Three.js). PixiJS ([`vocabularies/pixijs.md`](../vocabularies/pixijs.md)) and kinetic-typography compositions should drop in via a custom adapter.

### Not a replacement

hyperframes sits alongside the ffmpeg + Recordly + desktop-control recipes above, not instead of them. Pick the substrate by where the truth lives. A Scrutinizer feature demo video has three parts — a screen recording of the running app (Recordly), title cards and captions (hyperframes), and final encoding (ffmpeg). Stack them.

## Anti-patterns

- **Don't capture with system audio on** unless narration is intentional. Dogs bark, notifications ding, system alerts leak into shipped reels.
- **Don't burn subtitles in the default SRT font.** Use the brand's typography so captions feel authored, not tacked on.
- **Don't edit at 30 fps then upload at 60** (or vice versa). Match the recording's frame rate or re-encode deliberately.
- **Don't ship a demo whose first 3 seconds don't hook attention.** The opening frame is most of the commitment decision.
