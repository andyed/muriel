# Documentation link audit — 24 October 2026

Audited the rebuilt documentation in the isolated `codex/docs-polish` worktree.
This report records build and link-check evidence, not publication status.
The initial polish commit is `66f9cd1`; the link repairs and jury visual are the subsequent scoped docs update.

## Results

- Scanned 79 generated HTML files for links and images inside MkDocs articles.
- Initial pass: 92 broken internal link occurrences and 17 external URLs returning 404.
- Final pass: **4,227 internal article links/assets checked; zero missing files or anchors.**
- **199 unique external URLs:** 180 HTTP checks passed; zero confirmed 404/410 responses;
  14 blocked checks, three responses requiring review, and two timeouts remain.
- Retried two transient GitHub 503 responses; both returned 200.
- MkDocs build completed without warnings. Seven focused regression tests passed on
  BIGFU against snapshot `4a73d24092342aa0f061f68ab09e3cdf8c2749c8`.
  The runner's automatic dependency setup failed on a Windows Python installation
  link; the dependency-free tests then ran directly on the same snapshot with its
  installed Python 3.15. No runner configuration was changed.

[Full machine-readable results](link-audit-2026-10-24.json) include referring pages,
response codes, redirect destinations, and the successful 503 retries.

## Combined jury integration

The final combined build scans 80 HTML files and checks **4,249 internal article
links/assets with zero failures**. The 199 external destinations are unchanged
from the recorded HTTP pass. Twenty rendered states (five pages at 1440, 768,
390, and 320 pixels wide) passed overflow, JavaScript-error, metadata, image-load,
and sampled text-contrast checks; minimum sampled contrast was 10.13:1.

The initial integration provided the other agent's landscape and portrait
illustrations plus an HTML account of the case. The user subsequently clarified
that the visual was not ready. The page and all social visual assets are now
excluded from the site build, and the homepage promotion has been removed.
The restored docs-only build checks 4,227 internal links with zero failures.
The user separately authorized the Loupe jury update; its tool and protocol are
integrated independently of the held visual.

The Loupe integration passes **26 tests on BIGFU** (including the raster tests)
against snapshot `a3fae4e36`. Its final site build checks **4,288 internal links**
with zero failures. Its one additional external destination, the anatomy
prior-art repository, returned HTTP 200. The original 199-URL HTTP report above
remains a record of the earlier audit. The source integration takes the jury
changes from `4027532` without the unrelated prose-channel work. No package
tag or binary release is implied by publishing this repository update.

## Repairs

- Kept the working SMG homepage and specific paper link; removed the broken library-directory destination.
- Replaced the missing Material 3 charting URL with the legacy Material 2 guide,
  labeled its maintenance status, and removed unsupported claims about a shared
  Material Charts library. Retained the old section anchor for incoming links.
- Updated Carbon, Paul Tol, Perception, K-Dense, Hermes, and KaTeX destinations.
- Replaced private source-repository links with public demos or local case-study descriptions.
- Corrected the Questions, Options, and Criteria DOI against CrossRef metadata.
- Replaced an absent FT licence file with the publisher's actual licence note,
  distinguishing software licensing from content reuse.
- Added a MkDocs hook to translate canonical repository paths into published page
  paths, or GitHub links for repository-only files. Native site pages and fenced
  examples retain their existing paths. Gallery logo assets now publish with the site.
- Repaired incorrect relative paths and heading fragments in canonical source files.
- Added an internal-link gate and focused regression checks to the docs build workflow.
  External network availability is not a deployment gate.

## Checks that remain inconclusive

These links were retained. Access blocks and timeouts do not establish a dead page.
The Perception destination is supported by its official indexed site, but direct
HTTP requests timed out during this run. Material's replacement was also inspected
in a browser because its content requires JavaScript.

| URL | Result |
| --- | --- |
| [https://doi.org/10.1080/00401706.1987.10488204](https://doi.org/10.1080/00401706.1987.10488204) | blocked (403) |
| [https://doi.org/10.1109/TVCG.2007.70539](https://doi.org/10.1109/TVCG.2007.70539) | review (202) |
| [https://doi.org/10.1109/TVCG.2016.2599030](https://doi.org/10.1109/TVCG.2016.2599030) | review (202) |
| [https://doi.org/10.1145/1456650.1456652](https://doi.org/10.1145/1456650.1456652) | blocked (403) |
| [https://doi.org/10.1145/192426.192435](https://doi.org/10.1145/192426.192435) | blocked (403) |
| [https://doi.org/10.1145/223904.223934](https://doi.org/10.1145/223904.223934) | blocked (403) |
| [https://doi.org/10.1145/345513.345282](https://doi.org/10.1145/345513.345282) | blocked (403) |
| [https://doi.org/10.1145/642611.642681](https://doi.org/10.1145/642611.642681) | blocked (403) |
| [https://doi.org/10.1147/sj.353.0514](https://doi.org/10.1147/sj.353.0514) | review (202) |
| [https://doi.org/10.1207/s15516709cog1801_3](https://doi.org/10.1207/s15516709cog1801_3) | blocked (403) |
| [https://doi.org/10.1207/s15516709cog2803_3](https://doi.org/10.1207/s15516709cog2803_3) | blocked (403) |
| [https://fuidesign.com/](https://fuidesign.com/) | unverified (timeout) |
| [https://mitpress.mit.edu/9780262090353/improvisational-design/](https://mitpress.mit.edu/9780262090353/improvisational-design/) | blocked (403) |
| [https://mitpress.mit.edu/9780262133548/design-by-numbers/](https://mitpress.mit.edu/9780262133548/design-by-numbers/) | blocked (403) |
| [https://mitpress.mit.edu/9780262182621/processing/](https://mitpress.mit.edu/9780262182621/processing/) | blocked (403) |
| [https://observablehq.com/plot/](https://observablehq.com/plot/) | blocked (429) |
| [https://scifi.stackexchange.com/questions/214058/what-is-the-name-of-this-sci-fi-circular-interface-seen-on-computers-and-hologra](https://scifi.stackexchange.com/questions/214058/what-is-the-name-of-this-sci-fi-circular-interface-seen-on-computers-and-hologra) | blocked (403) |
| [https://www.experienceperception.com/](https://www.experienceperception.com/) | unverified (timeout) |
| [https://www.npmjs.com/package/@chenglou/pretext](https://www.npmjs.com/package/@chenglou/pretext) | blocked (403) |

## Run again

After building the site from the repository root:

```bash
python site-docs/audit_links.py --site site-build --out /tmp/muriel-links.json
python site-docs/audit_links.py --site site-build --external --out /tmp/muriel-links-external.json
```

Exit status is nonzero for missing internal files/anchors or confirmed HTTP 404/410
responses. Blocked, review, and unverified results require inspection of the JSON;
a successful exit does not mean every external destination was verified.

The audit reads anchors, images, media sources, video posters, and image/source `srcset` attributes in MkDocs
articles and across standalone HTML pages (including demo navigation and the
showcase). Absolute links to muriel.mindbendingpixels.com are checked against
the local build, so a successful production response cannot hide a missing
preview target. MkDocs theme navigation remains outside the article scan.
It does not validate links generated by JavaScript, remote fragments, scripts,
stylesheets, or the accuracy of every linked claim. HTTP 200 alone cannot
establish relevance or rule out a JavaScript-rendered error page.

## Examples integration follow-up

`examples/gallery/README.md` is now the shared examples index, reached from the
homepage and top-level navigation. `/gallery/` retains its URL as a canonical
redirect with a plain-link fallback; the demo URLs underneath it are unchanged.
The showcase is a curated tour, not a second catalogue. Keep new examples in
the shared index and pair each hosted demo with its guide and source.

Eleven hosted demos use the shared `examples/demo-nav.css` navigation. Spatial
demos consume the same source through `render_assets/_lib/demo-nav.css`; CI's
existing dereferencing copy includes it in the gallery. The showcase also uses
the navigation styling. External project demos are identified as external links;
this change does not modify their applications or release them.

The expanded built-site audit checks **4,420 internal links with zero missing
files or anchors**. Nine link regression tests passed on BIGFU against snapshot
`9bc48ab8b`. The original external HTTP report is historical: this pass does not
claim a new successful crawl of all external destinations. The unfinished jury
landing page and social images remain excluded from the generated site.

Browser verification covered 39 page/viewport states at 1440, 390, and 320 pixels.
After correcting the showcase’s minimum-content grid overflow at 320 pixels, all
checked states had no horizontal overflow or page JavaScript errors. New demo
navigation text measured 15.42:1; sampled showcase text was at least 8.19:1.
The redirect → index → Linked Atlas → guide journey, Atlas exact selection, and
showcase motion preset were exercised in system Chrome on the Mac.


## Shipping verification: films and card focus

The release build contains 81 HTML files and checks **4,461 internal links**
with no missing files or anchors, including the new video sources and posters.
Ten link tests and three focus lifecycle tests passed on BIGFU snapshot
`5085dbb98`. The 29 MB of existing film deliveries were verified locally by
ffprobe, checksum manifest, and decoded browser playback rather than uploaded
to the test runner.

The film showcase, production notes, and examples index passed nine additional
page/viewport checks at 1440, 390, and 320 pixels: no horizontal overflow or
JavaScript errors. Both films played and paused through native keyboard controls
at each width. They do not autoplay or loop; preloading is disabled. Documentation
text in the checked pages met the 8:1 target.

AgentChan focus was checked for all twelve cards across five viewport/motion
configurations, including 320px phones, landscape, and reduced motion. Selection
holds the camera still, supports previous/next and keyboard dismissal, and
returns each card to its original transform after rapid reversals. The shared
controller retains click-again dismissal in the other mountain demo.
