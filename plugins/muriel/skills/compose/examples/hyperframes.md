---
title: HyperFrames films
description: How two finished films combine captured spatial interfaces, HyperFrames composition, typography, and sound.
---

# HyperFrames films

[Watch both films in the showcase](https://muriel.mindbendingpixels.com/showcase/#hyperframes) ·
[Browse all examples](gallery/README.md) · [Read the video guide](../channels/video.md#html-mp4-via-hyperframes)

These films use the same material as the interactive examples: a collection,
its spatial arrangements, and the detail within each item. The app provides
the footage. HyperFrames composes the sequence, transitions, and typography.
The previews preserve the existing edits at 1280 × 720, 30 fps; playback is
manual, with native video controls and no automatic looping.

## Cats. Lots of cats.

[Watch on YouTube ↗](https://www.youtube.com/watch?v=FGobAjvw32g) ·
[Play the on-page preview](https://muriel.mindbendingpixels.com/showcase/#wunderkammer-film) ·
[Collection guide](../references/collections.md) ·
[Wunderkammer source](https://github.com/andyed/wunderkammer)

The published 28-second film, “Cats. Lots of cats. | Wunderkammer, a collection
explorer for people and language models,” tours 489 cat images through
Wunderkammer. The on-page preview is silent. The artwork was generated
with Adobe Firefly; this is an illustrative collection, not a historical
art dataset. Era and style labels come from the generation prompts.

### What happens on screen

| Time | Scene |
| --- | --- |
| 0–2.7 s | A single cat in the detail view. “Cats.” appears, with the Firefly provenance label. |
| 2.7–13.3 s | A flash opens into rows of cat images rushing into an aisle. “Lots of cats.” becomes “Walk the aisle” as the camera travels through the shelves. |
| 13.3–16.7 s | The wall holds, then filters to ginger coats. |
| 16.7–19.2 s | Images float in space, placed by colour. |
| 19.2–21.9 s | An axes view places era horizontally and lightness vertically. |
| 21.9–24.8 s | A comparison connects an observation to its cited images. |
| 24.8–27.8 s | The Wunderkammer end card names the collection explorer, repository, and MIT licence for the software. |

### How it was made

The aisle flight is captured frame by frame from Wunderkammer, with camera and
rack positions set for each frame. Repeated racks extend the hallway for the
long cut. Detail, filtering, axes, and comparison footage come from the running
interface; the colour-space dolly is also captured frame by frame.

HyperFrames assembles the shots, dark caption panels, and flashes through white.
Keeping the panels separate from the captured interface makes their timing and
type editable without recapturing the underlying view. The film has no audio.

## Psychodeli spatial reel

[Watch the 39-second film](https://muriel.mindbendingpixels.com/showcase/#psychodeli-film) ·
[Spatial guide](../channels/spatial.md) · [Explore Psychodeli](https://psychodeli.com/)

Recorded Psychodeli visuals play on tiles arranged with Wunderkammer’s spatial
machinery. This is an authored camera sequence through those arrangements.
The film contains music and a chant texture, with no spoken instructions.

### What happens on screen

| Time | Scene |
| --- | --- |
| 0–10 s | Shelves of moving visuals rush into a warehouse aisle; the camera travels between them. |
| 10–14 s | A swoop through stacks of video tiles. |
| 14–20.57 s | The camera skims along a wall of moving images. |
| 20.57–33.87 s | Cards lift off the wall into a sphere around a central sequence of Psychodeli visuals. A brand card turns into view. |
| 33.87–39.07 s | The Psychodeli wordmark lands with “A dance partner for your senses.” The end card includes the website, platform call to action, and QR code. |

### How it was made

Captured warehouse, stacks, wall, and sphere shots become video layers in a
HyperFrames composition. The wordmark’s structure stays fixed while light moves
through its bands. The cuts and brand reveal follow changes in the soundtrack:
the chant’s return, a quieter passage for the card turn, and a surge for the logo.

The visuals are Psychodeli recordings. The soundtrack is Andy’s Adobe Firefly
generation, edited from “Track 4 — Buddhist monk chanting trance dub — echoes,
stereo spins, get trippy.” There is no added voiceover.

## Use the approach

1. Capture the product’s actual interaction or rendering before adding titles.
2. Keep shots, caption timing, and brand motion in the composition.
3. Inspect the rendered text and transitions at the intended viewing size.
4. Keep the final film beside its interactive example and explain which parts
   were captured and which were authored.

The [video channel](../channels/video.md) covers the production workflow;
[motion craft](../references/motion-craft.md) covers staging and continuity.
The [media manifest](https://muriel.mindbendingpixels.com/brand-assets/showcase/manifest.json)
records the delivery copies, durations, byte sizes, and checksums used here.
