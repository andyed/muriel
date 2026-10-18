---
reference: collections
status: experimental
requires:
  item_images: required
  stable_item_identity: required
output:
  kinds: [collection-document, comparison-recipe, observations, evidence-packet, exploration-critique]
  registers: [app, web, data-product, science]
---

# Collections — an explorer for many images

Use this reference when the deliverable is a set of images that a person will
survey, filter, compare or check, rather than one composed figure. muriel's
default engine for this is [Wunderkammer 0.1.0](https://github.com/andyed/wunderkammer/tree/v0.1.0)
(MIT), a collection explorer for people and language models:

- The agent writes the collection as one JSON document.
- The person pans, zooms, filters by facets, groups, compares groups and opens
  items.
- The agent reads back exactly what the person selected.

It runs from static files with no server.

Wunderkammer's spatial view uses muriel's rendering primitives, vendored at a
pinned commit
([`wall/spatial/lib/VENDOR.md`](https://github.com/andyed/wunderkammer/blob/v0.1.0/wall/spatial/lib/VENDOR.md)).
muriel imports no Wunderkammer code, and this reference names it by released
version only. Every URL below is pinned to `v0.1.0` or `wunderkammer@0.1.0`.
When a new version is released, update the pins and re-check the claims that
carry a date.

It is a default, not a requirement. Another explorer that passes the
[exploration-quality axis](#exploration-quality) is a sensible substitute: the
axis is muriel's opinion, and the engine is a preference.

## When to reach for a collection explorer

Use one when at least one of these holds:

- **Dozens to thousands of images.** Below a dozen, a figure grid or contact
  sheet is faster to read than an explorer is to learn. Above that, a person
  needs an overview, filters and a way back to where they were. A document
  can list 1 to 50,000 items. The bundled example has 297.
- **A comparison between groups.** The question is how an attribute is
  distributed across 2–6 groups (decades, sources, conditions), and the person
  should see the items in each group, not only their shares. If the images are
  irrelevant to the question, use [`channels/charts.md`](../channels/charts.md).
- **Claims a person should be able to check.** The agent says something about
  the collection, such as "jazz is less common in the 1990s", and the person
  should be able to open the exact items behind it.

Do not use one for a single image or composed figure, or for numbers with no
images behind them. When the output must be one self-contained file, see the
[fallback](#fallback).

## The contract in brief

There are four parts, and all of them are static files. The full contract is
[`docs/CONTRACT.md`](https://github.com/andyed/wunderkammer/blob/v0.1.0/docs/CONTRACT.md).
This section covers what an agent needs for a first draft that validates.

### Collection document: `wunderkammer.collection` v1

```json
{
  "format": "wunderkammer.collection",
  "version": 1,
  "corpus": { "id": "example:album-covers", "revision": "2026-10-17" },
  "ui": { "title": "Album covers", "defaultGroup": "decade",
          "facetOrder": ["decade", "genre"], "hiddenFacets": ["catalog"] },
  "images": { "cors": true },
  "clips": [
    { "id": "a1", "title": "Example title",
      "cover": "https://example.org/a1-256.webp",
      "props": { "decade": "1980s", "genre": ["electronic", "pop"], "catalog": "XL-104" },
      "sourceUrl": "https://example.org/a1" }
  ]
}
```

- **Required fields:** `format`, `version`, `corpus.id` and `clips` (1 to
  50,000 items). Each clip needs a non-empty `id`.
- **Identity:** an item's identity is its `url`, or its `id` when it has no
  `url`. Repeated identities are an error.
- **Attributes** go in `props` as strings, finite numbers, booleans or arrays
  of them. Facets and their counts are derived from `props`, so supply neither
  yourself. Hide per-item identifiers with `ui.hiddenFacets`. A `props` key
  that names a clip field (`title`, `source` …) is refused.
- **Links and images:** `sourceUrl` must be http(s). Images (`cover`,
  `detailCover`, `coverVariants[].src`, `media[].src`) may be http(s),
  `data:image/` or `blob:`. Relative URLs resolve against the document's URL.
- **Cross-origin covers:** `images.cors: true` declares that covers on other
  origins send CORS headers. Without CORS, those covers stay blank in the 3D
  views.
- **Plain text only:** every string is set as text (`textContent`). `note` is
  never HTML.
- **Validation:** unknown keys are refused, with the list of supported ones.
  All problems are reported at once with their paths, up to 25 in one
  `CollectionError`, so a first draft can be fixed in a single pass.
- **Sprite sheets:** with a few hundred covers or more, pack them into
  sprite-sheet pages with
  [`scripts/collection-sheets.py`](https://github.com/andyed/wunderkammer/blob/v0.1.0/scripts/collection-sheets.py).
  The script is in the repository, not the npm package. On the 297-image
  example, the overview needed 3 image requests instead of 297
  ([`docs/PERF.md`](https://github.com/andyed/wunderkammer/blob/v0.1.0/docs/PERF.md),
  "Collection sprite sheets").

### Comparison recipe

A question-sized comparison: 2–6 groups of one attribute, one measured
attribute, and counts or shares. Every field is required, though `question`
and `scope.query` may be empty strings.

```json
{
  "version": 1,
  "question": "How does genre distribution change across release decades?",
  "corpus": { "id": "example:album-covers", "revision": "2026-10-17" },
  "scope": { "query": "", "facets": {} },
  "groupBy": "decade", "groups": ["1970s", "1980s", "1990s"],
  "measure": "genre", "metric": "share",
  "categoryLimit": 8, "sort": "difference"
}
```

- **Allowed values:**
  - `metric`: `share` or `count`;
  - `sort`: `difference`, `total` or `name`;
  - `categoryLimit`: an integer from 4 to 20.
- **Corpus:** repeat the collection's `corpus.id` and `corpus.revision`.
  Otherwise the page notes that the recipe names a different corpus.
- **Validation:** `validateComparison()` stops at the first problem, unlike the
  collection and observation validators.
- **Counting:** the rules are stated in the evidence packet's
  `countingPolicy`:
  - an item can fall in several groups and carry several values, so shares
    need not sum to one;
  - an absent attribute counts as `(Unknown)`;
  - a share with a zero denominator is `null`.

### Observations: `wunderkammer.observations` v1

An observation is a claim about a comparison. It points at the cells or items
behind it rather than summarizing them.

```json
{
  "format": "wunderkammer.observations", "version": 1,
  "comparison": { "version": 1, "...": "the recipe above, unchanged" },
  "observations": [
    { "id": "jazz-falls",
      "text": "Jazz is less common in the 1990s than in the 1970s.",
      "evidence": { "cells": [{ "value": "Jazz", "cohort": "1970s" },
                              { "value": "Jazz", "cohort": "1990s" }],
                    "items": ["a1"] } }
  ]
}
```

- **The figures are computed by the page.** Each cited cell's count,
  denominator and share are taken from the same rows as the evidence export.
  In the panel, the text is labelled as the author's and the figures as
  computed. v1 does not parse numbers out of the text, so an authored claim
  has no numbers of its own. State the direction and cite the cells. The size
  is then shown by the page.
- **Limits:**
  - 12 observations;
  - 600 characters of text, 12 cells and 200 items per observation;
  - ids of 1–40 letters, digits, `-` or `_`.
- **Cells:** a cell's `cohort` must be one of the recipe's groups. A cell
  without one cites its value in every group.
- **Unresolved citations are shown, never dropped.** These are a value the
  measure lacks, a group the recipe lacks, or an item outside the collection.
- **Staleness:** observations apply to the comparison they were written for.
  After the person changes it, they are shown without figures, with a button
  back to the original comparison.
- **Delivery:** two static files,
  `wall/compare.html?collection=<collection.json>&observations=<observations.json>`.
  Once loaded, the observations travel in the page's link.

### Hand-back: `window.wunderkammer.export()`

Both pages define `window.wunderkammer.export()`. Only identities and titles
are in the packet, never notes or paths.

- **The wall** returns `{ format: "wunderkammer.export", version: 1, … }`:
  - `corpus`;
  - `scope`: label, query, facets and branch counts;
  - `view`: mode and grouping;
  - `focus`: the focused item;
  - `highlight`: the pinned highlight with its matching keys;
  - `count` and `total`;
  - `evidence`: every in-scope item as `{ key, title }`, in corpus order.
- **The comparison page** returns the evidence packet for the current
  selection:
  - cohorts with their denominators;
  - rows of cells with count, share and keys;
  - `countingPolicy`, `coverage` and `warnings`;
  - the selected items.

  For a selected observation, the packet adds `observation`, with its computed
  figures and any unresolved citations.
- **Reading it:** open the page as the top-level document in a browser the
  agent drives, and evaluate `window.wunderkammer.export()` with the
  page-JavaScript tool. In the Claude Code desktop app, that is the browser
  pane's `javascript_tool`.
- **Frames:** a same-origin frame can be read as
  `frame.contentWindow.wunderkammer.export()`, but a cross-origin frame cannot.
- **Not built in 0.1.0:** an `onSelection` callback through `mount()`, and a
  "copy for the conversation" button.
- **Before acting on a packet,** check that its `count` matches the scope the
  person described. Quote identities from the packet rather than from memory
  of the page.

### Embedding: `mount(element, collection)`

```js
import { mount } from 'https://cdn.jsdelivr.net/npm/wunderkammer@0.1.0/wall/embed.mjs';

const wall = mount(element, collection, {
  wallUrl: 'https://static.example.org/wunderkammer/wall/index.html',   // see the loading table
});
await wall.ready;   // resolves on the wall's view-ready message
```

- **`collection`** is an object or a URL.
- **An object** is validated in the host page first, so a bad one throws a
  `CollectionError` before any frame exists. It is then posted to the wall's
  origin only, and validated again there.
- **A URL** is fetched by the wall. If it fails, the host gets a generic error
  and the details appear inside the frame.
- **`wallUrl`** must be passed whenever `embed.mjs` comes from a CDN. Its
  default is the directory above `embed.mjs`. On a CDN that is the package
  root, which holds no page.
- **Other options:** `title` (the iframe's title) and `timeout` (default
  20,000 ms).
- **`wall.ready`** rejects on the wall's error message or on timeout.
  `wall.destroy()` removes the frame.

## Loading by pinned version

Pin every reference to the release: `wunderkammer@0.1.0` on a CDN, `v0.1.0`
on GitHub. Never use `@latest`, a bare package name or a branch.

| What | jsDelivr | unpkg | Static host |
|---|---|---|---|
| ES modules (`wall/embed.mjs`, `wall/collection.mjs`, `wall/observations.mjs`) | yes | yes | yes |
| `wall/compare.html`, opened or framed | no: HTML is served as `text/plain` | yes | yes |
| `wall/index.html`, the wall, opened or framed | no | no, in 0.1.0 | yes |

- **Content types** were checked on 2026-10-17 (Wunderkammer's contract) and
  again on 2026-10-18 against `swagger-ui-dist@5.17.14/index.html`:
  - jsDelivr serves HTML as `text/plain` and unpkg serves it as `text/html`;
  - both serve JavaScript with a JavaScript type.
- **The wall page does not boot from a CDN in 0.1.0.** `wall/index.html`
  loads its stylesheets and `wall.mjs` by root paths (`/wall/wall.mjs`).
  - On a CDN those paths resolve outside the package. On unpkg, `/wall/…`
    belongs to an unrelated npm package named `wall`.
  - Reproduced on 2026-10-18 by serving the package under
    `/wunderkammer@0.1.0/`. The wall page's seven `/wall/` requests returned
    404 and `window.wunderkammer` stayed undefined. `compare.html`, whose
    paths are relative, loaded and exported normally.
  - Serve the wall from a static host instead: a checkout of the tag
    (`npx http-server -p 8080 .`, then `/wall/?collection=<url>`), or the
    output of `scripts/build-demo.mjs`, which rewrites those paths.
- **Framing from an artifact host is untested.** unpkg sends no
  `X-Frame-Options` or `frame-ancestors` header (checked 2026-10-18), so
  framing is governed by the host page's own content security policy.
- **Three.js** 0.169.0 is loaded from jsDelivr by both pages, for the 3D view
  and the album walls only. Without the network or WebGL, those views are
  withdrawn with a notice. The flat wall, facets, detail pane, comparison
  matrix and evidence list remain usable.

## Fallback

Use muriel's [linked-atlas lab](../examples/linked-atlas/) instead of
Wunderkammer when:

- **A single file is required.** Wunderkammer is a wall page, its modules and
  a collection document, with Three.js from a CDN, and it cannot be inlined
  into one HTML file. The lab has no runtime dependencies: one page, one
  stylesheet and three small ES modules, all of which can be inlined.
- **WebGL is unavailable and the task needs the views that use it.**
  Wunderkammer's 3D view and album walls need WebGL. Its flat wall and
  comparison matrix do not, so check which views the task needs before
  switching.

The lab is drawn in SVG and HTML, and includes:

- semantic zoom with hysteresis, and an overview linked to a detail view;
- brushing with replace, add, subtract and intersect;
- summaries that show selected/total denominators;
- an accessible record table;
- undo;
- a read-only `window.linkedAtlas.snapshot()`.

It is a reference implementation of the interaction contract for 192
synthetic records, not a collection engine. It has no image tiles, document
validator, comparison recipe or observations. Adopting it means writing those
against its model while keeping its selection and camera semantics.

## Exploration quality

This is a critique axis for any collection page, whether Wunderkammer or a
substitute. Each question is answered from evidence an agent can gather:

- a screenshot at fit-to-all;
- one after zooming into a group;
- one after opening and closing an item;
- the hand-back packet.

Report each failure with its evidence, in
[`muriel-critique`](../../../agents/muriel-critique.md)'s severity scale.

| Question | Passes when | Evidence | Severity if it fails |
|---|---|---|---|
| **Does the overview show the collection's structure?** | At fit-to-all, every item is on screen, grouped by an attribute that answers the person's first question, each group is labelled with its count, and the total is shown. | Fit-to-all screenshot, and `export().total` against the document's item count. | HIGH: for example, an ungrouped grid, or grouping by a per-item attribute such as a file name. |
| **Are the facets useful, with counts?** | Each visible facet splits the collection into two or more values, none of which covers nearly every item. Every value shows its count, with the count's meaning named (Wunderkammer: *In view / available*). Facets have readable labels (`ui.facetLabels`), and per-item identifiers are hidden. | Facet-rail screenshot. For each `props` key, the number of distinct values against the number of items. | MEDIUM. HIGH when counts are missing. |
| **Does zoom keep orientation?** | After zooming into a group, the group's name is still visible. The whole collection is one action away (Fit or Back). Opening and closing an item returns to the same view. A zoom limit is a no-op, not a jump. | Before and after screenshots, and `export().scope` and `export().view` before and after opening an item. | HIGH. |
| **Can a selection be handed back?** | The person's scope, focus and selection can be read as exact identities, the packet's count equals the count on screen, and the packet holds no notes or local paths. | The hand-back packet against the on-screen count. | HIGH when there is no packet or the counts disagree. CRITICAL when private fields leak. |
| **Do observations cite evidence?** | Every observation cites at least one cell or item, and none is unresolved. The text contains no figures of its own. Selecting an observation lights exactly its cited items. | Observation panel, and the packet's `observation.figures` and `observation.unresolved`. | CRITICAL when an authored number disagrees with the computed figure. HIGH for an observation with nothing resolvable. |

The universal rules still apply. Facet labels, counts, group titles and
observation text are readable text under the 8:1 floor:

- **Wunderkammer's own audit:** its facet and scope controls measured at least
  8.528:1 against their painted backgrounds
  ([`docs/FACETING.md`](https://github.com/andyed/wunderkammer/blob/v0.1.0/docs/FACETING.md#implementation-verification)).
  That audit did not cover every text element.
- **The embedding page:** run `python -m muriel.contrast <page.html>` on the
  page you wrote.
- **The rest of the wall's text:** measure it on a capture
  (`python -m muriel.capture <url>`).

## Building a document: `muriel.collection`

```bash
python -m muriel.collection build <folder|csv> --out collection.json [--title T] [--group FIELD]
python -m muriel.collection validate collection.json
```

- **`build`** reads a folder of images or a CSV and writes a
  `wunderkammer.collection` v1 document. `--title` names the collection, and
  `--group` names the attribute the wall groups by when it opens.
- **`validate`** follows muriel's CLI convention for exit codes:
  - exit 0: the document is valid;
  - exit 1: every problem is listed with its path;
  - exit 2: nothing was read.
- **Validate before opening a browser.** A collection given to a frame by URL
  reports its problems inside the frame, not to the host. The page validates
  again on load, and when the two validators disagree, the page's
  ([`wall/collection.mjs`](https://github.com/andyed/wunderkammer/blob/v0.1.0/wall/collection.mjs))
  is the reference.

A typical pass:

1. Build and validate the document, then fix every listed problem.
2. Serve the wall with `?collection=` and check the overview against the
   exploration-quality axis.
3. For a comparison, write the recipe. For claims, write observations that
   cite cells. Open `compare.html` with both.
4. Let the person explore, then read the hand-back and quote the identities in
   it.

## Anti-patterns

- **Numbers in observation text.** Cite the cell, and let the page show the
  figure.
- **A summary in place of the collection.** Show the collection, and use
  observations as pointers into it.
- **`@latest`, a branch URL, or the wall page from jsDelivr.** Pin the release,
  and serve HTML from unpkg or a static host.
- **HTML in `note` or `title`.** It is shown as literal text.
- **Treating the hand-back as the person's conclusion.** It records what they
  selected, not what they concluded from it.
