# Dimensions — common screen-size footprints

Cross-channel reference sheet for output sizing. When the task is "make me a thing for X," this is where you look up how big "a thing" should be.

Part of the [Render](../render.md) skill. Channels that need these values:
- [`raster.md`](raster.md) — store assets, social cards, paper figures as raster
- [`interactive.md`](interactive.md) — canvas sizes, viewport tiers for capture
- [`web.md`](web.md) — Playwright window sizes, `@page` rules
- [`video.md`](video.md) — ffmpeg target resolutions
- [`science.md`](science.md) — paper column widths, figure export sizes

## How to pick a size

1. **Hard requirement first.** Store assets and paper figures have *exact* dimensions that reject on mismatch. These are in the "hard" column below. Match them exactly.
2. **Aspect-fit second.** Social cards and thumbnails have canonical aspect ratios; the host will crop anything off-spec. Hit the aspect even if pixel count is flexible.
3. **Retina-scale third.** When in doubt, design at 2× the logical size. Desktop browsers treat 1600×900 as crisp at 2× on retina. Upload larger; let the target downscale; never upscale.
4. **Vertical for mobile-first, horizontal for shared.** Vertical (9:16) is for Reels/Shorts/TikTok/Stories. Horizontal (16:9) is for Twitter/X, YouTube, Twitter-style shares. Square (1:1) is the Instagram-era fallback.

## Social cards and web embeds

**Hard requirements** — the platform crops or rejects anything else.

| Target | Size (px) | Aspect | Notes |
|---|---|---|---|
| **Twitter / X in-stream** | **1600×900** | 16:9 | Full-bleed preview, no crop on desktop. The word-fingerprints images use this. |
| **Twitter / X summary card** | 1200×628 | 1.91:1 | For `twitter:card` meta; displays smaller than in-stream |
| **Open Graph (default)** | 1200×630 | 1.91:1 | Facebook, LinkedIn, Mastodon, Bluesky, Slack, Discord — most platforms fall back to OG |
| **LinkedIn share** | 1200×627 | 1.91:1 | Same as OG; LinkedIn tolerates off-ratio but won't crop cleanly |
| **Substack featured image** | 1200×630 | 1.91:1 | Rendered at hero size above the title |
| **YouTube thumbnail** | 1280×720 | 16:9 | Max 2 MB. Larger uploads accepted; delivered at 1280. |
| **Instagram square** | 1080×1080 | 1:1 | The legacy default |
| **Instagram portrait** | 1080×1350 | 4:5 | Taller = more feed real estate without crop |
| **Instagram Stories / Reels** | 1080×1920 | 9:16 | Full-screen vertical |
| **TikTok** | 1080×1920 | 9:16 | Same as Reels. Upload larger (e.g. 2160×3840) if possible. |
| **Pinterest standard** | 1000×1500 | 2:3 | Tall rectangle; pins scale to 1000 wide |
| **Mastodon / Bluesky** | 1200×630 | 1.91:1 | Honors OG tags |

## Device displays — physical footprints for mockups and emulation

**Apple (current gen)**

| Device | Physical (px) | CSS (logical px) | Aspect | Notes |
|---|---|---|---|---|
| iPhone 15 Pro | 1179×2556 | 393×852 | ~19.5:9 | 3× scale |
| iPhone 15 Pro Max | 1290×2796 | 430×932 | ~19.5:9 | 3× scale |
| iPhone 15 / 14 | 1170×2532 | 390×844 | ~19.5:9 | 3× scale |
| iPhone SE | 750×1334 | 375×667 | 16:9 | 2× scale — floor for "small mobile" testing |
| iPad Pro 12.9" | 2048×2732 | 1024×1366 | 4:3 | 2× scale |
| iPad Pro 11" | 1668×2388 | 834×1194 | ~17:13 | 2× scale |
| iPad (10.9") | 1640×2360 | 820×1180 | ~7:5 | 2× scale |
| MacBook Air 13" | 2560×1664 | 1280×832 | 1.54:1 | 2× scale |
| MacBook Pro 14" | 3024×1964 | 1512×982 | ~1.54:1 | 2× scale |
| MacBook Pro 16" | 3456×2234 | 1728×1117 | ~1.55:1 | 2× scale |
| Studio Display 27" | 5120×2880 | 2560×1440 | 16:9 | 5K retina |
| Pro Display XDR 32" | 6016×3384 | 3008×1692 | 16:9 | 6K retina |
| iMac 24" | 4480×2520 | 2240×1260 | 16:9 | 4.5K retina |
| Apple TV 4K | 3840×2160 | 1920×1080 | 16:9 | 2× scale; top-shelf + screensaver target |

**Other**

| Device / class | Physical (px) | Notes |
|---|---|---|
| Fire TV (standard) | 1920×1080 | Primary target for Fire TV apps. CLAUDE.md notes ADB at `192.168.1.215:5555`. |
| Fire TV (4K) | 3840×2160 | |
| Android flagship (2024) | ~1080×2400 to 1440×3200 | Highly variable; design for CSS 360×800 as a safe floor |
| Pixel 8 Pro | 1344×2992 | CSS 448×998 |
| Chromecast with Google TV | 1920×1080 or 3840×2160 | |

## Web viewport tiers

Use these as Playwright / headless-Chrome window sizes when capturing or testing responsive behavior. They are **CSS pixel** sizes, not physical; the rendering engine will up-scale internally.

| Tier | Viewport (CSS px) | Target |
|---|---|---|
| Mobile small | 375×667 | iPhone SE floor |
| Mobile standard | 390×844 | iPhone 14/15 |
| Mobile large | 430×932 | iPhone 15 Pro Max, Pixel 8 Pro |
| Tablet portrait | 820×1180 | iPad (10.9") |
| Tablet landscape | 1180×820 | iPad rotated |
| Tablet pro portrait | 1024×1366 | iPad Pro 12.9" |
| Laptop | 1280×800 | MacBook Air 13" CSS-level |
| Laptop large | 1440×900 | Common dev default |
| Desktop FHD | 1920×1080 | The single most common desktop size on the internet |
| Desktop QHD | 2560×1440 | Common for external monitors |
| Desktop 4K | 3840×2160 | Top of the market |
| Ultrawide 21:9 | 2560×1080 | Gaming/power-user monitors |
| Ultrawide 32:9 | 3840×1080 | Dual-monitor-replacement displays |

For responsive screenshot sets, the sensible minimum is: `{375, 820, 1280, 1920}` — mobile / tablet / laptop / desktop. Add 1440 if the design has a distinct "laptop" tier, and add 3840 only if the design has 4K-specific layout rules (rare).

## Video

| Target | Resolution | Aspect | Notes |
|---|---|---|---|
| **1080p HD** | 1920×1080 | 16:9 | The default. ffmpeg `-s 1920x1080`. |
| **4K UHD** | 3840×2160 | 16:9 | ffmpeg `-s 3840x2160`. 4× the pixel count of 1080p. |
| **8K UHD** | 7680×4320 | 16:9 | Rarely shipped; useful for downscaling to 4K/1080p with headroom |
| **Vertical (mobile)** | 1080×1920 | 9:16 | Reels / Shorts / TikTok |
| **Square** | 1080×1080 | 1:1 | Instagram feed video |
| **Cinema DCI 4K** | 4096×2160 | ~1.9:1 | Slightly wider than UHD; theatrical |
| **720p HD** | 1280×720 | 16:9 | Legacy; only for fallback or low-bandwidth |
| **YouTube preferred upload** | 3840×2160 | 16:9 | Upload at 4K even if delivering at 1080p — YouTube's transcoder treats higher-source inputs better |

Screen recording on macOS via `Cmd+Shift+5` captures at the display's native resolution. Trim/encode to the target with ffmpeg in post — see [`channels/video.md`](video.md) for the editing recipes.

## Paper and print

**Page sizes**

| Size | Inches | mm | px @300 DPI | px @600 DPI |
|---|---|---|---|---|
| US Letter | 8.5 × 11 | 216 × 279 | 2550×3300 | 5100×6600 |
| US Legal | 8.5 × 14 | 216 × 356 | 2550×4200 | — |
| A4 | 8.27 × 11.69 | 210 × 297 | 2480×3508 | 4960×7016 |
| A3 | 11.69 × 16.54 | 297 × 420 | 3508×4961 | — |
| A5 | 5.83 × 8.27 | 148 × 210 | 1748×2480 | — |

**Conference paper column widths** — the common sizes science figures have to fit.

| Venue / style | Single col | Double col / full width | Notes |
|---|---|---|---|
| **ACM (SIGCHI, CHI, IUI)** | 3.33 in (84.6 mm) | 7.00 in (177.8 mm) | Recent `acmart` template; `\columnwidth` ≈ single |
| **IEEE (two-column)** | 3.50 in (88.9 mm) | 7.16 in (181.9 mm) | Legacy widths still shipped by most IEEE templates |
| **Springer LNCS** | — | 4.80 in (122 mm) | Single-column format; full width is the column |
| **PNAS** | 3.42 in (87 mm) | 7.00 in (178 mm) | |
| **Nature (narrow)** | 3.54 in (90 mm) | 7.28 in (185 mm) | |

**How to use:** for a matplotlib figure that will land in a CHI single column, set `figsize=(3.33, h)` and save as PDF. `h` depends on your aspect ratio; 2.0–2.5 is typical. The `channels/science.md` rcparams defaults assume a 10×6 figsize that's designed for a double-column or full-width placement, not a single column — override `figsize` per-figure when targeting single-column.

**Conference posters**

| Size | Inches | cm |
|---|---|---|
| A0 | 33.1 × 46.8 | 84.1 × 118.9 |
| 36" × 48" | 36 × 48 | 91 × 122 |
| 48" × 36" (landscape) | 48 × 36 | 122 × 91 |

At 150 DPI for poster print, A0 = 4968×7020 px. Don't exceed that — printers can't resolve more.

## App store assets

For the complete Amazon Appstore / Apple tvOS / Google Play store-specific dimensions, see the table in [`channels/raster.md`](raster.md#common-store-dimensions). That's where the existing canonical reference lives — this file doesn't duplicate it to avoid drift.

## Favicons and app icons

**Favicon set** (for a new web project, ship all of these):

| Size | Purpose |
|---|---|
| 16×16 | Legacy tab |
| 32×32 | Modern tab, pinned |
| 48×48 | Windows site tile |
| 180×180 | `apple-touch-icon` (iOS home screen) |
| 192×192 | Android home screen, PWA manifest |
| 512×512 | PWA manifest, high-res Android |
| 512×512 (maskable) | Android adaptive icon (full-bleed safe zone) |

**iOS app icon** — generate from a 1024×1024 master:

| Size | Purpose |
|---|---|
| 1024×1024 | App Store listing |
| 180×180 | iPhone (@3x) |
| 120×120 | iPhone (@2x) |
| 167×167 | iPad Pro |
| 152×152 | iPad |
| 87×87, 80×80, 60×60, 58×58, 40×40, 29×29, 20×20 | Settings, Spotlight, notifications |

**Android adaptive icon**: 108×108 dp (432×432 px at xxxhdpi), with the 72×72 dp (288×288 px) central "safe zone" containing all meaningful content. The outer border is at the mercy of the launcher's mask shape.

## Pixel density and scale factors

- **1× (standard):** legacy desktops; rarely a concern for new work
- **2× (retina):** MacBook, iMac, iPad, iPhone SE. Design at 2× target for crisp rendering.
- **3× (super retina):** iPhone Pro models. Physical pixels are 3× CSS pixels.
- **Desktop DPI:** browsers treat 96 DPI as 1× regardless of physical DPI. macOS and modern Windows handle the physical↔logical mapping transparently.

**Rule of thumb for export resolution:**
- Social card upload: 2× the target (e.g., upload 2400×1260 for a 1200×630 OG slot) so retina feeds display crisply
- Paper figure: 300 DPI minimum, 600 DPI for high-end journals, 150 DPI for posters
- App icon: master at 1024×1024 (or 2048 for Apple Vision Pro), generate all smaller sizes via Pillow `Image.LANCZOS`

## Naming convention for exported files

Consistent prefixes so multiple assets live in one directory without ambiguity:

```
twitter-instream-1600x900.png
og-card-1200x630.png
linkedin-share-1200x627.png
yt-thumb-1280x720.png
ig-story-1080x1920.png
ig-square-1080x1080.png
reel-1080x1920.mp4
firetv-screen-1920x1080.png
tvos-topshelf-2320x720.png
play-feature-1024x500.png
letter-poster-300dpi.pdf
a4-handout-300dpi.pdf
chi-singlecol-fig1.pdf
chi-doublecol-fig2.pdf
ieee-singlecol-fig3.pdf
icon-master-1024.png
favicon-512-maskable.png
mbp16-mockup-3456x2234.png
ipad-pro-129-mockup-2048x2732.png
```

Pattern: `{platform}-{role}-{widthXheight}.{ext}` for raster; `{platform}-{role}-{dpi|size}.{ext}` for paper. Platform prefix keeps sorting aligned; width×height is the canonical identifier.

## Code counterpart

All values in this file are also available as importable Python constants in [`render_assets/dimensions.py`](../render_assets/dimensions.py). Mirror of the markdown structure, standard-library-only, with three small classes (`Size`, `Device`, `PaperSize`), a dotted-name `REGISTRY` for programmatic lookup, and a `figsize_for(venue, columns, aspect)` helper so notebooks don't hardcode inch values.

```python
from render_assets.dimensions import (
    TWITTER_INSTREAM, OG_CARD, VIDEO_1080P, A4,
    figsize_for, lookup, device,
)

cvs_w, cvs_h = TWITTER_INSTREAM       # → (1600, 900)
OG_CARD.scale(2)                      # → Size(2400, 1260) for retina upload
A4.px_300dpi                          # → Size(2481, 3507)
figsize_for('chi', columns=1)         # → (3.33, 2.0)
device('iphone-15-pro').css           # → Size(393, 852)
lookup('twitter.instream')            # → Size(1600, 900)
```

Run the module directly to print the full registry + device list + paper table + figsize examples:

```bash
python -m render_assets.dimensions
```

## TODO

- [x] **`render_assets/dimensions.py`** — Shipped. `Size` / `Device` / `PaperSize` NamedTuples, 34 registry entries, 17 devices, 5 paper sizes, `figsize_for()` for 7 academic venues, CLI self-test.
- [ ] **Viewport-sweep capture script** — `render_assets/capture.py` helper that takes a URL and a tier list (`['mobile', 'tablet', 'laptop', 'desktop']`) and produces a set of Playwright screenshots named by the convention above. Pairs with `channels/web.md` static capture recipes. Can now pull from `RESPONSIVE_TIER_LIST` in `dimensions.py` instead of hardcoding.
- [x] **CHI / IEEE figsize helper** — Shipped as `figsize_for(venue, columns, aspect)` in `render_assets/dimensions.py`. Supports chi, acm, iui, ieee, pnas, nature, lncs.
