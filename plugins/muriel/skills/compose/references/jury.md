---
reference: jury
status: experimental
requires:
  contested_visual_decision: required
  deterministic_checks_first: required
output:
  kinds: [juror-ballot, direction-ranking, split-report, panel-finding, ledger]
  registers: [app, web, editorial, data-product, science]
---

# Jury — panel judgement for contested visual decisions

Use this reference when one critic is not enough and averaging several critics
would be worse than either. A jury ranks materially different directions and
widens defect coverage. It does not produce a more confident number.

Muriel convenes the panel. She is not on it. SKILL.md makes her a visual
collaborator, not a detached critic; the jury is a body she summons, and its
finding is evidence she carries back into the build. The calling agent still
owns product truth.

## Contents

1. [Load gate](#load-gate)
2. [Jurisdiction](#jurisdiction)
3. [Two bodies, two aggregation rules](#two-bodies-two-aggregation-rules)
4. [Seat definition](#seat-definition)
5. [The roster](#the-roster)
6. [Ballot mechanics](#ballot-mechanics)
7. [The sealed round](#the-sealed-round)
8. [Splits are the product](#splits-are-the-product)
9. [Delphi round](#delphi-round)
10. [The ledger](#the-ledger)
11. [Unanimity smell test](#unanimity-smell-test)
12. [The chair](#the-chair)
13. [Worked example](#worked-example)
14. [Anti-patterns](#anti-patterns)
15. [Prior art](#prior-art)

## Load gate

Load when all three hold. **Contested** — the question survives after the
deterministic checks ran and their results were stipulated. **Consequential** —
the answer changes implementation, not decoration; Compare-mode direction
selection is the clearest earn. **Committed** — the artifact enters a repo,
paper, published page, or shipped surface this session.

**Cost is per seat per option, not per panel.** Budget one critique per seat
per option, plus that seat's lens cost: the Squinter renders a four-level blur
ladder per option, the Thumbnail reads two downscales per option, the Forger
*builds* a forgery per option it audits. A three-seat panel on one artifact is
roughly 4-6× a single critique. The five-seat, three-option panel in the worked
example below is 15-25×. Scale the gate to that number, not to a flat 5×.

Do **not** load for: a test render or intermediate frame; anything a compute
tool answers; a settled direction needing only execution notes; backend, copy,
or spacing work; a decision the calling agent has made and only wants ratified.
A single artifact with no alternatives is out of scope **only when its premise
is settled** — run [`muriel-critique`](../../../agents/muriel-critique.md)
alone. A single artifact whose premise is contested is in scope, and votes on
the single-artifact ballot defined under [Ballot
mechanics](#ballot-mechanics). When in doubt, run one critic: one with a clean
ledger beats five with correlated priors.

## Jurisdiction

The jury may not rule on facts. **Findings of fact** come from deterministic
tooling and enter as stipulated evidence, never as motions:

- `python -m muriel.contrast <file.svg>` — WCAG ratios per text pair;
- `python -m muriel.oklch <color>` — sRGB / OKLCH / in-gamut;
- `python -m muriel.devibe <path>` — AI-default design tells by regex over
  source: untouched shadcn/Tailwind defaults, AI-purple as primary, gradient
  headings, purple-to-blue gradients, neon glow, emoji-as-icons, the centred
  hero + three-feature-card skeleton;
- recorded seeds, dimensions, and export paths;
- **conditional, may return nothing** —
  `python -m muriel.tools.impeccable_bridge <path>` is a no-op when Node, npx,
  or the third-party `impeccable` CLI is absent, and degrades silently; the
  polish-rule regex checks (hit-area minimum, `transition: all`,
  `will-change: all`, missing `tabular-nums`, `scale < 0.95` press) are **not
  built** — they are a queued TODO item. A source that produced no output is
  not a stipulated clean bill. Record it as unavailable, and the question stays
  in jury jurisdiction rather than being struck.

**"Is this measurable?" depends on the substrate.** `devibe` reads HTML, CSS,
JSX, and SVG source and is decisive there; it is silent on a raster, a PDF, or
a screenshot, where there is no source to scan. Scope the Forger accordingly:
when the artifact has scannable source, `devibe`'s tell list is stipulated fact
and a Forger ballot claiming any of it is struck as `noise`; the Forger's
jurisdiction is what survives the scan — whether the *composition* is
reproducible from a generic template, which no regex answers. When the artifact
is a raster, the whole tell list returns to the Forger.

A juror may not vote a measured contrast failure down to "fine, it's
decorative." The 8:1 floor on readable text is on no ballot, in no round, under
no severity discount. Reproducibility is the same: a missing seed is a fact,
and facts are repaired, not debated.

**Jury jurisdiction** is only the genuinely contested: composition and focal
dominance; hierarchy and reading order; which of N directions earns
implementation; brand voice; whether an encoding earns its complexity; whether
the framing itself is wrong. The chair's first duty is kicking measurable
questions back to the compute tools. A ballot claim a tool could have settled
is struck, the tool is re-run, and the strike is logged as `noise`.

## Two bodies, two aggregation rules

One panel, two jobs, two rules. Never mix them.

| Body | Question | Aggregation |
|---|---|---|
| **Defect finding** | What is wrong here? | Union, max severity, no vote |
| **Direction selection** | Which earns build? | Comparative, split reported |

**Defect finding — worst critic wins.** Union every seat's findings; where two
name the same defect, keep the higher severity. Nobody votes a defect away,
because the loss is asymmetric: a false positive costs one wasted fix, a false
negative ships. Severity vocabulary is `CRITICAL | HIGH | MEDIUM | LOW`,
identical to
[`agents/muriel-critique.md`](../../../agents/muriel-critique.md), and the
rollup is unchanged — any CRITICAL → FAIL, any HIGH → NEEDS REVISION,
MEDIUM/LOW only → PASS.

**Direction selection — the jury proper.** There is no "worst" when ranking
viable options, so worst-case aggregation is meaningless. Use comparative
judgement, report the ranking with its scale values, report the split. A seat
may serve both bodies in one sitting; the chair routes each half of its ballot
to its own rule.

**A CRITICAL does not eliminate an option from the ranking.** This is the one
place the bodies touch, so the rule is normative here and not inferable from an
example. A CRITICAL sets that option's *verdict* to FAIL, which gates
committing it; the comparative ranking is computed over every option that was
seated, including that one. The winner ships only after its CRITICALs are
repaired and the re-render confirms the repair.

The single exception: a CRITICAL is **form-fatal** when its `fix` cannot be
applied without turning the option into a different option — the fix changes
the encoding, not the execution. A form-fatal CRITICAL eliminates the option;
the chair drops it and recomputes the ranking over the remainder, and records
which finding was form-fatal.

Why this rule and not elimination-on-any-CRITICAL. Elimination lets one seat
veto the comparative body: a single repairable defect on the Bradley-Terry
winner would hand the build to the runner-up, which is a defect-finding seat
deciding direction selection. The two bodies answer different questions —
"what is wrong here" and "which form earns build" — and a repairable defect
is evidence about the first, not the second. The form-fatal carve-out is
where the defect genuinely *is* evidence about the form, and it is narrow on
purpose: the chair must be able to name the encoding change the fix requires.

**A jury and `muriel-critique` are mutually exclusive.** Run one or the other
on an artifact, never both.
[`muriel-critique`](../../../agents/muriel-critique.md) is a generalist whose
coverage overlaps four of the five seats — hierarchy (Squinter), the
numeric-claim probe list (Pedant, which this reference delegates back to it),
AI-tell (Forger), and multi-scale evaluation (Thumbnail). Under union
aggregation, running both double-counts by construction: the same defect
arrives twice from correlated estimators and looks like corroboration.

## Seat definition

N copies of one critic is not a jury. Same base model, same priors, correlated
errors — you paid per seat per option for noise reduction on a biased
estimator. Prompt flavor
("harsh critic", "warm critic") changes tone, not the loss function, and
decorrelates nothing. A seat is three things, all stated when it is defined:

- **Lens** — the transformation applied before the seat sees the artifact. The
  real source of diversity: it changes the input, not the prompt.
- **Loss function** — what it optimizes against, and so what it is willing to
  be wrong about.
- **Evidence access** — what it may see, *including what it is denied*. A seat
  that read the brief and one that did not are different estimators.

Two seats sharing a lens and a loss function are one seat. Cut one.

## The roster

Five seats, all five shipped as agents. Seat them as subagents. Running one
inline as a scripted prompt is a weaker thing than seating it — say so on the
ballot rather than pretending otherwise.

**Evidence denial requires context isolation, and only a subagent provides
it.** A scripted prompt runs inside the chair's context. Anything the chair has
read — the brief, the option set, an unsealed ballot — is available to the
model producing that "seat's" output whether or not the prompt mentions it. The
denial is nominal: it is an instruction not to use evidence, not an absence of
evidence. Every ballot therefore carries `Isolation`, and an inline seat may
not be the sole source of a CRITICAL. Its findings still enter the union at
HIGH or below; promoting one to CRITICAL needs a second seat naming the same
defect.

**The Stranger may never be scripted inline.** It is the only seat defined by
denial of the brief. Run inside a context that has already read the brief, it
is the chair's own opinion wearing a persona — the exact failure the seat
exists to prevent, and worse than not seating it, because the ballot claims an
independence it does not have. It ships as a subagent and enforces this at its
own boundary: it audits its invocation for briefing material and aborts rather
than filing a contaminated ballot. If it aborts, reseat it cleanly or record
the Stranger as unseated. Do not argue with the abort.

**The Squinter — SHIPPED as an agent.** *Lens:* heavy Gaussian blur (sigma ≈ 2%
of the long edge), plus a luminance-only pass. *Loss:* misses in hierarchy;
willing to be wrong about detail it can no longer see. *Access:* blurred
renders only; denied the sharp artifact, all text, the brief. *Judges:* focal
dominance, reading order, figure/ground, whether the composition has one center
of mass or three. The actual test for hierarchy, not a proxy, and the blur is
deterministic, so the lens replays.

**The Thumbnail — SHIPPED as an agent.** *Lens:* the artifact at 1/8 scale, at
16 px, and at 16 px zoomed 8× for inspection — the three downscale companions
`muriel.squint` already writes on every run, so the lens replays. *Loss:*
misses in scale survival. *Access:* downscaled renders plus the intended use
sizes; denied the full-size render and the blur ladder. *Judges:* whether the
primary signal survives an OG preview, favicon, slide thumbnail, or paper
figure at column width.

It is not a smaller Squinter, and the distinction is what keeps the two seats
from correlating. Blur preserves position and area while removing high spatial
frequency, so a large pale mass survives `heavy` intact. Downscale destroys
sub-pixel features outright — hairlines, thin strokes, small type — and
aliasing invents structure that was never in the source. An artifact can pass
the hierarchy test cleanly and die at 16 px, and the reverse.

**The Stranger — SHIPPED as an agent; never seat it inline.** *Lens:* a
single `Read` of the artifact, no re-read, followed by three questions answered
from that one pass — what is this for, what is the one number, where do I
click. *Loss:* misses in premise; willing to be wrong about execution entirely.
*Access:* one pass over the artifact; **the brief is withheld from the
invocation**, as are the option set, every other ballot, and project context.
The only seat that can catch that the panel is grading the wrong thing well,
because every other seat is anchored to the brief. Fails on premise, not
execution.

The earlier form of this lens — "5-second exposure, then the artifact is
withdrawn" — is unexecutable in any harness and was replaced. You cannot
withdraw an image from a model's context, and a model has no exposure duration;
a prompt saying "you saw this for five seconds" is a costume. Single-read,
no-re-read, brief-withheld is the executable version of the same denial, and it
is enforceable only across a subagent boundary.

**What the Stranger actually measures.** It is not a naive human. It shares a
base model with every other seat, so isolation removes brief anchoring and does
nothing about model priors, training-set familiarity, or genre knowledge. Its
ballot reports what this model concludes from the artifact alone — a real and
otherwise-unavailable signal, and not the same as first-time human
comprehension. Its ballot therefore carries a mandatory `Prior strength` line:
`high` where the model has strong genre priors (a bar chart, a login form),
`low` where the artifact is novel enough that the reading approaches first
contact. Weight the seat by that line. Do not let a quiet Stranger on a
familiar genre be read as evidence that real strangers will understand it.

**The Forger — SHIPPED as an agent.** *Lens:* none on input; the lens is on
output. The seat asserts "I can reproduce this from a generic template in four
minutes," then *actually attempts it* and reports how close it got. *Loss:*
misses in distinctiveness. *Access:* the artifact and a generic component
library; denied the brand tokens, so it cannot cheat by copying them. Converts
the anti-slop check from rubric to proof obligation: "this looks generic" is
unfalsifiable, "here is the forgery, 4 minutes, differs only in accent hue" is
not. *Reports:* elapsed time, forgery path, and a named list of what it could
not reproduce. An empty list is CRITICAL.

**The Pedant — SHIPPED as an agent.** *Lens:* text extraction only — labels,
legend entries, ticks, captions, units, callouts, flattened with source
locations. *Loss:* misses in labeling. *Access:* extracted text plus any
sibling data file; denied the rendered composition, so a handsome layout cannot
charm it. *Judges:* unlabeled numbers, missing units, terminology drift between
legend and caption; applies the numeric-claim probe list from
[`agents/muriel-critique.md`](../../../agents/muriel-critique.md)
exhaustively. Unglamorous, highest hit rate of the five — most shipped defects
are a missing unit, not a broken layout.

**Its denial depends on substrate, and the ballot must say which it got.** On
source artifacts — SVG, HTML, Markdown, LaTeX, a plotting script — the denial
is real: the seat greps text nodes and never reads the render. On rasters there
is no OCR path that returns strings (`muriel.detectors.text` returns bounding
boxes only and is not a subcommand), so either the chair supplies extracted
text and the denial holds, or the seat reads the raster itself and records
`Isolation: subagent (denial partial — raster read)`. Its findings stay valid
either way; the claim of compositional blindness does not.

Note also that its probe list comes from `muriel-critique`, which is why the
two bodies may not both run — see [Two bodies, two aggregation
rules](#two-bodies-two-aggregation-rules).

## Ballot mechanics

**Randomize option order per juror.** LLM judges have strong position bias;
first and last presented options are systematically advantaged. Cheapest
available fix, and where most naive panels leak. Derive the permutation from a
**named digest, per seat**, so the panel replays:

```sh
printf '%s' "<decisionId><seatId>" | shasum
```

Read the hex digest left to right, two characters at a time, and use each byte
to pick the next option out of the remaining list (`byte % remaining`). Record
the result as `Order seen`. A ballot without `Order seen` is invalid. Do not
substitute a language-level hash — Python's `hash()` is salted per process, so
it does not replay across sessions, which is the entire point.

**Comparative judgement over absolute scoring whenever there are options.**
Absolute LLM scores are range-restricted — nearly everything lands 6-8/10 — and
badly calibrated across sessions. Pairwise forced choice builds a scale out of
binary decisions and yields an inter-rater reliability statistic for free. Run
the full pairwise set when N is 4 or fewer (6 comparisons per seat at most);
sample above that. Fit Bradley-Terry over the pooled comparisons for the
ranking.

**Two statistics, both raw proportions the chair computes by counting.** The
chair is an LLM with no fitting library; anything it cannot get by tallying the
ballots will not be computed. Bradley-Terry strengths are reported for the
ranking, but neither threshold below is defined on them, because a strength
means three different things under sum-to-one, log-odds, and probability
normalization.

- **Separation** — `P(top1 > top2)`, from the pooled pairwise tally: count the
  comparisons between the top two options across all seats, divide the wins
  for the higher-ranked option by the number of non-tied comparisons between
  them. 0.50 is a coin flip; 1.00 is unanimous.
- **Concordance** — the fraction of agreeing seat-pair judgements. For every
  unordered pair of seats and every option pair, score 1 when both seats gave
  the same strict judgement or both tied, 0.5 when exactly one of them tied,
  and 0 when they chose opposite options. Divide by (seat pairs × option
  pairs). This is the reliability figure.

**Reasoning before the vote.** The ballot emits reasoning *above* its
comparisons, ranking, and ship decision. A vote written first anchors the
rationale that follows, and you get justification, not judgement.

**Single artifact, no alternatives.** In scope when the artifact's premise is
contested; see [Load gate](#load-gate). Do not fake a comparison. Require a
forced rank of the issues — no ties, which stops a seat calling everything
equally critical — plus one binary ship call **scoped to that seat's own loss
function**. Binary decisions carry more than five absolute scores clustered
at 7. `Ship (this seat's loss only)` is not a panel ship decision and never
aggregates into one: the Squinter answering `no` means hierarchy fails, not
that the artifact is blocked. The chair reports the spread of these binaries as
part of the split; it does not tally them into a verdict.

Every juror agent emits exactly this block and nothing outside it:

```text
Juror ballot
Seat: <squinter | thumbnail | stranger | forger | pedant>
Decision ID: <stable task-local id>
Isolation: subagent | inline (denial nominal)
Order seen: <option ids, in the order presented>
Evidence seen: <what this seat was given>
Evidence denied: <what this seat was refused>
Reasoning: <prose; must precede Pairwise, Ranking, Issue rank, Ship>
Pairwise: <A>B, C>A, B~C>          (omit if no alternatives)
Ranking: <option ids, best first>  (omit if no alternatives)
Findings:
  - id: <seat-local id>
    target: <option id or "artifact">
    rule: <named rule or framework>
    severity: CRITICAL | HIGH | MEDIUM | LOW
    evidence: <concrete: where, what, measured or observed>
    fix: <one sentence, actionable>
    form_fatal: yes | no    (required on CRITICAL; see Two bodies)
Issue rank: <finding ids, worst first, no ties>  (single-artifact only)
Ship (this seat's loss only): yes | no           (single-artifact only)
Confidence: low | medium | high
Recused: <criteria this seat did not judge>
```

`Recused` is mandatory and non-empty for any seat whose access denies it
something. The Squinter recuses from typography; the Pedant from composition. A
seat that recuses from nothing is a generalist, and it will correlate with
every other generalist. `Isolation` is mandatory on every ballot: `subagent`
only when the seat ran in its own context, `inline (denial nominal)` otherwise.
A seat that reports `subagent` while running as a scripted prompt in the
chair's context is the one lie this format cannot survive.

## The sealed round

Round 1 ballots are sealed. Jurors do not see each other's ballots, a running
tally, or the panel size. Break this and the panel measures conformity, and
round 2 has no baseline. The chair unseals all ballots at once, after the last
lands, and never summarizes round 1 to a juror still voting.

## Splits are the product

Averaging jurors destroys the only thing a panel uniquely produces. A mean of
five rankings is a number; the disagreement behind it is a design finding.
Where the panel splits, that split **is** the unsettled decision — which is
muriel's whole remit. Report it, name what each side optimizes for, hand it up:

> Reader and implementer split on the disclosure control. Reader optimizes
> discoverability, wants always-visible. Implementer optimizes density,
> wants hover. This is a product call, not a visual one.

That returns cleanly to muriel's boundary: the calling agent owns product
truth. A jury resolving this by fiat oversteps the skill's contract. Report a
split when any of these five hold:

1. Two seats rank the top option differently.
2. One seat's top option is another's bottom option.
3. Separation between the top two is under 0.65 — `P(top1 > top2)` from the
   pooled pairwise tally, as defined under [Ballot
   mechanics](#ballot-mechanics).
4. One seat's `Ship (this seat's loss only): no` contradicts a majority `yes`.
5. **Two seats' fixes on the same target are mutually exclusive** — applying
   one makes the other impossible.

The split report names, per side: the seats, the favored option, the loss
function driving it, and the product question that would resolve it. It names
no winner.

**Trigger 5 is how the panel acquits a correct form.** Union aggregation has no
acquittal by itself: every finding survives, so a form both seats attack from
opposite directions collects both attacks and fails. Concrete case — a Tufte
small-multiples grid. The Squinter fires HIGH, "no mass dominates," and its fix
is to break the grid by scaling tiles. The Forger fires HIGH, "equal-weight
tiles are counterfeit stock," and its fix is to make the tiles more distinctive
per-tile. Meanwhile the form is correct: uniform tiles carrying one variable
each is what small multiples *are*, and the equality is the encoding.

Under union-max both findings ship, the rollup reads NEEDS REVISION, and a
chair forbidden a preference cannot say the form is right. Under trigger 5
the chair checks the fixes before the union, finds them mutually exclusive, and
routes both findings to the split report instead of the defect union. The
output becomes: two seats attack this form from opposite sides, one wants less
uniformity and one wants more, and neither fix can be applied without defeating
the other. That is a legible acquittal — it says the form is answering to a
constraint neither seat holds — and the chair reaches it by a mechanical test,
not by holding an opinion.

Route to the split, do not merge, and do not let either finding also enter the
union. A finding routed to a split is recorded in the ledger with the
disposition it later earns, exactly as a union finding is.

## Delphi round

Optional. Run one only when the split blocks a commit that must happen this
session. Unseal round 1, show every juror the full split — all ballots, all
reasoning — allow revision, and **record who moved**. A revised ballot carries
two extra lines: `Moved: yes | no` and `Moved because: <the specific evidence
in another ballot that changed it>`.

Movement toward the most confident or most verbose juror is a failure mode, not
consensus. If a seat moves and cannot name specific evidence in another ballot,
the chair discards the revision and keeps round 1. Three or more seats moving
in one round is a cascade: report round 1 as the finding and record the
cascade. Convergence is not the goal — a split that survives round 2 with both
sides stating their loss functions more sharply beats a unanimous round 2.

## The ledger

Severity inflation is the failure mode that kills harsh-critic systems. If
brutality is the reward, everything becomes CRITICAL, the scale collapses, and
under any-CRITICAL → FAIL the panel fails everything and carries zero bits.
Harshness is also cheap and usually unfalsifiable — "this lacks conviction" can
never be wrong. The antidote is scoring each seat against what happened next.

**Disposition vocabulary** — three resolved values plus one open. `hit`: fixed
**and** the re-render confirms it. `miss`: the human dismissed it with a stated
reason. `noise`: nobody could act on it, or the chair struck it for straying
into findings of fact. `open`: unresolved, excluded from all rates.

**The transition point is the re-render, and it has an owner.** Every finding
is emitted `open`. It leaves `open` at exactly one moment: when the artifact is
re-rendered after the fix pass — the Muriel delta. The agent owning that fix
pass writes the disposition, one per finding, at that re-render: `hit` if the
re-render shows the defect gone, `miss` if the human declined the fix and said
why, `open` if the finding was neither fixed nor declined. There is one
exception with a different owner and an earlier moment: the chair writes
`noise` at strike time, during the sitting, because a struck claim needs no
re-render to be resolved. Without a named moment and a named owner, everything
stays `open` forever, `open` is excluded from every rate, and the trailing-20
threshold below can never trip even in principle.

**Record shape.** One record per finding, versioned, emitted beside the
existing `muriel.design` trace and sharing its `decisionId`:

```json
{"kind":"muriel.jury.finding","version":1,"decisionId":"…",
 "seat":"squinter","findingId":"…","rule":"…","target":"…",
 "claimedSeverity":"CRITICAL","effectiveSeverity":"HIGH",
 "disposition":"hit|miss|noise|open","dispositionReason":"…",
 "proof":"…","recordedAt":"…"}
```

`claimedSeverity` is recorded verbatim so any discount is auditable. `proof` is
the render, test, or capture that confirms a `hit`. `dispositionReason` is
required for `miss` and `noise` and must be the human's stated reason, not the
chair's paraphrase.

**Where it lands.** A schema, not infrastructure. Do not build storage for it.
It is the finding-level child of the TODO item *"Effectiveness observability —
make the Muriel delta measurable"*, and it maps onto Session Cartographer's
proposed generic `skill_outcome` event: `kind` → event type, `decisionId` →
correlation key, `disposition` → outcome, `proof` → verification reference.
Persist only where an authorized event-log sink already exists, on the same
terms as `design-synthesis.md`'s trace: no telemetry dependency added merely to
emit a record, no reasoning exposed.

**Scoring rule**, over a seat's trailing 20 *resolved* findings. `miss` does
not count against a seat:

```text
precision       = hit  / (hit + noise)
noise_rate      = noise / (hit + miss + noise)
dismissal_rate  = miss  / (hit + miss + noise)     reported, never penalised
```

The earlier form put `miss` in the precision denominator, which made a seat's
standing a function of human agreement: "the human dismissed it with a stated
reason" scored identically to "nobody could act on it." Those are different
events. A correct-but-unwelcome finding is the first and scored as the second,
so the seat most exposed was the Stranger, whose entire job is to produce the
finding a team dismisses — the panel would have unseated its only check on
grading the wrong thing well. `noise` is the actual slop signal: nobody could
act on it, or it belonged to a tool. Score that; record `miss` and report
`dismissal_rate` beside precision so a human can see a seat generating
dismissals without the system acting on it.

The tradeoff, stated plainly: excluding `miss` means a seat that produces many
dismissed findings pays nothing for the reviewer's time it consumes, and
`dismissal_rate` is visible but toothless. That is the price of not letting the
panel converge on agreeable findings, and it is the cheaper error.

**Pre-ledger defense — one CRITICAL per seat per artifact.** Nothing writes
the ledger yet, so no seat has 20 resolved findings, so the discount table's
first row applies to every sitting and no discount engages. Until a sink
exists, the cap is the whole defense against severity inflation: a seat may
claim **at most one CRITICAL per artifact**, and it must be the finding it
ranks first. A second CRITICAL from the same seat is recorded at HIGH with
`claimedSeverity: CRITICAL` preserved, so the ledger sees the inflation when it
comes online. This is crude and deliberately so — it forces the seat to spend
its one veto on its best finding, which is exactly the discipline the ledger
buys once it can measure. Inline-seated seats are additionally barred from
being the sole source of a CRITICAL; see [The roster](#the-roster).

**Discount rule**, applied by the chair when setting `effectiveSeverity`:

| Condition | Effect |
|---|---|
| fewer than 20 resolved | face value, `provisional`; CRITICAL cap in force |
| `noise_rate > 0.30` | `effectiveSeverity` capped at HIGH |
| `noise_rate > 0.50` | `effectiveSeverity` capped at MEDIUM |
| `precision < 0.25`, 20+ resolved | unseated: recorded, never aggregated |

A capped seat can no longer trigger FAIL on its own; an unseated seat is
reinstated only manually. This is what makes "worst critic wins" principled
rather than merely loud: standing goes to the seat with the highest precision
at an acceptable `noise_rate`, and a seat that shouts gets quieter
automatically. Recall is deliberately not part of standing — the record shape
has no false-negative field and the disposition enum has no value for a defect
a seat failed to raise, so a recall figure would be uncomputable from what this
schema stores. Findings of fact are exempt — they were never the jury's to
claim.

## Unanimity smell test

If the panel agrees on everything, it is one juror wearing hats. Cut to one
critic and save the tokens. Check both after unsealing round 1:

- **Concordance** at or above 0.90, computed as defined under [Ballot
  mechanics](#ballot-mechanics).
- **Unique contribution** — fewer than half the seats, rounded up, produced a
  finding or comparison judgement no other seat produced. That is 2 of 3, 2 of
  4, 3 of 5. The old absolute "fewer than 2 of N" was far stricter at N=3 than
  at N=5, so a three-seat panel could pass a test a five-seat panel failed on
  the same proportion of unique contributors.

If either trips, record `panelCollapsed: true` with the tripped condition, ship
the strongest single ballot as the finding, and do not convene that seat
combination again for that artifact class until a seat's lens or evidence
access changes. Adding a personality is not a change.

**"Strongest" is mechanical, because the chair holds no preference.** Rank the
ballots by: (1) count of findings no other seat produced, most first; (2)
fewest claims struck as `noise` this sitting; (3) lowest `noise_rate` in the
ledger, seats without 20 resolved findings ranking last. Ship the top ballot.
If two ballots tie through all three, ship both unmerged and say they tied —
that is still not a preference.

## The chair

The chair is **not** a juror. It casts no ballot, breaks no tie by preference,
and contributes no findings of its own. Duties, in order:

1. **Fix the question.** One sentence the panel can answer. If it contains a
   measurable term, stop and run the tool.
2. **Run the deterministic checks**, enter them as stipulated facts, and repair
   fact-level failures before seating anyone.
3. **Seat the panel.** Only seats whose lenses and losses differ for this
   artifact. Three is a real panel; five is the ceiling. Do not seat the
   Stranger inline.
4. **Assign evidence access per seat**, denials included, and enforce it.
   Record each seat's `Isolation` honestly.
5. **Randomize option order** per seat with the `shasum` digest; record the
   permutations.
6. **Enforce jurisdiction.** Strike claims belonging to the compute tools; log
   each strike as `noise` against that seat, at strike time.
7. **Route mutually exclusive fixes to the split** before aggregating, so the
   union never stacks contradictory fixes on one target.
8. **Unseal, aggregate** by the correct rule per body. Apply the one-CRITICAL
   cap and the inline-seat CRITICAL restriction, then the ledger discounts.
   Ranking is computed over every seated option; a CRITICAL gates the commit
   and only a form-fatal CRITICAL eliminates.
9. **Run the unanimity smell test.**
10. **Write the finding,** with the split left unresolved, and emit one ledger
    record per finding at `disposition: open`.

The chair may not resolve a split. It reports the split and names the product
question. That is the finding.

## Worked example

Compare mode. Three directions for a per-AOI dwell readout in a gaze-analysis
app, about to be committed to the canonical panel component. Chair's question:
which dwell-readout direction earns implementation? **A** — small-multiples
strip, one mini heatmap per AOI, sorted by dwell. **B** — ranked horizontal
bars, dwell in ms, AOI labels inline. **C** — annotated stimulus overlay, dwell
numerals on the stimulus. Findings of fact, stipulated and not votable:

```text
dwell-a.svg → tick labels 4.6:1 on panel fill. CRITICAL. Repaired
  pre-seating (label → cream); re-run 12.1:1.
dwell-b.svg → minimum text pair 11.2:1. Clean.
dwell-c.svg → numerals 7.4:1 over the darkest sampled stimulus region.
  CRITICAL. Repaired pre-seating (opaque plate); re-run 12.9:1.
All three at 1400×900, seed 7, exported to render_assets/dwell/.
```

None of that entered a ballot; two directions were repaired, not debated.
Panel: all five seats, each as a subagent. The pedant read SVG source, so its
denial is real and its `Isolation` is plain `subagent`; on a PNG export it
would have carried `subagent (denial partial — raster read)` instead.

The stranger was invoked with three artifact paths and a decision id, and
nothing else. It did not receive the brief above, the question being decided,
or the fact that the three artifacts are alternatives to one another.

Round 1 sealed; ballots abridged to load-bearing lines:

```text
squinter   order B,A,C   pairwise B>A, B>C, C>A   ranking B,C,A   high
  Blurred, B is one descending wedge: a single unambiguous reading order.
  A is nine equal-weight blobs, no focal point survives. C is the stimulus.
  A / "one dominant focal point" / HIGH — nine tiles at equal area and
  luminance; blur leaves no rank. Fix: scale tile area by dwell.
  Recused: typography, labeling, units

thumbnail  order C,B,A   pairwise B>C, B>A, A~C   ranking B,C,A   medium
  At 1/8 scale B keeps bar length; labels vanish but rank survives. A
  becomes noise. C's numerals are gone by 1/4 scale.
  C / "evaluate at multiple implied scales" / MEDIUM — panel ships in a
  320px rail. Fix: add a rank strip.   Recused: full-size composition

stranger   order A,C,B   pairwise C>B, C>A, B>A   ranking C,B,A   high
  (brief denied; one Read per option, no re-read) On C I can say what it is
  for — where people looked on this screen — and point at the region. On B I
  read a ranking but could not say what the rows are; "AOI_03" meant nothing.
  B / "premise" / HIGH — identifiers opaque to anyone who did not define
  the AOIs; ranking legible, referent not. Fix: naming, not charting.
  Recused: craft, hierarchy, contrast

forger     order C,A,B   pairwise C>B, C>A, A~B   ranking C,A,B   high
  (tokens denied) Forged B from a stock bar component in 3m40s, reached
  ~90%: same encoding, sort, inline labels. Could not reproduce the
  dwell-band shading. Forged C: gave up at 4m; AOI polygon registration is
  not template work.
  B / "anti-slop: domain-specific decisions" / MEDIUM — 90% forgeable in
  3m40s. Fix: make the dwell band carry more, or accept B as commodity.
  Recused: hierarchy, contrast, labeling

pedant     order A,B,C   pairwise B>C, B>A, C>A   ranking B,C,A   high
  B labels units on the axis. C prints bare numerals with no unit in frame.
  A's legend says "dwell", its caption "fixation time" — not synonyms.
  C / "label every number" / HIGH — 14 bare numerals, no unit anywhere.
  A / "terminology drift" / CRITICAL, form_fatal: no — legend vs caption in
    one figure. Fix: pick one term and use it in both.
  Recused: composition, scale survival, brand voice
```

One mechanic fires on the pedant's CRITICAL before aggregation. It is not
form-fatal — aligning two words does not change A's encoding — so under [Two
bodies](#two-bodies-two-aggregation-rules) it gates A's commit and does not
delete A from the ranking. A's verdict is FAIL and A still ranks last on its
own merits, which is the ranking doing its own job rather than borrowing the
defect body's. Had the pedant been scripted inline, the inline-seat restriction
would have capped this at HIGH with `claimedSeverity: CRITICAL` preserved,
because no second seat named the drift — one more reason to seat subagents.

Finding, written by the chair:

```text
Muriel jury finding
Decision ID: gaze-dwell-readout-01
Question: which dwell-readout direction earns implementation
Panel: squinter, thumbnail, stranger, forger, pedant (all subagents)
Stipulated facts: 3 contrast runs; A and C repaired pre-seating; seed 7;
  devibe not applicable (SVG exports, no scannable component source)
Ranking: B 0.52 > C 0.41 > A 0.07 (Bradley-Terry, 15 comparisons)
Separation: P(B>C) = 3/5 = 0.60  (< 0.65 — split trigger 3)
Concordance: 20/30 = 0.67   Unique contributors: 4/5   Collapsed: no
Defects (union, max severity):
  CRITICAL A — terminology drift, legend vs caption      (pedant)
             form_fatal: no — gates A's commit, does not delete it
             from the ranking
  HIGH     A — no focal point survives blur              (squinter)
  HIGH     B — AOI identifiers opaque without the brief  (stranger)
  HIGH     C — 14 unlabeled numerals                     (pedant)
  MEDIUM   C — numerals die below 1/4 scale              (thumbnail)
  MEDIUM   B — 90% forgeable in 3m40s                    (forger)
No mutually exclusive fix pairs on one target — nothing routed to the
  split by trigger 5.
Verdict on A: FAIL (CRITICAL, not form-fatal). A ranks last on the
  comparative body; the defect body gates its commit. Neither eliminated
  it from the ranking.

Split: squinter + thumbnail rank B first; stranger + forger rank C first.
  Squinter and thumbnail optimize signal survival under degradation — B
  wins because bar length is the strongest channel and survives blur and
  downscale. Stranger and forger optimize referential grounding and
  distinctiveness — C wins because the answer is spatial and the spatial
  version cannot be forged. They are not disagreeing about craft. They
  disagree about whether this panel ranks AOIs or locates them.

Product question, unresolved: does the dwell readout serve triage (which
  AOI, ranked) or inspection (where, in place)? Product call, not visual.
  Returned to the calling agent. If triage: ship B; carry AOI names not ids
  (stranger, HIGH); strengthen or drop the dwell band (forger, MEDIUM). If
  inspection: ship C; add units (pedant, HIGH); add a downscale-surviving
  rank strip (thumbnail, MEDIUM).
```

No Delphi round: the commit was not blocked this session, and the split is the
useful output. Six ledger records emitted, one per finding and not one per
seat, all at `disposition: open`. They stay `open` until the calling agent
picks a direction, applies the fixes, and re-renders; the agent that owns that
fix pass writes each disposition at that re-render.

Both reported statistics are countable from the ballots above. Separation: the
five B-vs-C comparisons split 3 for B, 2 for C, none tied, so `P(B>C)` is 3/5 =
0.60, under the 0.65 trigger. Concordance: 10 seat pairs × 3 option pairs = 30
judgements, of which 16 agree outright and 8 involve exactly one tie at half
credit, so 20/30 = 0.67, well under the 0.90 collapse threshold.

## Anti-patterns

Do not:

- **Convene a jury on a measurable fact.** Contrast, gamut, dimensions, token
  adherence, and regex-detectable polish rules are settled by tools. A panel
  deliberating a contrast ratio can get it wrong.
- **Seat N copies of one critic.** Same lens, same loss, different adjectives
  buys correlated errors at one full critique per seat per option. If two seats
  do not deny each other's evidence or optimize different losses, cut one.
- **Run a jury and `muriel-critique` on the same artifact.** The generalist
  overlaps four of five seats; the union then counts one defect twice and it
  reads as corroboration.
- **Claim a denial a scripted prompt cannot enforce.** Evidence denial needs a
  subagent boundary. Inline, mark `Isolation: inline (denial nominal)` and
  accept the CRITICAL restriction; never seat the Stranger this way.
- **Stack mutually exclusive fixes in the union.** Two seats attacking one
  target from opposite directions is a split, not two defects, and routing it
  to the split is the only way the panel can acquit a form that is right.
- **Average away a split.** The mean of five rankings discards the finding. The
  split is the product; the ranking is the byproduct.
- **Let severity inflate.** A seat whose every finding is CRITICAL carries zero
  bits under any-CRITICAL → FAIL. Score dispositions, apply the discount, cap
  the shouters.
- **Convene on a test render.** Panels are for work about to be committed. A
  draft-DPI intermediate does not earn five seats.
- **Let the chair vote.** A chair with a preference is a sixth juror holding
  procedural power, and it will resolve splits it was meant to report.
- **Show round 1 ballots to a juror still voting.** That measures conformity.
- **Skip `Order seen`.** Without the recorded permutation you cannot separate
  judgement from position bias, and the panel does not replay.
- **Let a seat recuse from nothing**, or **run a Delphi round to manufacture
  agreement.** A seat that judges everything correlates with every other
  generalist; movement nobody can source to specific evidence is deference.

## Prior art

Adapt from the design-school crit and the award jury, which get the structure
right and the measurement wrong. Right: a chair who owns the question rather
than an opinion; a stated brief the work is judged against; recusal when a
juror has a stake; reasoning voiced before the score is committed. Wrong: halo
and star effects contaminate every subsequent criterion once one juror names a
favorite; the loudest or most senior voice dominates because deliberation is
public from the first minute; and absolute rubric scores show poor inter-rater
reliability across juries and across sittings. Comparative judgement —
Thurstone's law of comparative judgement via Bradley-Terry, as deployed in
educational assessment — exists largely *because* absolute-scoring juries in
education proved unreliable, and it yields the reliability statistic as a side
effect of the binary decisions. The sealed first round is the fix for public
deliberation; the Delphi round with a who-moved record is the fix for treating
convergence as evidence.
