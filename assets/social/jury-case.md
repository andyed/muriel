# The jury cases behind the jury card

On 2026-10-24 six muriel juror agents reviewed one dashboard panel three times:
the first draft, the draft after one round of fixes, and after a second round.
Each juror ran as its own subagent and saw none of the others' ballots. The
Stranger got the file path and the case id only.

| Case | Artifact | Would ship it |
|---|---|---|
| jx-1024-p2 | `jury-exhibit/panel.html`, the first draft | 1 of 6 (Stranger) |
| jx-1024-p3 | `jury-exhibit/panel-after-r1.html`, every p2 fix applied | 3 of 6 (Stranger, Thumbnail, Loupe) |
| jx-1024-p4 | `jury-exhibit/panel-after.html`, every p3 fix applied | 6 of 6, with the Squinter re-run as jx-1024-p4s |

The card's "1 of 6 → 6 of 6" compares p2 with p4.

**The Squinter's p4 vote.** In p4 the Squinter voted no on one HIGH: the four
KPI tiles tie under blur, with no single centre. Its ballot said the finding
drops if the chair states that the tiles are meant as equal peers. They are,
so the chair re-ran it as jx-1024-p4s on the same, unchanged panel, stating
the intended reading order: the four tiles as peers, then the signups chart,
then the revenue chart. It voted yes and noted that the statement anchored
its reading. In p2 the Squinter had no such statement. With one, its p2 HIGH
would still stand, because the chart outweighed the KPI row the layout
put first.

**The artifact.** The draft is a Q3 dashboard panel that Claude Code wrote
quickly, the way a coding agent writes a first draft: stock Tailwind colours,
rounded cards, two identical primary buttons, an inline SVG bar chart. No
defects were planted. Two were unintended slips in the chart: the bars sit on
a baseline that the tick spacing puts at 250, and the axis line ends 6 px
before the gridlines. All figures are sample data.

**Panel size.** jury.md caps a review panel at five jurors. These cases seated
all six on purpose, because the card exists to show the whole roster.

## The pins, and the catches in the reply text

The six numbered pins on the card's "Before" panel sit where each p2 ballot
locates the problem, in the draft's 1200×662 pixels. The reply post lists
them in the same order.

| # | Juror | Catch | p2 source | Severity |
|---|---|---|---|---|
| 1 | Squinter | numbers vanish when blurred | F1 | HIGH |
| 2 | Thumbnail | labels unreadable at preview size | t1 | HIGH |
| 3 | Stranger | no clear main button | Q3 answer ("I could not tell which one is meant as the main action") | not filed; the Stranger recuses hierarchy |
| 4 | Forger | 21 of 23 choices are stock | fg-1 | HIGH |
| 5 | Pedant | two numbers with no unit | P2, P3 | HIGH |
| 6 | Loupe | 26 notches at the axis | F2 | MEDIUM |

Two jurors found the same defect through different lenses. The Pedant, reading
only the source text and coordinates, worked out that the bars start at an
unlabelled 250 (P4). The Loupe, reading only 4× pixel crops, measured the same
baseline (F1).

The Forger's p2 counterfeit is kept as `jury-exhibit/forger-counterfeit.png`.

## Case jx-1024-p2: the first draft

### Every finding, worst first

| Juror | Id | Severity | Finding |
|---|---|---|---|
| Pedant | P1 | CRITICAL | Title says "Q3", the chart says "Last 13 weeks" with ticks W1–W13: the plotted weeks can't be recovered |
| Squinter | F1 | HIGH | At heavy blur only the chart survives; the KPI row the layout puts first is gone |
| Thumbnail | t1 | HIGH | At 400 px the KPI labels are unreadable; "3.1" and "4.2" become anonymous |
| Forger | fg-1 | HIGH | Stock-parts counterfeit in 1:48 matched 21 of 23 decisions |
| Pedant | P2 | HIGH | "Churn 3.1" and its delta have no unit |
| Pedant | P3 | HIGH | "Avg. session 4.2" and its delta have no unit |
| Pedant | P4 | HIGH | Bars start at 250, so their lengths don't match the tick values |
| Loupe | F1 | HIGH | Same baseline at 250, measured from pixels |
| Stranger | s1 | MEDIUM | Churn and Avg. session numbers have no unit or period |
| Squinter | F2 | MEDIUM | The red revenue chip outranks its three peers |
| Thumbnail | t2 | MEDIUM | At 400 px the green delta chips lose magnitude and direction |
| Pedant | P5–P10 | MEDIUM | Unstated delta bases, unverified values, undefined "Active users", relative timestamp, untitled y-axis, no accessible chart label |
| Loupe | F2 | MEDIUM | Rounded bottom corners leave 26 notches at the axis |
| Loupe | F3 | MEDIUM | Axis ends at x 1142, gridlines at 1148 |
| Squinter | F3 | LOW | The blue header buttons outrank the title, on hue only |
| Stranger | s2 | LOW | Only one delta chip names its comparison base |
| Thumbnail | t3 | LOW | Axis ticks and week labels are at the legibility threshold at 600 px |
| Pedant | P11 | LOW | CSS classes `up`/`down` encode favourability, not direction |

**Ship (each juror judging only by its own lens):** Stranger said yes. Squinter,
Thumbnail, Forger, Pedant and Loupe said no.

### Ballots, verbatim

```text
Juror ballot
Seat: squinter
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact (single option, k=1; chair supplied none; derived: printf '%s' "jx-1024-p2squinter" | shasum. At k=1, n mod 1! = 0 for any digest, so the order is the identity. I did not compute the digest because this seat's Bash may run muriel.squint only.)
Evidence seen: squint-heavy, squint-luma, squint-medium, squint-light, read in that order, each recorded before the next was opened. Sigma 60 / 36 / 18 px (heavy / medium / light); half_survival_px 126.0 / 75.6 / 37.8; luma = the heavy blur with colour removed. Matte #f3f4f6 (the artifact is opaque, so the matte has no effect). Stipulated order: none. Frame 1200x662, long edge 1200. Also read: references/jury.md (plugins/muriel/skills/compose path). Standing context (CLAUDE.md, MEMORY.md) was loaded at spawn; I found no string in it that I could tie to this artifact or to the question. Glob was unavailable; squint's exit 0 confirmed the path.
Evidence denied: sharp render, all text, brief, brand tokens, ballots. Also not read: thumb-eighth, thumb-16px, thumb-16px-zoom. squint wrote them to the out-dir but did not open them.
Reasoning: Per-level record, heaviest first.
  HEAVY (halves masses under 126 px): One centre of mass. A saturated blue horizontal band at x~130-1100, y~380-560 (about 80% of the width, 27% of the height, 20% of the frame) sits lower-centre. A much weaker pale-blue patch fills the top-right corner (x~900-1200, y~0-130). There is a faint pink-grey blob at x~300-470, y~130-260 and a faint grey smudge in the top-left corner (x~0-200, y~0-150). The rest of the upper 55% is near-white ground. The eye goes: band, top-right patch, pink blob, top-left smudge. Single centre of mass: yes, the band.
  LUMA: The band holds as mid-grey, darkest at x~950-1050, so its dominance does not depend on hue. The top-right patch drops to pale grey, level with the top-left corner. The pink blob holds as a light-grey disc at x~330-450, y~140-240, about equal to the top-right patch. The primary is not saturation posing as dominance.
  MEDIUM (halves masses under 75.6 px): The band spans x~100-1130, y~370-550, and its top edge rises from left to right (y~440 to ~370). The top right separates into a pale-blue pill (x~910-1160, y~30-85). The top left shows a grey bar (x~30-210, y~30-80). A row of four small masses appears at y~150-230, centred at x~100, 390, 650 and 940. Member 2 is red-pink and clearly the strongest; members 1, 3 and 4 are faint grey-green. Order: band, member-2 blob, top-right pill, top-left bar, members 1/3/4.
  LIGHT (halves masses under 37.8 px): The band resolves into 13 vertical blue bars (x~105-1125, y~370-555), broadly rising to the right. The row resolves into four peer tiles inside a white strip (y~110-240). Each tile has a dark-grey value mass (x~60-160, 340-465, 625-670, 915-970; y~150-185) above a small chip. Chips 1, 3 and 4 are green; chip 2 is red (x~340-440, y~195-225). A small grey block sits at x~60-170, y~280-300 above the bars. The top-right pill splits into two adjacent blue pills. The top-left bar sits at x~30-200, y~35-70.
  RECOVERED ORDER (no stipulation existed in context, so it was not anchored): 1 bar chart, 2 top-right pills, 3 tile-2 red chip, 4 top-left title bar, 5 the four value masses, 6 green chips, 7 the small block above the chart.
  INTENDED ORDER, INFERRED (single call, no stipulation): The layout reads as a header row, then a four-tile peer row directly under it, then a small label block, then the chart. Inferred intent by position: title, KPI row (values first, chips under their values), chart label, chart; header pills tertiary. The inference is genuinely ambiguous: position says the KPI row comes first, area says the chart. I graded on position. If the chair stipulates the chart as primary, F1 drops, F2 stays MEDIUM as a divergence below a matching top-1, and F3 stays LOW.
  COMPARISON: The recovered top-1 (chart) is not the inferred top-1 (KPI row). At heavy the KPI row is absent except for one pink trace from tile 2's chip. The value masses are 45-125 px wide, under the 126 px half-survival width. Within the row, member 2 breaks rank from medium upward, and it does so on lightness as well as hue, since it survives luma. The top-right pills come in second at heavy, ahead of the title, but mostly on hue; at luma they level with the title corner.
  COMPARISON-FORM PRECONDITION: The four-tile row reads as a peer-tile comparison form. No intent was stipulated, so the envelope exemption was unavailable and I graded normally. Under the exemption, the row envelope (white strip y~110-240) fails to separate from its surround at heavy, which would be HIGH on the envelope. That coincides with F1 and is not filed twice. Member 2 dominating its peers is MEDIUM under either reading.
Findings:
  - id: F1
    target: artifact
    rule: SKILL.md "Give each composition one dominant focal point and a legible reading order"
    severity: HIGH
    evidence: At heavy (half_survival 126 px) the only mass is the blue chart band (x~130-1100, y~380-560, ~20% of the frame). The KPI row at y~110-240, which the layout places first, leaves only a faint pink trace at x~390, y~190. All four value masses (45-125 px wide) fall under the 126 px half-survival width and are gone. Recovered top-1 = chart; inferred top-1 = KPI row.
    fix: If the KPI row leads, give the four value masses enough area or a filled tile to clear ~126 px of mass, and lighten the chart bars to a tint so the chart drops to second; if the chart leads, the chair should stipulate it and this finding drops.
  - id: F2
    target: artifact
    rule: Peripheral acuity falloff
    severity: MEDIUM
    evidence: At medium (half_survival 75.6 px) tile 2's red chip (x~340-460, y~150-230) is the only member of the four-tile row to separate from the ground; members 1, 3 and 4 (x~100, 650, 940) are faint grey-green. At heavy it is the row's only trace, and it holds at luma as a light-grey disc, so this is lightness, not hue alone. The first saccade into the row lands on a chip, not on a value, and tile 2 outranks its peers and the title.
    fix: Bring chip 2 to the visual weight of the green chips (tint or outline instead of a filled block), or carry the emphasis on tile 2's value mass; if the stand-out is intended, the chair should stipulate it and this finding drops.
  - id: F3
    target: artifact
    rule: Bertin (hue does not carry rank under degradation)
    severity: LOW
    evidence: At heavy the top-right pale-blue patch (x~900-1200, y~0-130; two pills at x~905-1165, y~40-80 at light) is the second mass after the chart, ahead of the top-left title bar (x~30-200, y~35-70). At luma it falls to parity with the title corner, so it outranks the title only in colour.
    fix: Reduce the header pills to a lighter tint or outline so the title bar is not outranked at heavy.
Issue rank: F1, F2, F3
Ship (this seat's loss only): no
Confidence: medium
Recused: typography, contrast ratios, copy, labeling, units, brand voice, scale survival, reproducibility, meaning of chip colours
```

```text
Juror ballot
Seat: thumbnail
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact (single option, k=1, so the permutation is trivial. The chair supplied none, so I derived it: printf '%s' "jx-1024-p2thumbnail" | shasum = 797a9fc9...; n mod 1! = 0)
Evidence seen: muriel.squint downscales (exit 0, matte #f3f4f6). These were px16_zoom 128x72, also magnified to 512x288 nearest-neighbour from the same 16 px render; px16 16x9; and eighth 150x83, also magnified 6x nearest-neighbour. Under the chair's authorization I also made ImageMagick downscales to 400x221 and 600x331 on the same matte, and read crops of them at 4x and 3x nearest-neighbour. I measured glyph row extents on the 400 and 600 renders. The manifest gives 1200x662, which matches the filename's claim. Intended sizes were stipulated by the chair: 1200 px at 100%, about 600 px in split-screen, and about 400 px as a Slack screenshot. Not a favicon.
Evidence denied: full-size render, blur ladder (light/medium/heavy/luma were written by the lens and not opened), brief, brand tokens, ballots
Reasoning:
  px16_zoom / px16 (16x9). Is: a pale web panel or page card. It does not read as a photo. It is not a favicon, so rule a is recorded and not fired. Survives: a saturated blue horizontal band across rows 5-7, which is the bar chart. The band's top row runs from near-white at the left to mid-blue at the right, so the rising signups trend survives even at 16 px as a left-to-right luminance ramp. Also surviving: a blue block at top right (the button pair) and one warm pixel pair at upper left-centre (the revenue chip), the only warm hue in the frame. Gone: all text and numerals, and the four KPI tiles as separate units; they merge into one white field. Invented: nothing that changes the reading. The chip reads pinkish rather than red.
  eighth (150x83). Is: a dashboard with a title block, two buttons, four KPI tiles and a bar chart. Survives: all 13 bars, the rising trend and the dips at W3/W5/W7/W9/W11. The four large KPI numerals hold as bold figures, the red pill under the revenue figure is the single warm accent, and three green pills and the title mass also survive. Gone: KPI labels, chip text, axis ticks, week labels, subtitles, legend text, button labels and gridlines. Invented: every bar gains a 1 px pale-blue rim (#9dc0fa) on its top and both sides, with a darker ringing column just inside. The bars therefore read as dark cores under a pale overlay, which suggests a second series that does not exist. The legend swatch resamples to the rim colour rather than the bar colour. 150 px is below every stipulated size, so I recorded this under rule d and did not fire. Rule b passes: the primary signal (four KPIs, rising signups, one negative KPI) can be recovered at 1/8.
  400 px (Slack, stipulated). Survives: the title, the KPI values, the bars and their trend, and the red chip. The red chip's text sits in 4 rows inside an 8-row pill and is marginal but readable. The bar halo artifact does not occur at this size. Gone: the KPI labels are 3 px tall with sub-pixel strokes, and the letterforms can only be guessed from genre. Of the values, "$184.2k" keeps its identity through the $ sign, "12,480" is ambiguous, and "3.1" and "4.2" are anonymous. Green chip glyphs are 3 rows tall and the magnitudes 8.2% / 0.4 / 0.3 cannot be resolved. Each arrow is a 3x3 px block; its direction survives only as a one-pixel difference in row width (up: 1-3-3, down: 3-1-1). Axis ticks and W1-W13 are 3 px and gone. Subtitles, legend label and button labels are gone. Required versus expected: in a click-to-expand inline preview, losing ticks, subtitles, legend text and button labels is acceptable. Losing the KPI labels is not, because a KPI value without its name carries no signal. Caveat: I read "near 400 px" as 400 device px. On a 2x display Slack resamples to about 800 device px, and the label tier would land between my 400 and 600 measurements, about 5-6 px. That would demote t1 to MEDIUM. Display density is the chair's fact to supply.
  600 px (split-screen, stipulated). Survives: KPI labels and chip text at 5 glyph rows, legible. Arrow direction, button labels and both chip colours also survive. Marginal: y-tick numerals and W1-W13 at a 4 px cap height with soft strokes. "1500" and "1000" differ by a 2-3 px glyph. "Updated 2h ago", "Last 13 weeks" and the legend label are in the same tier. They are at the threshold but have not dissolved. Gridlines resample to a 1-2 px band barely distinct from the card. That is a visibility question I leave to contrast tooling, so I make no finding on it. Caveat: if the live page reflows at half-width instead of scaling, the 600 px raster is not what the user sees, and t3 applies only to scaled captures (screen-share, zoom-to-fit, pasted screenshot).
  1200 px at 100%: no resampling, so it is outside this lens, and the full-size render was denied. Not judged.
  No unseal or tally was offered.
Findings:
  - id: t1
    target: artifact
    rule: c. Text survival against intent
    severity: HIGH
    evidence: At 400 px (Slack inline preview), the KPI tile labels "Active users", "Revenue", "Churn" and "Avg. session" resample to 3 px glyph height with sub-pixel strokes and cannot be read. "3.1" and "4.2" become anonymous numbers and "12,480" loses its identity. Only "$184.2k" keeps meaning, through the $ sign. At 600 px the same tier measures 5 rows and holds.
    fix: Raise the KPI label tier to about 1.6x its current size (or one weight step heavier and about 1.4x) so it lands at 5 px or more in a 400 px preview.
    form_fatal: no
  - id: t2
    target: artifact
    rule: c. Text survival against intent
    severity: MEDIUM
    evidence: At 400 px the three green delta chips' glyphs are 3 rows tall. The magnitudes (8.2%, 0.4, 0.3) are unresolvable, and each arrow is a 3x3 px block that is up or down only by a one-pixel row-width difference, so "Churn, down 0.4" and the two up chips read as identical green pills. Colour still carries polarity. The red revenue chip's text is slightly larger (4 rows) and survives marginally.
    fix: Set the green chips' text and arrow at least as large as the revenue chip's text, which survives at 400 px, so direction and magnitude hold in the preview.
    form_fatal: no
  - id: t3
    target: artifact
    rule: c. Text survival against intent
    severity: LOW
    evidence: At 600 px (split-screen) the smallest type tier (y-tick numerals 2000/1500/1000/500, week labels W1-W13, subtitles, legend label) measures a 4 px cap height with soft strokes. It is at the threshold but not dissolved, and one step smaller loses it. This applies only if the 600 px view is a scaled capture rather than a reflowed page.
    fix: Bump the axis-tick and week-label tier about 1.25x so numerals land at 5 px or more at 600 px, or confirm the live page reflows at half-width and drop this finding for the live surface.
    form_fatal: no
Issue rank: t1, t2, t3
Ship (this seat's loss only): no
Confidence: medium
Recused: full-size hierarchy, contrast ratios (including gridline and grey-label visibility), labeling correctness (units, axis range), terminology, distinctiveness, brand voice
```

```text
Juror ballot
Seat: stranger
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact (single artifact, k=1; chair supplied none, so the permutation is trivial)
Evidence seen: <scratchpad>/redo/exhibit/panel-desktop-1200x662.png, read once. The path carried some meaning: "panel-desktop-1200x662" told me it is a desktop-sized panel, and "redo/exhibit" hinted that it is a specimen being redone. I did not use either to work out what it is for. The harness also loaded the user's general CLAUDE.md and memory index into my context. They describe the user's research projects, not this artifact, and the chair's invocation contained only the path and the decision id. The audit was clean, so I proceeded.
Evidence denied: brief, design rationale, option purpose, project context, brand tokens, ballots
Reasoning: Q1, what is this for: this is a business dashboard summarizing one quarter ("Q3 Overview") for some software product. It shows active users, revenue, churn, average session and weekly signups over the last 13 weeks. It is for someone on the team, a manager or product person, checking how the quarter is going and possibly pulling the data or the full report. I was not told whose business it is or which year, but I could tell what it is for straight away.
  Q2, what is the one number: four headline numbers sit side by side with equal weight, but the one I came away with is revenue, $184.2k, down 12% vs Q2. It is the only alarm-coloured chip and the only change that says what it is compared against. My one-sentence takeaway: users and signups are growing, but revenue fell 12% from last quarter. If the intended takeaway is the signup growth or the user count, this is not what I took from it. Two of the four numbers I could not fully read: "Churn 3.1" and "Avg. session 4.2" carry no unit, so I could not tell what 4.2 counts (minutes? pages? something else?) or whether 3.1 is a percent, and over what period. The change chips show 8.2% on one card and bare 0.4 and 0.3 on others, and only revenue says "vs Q2". I assumed the rest also compare to Q2, but that is my guess, not something the panel told me.
  Q3, where do I click: two buttons at top right, "Export CSV" and "View full report". I could not tell which one is meant as the main action. If I had to act I would pick "View full report" as the next step. My eye went first to the "Q3 Overview" title, then to the red revenue chip, then down to the bar chart. The panel seems to want me to read the headline numbers, notice the revenue drop, and then open the full report.
  Evaluation: I understood the premise fine. A quarterly business summary is about the most familiar genre there is, so this tells the chair less about a real first-time viewer than it seems to. My only admissible problems are about what two numbers and the change chips refer to. Those problems would still be there if the panel were beautifully made.
Findings:
  - id: s1
    target: artifact
    rule: b. Referent opaque (partial: the quantity is named but its unit and period are missing, so MEDIUM rather than the rule's default HIGH)
    severity: MEDIUM
    evidence: I could tell "Churn" is about people leaving and "Avg. session" is about how long or how much people use the product. But from "3.1" and "4.2" alone I could not tell what either number counts: whether 3.1 is a percent, over what period, and whether 4.2 is minutes, pages or something else. With the unit missing, I also could not judge whether the green "down 0.4" on churn and "up 0.3" on session are big or small moves.
    fix: Put the unit, and for churn the period, directly on each headline value.
    form_fatal: no
  - id: s2
    target: artifact
    rule: b. Referent opaque
    severity: LOW
    evidence: Only the revenue chip says what it is compared against ("vs Q2"). The other three chips (8.2%, 0.4, 0.3) give no baseline and mix a percent with bare numbers, so I could not tell whether they are quarter-over-quarter, week-over-week, percent changes or absolute changes. I assumed vs Q2 but could not confirm it from the panel.
    fix: Give every change chip the same stated baseline and unit, or state one shared baseline once at the top of the panel.
    form_fatal: no
Issue rank: s1, s2
Ship (this seat's loss only): yes
Confidence: medium
Prior strength: high
Recused: craft, hierarchy (including which of the two buttons, or which headline card, should dominate), contrast ratios, typography, scale survival, labeling correctness (including the chart's y-axis range), distinctiveness, brand voice
```

```text
Juror ballot
Seat: forger
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact   (printf '%s' "jx-1024-p2forger" | shasum -> 92824bcbd5c3d183b6c07fae4c344c946cb7cf6a; byte 0x92 % 1 = 0)
Evidence seen: the artifact raster exhibit/panel-desktop-1200x662.png; its intended use (analytics dashboard panel in a web app); a generic component library (Tailwind v3 default palette and scales; Tremor, shadcn and Recharts idioms; Inter/system-ui)
Evidence denied: the artifact source exhibit/panel.html (not read; I did not run devibe on it, render it or grep it). No brand tokens or design-system export were supplied.
Reasoning:
  Elapsed: 01:48 (2026-10-24T15:57:19Z to 15:59:07Z; inventory and pixel sampling ran from 15:52:59Z). This is an observation only and no severity keys off it.
  Forgery: <scratchpad>/redo/jury/forger/artifact.forgery.html; sidecar <scratchpad>/redo/jury/forger/artifact.forgery.md; renders <scratchpad>/redo/jury/forger/artifact.forgery.render-draft-desktop-1200x690.png (pass 1) and <scratchpad>/redo/jury/forger/artifact.forgery.render-desktop-1200x666.png (pass 2); original staged as <scratchpad>/redo/jury/forger/artifact.original-desktop-1200x662.png
  Not reproduced: (9) Churn delta coloured by valence (green ▼ 0.4) rather than by sign; (10) Revenue delta escalated to a solid red-500 pill with white text and the comparison basis "–12% vs Q2", unlike the other three tinted, glyphed badges
  Counts: F=23 R=2 Rs=0; inventory=24; template-default=21, domain-specific=2, convention=0, encoding-optimal=1. R/F = 0.087.
  Passes: 1 draft, 1 revision, 2 of 2 renders. The ceiling bound. The forgery is complete.
  Render: rung 1 for the counterfeit: /opt/homebrew/bin/python3 -m muriel.capture file://.../artifact.forgery.html --tiers desktop --selector '#panel' --scale 1 --slug artifact.forgery.render[-draft]. Rung 2 for the original, which was supplied as a raster and read as-is; it was not regenerated from panel.html.
  Scope disclosure: to get exact hex values and geometry for the inventory I sampled pixels in the supplied PNG with Pillow (/opt/homebrew/bin/python3 -I -c, read-only, no writes). That call is not on the scoped compute list. Other housekeeping was shasum, mkdir/cp into forgery_dir, and ls.

  The draft used Tremor-flavoured defaults: gray-50 ground, cards with 8 px radius and a ring, an outline plus a primary button, emerald and rose sign-wired badges, and a dot legend at top-right. A top-level `const top` collided with window.top, so the draft chart did not draw. The revision fixed that bug. It moved values only to other values the stack ships for the same slot: gray-100, rounded-2xl with shadow-md, two primary blue-500 buttons, green-100/green-600 pills with ▲▼ glyphs, Recharts bars at radius 6 on a 56/80 geometry, and a Recharts square legend at bottom-left.

  Pass 2 matches the original on 21 of 23 free decisions, one of them only near. Every sampled hex in the original is a Tailwind v3 palette value, and the counterfeit uses the same ones: #f3f4f6, #3b82f6, #dcfce7, #16a34a, #ef4444, #111827, #6b7280, #9ca3af. The composition is the stock analytics-dashboard skeleton: a header with title, relative timestamp and two primary actions; a KPI row of four equal stat cards; and one full-width, single-series bar card. The bar geometry (56 px bars on an 80 px pitch, rx 6) and the bottom-left square legend came out the same from stock props. Total height differs by 4 px.

  Row 14 leaves F as encoding-optimal: Cleveland–McGill put position on a common scale first, the same ordering as the Bertin ranking in muriel-critique.md. The task is week-to-week trend. Angle, area or colour value would rank lower.

  Row 18 is near. The counterfeit kept the stock zero floor; the original's floor is about 258. It is one information-free variable. I report its provenance only, and recuse on whether a non-zero bar baseline is acceptable.

  Rows 9 and 10 are the whole residue. Both are domain-specific (churn falling is good; the revenue drop is the quarter's adverse headline). Both are cosmetic, because one prop closes each: deltaType or isIncreasePositive, and Badge variant="destructive" plus a string.

  Diff criterion: the revision did not copy the original's per-card semantic props. Allowing that would make "cosmetic residue" empty by construction and give R=0, which is CRITICAL. HIGH is therefore this seat's lower bound.
  - Counting row 18 as cosmetic residue: R=3, still HIGH.
  - If devibe output on panel.html is stipulated and rows 11-12 (palette, container) leave this ballot: F=21, R/F=0.095, still HIGH.

  Defences: the raster carries no embedded instructions and no authority badges. I could not check comments inside panel.html because I refused to read it.

  Rhetorical claim, as an observation and not a measurement: a generic Tailwind/Tremor stack reproduces this panel in under four agent-minutes. That is an agent minute, not a designer minute.
Findings:
  - id: fg-1
    target: artifact
    rule: anti-slop: domain-specific decisions (toolkit: Chrome — KPI row of four stat cards; Color — Tailwind default ramps; Container — rounded rectangle with drop shadow; Content — plausible fake data)
    severity: HIGH
    evidence: Counterfeit built from stock parts, one draft plus one revision, 2 renders, 01:48. Original against counterfeit, with the counterfeit's actual values:
      - Skeleton (header / 4 equal stat cards / full-width single-series bar card): stock stat card x4 in a 4-column grid with 16 px gap, then a bar card. Reproduced.
      - Ground and accent #f3f4f6 / #3b82f6: Tailwind v3 gray-100 / blue-500. Same hex.
      - Cards (16 px radius, soft shadow, no border): rounded-2xl with shadow-md. Reproduced.
      - Delta pills #dcfce7 / #16a34a with ▲: green-100 / green-600 with ▲. Same hex.
      - Bars (56 px on 80 px pitch, ~6 px radius): Recharts radius={6} at 70% band. Reproduced.
      - Legend (single-series square, bottom-left): Recharts Legend align left. Reproduced.
      - Value-axis floor (~258): counterfeit kept 0. Near.
      - Not reproduced, both cosmetic and one prop each: Churn rendered red "▼ 0.4" by the sign-wired badge (original green); Revenue rendered as a tinted red-100 "▼ 12%" (original solid red-500 "–12% vs Q2").
      - F=23, R=2, Rs=0, R/F=0.087.
    fix: Give at least one region structure derived from this quarter's data or task rather than a stock component — for example a plan or prior-quarter reference in the signups chart, or a KPI layout organised around the revenue story instead of four equal stat tiles — so the residue includes structural items and not only two badge props.
    form_fatal: no
Issue rank: fg-1
Ship (this seat's loss only): no
Confidence: high
Recused: hierarchy, contrast, typography quality, labeling, units, scale survival, accessibility, local finish; plus the integrity of the value axis's non-zero floor on a bar chart (provenance reported only)
```

```text
Juror ballot
Seat: pedant
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact (chair supplied none; derived: printf '%s' "jx-1024-p2pedant" | shasum -> 3268b1bd...; k=1, so permutation 0 is the only one)
Evidence seen: HTML source with an inline SVG at <scratchpad>/redo/exhibit/panel.html (89 lines). I read the whole source file and grepped it for text nodes. I found 37 text-bearing strings. I also used the SVG coordinates in the source (gridline y, axis-line y, rect y and height) to check the tick scale. There is no sibling data file. I did not open panel-desktop-1200x662.png.
Evidence denied: rendered composition, brief, ballots
Reasoning: The 37 strings are: <title> "Q3 Overview" L5; h1 "Q3 Overview" L32; "Updated 2h ago" L33; the buttons "Export CSV" L36 and "View full report" L37; four KPI cards at L42-45 with labels "Active users", "Revenue", "Churn" and "Avg. session", values "12,480", "$184.2k", "3.1" and "4.2", and deltas "▲ 8.2%", "−12% vs Q2", "▼ 0.4" and "▲ 0.3"; h2 "Weekly signups" L49; subtitle "Last 13 weeks" L50; y ticks "2000", "1500", "1000" and "500" L60; x ticks "W1" through "W13" L78-81; and the legend "Signups" L84. There is no aria-label, alt, <desc>, <figcaption>, role or SVG <title>.
Probe list:
- Percentages. "8.2%" L42 and "−12%" L43 are both unverified because there is no data source. Only the Revenue delta names its comparison base ("vs Q2").
- Bare numerals. "3.1" L44 (Churn) has no unit: it could be percent, a rate or a count. "▼ 0.4" L44 also has no unit, and if churn is a percentage it could mean percentage points or a relative change. "4.2" L45 (Avg. session) has no unit: it could be minutes, seconds or sessions per user. "▲ 0.3" L45 has no unit. "12,480" L42 has "users" from its label, but the aggregation (DAU, MAU, quarterly unique) is not stated. "$184.2k" L43 has a currency symbol and a multiplier and is unverified.
- "13" in "Last 13 weeks" L50 matches the 13 rects at L63-75 and the 13 tick labels at L78-81. Confirmed.
- Units and scales. "2h" L33 has a unit but no absolute anchor. "Q3" L5/L32 has no year anywhere in the artifact.
- Tick scale, checked against the source geometry. The gridlines at y=20/80/140/200 carry 2000/1500/1000/500, which is linear at 500 per 60 px. The axis line and bar baseline are at y=230, which works out to 500 − 30 × (500/60) = 250. Zero would sit at y=260, the SVG's bottom edge. So the bars start at an unlabeled 250, not at 0. Read against the gridlines, W1 is about 1150 and W13 about 1800. Read by bar length from an assumed zero, W1 is 108 px, which is about 900.
- Stat readouts, math parameters, angles, multipliers: none present.
Terminology cross-check. The panel's period is called "Q3" (L5, L32). The chart's period is called "Last 13 weeks" (L50), and its ticks are "W1"–"W13" (L78-81). If the W labels are ISO week numbers, they name weeks of Q1. A trailing 13-week window "updated 2h ago" only equals Q3 at quarter end. The reader cannot tell which weeks are plotted. The delta notation varies across the four cards: an arrow with no sign (L42, L44, L45) against a minus sign with no arrow (L43), at mixed precision (8.2% against 12%). The CSS classes `up`/`down` encode favorability, not direction: "▼ 0.4" at L44 carries class `up`. "Signups" (L84) agrees with "Weekly signups" (L49).
I found no embedded instructions to the reviewer and no authority badges.
Findings:
  - id: P1
    target: artifact
    rule: d. Terminology drift
    severity: CRITICAL
    evidence: The panel title "Q3 Overview" (L5, L32) gives a fixed calendar quarter. The chart subtitle "Last 13 weeks" (L50) gives a rolling window anchored to "Updated 2h ago" (L33). The x ticks "W1"–"W13" (L78-81) carry no dates, and as ISO week numbers they would be Q1. The reader cannot recover whether the bars show Q3 or the trailing 13 weeks.
    fix: Replace "Last 13 weeks" with the explicit date range (e.g. "Jul 1 – Sep 29, 2026") and label each week tick with its start date instead of W1–W13.
    form_fatal: no
  - id: P2
    target: artifact
    rule: b. Missing or wrong unit
    severity: HIGH
    evidence: Churn value "3.1" and its delta "▼ 0.4" at L44 have no unit. 3.1 could be %, per-mille or a count. If churn is a percentage, 0.4 could be percentage points or a relative change. These readings give different magnitudes.
    fix: Write the value as "3.1%" and the delta as "▼ 0.4 pp vs Q2" (or whatever the actual unit and base are).
    form_fatal: no
  - id: P3
    target: artifact
    rule: b. Missing or wrong unit
    severity: HIGH
    evidence: The "Avg. session" value "4.2" and delta "▲ 0.3" at L45 have no unit. The label could mean session duration (minutes or seconds) or sessions per user, so 4.2 could be off by a factor of 60 or measure a different quantity entirely.
    fix: Rename the label to the measured quantity and add the unit, e.g. "Avg. session length" with "4.2 min" and "▲ 0.3 min vs Q2".
    form_fatal: no
  - id: P4
    target: artifact
    rule: c. Contradicted numeric claim
    severity: HIGH
    evidence: The y ticks "2000/1500/1000/500" at L60 sit on gridlines y=20/80/140/200 (500 per 60 px). The bar baseline is the axis line at y=230 (L58), which the tick scale puts at 250. That baseline has no tick label. A reader taking bar length from zero reads W1 (height 108, L63) as about 900, but against the gridlines it is about 1150. The bar lengths are not proportional to the labeled values.
    fix: Move the bar baseline to the 0 position and add a "0" tick; if the cut stays, label the baseline "250" and mark the axis as broken.
    form_fatal: no
  - id: P5
    target: artifact
    rule: a. Unlabeled number
    severity: MEDIUM
    evidence: The deltas "▲ 8.2%" (L42), "▼ 0.4" (L44) and "▲ 0.3" (L45) state no comparison base. Only "−12% vs Q2" (L43) names one. The notation also changes between cards: arrow without sign at L42/44/45, minus without arrow at L43, and mixed precision ("8.2%" against "12%").
    fix: Add "vs Q2" (or the true base) to every delta and use one sign convention and one precision across all four cards.
    form_fatal: no
  - id: P6
    target: artifact
    rule: c. Unverified numeric claim
    severity: MEDIUM
    evidence: No source of truth exists for "12,480", "$184.2k", "−12%", "8.2%", "3.1", "0.4", "4.2", "0.3" (L42-45) or for the 13 bar heights (L63-75). The only internal checks that passed are the 13-bar count and the linear tick spacing. All values are reported as unverified, not as wrong.
    fix: Supply the generating data file, or a query or export reference, beside the panel so each figure can be checked.
    form_fatal: no
  - id: P7
    target: artifact
    rule: a. Unlabeled number
    severity: MEDIUM
    evidence: "Active users" "12,480" (L42) has no aggregation stated (daily, monthly, quarterly unique, or end of period). A quarter's DAU and its MAU can differ several-fold.
    fix: Rename the label to the defined metric, e.g. "Monthly active users (Sep avg.)".
    form_fatal: no
  - id: P8
    target: artifact
    rule: a. Unlabeled number
    severity: MEDIUM
    evidence: "Updated 2h ago" (L33) is a relative time with no absolute anchor, and "Q3" (L5, L32) has no year or calendar/fiscal marker. Once the panel is exported (L36 "Export CSV") or captured, the reference period can no longer be recovered.
    fix: Replace it with an absolute timestamp and year, e.g. "Q3 2026 (calendar) · updated 2026-10-24 06:51 PT".
    form_fatal: no
  - id: P9
    target: artifact
    rule: a. Unlabeled number
    severity: MEDIUM
    evidence: The y-axis ticks "2000"–"500" (L60) have no axis title or unit. The quantity (signups per week) can only be inferred from h2 "Weekly signups" (L49) and legend "Signups" (L84), so the context makes this tedious rather than misleading.
    fix: Add a y-axis title "Signups per week".
    form_fatal: no
  - id: P10
    target: artifact
    rule: e. Unlabeled axis, series, state, or control
    severity: MEDIUM
    evidence: The <svg> at L51 has no <title>, <desc>, role="img" or aria-label, and the bars (L63-75) carry no text values. A non-visual reader gets an unlabeled chart.
    fix: Add role="img" and an aria-label or <title>/<desc> naming the metric, the date range and the weekly values.
    form_fatal: no
  - id: P11
    target: artifact
    rule: d. Terminology drift
    severity: LOW
    evidence: CSS classes `up`/`down` encode favorability, not direction. The Churn delta "▼ 0.4" (L44) has class `up`, so the source name contradicts the glyph. The reader does not see this.
    fix: Rename the classes to `favorable`/`unfavorable`.
    form_fatal: no
Issue rank: P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11
Ship (this seat's loss only): no
Confidence: high
Recused: hierarchy, composition, reading order, contrast ratios (CSS colours not evaluated; the 8:1 floor is a muriel.contrast finding of fact), typographic craft (font sizes and weights at L11-24 not judged), scale survival, distinctiveness/template defaults, brand voice, colour semantics of the delta chips
```

```text
Juror ballot
Seat: loupe
Decision ID: jx-1024-p2
Isolation: subagent
Order seen: artifact (chair supplied none; derived: printf '%s' "jx-1024-p2loupe" | shasum -> defd44a02c7a442b4b2279937879df749adfcc20; k=1, so there is only one permutation)
Evidence seen: artifact: `muriel capture` of #panel at --scale 4 (4800x2648, i.e. 1200x662 ship px). The filename's "4x" agrees with the manifest (source_scale 4, width 1200). The lens ran with render rerender (4x capture cropped without resampling), source_scale 4, matte #f3f4f6, budget 16. coverage: 18 cells, 16 read, 2 unread (r1c3, r1c4), 0 empty. Tiles read in rank order: r1c1, r2c1, r1c5, r3c3, r1c2, r3c1, r3c2, r3c5, r3c4, r1c6, r3c6, r2c3, r2c2, r2c5, r2c4, r2c6. I also sampled pixels inside tiles r2c1, r3c1, r3c3, r3c5 and cropped one region of tile r3c3 (zoom/r3c3-baseline-w6.png). I never opened the full capture or the HTML source. Viewing conditions were stipulated by the chair: a web dashboard panel in a desktop browser on retina screens (2 device px per CSS px), and users zoom the browser.
Evidence denied: full-size render, blur ladder, downscales, overview, brief, brand tokens, ballots
Reasoning:
  r1c1 (0,0). In it: title, subtitle, a metric card's top-left and bottom-left corners with its shadow, a label, a large value, and a green delta pill holding a triangle and a percentage. Checked: card corner arcs against the shadow, pill edge around its glyphs, triangle-to-text spacing, the % and the comma in the value for clipping. Wrong: nothing.
  r2c1 (0,224). In it: a metric card's bottom edge, the chart card's top-left corner, the chart header and subtitle, y ticks 2000/1500/1000 with their gridlines, and two bar tops. Checked: the start of every gridline (all at ship x 92), tick labels against their gridlines (vertically centred), descenders in the header, and bars against the 1000 gridline (bar drawn on top, correct order). Wrong: nothing.
  r1c5 (896,0). In it: two buttons, a metric card's top-left corner, a label, a value, and a delta pill. Checked: button padding on Export CSV (18 and 18 ship px), the left padding on the second button, and the pill's fit. The second button runs off this tile, so I judged it in r1c6. Wrong: nothing.
  r3c3 (448,406). In it: bottoms of bars W5 to W8, the x-axis rule, x labels, and the card's bottom edge. Checked: each bar's bottom corners where they meet the axis, label centring, and gridlines passing behind the bars. Wrong: the bars round their bottom corners as well as their tops (F2). Pixel sample at W6: the fill pulls in from x+0 at ship y 550 to about x+4.5 at y 555.5, leaving a white wedge of about 6x6 ship px between each bottom corner and the axis. Where a bar is present, its fill also covers the upper half of the 1 px axis, so the rule runs at half thickness under bars and full thickness in the wedges.
  r1c2 (224,0). In it: the right corners of one metric card and the left edge of the next, a label, a value, and a red delta pill. Checked: pill padding (8.5 and 7.75 ship px), the leading dash and the % for clipping, and the gap between the cards. Wrong: nothing.
  r3c1 (0,406). In it: ticks 1000 and 500 with their gridlines, the x-axis rule, bars W1 and W2, x labels, the legend swatch and label, and the card's bottom-left corner. Checked: gridline spacing against the axis position, plus the legend swatch against its label. Measured gridlines: 1000 at ship y 466, 500 at 526, a step of 60 px per 500. The axis is at 556, half a step below 500. Zero on that scale falls at 586. Bar tops agree with the gridlines (W1 top 448 reads about 1150), but the bars start at 556, the scale's 250. No tick sits at the axis. Wrong: F1. The F2 wedges recur here. Legend is clean.
  r3c2 (224,406). In it: bars W2 to W5, labels, gridlines, axis. Checked: label centre against bar centre (W3 and W4 within 0 px), and gridlines behind bars. Wrong: F2 recurs. Nothing new.
  r3c5 (896,406). In it: bars W11 to W13, the right end of the axis, the right ends of the gridlines. F3 first appears here and is whole in r3c6, so I report it from there.
  r3c4 (672,406). In it: bars W8 to W10 and their labels. F2 recurs. Labels centred. Nothing new.
  r1c6 (944,0). In it: the second button whole, and a metric card's top-right and bottom-right corners. Checked: button text padding (18 and 18 ship px, last glyph not clipped), and whether the button's right edge and the card's right edge line up (both at ship x 1168). Wrong: nothing.
  r3c6 (944,406). In it: the chart card's bottom-right corner, bars W12 and W13, and the right ends of the axis and gridlines. Checked: the axis end against the gridline ends. The gridlines at y 466 and 526 end at ship x 1148, and the axis ends at 1142. Wrong: F3.
  r2c3, r2c2, r2c5, r2c4, r2c6 (y 224, columns 2 to 6). In them: metric card bottom corners and the gaps between cards, the chart card's top edge and top-right corner, gridline runs at 2000/1500/1000, and rounded bar tops crossing gridlines. Checked: crossing order (bars on top everywhere), card corner arcs and shadows, and gridline right ends (1148, consistent). Wrong: nothing.
  Unread: r1c3 and r1c4 fell outside the 16-tile budget and are not judged. Unread is not clean.
  F1 is graded HIGH, not CRITICAL. Values read against the gridlines are right and bar order is preserved. Only proportional length is off: bar length encodes value minus 250, which overstates the ratios between bars by roughly 5 to 8% at these values (W4/W3 reads 1.33 by length against 1.26 by value). The 250 baseline is an extrapolation from four gridlines exactly 60 px apart, which assumes a linear scale. Under stipulated zoom on retina, F2 and F3 are plain at 1x and do not change any value, so they are MEDIUM.
Findings:
  - id: F1
    target: artifact
    rule: e. Repeats end on purpose
    severity: HIGH
    location: r3c1 @ 92-256,556
    evidence: The gridlines step every 60 ship px per 500 (1000 at y 466, 500 at 526). The x-axis rule and the bar bottoms sit at y 556, half a step below 500, where the scale reads 250, not 0 (zero falls at y 586). The grid repeat does not land on its axis, and no tick marks the axis. Bars are therefore drawn from 250, and their lengths overstate the differences between them.
    fix: Draw the axis and the bar bottoms at the y-scale's zero (ship y 586, a full 60 px step below the 500 gridline) so the grid step lands on the axis and bar length equals value.
    form_fatal: no
  - id: F2
    target: artifact
    rule: b. Joints meet
    severity: MEDIUM
    location: r3c3 @ 508,556
    evidence: The bars round their bottom corners as well as their tops, so each bar meets the axis only between its corners. A white wedge of about 6x6 ship px (about 12x12 device px on retina) opens between each bottom corner and the axis. That is 26 notches across 13 bars, seen in r3c1, r3c2, r3c3, r3c4, r3c5, r3c6. The bar fill also covers the top 0.5 ship px of the 1 px axis, so the rule changes thickness at every bar.
    fix: Round only the top corners of each bar (for example border-radius 6px 6px 0 0) so the bars sit square and flush on the axis.
    form_fatal: no
  - id: F3
    target: artifact
    rule: a. Line ends land
    severity: MEDIUM
    location: r3c6 @ 1142-1148,556
    evidence: The x-axis rule ends at ship x 1142, while the gridlines above it (y 466, 526 and up) end at 1148. The grid overshoots the axis by 6 ship px (12 device px) at the right end. The left ends agree at x 92.
    fix: End the axis and the gridlines at the same x by giving them one plot-area right edge.
    form_fatal: no
Issue rank: F1, F2, F3
Ship (this seat's loss only): no
Confidence: medium
Recused: hierarchy and focal dominance, reading order, scale survival, contrast ratios (including the 8:1 text floor and the white-on-red pill), stipulated line ends (no muriel.line_ends output was supplied), wording, units and tick labelling as text (for example a missing "0" string or a missing unit on the "Avg. session" value), typeface consistency between the buttons and the rest, distinctiveness and template defaults, premise, empty space, and unread cells r1c3 and r1c4
```

## Case jx-1024-p3: after one round of fixes

Every fix the p2 ballots asked for went into `panel-after-r1.html`. The docstring
of the script that wrote it maps each change to its finding id. Three jurors
said ship; three did not.

| Juror | Ship | Worst finding |
|---|---|---|
| Stranger | yes | LOW: the image doesn't say it is an "after" (not a defect in a dashboard) |
| Thumbnail | yes | MEDIUM: the Q2 line's key dissolves at 400 px |
| Loupe | yes | none; noted that buttons don't inherit the page font |
| Squinter | no | HIGH: under blur the chart still outweighs the KPI row |
| Pedant | no | HIGH: "57%" was week 1 to week 13 while its partner clause compared with Q2 (+39% on that base); HIGH: revenue had no period |
| Forger | no | CRITICAL: a stock rebuild matched all 26 free decisions, so nothing was left uncopied |

Two of the Pedant's findings, and the Thumbnail's, were mistakes introduced by
the first fix pass.

## Case jx-1024-p4: after a second round

Every p3 fix went into `panel-after.html`:

- the KPI tiles got a dark fill, so they lead under blur;
- the primary button became tinted, not solid;
- signups and revenue became two aligned charts, each against its Q2 average,
  so the story is drawn as well as written;
- both Q2 lines got direct labels;
- the summary sentence now compares both series with Q2;
- every period and comparator is named;
- "Sample data" became a chip beside the title;
- buttons inherit the page font.

All six jurors said ship. The Squinter's yes is from jx-1024-p4s, described at
the top. Open findings, none blocking: the Loupe's MEDIUM (the dashed Q2 line
sits 1 px above the 1,000 gridline, so the two read as a doubled stroke), the
Pedant's MEDIUMs (Q3 labelled as 13 weeks to Sep 29, no x-axis title,
unverifiable sample figures, valence carried only by colour), and LOWs from the
Thumbnail, Squinter and Forger. The card shows the panel exactly as judged, so
these stay unfixed in it.

### Ballots, verbatim

```text
Juror ballot
Seat: stranger
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: artifact (single artifact, k=1; the chair supplied no order, and with one artifact every permutation is the same)
Evidence seen: assets/social/jury-exhibit/panel-after-desktop-1200x747.png (one Read). The filename carried meaning, and I am declaring it: "social", "jury-exhibit" and "panel-after" suggest this is the "after" half of a before/after pair, shown as an exhibit, possibly about this jury process. I know the jury process exists only from my own seat file. The harness also loaded CLAUDE.md and memory files, which describe muriel as a visual production toolkit. Neither says anything about this artifact's purpose. I did not use any of this in the answers below, and I discount myself slightly for having seen it.
Evidence denied: brief, design rationale, option purpose, project context, brand tokens, ballots
Reasoning:
  Q1 What is this for? It is a quarterly business dashboard for a product with users, signups and revenue. Someone who runs the business would want it, such as a founder, PM or exec checking how Q3 2026 went. It makes one argument in its subtitle: signups grew 39% over Q2 while revenue fell 12% below Q2. Put another way, growth isn't turning into money. The "Sample data" chip tells me the numbers are a demo and not a real company's. It never says what the product is. For a dashboard that is normal, because its readers already know.
  Q2 What is the one number? The takeaway is the gap between the two figures, not either one alone. Revenue down 12% is the number I left with. It has the only red badge on the page, and the lower chart shows weekly revenue sliding under its Q2 average line. The headline's other half, signups +39%, shows up only in the subtitle and the upper chart. There is no signups card. The first card shows monthly active users, 12,480, up 8.2%, so that number competes for attention. Even so, I had the intended pairing within the one look.
  Q3 Where do I click? The primary action is "View full report", top right. I picked it because it is filled with a tint while "Export CSV" next to it is only outlined. My eye went to the title, then the subtitle sentence, then the row of four cards, landing on the red badge. Then down to the charts, which confirm the subtitle. What it wants me to do next is open the full report, or export the data.
  Evaluation: I understood what this is for and what it argues from one look. I have no premise findings. If the artifact is supposed to argue something other than "this business's Q3", for example "this is what a fixed panel looks like", nothing inside the frame says so. I would read it as a dashboard screenshot. I am stating my reading plainly so the chair can check it against the brief. I am not filing it as a finding.
Findings: none
Issue rank: none
Ship (this seat's loss only): yes
Confidence: medium
Prior strength: high (a KPI-card and bar-chart business dashboard is one of the most familiar artifact types this model knows. My easy reading says little about a real first-time viewer.)
Recused: whether the badge baselines are consistent ("vs Jun" on two cards, "vs Q2" on the others) and whether 39% and -12% match the bars (Pedant); whether the red revenue badge and the missing signups card are the right emphasis on the page (Squinter); text contrast of the badges, the "Sample data" chip and the grey date line (contrast tool, not mine); whether the cards and dashed average lines survive at thumbnail size (Thumbnail); finish on the bars, cards and buttons (Loupe); whether the generic SaaS-dashboard look is distinctive (Forger); typography and spacing.
```

```text
Juror ballot
Seat: squinter
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: artifact (single option; chair supplied none; with k=1 every permutation from printf '%s' "jx-1024-p4squinter" | shasum is the identity, so the digest was not executed, because this seat's Bash runs only muriel.squint)
Evidence seen: squint ladder on assets/social/jury-exhibit/panel-after-desktop-1200x747.png (1200x747, long edge 1200), read heavy, luma, medium, light in that order. heavy sigma 60 px, half_survival_px 126.0. luma is the heavy blur with colour discarded (sigma 60 px inherited; half_survival_px not reported). medium sigma 36 px, half_survival_px 75.6. light sigma 18 px, half_survival_px 37.8. Matte #F4F2EE, which has no effect because the artifact is opaque. Stipulated order: none. Standing context (CLAUDE.md, MEMORY.md) checked: it does not name this decision, this artifact, or an intended order. Glob was unavailable, so squint's exit 0 confirmed the path. The thumbnail companions (thumb-eighth, thumb-16px, thumb-16px-zoom) were written but not opened. Outputs are in <scratchpad>/after/jury2/squinter/
Evidence denied: sharp render, all text, brief, brand tokens, ballots
Reasoning: Recovery is labelled INFERRED: one call with no stipulation. Confidence drops one step for that.
  HEAVY (masses under 126 px halved): One mass sits well off the ground: a dark horizontal band at y≈130–290 running x≈60–1170, about 93% of the width and 21% of the height. Inside it are four lobes of near-equal darkness centred at x≈230, 520, 800 and 1080 (y≈210), joined by lighter bridges, with a faint mauve tint at x≈380, y≈240. Below are two very pale bands, barely off the ground: blue-grey at y≈330–500, x≈150–1000, and pink at y≈570–700, x≈160–980. The top strip (y<90) is indistinguishable from the ground. Eye order: band (no lobe preferred; the eye scans it laterally), then blue band, then pink band. At the band level there is one mass. At the member level there is a four-way tie.
  LUMA: The band survives intact with the same four lobes. The lobe at x≈800 is marginally darkest, too slightly to call a break in rank. The blue and pink bands collapse to near-ground grey and match each other. The top strip is empty. Lightness carries the band's dominance, so this is not saturation posing as dominance. Hue carries the lower tiers.
  MEDIUM (masses under 75.6 px halved): The band resolves into four navy discs about 150 px wide at x≈235, 520, 800 and 1095, all of equal area. Between them are mid-grey bridges, green-tinted at x≈100, 660 and 950 and mauve at x≈380. The blue band (y≈380–490, x≈140–1020) and the pink band (y≈580–690, x≈145–1000) sharpen. In the header, a pale yellow smudge (x≈310–400, y≈0–80) and a pale teal smudge (x≈1050–1150, y≈0–90) appear. The dark upper-left header mass has not yet separated. Order: discs, blue, pink, then the yellow and teal smudges.
  LIGHT (masses under 37.8 px halved): The header strip at y≈30–90 shows a dark-grey block upper-left (x≈35–285) with a yellow pill to its right (x≈305–400). Upper-right are a grey bar and a teal pill (x≈900–1160). Below are four equal cards at y≈130–280 (x≈35–295, 330–580, 615–865, 905–1160). Each has a navy right block and a lighter left half with a green lower patch. Card 2's patch is mauve instead. Card 3's navy block is the widest, about 58% of the card against 40–48% for the others. A white containing surface (x≈50–1170, y≈300–700, about 53% of the frame) holds two rows of 13 small columns: blue at y≈380–490, where the rightmost two are taller, and pink at y≈585–680, all equal. Each row has a small dark mass at upper-left and a pale teal pill at right (x≈1040–1130).
  RECOVERED ORDER (written before inferring intent): (1) card row, with four peers and no member first; card 3 is a marginal tiebreak at luma and light only. (2) Blue column strip. (3) Pink column strip. (4) Header: the pills appear at medium, the title block only at light.
  INFERRED INTENT: From the structure: a header, a peer-card row, then two stacked chart strips. Intended order: card row first, the strips second in top-to-bottom order, and the header as a label tier with the title block above its pills.
  COMPARISON: Top-1 matches at the band level, and the order below it matches by position. The header pills outlast the title block (sq-2). The card row reads as a peer-tile comparison form. The comparison-form exemption is unavailable because the chair stipulated no intent, so I graded normally: four lobes tie at heavy, which is HIGH (sq-1). If the chair stipulates peer tiles, the envelope test passes cleanly: the band is the strongest mass in the frame at both heavy and luma. Card 3's wider navy block does not separate at heavy, so under that reading I would file no break-of-rank MEDIUM.
  CONDITIONAL, NOT FILED (intent unknown; filing would inflate):
  (a) If the intended top-1 is the chart surface rather than the card row, recovered top-1 does not equal intended top-1, which is HIGH. That surface is near-ground at heavy and collapses at luma.
  (b) If card 2's mauve patch is meant to flag that card as an exception, the signal is hue-only and gone at luma, so it carries no rank (Bertin).
Findings:
  - id: sq-1
    target: artifact
    rule: SKILL.md — "Give each composition one dominant focal point and a legible reading order."
    severity: HIGH
    evidence: At heavy (sigma 60 px, masses under 126 px halved), the only off-ground mass is the band at y≈130–290, x≈60–1170. It carries four lobes of near-equal darkness at x≈230, 520, 800 and 1080. Luma keeps all four, and the x≈800 lobe is marginally darker but not separable. There is no single centre of mass inside the dominant band. It reads as a peer-tile row, but the exemption is unavailable without a stipulation.
    fix: Either give the headline card roughly double its peers' dark area (for example, span two columns), or have the chair stipulate peer-tile intent, under which the band passes the envelope test and this finding drops.
  - id: sq-2
    target: artifact
    rule: Bertin — position, area, and lightness survive degradation; hue does not
    severity: LOW
    evidence: At medium (sigma 36 px, masses under 75.6 px halved), the only header masses visible are a pale yellow smudge at x≈310–400, y≈0–80 and a pale teal smudge at x≈1050–1150, y≈0–90. The upper-left dark header block (x≈35–285 at light) has not separated. At luma all three are gone. Hue-carried pills outlast the header's primary mass, and nothing below is displaced.
    fix: Desaturate or shrink the header pills so that the upper-left title block is the last header mass to vanish down the ladder.
Issue rank: sq-1, sq-2
Ship (this seat's loss only): no
Confidence: medium
Recused: typography, contrast ratios, copy, labeling, units, brand
  voice, scale survival, reproducibility, thumbnail companions (written by the lens, not opened)
```

```text
Juror ballot
Seat: squinter
Decision ID: jx-1024-p4s
Isolation: subagent
Order seen: artifact (single option; the chair supplied none. With k=1 every derivation, whether n mod k! in the seat definition or byte % remaining in jury.md, gives the identity. The shasum digest was not computed because this seat's Bash is limited to muriel.squint.)
Evidence seen: squint ladder for assets/social/jury-exhibit/panel-after-desktop-1200x747.png (1200x747, long edge 1200), read heaviest first: heavy (sigma 60 px, half_survival_px 126.0), luma (heavy blur, colour discarded), medium (sigma 36 px, half_survival_px 75.6), light (sigma 18 px, half_survival_px 37.8). Matte #F4F2EE as supplied; the chair says the artifact is opaque, so the matte had no effect. Stipulated order was in the invocation: KPI tile row (four peers, comparison form) > upper chart strip > lower chart strip; the header (title block, then two buttons) is the label tier. Path confirmed by a clean squint run (exit 0) because this seat has no Glob tool. The sharp render was never read. Thumbnail companions were written to the out-dir and not opened. Standing context (CLAUDE.md, MEMORY.md) does not name this artifact or this decision. The filename token "after" was ignored as an assertion. jury.md was read from plugins/muriel/skills/compose/references/jury.md, because the seat definition's relative link (skills/compose/references/jury.md) does not resolve from the repo root.
Evidence denied: sharp render, all text, brief, brand tokens, ballots
Reasoning: Recovery label: ANCHORED. This was a single call with the stipulation already present, so my reading was anchored before I opened a level. Confidence drops one step, from high to medium.
  HEAVY: One centre of mass. A dark slate band spans almost the full width (x~40-1160, y~110-290) on a pale ground. Inside it sit four darker lobes of near-equal depth and size at x~230, 520, 800, 1080. Each lobe sits right of its tile's centre, and the offset is the same in all four. A faint warm/mauve tint at x~360-400, y~220-260 lies between lobes 1 and 2. Below the band are two very low-contrast washes: a blue one at y~330-500, x~100-1000 and a rose one at y~570-700, x~150-1000. The upper wash is slightly larger (about 170 px tall against 130 px). The header area (y<90) has no mass. Only hue tints remain there: warm at x~300-450 and blue-grey in the upper-right corner. Eye order: band, then blue wash, then rose wash.
  LUMA: The band's dominance holds without hue, so it is carried by lightness and is not saturation posing as dominance. The four lobes are still near-equal. Lobe 3 (x~800) is perhaps marginally deeper, within a tie. The mauve tint near tile 2 is gone. Both chart washes fall almost to the ground and become faint grey bands of about equal lightness. The two header tints are gone completely.
  MEDIUM: The band becomes one continuous dark slab (x~40-1160, y~120-290). The gutters between tiles do not separate at this level, and four near-black cores of equal size sit at x~235, 520, 800, 1095. The secondaries now separate cleanly from the primary and from each other: a blue band at y~380-490 and a rose band at y~580-680, both x~140-1020, of similar area, on a lighter card (x~100-1050, y~320-720). Header: a yellow tint at x~300-400, y~20-90 and a teal-grey tint at x~1050-1150, y~10-100. The dark title text does not register as a mass at this level.
  LIGHT: Four separate dark rounded tiles (x~35-300, 325-585, 610-870, 900-1165; y~130-280). Each has a dark right half and a lighter left half. Tiles 1, 3 and 4 carry a green bottom-left patch. Tile 2 carries a rose patch instead, which differs by hue only and is gone at luma. The card holds an upper strip of 13-14 blue bars (y~370-490, rising toward the right) and a lower strip of 13 rose bars (y~580-680, uniform height), each with a small left label mass and a small right label mass. Header: a dark title block at upper left (x~35-280, y~40-70) with a yellow pill beside it (x~305-400) and a thin line below; at upper right a grey ghost-button block (x~905-1000) and a teal pill (x~1030-1160). At this level the order inside the header is title first (darkest), then the buttons.
  RECOVERED ORDER (anchored): (1) the tile-row envelope; (2) the upper blue strip; (3) the lower rose strip; (4) the header label tier, which resolves only at light (title, then buttons).
  COMPARISON: This matches the stipulated order. The comparison-form exemption applies because the chair stipulated the KPI row as peer tiles, so the dominance test was run on the envelope. At heavy the envelope is the largest and darkest mass in the frame and separates strongly from its surround, so there is no envelope finding. No member breaks rank at heavy or luma: the four lobes tie, and tile 2's rose patch is hue-only and does not survive luma. The (2)>(3) split between the chart strips rests on position. At luma the two strips are near-equal in area and lightness, and blue against rose is a hue difference. Position survives degradation (Bertin), so the order holds and I emit no finding on it. The chart strips sit close to the ground at heavy and luma. That is weak, but they are stipulated secondaries and meet no threshold. One LOW: the header's accent fills survive further up the ladder than the title block, and do so by hue alone.
Findings:
  - id: sq-1
    target: artifact
    rule: Bertin: position, area and lightness survive degradation; hue and shape do not
    severity: LOW
    evidence: At medium and heavy, the only header signals are hue tints: yellow at x~300-450, y~0-90 (the pill beside the title) and teal-grey at x~1030-1160, y~0-100 (the right button). The dark title block at x~35-280, which leads the header at light, does not register by medium. At luma all three are gone. Inside the label tier, saturation outlasts the stipulated title-first order, though it displaces nothing in the content tiers.
    fix: Pull the yellow pill and the teal button fill toward the header ground in saturation, or give the title block more area or darkness, so the title is the last header mass to fade.
    form_fatal: no
Issue rank: sq-1
Ship (this seat's loss only): yes
Confidence: medium
Recused: typography, contrast ratios (including the 8:1 floor), copy, labeling, units, brand voice, scale survival (thumbnail companions unread), local finish (line ends, joints, gutters at 1x), distinctiveness / AI-tell, premise, reproducibility
```

```text
Juror ballot
Seat: thumbnail
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: artifact (chair supplied none; derived: printf '%s' "jx-1024-p4thumbnail" | shasum -> 5f04b28b...; k=1, so the permutation is trivial)
Evidence seen: muriel.squint manifest (exit 0, source 1200x747, which matches the
  filename's claim). Levels read: px16_zoom 128x80, px16 16x10 (plus my own 32x
  nearest-neighbour of that same 16x10 and its pixel dump), eighth 150x93 (plus a
  6x and 12x nearest-neighbour crop). Chair-permitted downscales: 600x374 and
  400x249 (magick -resize from the source; the source itself was never viewed),
  with nearest-neighbour crops and ASCII ink maps. Intended sizes were stipulated
  by the chair: 1200 px at 100% on desktop, about 600 px in a split screen, about
  400 px in a Slack screenshot. Not a favicon. Scratch:
  <scratchpad>/after/jury2/thumbnail
Evidence denied: full-size render, blur ladder (written by the lens run, not
  read), brief, brand tokens, ballots
Reasoning:
  px16 / px16_zoom (16x10).
    Is: an app or web screen. There is a light header row, then a navy band
      across row 2, then a white field holding a pale-blue band (rows 5-6) and a
      pale-salmon band (row 8).
    Survives: the three-tier layout and the order blue above salmon.
    Gone: all text, the separation between the four tiles, every bar, both
      reference lines, the chip colours.
    Invented: the four KPI tiles merge into one continuous navy strip that
      reads like a toolbar. One warm-yellow pixel at (4,0) and one teal pixel at
      (14,0) read as header ornaments.
    Rule a: not a favicon. The class "dashboard screen" survives in outline.
      Recorded, not fired.
  eighth (150x93).
    Is: a dashboard. A title, four dark KPI tiles with large white numerals and
      coloured chips, two bar charts.
    Survives:
      - the four tiles, with their gutters;
      - the numerals, as bold white shapes;
      - the chip colours green / red / green / green, so red marks only the
        second tile;
      - blue bars rising left to right and crossing above a teal dotted line;
      - salmon bars sitting under a teal dotted line, with the gap widening to
        the right;
      - a yellow pill beside the title.
    Gone: tile labels, chip text and arrows, the subtitle sentence, the date
      line, all y ticks and x labels, both "Q2 avg" values, button text, badge
      text.
    Invented: the numerals fill in. "12,480" resolves toward "10,480"/"13,480"
      because the 2's counter closes, and the "$" in "$184.2k" fuses with the 1.
    Rule b: the argument survives at 1/8: signups up and above the Q2 average,
      revenue down and below it, one red tile among green. 150 px is not a
      stipulated size, so the numeral fill-in is recorded, not fired.
  600x374 (split screen). Every text element keeps at least 6 rows of ink:
    title, subtitle, date line, tile labels and numerals, chip text with its
    up/down arrows, chart titles, y ticks, all 13 week labels, and both "Q2 avg"
    labels. Both dashed lines survive as continuous dotted rows. Nothing that
    this size needs is lost.
  400x249 (Slack).
    Survives:
      - title (8 rows of ink);
      - KPI numerals (about 10 rows);
      - tile labels and the subtitle "Signups ran 39% above Q2 while revenue
        fell 12% below it" (5 rows);
      - chip text and arrow triangles (marginal but recoverable);
      - chart titles (5 rows);
      - both dashed lines, the bar trends, and the gap between bar tops and the
        dashed line in each chart.
      - "Q2 avg" stays legible, but its values are ambiguous: the "$" in
        "$16.1k" collapses toward "8"/"S".
    Gone:
      - x-axis week labels: 3 rows of ink, no pixel darker than L~140 on L~237,
        so a grey texture with no glyphs;
      - y ticks: 3-4 rows, faint;
      - the date range / "updated" line: 4 rows, faint.
    Rule c: these are reference detail. The title, subtitle and chart titles
      carry the claim, and "Q3 2026" with 13 bars implies the week span, so they
      are expected to dissolve in a Slack preview. Not fired.
    Rule d at 600 and 400: no moire. The dashed lines keep their period, the two
      series sit in separate panels and their hues do not converge, and the tile
      gutters hold.
    Closest call: the "Sample data" badge. Its yellow pill survives at every
      level. Its words are 4 rows of ink at 400 (recoverable only on
      inspection) and gone at 1/8. The numerals it qualifies are 10 rows at 400
      and still form shapes at 1/8. The disclosure fails before the numbers it
      discloses. This is not dissolved at 400, so it is LOW, not HIGH.
  The 400 render models a 1x display. A 2x Slack client shows about 800 device
    px and is strictly better. 1200 px (100%) was denied and is not judged.
Findings:
  - id: t1
    target: artifact
    rule: c. Text survival against intent
    severity: LOW
    evidence: At 400 px (Slack) the "Sample data" badge text is 4 rows of ink.
      It reads only on close inspection, and its word shape is held up mainly
      by the yellow pill. At eighth it is a yellow blob with no text. The KPI
      numerals and the subtitle percentages it qualifies survive with 10 and 5
      rows at 400. Any Slack preview below about 400 px, or a lossy re-share,
      drops the caveat while the numbers remain.
    fix: Set the badge text at least at the subtitle's size and weight, so the
      disclosure survives 1/3 scale with at least the subtitle's margin.
    form_fatal: no
Issue rank: t1
Ship (this seat's loss only): yes
Confidence: high
Recused: full-size hierarchy, contrast ratios, labeling correctness,
  terminology, distinctiveness, brand voice, blur-ladder reading, 100% (1200 px)
  rendering
```

```text
Juror ballot
Seat: forger
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: panel-after  (printf '%s' "jx-1024-p4forger" | shasum -> 1432118f510d9759c9c482ae82460234209a7b4c; byte 0x14 % 1 = 0; single option)
Evidence seen: artifact raster assets/social/jury-exhibit/panel-after-desktop-1200x747.png; intended use (analytics dashboard panel in a web app); generic component library (Tailwind Play CDN stock palette/radius/shadow, Chart.js 4 stock bar component, Inter); jury.md; muriel-critique.md §Bertin
Evidence denied: panel-after.html (artifact source, named in the invocation, not opened); sibling sources panel.html and panel-after-r1.html (not opened); forger-counterfeit.png in the exhibit dir (an earlier counterfeit, not opened, to keep the round sealed); panel-desktop-1200x662.png and panel-after-r1-desktop-1200x716.png (earlier states, not opened); no brand.toml or token export was supplied and none was searched for
Reasoning:
  Elapsed: 01:49 (2026-10-24T17:31:53Z to 17:33:42Z). Observation only; it sets nothing.
  Forgery: <scratchpad>/after/jury2/forger/panel-after.forgery.html; sidecar panel-after.forgery.md; renders panel-after.forgery.render.d1-desktop-1200x644.png (draft 1) and panel-after.forgery.render-desktop-1200x789.png (revision), all in that directory
  Not reproduced: #5 "Sample data" disclosure pill; #6 subtitle stating the cross-series finding with derived QoQ figures; #7 static coverage line (explicit range, 13 weeks, refresh stamp) instead of a range picker; #12 KPI labels carrying each metric's window (Sep)/(Q3); #14 delta baselines aligned to each metric's window, all QoQ (vs Jun / vs Q2); #16 session delta in native minutes; #17 delta colour keyed to direction-of-good (churn decrease green); #25 dashed Q2-average reference line per chart, labelled directly in the right gutter
  Counts: F=27 R=8 Rs=3 (structural: #6, #14, #25). 30 decisions inventoried: template-default=19, domain-specific=8, convention=1 (#15 churn in percentage points), encoding-optimal=2 (#20 stacked panels on one aligned week axis; #21 position/length from zero on a common scale). R/F=0.296.
  Passes: 1 draft, 1 revision, 2 counterfeit renders. The ceiling was reached, and the counterfeit was complete at the ceiling. The original is a supplied raster and was read as-is, not regenerated from source.
  Render: rung 1. /opt/homebrew/bin/python3 -m muriel.capture file://<forgery_dir>/panel-after.forgery.html --tiers desktop --scale 1 --selector '#panel' --dir <forgery_dir> --slug panel-after.forgery.render(.d1)
  Method: the counterfeit was given the content inventory (metric names, headline values, 13 weekly values per series read off the raster, the period). Draft 1 is the generalist reflex on that content: slate-50 ground, white rounded-xl shadow-sm stat cards, "Last 90 days" select, slate-900 primary, two charts side by side in Chart.js default blue, deltas "from last month" coloured by sign. The revision edited variables only: eyedropped colours (#f4f2ee ground, #24303f tile, #a9c1da/#d9b8ae bars, #0e6e78/#d7ecee accent), rounded-lg, no shadow, grid-cols-1, top x ticks hidden, maxTicksLimit 3, a compact formatter, and copy strings that carry no dataset knowledge. It was barred from the analytic layer: baselines, derived comparisons, aggregation windows, disclosures.
  Result: all 19 template-default decisions were reproduced or came within one variable. The skeleton, header, four-tile KPI row, numerals, pill deltas, chart card, bars, axes, titles, x ticks and type all came straight from the stock stack. Every remaining gap was a value: tile fill, accent, ground, series hues, tick format "2k" vs "2,000". None of the 8 domain-specific decisions was reached. The forgery confirms the partition in both directions.
  The residue sits in one layer. It is the QoQ analytic frame: the Q2 baseline lines, the headline finding, window-aligned baselines and polarity-correct chips. That frame is distinctive and is not in the stack. It is carried as strings, one prop and one stock-reachable reference line inside an unmodified dashboard skeleton.
  Two scoring calls. #7 was scored cosmetic, the harsher call; scoring it structural makes Rs=4 and leaves the severity unchanged. If the chair rules #5 and #16 template-default, R=6, R/F=0.222 and the severity rises to MEDIUM.
  Scope: palette-default tells in the HTML source (untouched Tailwind values and the like) are devibe's stipulated jurisdiction. These findings are limited to whether the composition can be reproduced.
  The "four-minute forgery" claim is rhetorical. Here the counterfeit cost two passes, and the 01:49 is an agent's wall clock, not designer labour.
Findings:
  - id: forger-1
    target: artifact
    rule: anti-slop: domain-specific decisions (toolkit: Chrome, KPI row of four stat cards; Text effects, oversized display numerals and pill badges)
    severity: LOW
    evidence: The KPI row (#8 four equal tiles, #10 dark fill, #11 oversized numeral, #13 triangle-pill delta, #18 green/red tint chips) is the stock stat-card component. The counterfeit reproduced it as Tailwind grid-cols-4 tiles: draft 1 white rounded-xl shadow-sm with a text-3xl bold numeral; the revision #24303f rounded-lg with a 40 px bold white numeral, and bg-green-100/text-green-800 and bg-red-100/text-red-800 pills ("▲ 8.2% from last month"). At 100% it cannot be told apart except by chip tint (#cfebd7/#f9d3cd sampled from the original) and the delta strings. Cost: 2 passes, 01:49. The row's only residue is in strings and one prop: #12 "(Sep)/(Q3)", #14 "vs Jun/vs Q2", #16 "0.3 min", #17 churn chip green.
    fix: Let the QoQ comparison that already drives the headline and the Q2 reference lines shape the tile itself (for example, mark each metric's Jun/Q2 baseline inside its tile), rather than only relabelling the stock stat card.
  - id: forger-2
    target: artifact
    rule: anti-slop: domain-specific decisions (toolkit: Layout, Container, Chrome)
    severity: LOW
    evidence: The frame is a stock dashboard frame. It covers the header with the title left and outline-plus-primary actions right (#1-#4), one white hairline card of bar charts (#19, #22), three-tick compact axes (#23), one muted hue per series (#24), small bold "<metric> per week" titles (#26), week-start x ticks (#27), a single accent (#28), a warm ground (#29) and Inter (#30). The counterfeit reached all of it with Tailwind plus the Chart.js stock bar: draft 1 in slate-50, slate-900 and rgba(54,162,235,0.5); the revision with eyedropped #f4f2ee, #0e6e78, #a9c1da and #d9b8ae, and ticks "2k/1k/0" against the original's "2,000/1,000/0". Cost: 2 passes, 01:49. The residue in this region is #5, #6, #7 and #25, all of them annotations and copy laid over the stock frame.
    fix: Give the chart frame one structural decision that comes from the data (for example, mark the Q2/Q3 boundary or the Q2 band as part of the axis structure) so eyedropped values alone no longer reproduce the frame.
Issue rank: forger-1, forger-2
Ship (this seat's loss only): yes
Confidence: medium
Recused: hierarchy, contrast, typography quality, labeling, units, scale survival, accessibility, the quality of any residue item, and palette-default source tells (devibe jurisdiction)
```

```text
Juror ballot
Seat: pedant
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: panel-after (single option; chair supplied none; derived: printf '%s' "jx-1024-p4pedant" | shasum → c8c212e2d757a4379b9507f0c050e60f1d606fa9, n = 0xc8c212e2, n mod 1! = 0, identity)
Evidence seen: Source HTML with inline SVG, assets/social/jury-exhibit/panel-after.html (57 lines). I read the whole file as text. It has 42 visible text nodes (19 HTML, 23 SVG <text>) and one SVG aria-label holding 13 weekly data rows and a Q2 summary. Bar values were recovered from the SVG path geometry against the gridline scale. No sibling data file exists (the chair confirmed this). The sibling panel.html and panel-after-r1.html were not read. A directory listing showed PNG filenames, but no PNG was opened. Standing context (CLAUDE.md, MEMORY.md) does not name this artifact.
Evidence denied: rendered composition, brief, ballots
Reasoning: Inventory, by line. l5 <title> "Q3 2026 overview". l35 h1 "Q3 2026 overview", chip "Sample data". l36 story "Signups ran 39% above Q2 while revenue fell 12% below it." l37 "Jul 1 – Sep 29, 2026 (13 weeks) · updated Oct 1, 2026". l40-41 buttons "Export CSV", "View full report". l46-49 KPI tiles: "Monthly active users (Sep) 12,480 ▲ 8.2% vs Jun", "Revenue (Q3) $184.2k ▼ 12% vs Q2", "Churn (Sep) 3.1% ▼ 0.4 pp vs Jun", "Avg. session length (Q3) 4.2 min ▲ 0.3 min vs Q2". l53 SVG: "Signups per week", y ticks "0 / 1,000 / 2,000", "Q2 avg 1,040", "Revenue per week", y ticks "$0k / $10k / $20k", "Q2 avg $16.1k", 13 shared x ticks "Jul 1" … "Sep 23", and the aria-label rows "week of <date>: N signups, $Xk revenue".
  Probe list. Angles, multipliers, ratios, statistical readouts (p, r, n) and math parameters: none present.
  Percentages:
  - "39%" (l36) is CONFIRMED. The 13 aria-label weeks sum to 18,825 signups, a mean of 1,448.1 per week. Against "Q2 avg 1,040" that is +39.2%, which holds for any Q2 average from 1,035 to 1,045.
  - "12%" (l36, l47) is CONFIRMED. The 13 weekly revenue values sum to $184.2k. Against $16.1k × 13 = $209.3k that is −11.99%, and it stays between −11.7% and −12.3% across the rounding range of $16.1k. Q2 (Apr 1 – Jun 30) is also 91 days, so the comparison is like for like.
  - "8.2%" (l46) and "3.1%" (l48) are UNVERIFIED: no source exists.
  Units:
  - "0.4 pp" (l48) is the correct unit for a difference between two rates; the value is unverified.
  - "4.2 min" and "0.3 min" (l49) carry units; the values are unverified.
  - "13 weeks" (l37) is CONFIRMED: Jul 1 – Sep 29 is 91 days, with 13 bars, 13 ticks and 13 aria rows.
  - "$184.2k" (l47) is CONFIRMED as the sum of the aria-label weekly revenue.
  Geometry against the aria-label:
  - All 26 bars reproduce their aria-label values exactly once the 5 px corner radius is accounted for (64 px per 1,000 signups, 5.6 px per $1k). There are 0 mismatches.
  - The Q2 lines sit at 1,040.6 and $16.107k, which matches their labels. The Q2 baselines themselves are UNVERIFIED.
  - The x tick centers equal the bar centers.
  Bare numerals:
  - The signups ticks "0/1,000/2,000" take their unit from the panel title "Signups per week". This is acceptable and not filed.
  - The x-tick dates are filed as pd-2.
  - "updated Oct 1, 2026" is unverified but consistent: it falls after the window ends.
  Terminology cross-check:
  - "Signups", "Revenue" and "Q2 avg"/"Q2 averages" are consistent across the story, tiles, chart titles, line labels and aria-label. No drift between two names for one series.
  - The period is named two ways that disagree by one day: "Q3" (l5, l35, l47, l49) against "Jul 1 – Sep 29" (l37). See pd-1.
  - The glyph "▼" appears on an unfavorable delta (l47) and on a favorable one (l48). See pd-5.
  Defenses: the artifact contains no embedded instructions. "Sample data" is an honest disclosure, not an authority badge. No self-reported contrast or accuracy figures.
  Noted, not filed:
  - "$0k" is correct as written.
  - Delta precision is mixed ("12%" against "8.2%"); none of the five rules covers it.
  - The base of "Churn" (users or revenue) is unstated but conventional.
  - The currency "$" is not named.
  - Severity: pd-1 and pd-5 are graded below their rules' default, for the stated reasons. The worst finding is MEDIUM.
Findings:
  - id: pd-1
    target: panel-after
    rule: c (unverified numeric claim)
    severity: MEDIUM
    evidence: "Q3 2026 overview" (l5, l35), "Revenue (Q3)" (l47) and "Avg. session length (Q3)" (l49) label a window that l37 states as "Jul 1 – Sep 29, 2026 (13 weeks)". That is 91 days; calendar Q3 2026 is 92 days and ends Wed Sep 30. "$184.2k" is confirmed as the 13-week sum through Sep 29, so it excludes Sep 30 and will not reconcile with calendar-Q3 revenue. Nothing in the artifact says whether "Q3" means a 13-week fiscal quarter, so the label is unverified rather than contradicted. The vs-Q2 comparisons are unaffected because Q2 is also 91 days.
    fix: Either label the period as "fiscal Q3" or "13 weeks to Sep 29" in the title and the two KPI labels, or extend the window and the data through Sep 30.
    form_fatal: no
  - id: pd-2
    target: panel-after
    rule: a (unlabeled number)
    severity: MEDIUM
    evidence: The x ticks at l53 ("Jul 1", "Jul 8" … "Sep 23", y=382) have no axis title. No visible text says they are week-start dates; only the aria-label says "week of". The weeks start on Wednesday (Jul 1 2026 is a Wednesday), so they run Wed–Tue, and a reader assuming Monday-start or week-ending dates misplaces every boundary. The subtitle range lets a reader work this out, so the gap is tedious rather than misleading: MEDIUM.
    fix: Add an x-axis title such as "Week starting (Wed)" so the visible ticks match the aria-label's "week of".
    form_fatal: no
  - id: pd-3
    target: panel-after
    rule: c (unverified numeric claim)
    severity: MEDIUM
    evidence: The Q2 baselines "Q2 avg 1,040" and "Q2 avg $16.1k" (l53 SVG text, repeated in the aria-label) have no source anywhere in the artifact and no sibling file. The headline "39% above Q2 … 12% below it" (l36) and "▼ 12% vs Q2" (l47) are arithmetically confirmed against these baselines, but only against them.
    fix: Ship a sibling data file or the generating script carrying the Q2 weekly series, so that 1,040, $16.1k and the headline percentages can be checked.
    form_fatal: no
  - id: pd-4
    target: panel-after
    rule: c (unverified numeric claim)
    severity: MEDIUM
    evidence: These KPI values have no source of truth: "12,480" and "▲ 8.2% vs Jun" (l46), which imply a June MAU of about 11,534; "3.1%" and "▼ 0.4 pp vs Jun" (l48), which imply 3.5% in June; and "4.2 min" and "▲ 0.3 min vs Q2" (l49), which imply 3.9 min in Q2. None appears in the chart or the aria-label, so all are unverified. None is contradicted.
    fix: Include the Sep and Jun MAU and churn values and the Q2 and Q3 session-length means in the same sibling data file.
    form_fatal: no
  - id: pd-5
    target: panel-after
    rule: e (unlabeled state)
    severity: MEDIUM
    evidence: "▼ 12% vs Q2" (l47, class "unfavorable") and "▼ 0.4 pp vs Jun" (l48, class "favorable") carry the same glyph. The favorable/unfavorable state exists only as a CSS class name and appears in no text, and the KPI tiles have no aria-label. Direction, sign and unit are labeled, and the valence can be inferred from the metric names, so this is MEDIUM rather than rule e's default HIGH.
    fix: Put the valence in the text, e.g. "▼ 12% vs Q2 (worse)" and "▼ 0.4 pp vs Jun (better)", or add a per-delta aria-label that states it.
    form_fatal: no
Issue rank: pd-1, pd-2, pd-3, pd-4, pd-5
Ship (this seat's loss only): yes
Confidence: high
Recused: hierarchy, composition, reading order, contrast ratios, typographic craft, scale survival, distinctiveness, brand voice, colour choice of the delta chips
```

```text
Juror ballot
Seat: loupe
Decision ID: jx-1024-p4
Isolation: subagent
Order seen: artifact (chair supplied none; derived: printf '%s' "jx-1024-p4loupe" | shasum -> b7f1fb28...; k=1, so n mod 1! = 0, the identity permutation)
Evidence seen: artifact. render: rerender (a crop of the @4x Playwright capture of #panel, not resampled). source_scale: 4, which matches the filename panel4x-desktop-4800x2988.png and a ship size of 1200x747 CSS px. matte: #f4f2ee. coverage: 24 cells, 16 read, 8 unread, 0 empty. Tiles read in rank order: r1c1, r1c2, r1c5, r1c6, r3c2, r3c3, r2c1, r3c4, r3c1, r4c1, r4c2, r4c3, r4c4, r2c2, r2c4, r2c3. Pixel measurements were taken on the tile PNGs only. The full capture was written to disk by the chair's command and was never opened. Viewing conditions were stipulated by the chair: a web dashboard panel in a desktop browser on retina screens (2 device px per CSS px), and users zoom the browser. Ship px = CSS px. Standing-context check: no CLAUDE.md or MEMORY.md line names this artifact or the question. muriel.line_ends output was not stipulated.
Evidence denied: full-size render, blur ladder, downscales, overview, brief, brand tokens, ballots
Reasoning:
  r1c1 (0,0). Contents: page heading, subhead, date line, top-left corner of KPI card 1, KPI label, large numeral, top of delta chip. Checked: card corner radius against the page ground; chip inset in the card; heading and subhead descenders (g, p) and the parentheses in "(13 weeks)"; the comma descender of the numeral. Nothing wrong.
  r1c2 (224,0). Contents: end of heading, "Sample data" badge, subhead, end of date line, gutter between KPI cards 1 and 2, card 2 corner, label, numeral, red chip top. Checked: badge corners and text inset; both card corners at the gutter; the "(Sep)" paren clears the card 1 edge by about 31 ship px. Nothing wrong.
  r1c5 (896,0) and r1c6 (944,0). Contents: two outlined buttons, top-right corner of KPI card 4, label, "4.2 min", chip. Checked: both button outlines are closed at all four rounded corners; the label sits inside its box; Export's right edge is 1008.5 in both tiles, so the overlap agrees; the card corner; the "(Q3)" paren is clear of the card edge. Nothing wrong.
  r3c2, r3c3, r3c4 (y 448). Contents: feet of the Signups bars on their baseline; the Revenue chart's gridlines, dashed reference, bars, baseline and x labels. Checked: every bar foot against its axis, measured as fill reaching the row directly above the 1 ship px axis with no background row, 0 gap columns across all tiles; gridlines pass behind the bars (hidden inside the fills, correct order); the dashed reference is drawn on top; the dash cadence is constant at 6 ship px on and 5 off (period 44 tile px); x labels clear the axis. Nothing wrong. The reference runs off r3c4's right edge mid-gap at ship x 923. Its end is in unread r3c5.
  r2c1 (0,224). Contents: bottom of KPI card 1 and its chip, top-left corner of the chart card outline, "Signups per week", y labels 2,000 and 1,000, gridlines, dashed reference, first bars. Checked: the left ends of the gridlines, the baseline and the reference all start at ship x 125.0, so they are registered; the tick labels are centred on their rules; the outline corner is continuous. Defect: the dashed reference occupies ship y 417.3–419.5 and the 1,000 gridline 420.5–421.5, with 1 ship px of white between them (2 device px on retina; 2.6 px centre to centre). From the rule spacing the reference sits at about 1,040, so the two strokes are not meant to coincide. They run parallel across the full visible plot width, x 125 to at least 923. At viewing scale they read as one muddy line, a teal dash with a grey hairline showing through every gap, and the reference reads as sitting on 1,000. Under browser zoom it shows plainly as a doubled stroke.
  r3c1 (0,448). Contents: Signups baseline and "0" label, "Revenue per week", $20k/$10k/$0k labels and gridlines, reference, Jul 1 and Jul 8 bars. Checked: label centring on rules, bar feet, continuity of the chart card's left border. The reference clears the top of the Jul 1 bar by about 0.6 ship px. That is a data tangency and not finish, so no finding.
  r4c1 (0,491). Contents: lower Revenue chart and the bottom-left corner of the chart card. Checked: outline radius continuous; x labels clear the card bottom by about 25 ship px. Nothing wrong.
  r4c2, r4c3, r4c4. These overlap r3c2–r3c4 lower down, plus the bottom edge of the chart card. Nothing new.
  r2c2, r2c4, r2c3. Contents: bottom corners of the KPI cards, three gutters (each 14 ship px, consistent), chip ends, top border of the chart card, 2,000 gridline, Signups bars. The reference/gridline doubling seen in r2c1 continues here (same defect, reported once). The top of the Jul 15 bar rises about 1 ship px above the reference. That is data, so no finding.
  Unread: r1c3 and r1c4 (middle of the header, where the subhead ends) and r2c5–r4c6 (right ends of both plots: the end of the reference line, gridline and baseline ends, the last bars, the last x labels, the right edge of the chart card). I make no claim about line ends or label clipping there.
Findings:
  - id: L1
    target: artifact
    rule: b. Joints meet (doubled stroke where two outlines sit a pixel apart)
    severity: MEDIUM
    location: r2c1 @ 125,418 (continues through r2c2–r2c4 to at least 923,418)
    evidence: In the Signups chart, the 2.25 ship px dashed reference (y 417.3–419.5) runs parallel to the 1 ship px 1,000 gridline (y 420.5–421.5) with 1 ship px (2 device px) of background between them, across the whole visible plot width. The gridline shows through each 5 px dash gap directly under the reference, so at 1x the pair reads as one smeared line and under zoom as a misregistered double rule.
    fix: Suppress the 1,000 gridline in the Signups chart, or skip any gridline within about 4 CSS px of the reference line, so the dashed reference is not shadowed by a parallel hairline 1 px below it.
    form_fatal: no
Issue rank: L1
Ship (this seat's loss only): yes
Confidence: medium
Recused: hierarchy, scale survival, contrast ratios, stipulated line ends, wording and units, distinctiveness, premise, empty space, reference-line value and meaning, data-driven tangencies between marks and the reference line
```
