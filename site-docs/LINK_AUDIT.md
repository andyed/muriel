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

The new jury landing page provides the other agent's landscape and portrait
illustrations plus a readable HTML account of the case. The visual is integrated
without publishing the unrelated toolkit commits from the primary checkout.
Loupe is explicitly marked as a development preview; the existing five-role
protocol remains the published implementation.

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

The audit reads article anchors, images, and image/source `srcset` attributes.
It does not validate links generated by demo JavaScript, remote fragments, scripts,
stylesheets, navigation outside articles, or the accuracy of every linked claim.
HTTP 200 alone cannot establish relevance or rule out a JavaScript-rendered error page.
The checked file set includes demo HTML, but only MkDocs article content contributes
links. Treat this as documentation-link coverage, not a full crawler of every demo.
