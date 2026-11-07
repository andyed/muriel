# Redline critique presentation

Use when a critique or revision needs an inspectable visual handoff. The calling
agent assembles this **after** the critic/jury has reported; the read-only critic
keeps its existing report format. A presentation does not convene a jury, alter
its ballots, manufacture findings, or certify a fix.

## Review task

The reader needs to locate a finding, inspect the cited capture, compare a later
revision without losing the object, and identify what still needs work. Direct
revision buttons and a keyboard-operable scrubber offer the same route. Original
comparison returns to the selected revision and its selected finding. Actual
pixels preserves a readable inspection scale on small screens with scrolling;
Fit restores the overview. Playback is opt-in and stops on manual interaction,
Escape, or a hidden tab. No automatic playback, looping, or prerequisite video.

The presentation shell uses high-contrast neutral chrome. The product's own
identity remains in the unmodified captures. Do not apply Muriel styling to a
screenshot or hide a defect to make the comparison attractive.

## Build

```sh
muriel redline review.json --output review.html
# Equivalent from the checkout:
python -m muriel.redline review.json --output review.html
```

One HTML file includes PNG captures, findings, and provenance hashes; it opens
offline without a server or dependencies. Captures are embedded byte-for-byte.
JavaScript adds navigation and overlays. Without JavaScript, and when printing,
all frames and their evidence remain available as a linear report.

## Manifest v1

```json
{
  "version": 1,
  "title": "Export controls",
  "summary": "Two captured revisions. Device acceptance remains open.",
  "frames": [
    {
      "id": "original",
      "label": "Original",
      "image": "captures/original.png",
      "source": "Commit abc123; Chrome; 1280×800 CSS px; DPR 1; idle state",
      "note": "Captured before the spacing change.",
      "findings": [
        {
          "id": "controls-gap",
          "title": "Competing actions read as one group",
          "severity": "HIGH",
          "status": "open",
          "rule": "Spacing should express task grouping",
          "evidence": "Capture shows an 8 px gap between the two action groups.",
          "fix": "Separate the groups while retaining their order.",
          "rect": [40, 100, 240, 60],
          "measure": {"axis": "x", "from": [152, 130], "to": [160, 130], "label": "Group gap"}
        }
      ]
    }
  ]
}
```

The example describes the shape of a manifest, not evidence of a real product.
All text fields shown are required except `rect` and `measure`. `findings` may
be empty; this means no findings supplied, not PASS. Frames have distinct IDs.
Keep a finding's ID stable across revisions so it can be followed through the
sequence. IDs must be unique within a frame. PNG paths resolve relative to the
manifest; network URLs are rejected. At most 30 frames, each at most 20 MiB and
20,000 pixels per edge. The output cannot overwrite an input or the template.

Coordinates use **capture pixels**, with the top-left as origin, not CSS pixels.
The compiler reads each PNG's dimensions. Regions must fit that capture. A
measurement uses two axis-aligned endpoints; its value is computed from those
coordinates, never copied from a claimed label. Name the measured quantity and
record the acquisition method/DPR in `source` or `evidence`. A bounding box is
an authored locator, not an inferred measurement. Leave it out for a whole-
artifact finding. Use equally framed captures where possible; differing sizes
are aligned top-left on one fixed canvas, never stretched to match.

`severity` retains the critic's CRITICAL/HIGH/MEDIUM/LOW vocabulary. `status`
is supplied by the author for **that capture**:

- `open`: the finding remains visible or otherwise supported.
- `addressed`: the stated change is evidenced in this revision; this is not
  human acceptance or certification that every related behavior passes.
- `unverified`: the capture/review cannot settle the claim. Record what is
  missing and the next useful check.

Do not infer addressed from a missing finding, an attractive after image, or a
green verdict. Preserve evidence limits, disagreements, and remaining issues.
PNG structural validation and hashes establish file identity, not correctness
of the critique or measurements. Test the product independently.

## Presentation choices and proof

Exact captured states switch in place; a brief redline reveal is the only
animation, disabled for reduced motion. Do not morph screenshots into invented
intermediate product states. Playback advances the captured stages and can be
paused. If a motion film is requested, route that production through the video
channel using the same reviewed states and findings; this tool does not export
MP4 or infer an edit history from two images.

Verify original/current return, stable finding selection, first/last boundaries,
keyboard range and buttons, mobile scrolling, reduced motion, no-JS/print
fallback, image decoding, and actual-pixel coordinate alignment. Report these
as artifact checks. Improved reviewer comprehension needs human evidence.

The redline-presentation idea was prompted by
[Damir Sokolovsky's unslop](https://github.com/heydamir/unslop), especially its
in-place review story. This implementation is original; no unslop code or
assets are bundled. Muriel keeps evidence and unresolved issues in the review.
