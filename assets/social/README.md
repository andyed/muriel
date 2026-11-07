# Social cards

## The jury card

"Better visual work from your coding agent." The card shows a dashboard panel
a coding agent drafted, the same panel after two rounds of fixes from muriel's
six AI jurors, and how many of the six would ship each: 1 before, 6 after.

| File | Size | Use |
|---|---|---|
| `jury-1600x900.png` | 1600×900, 16:9 | X in-stream; Bluesky and LinkedIn image posts. Content stays inside the centre 1600×838, so a 1.91:1 crop loses nothing. |
| `jury-1080x1350.png` | 1080×1350, 4:5 | Instagram portrait feed |

Sizes are from `plugins/muriel/skills/compose/channels/dimensions.md`. Both are
set for a phone feed: nothing that must be read is under 34 px on the canvas.
The six numbered pins on the draft match the numbered catches in the reply
text, which carries the detail the image leaves out, and the URL.

`jury-exhibit/` holds the three panel states (HTML and 1200 px renders) and the
counterfeit the Forger built while judging the draft. `jury-case.md` has the
outcome of each review, which finding each pin marks, and the ballots behind
the "1 of 6 → 6 of 6" verbatim.

Regenerate (needs `rsvg-convert` and macOS Helvetica Neue):

```bash
python3 tools/gen_jury_card.py
```

```bash
python3 -m muriel.contrast assets/social/jury-1600x900.svg assets/social/jury-1080x1350.svg
```

The SVGs reference `jury-exhibit/` by relative path, so keep that folder beside
them.
