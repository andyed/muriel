---
channel: prose
status: active
requires:
  brand: optional
  audience: required
  reads:
    - muriel.aiism
output:
  kinds: [txt]
  registers: [app, blog, social, editorial]
peer_channels:
  - readme
  - web
  - polish
  - science
---

# Prose — plain text that communicates

Text is the one artifact every project ships, on surfaces nobody designs: a
store listing truncated after three lines, release notes read on a phone, an
error string, a report a person reads once. Until now Muriel judged prose only
negatively, through the anti-slop list in [`SKILL.md`](../SKILL.md#prose-anti-slop-ai-writing-tells).
The list says what not to write. This channel says how to write the thing.

Part of the [muriel](../SKILL.md) skill. The invocation gate still applies:
Muriel joins for copy whose structure or register is unsettled, or for an audit
of shipped text, not for a one-word label change.

## When to use

- Store listings, product pages and promotional text, where the surface
  truncates and the reader is deciding whether to install.
- Release notes, changelogs read by users, announcements.
- UI strings: labels, empty states, errors, permission prompts, onboarding.
- Explainers and technical briefs, README prose, documentation pages.
- A report, handoff or summary an agent writes for a person.

**Not** for: scientific manuscripts (read [`science.md`](science.md), whose
register carve-out wins), the visual composition of a README
([`readme.md`](readme.md)) or an editorial page ([`web.md`](web.md)), or an
affordance problem dressed as a copy problem (see *Affordances before
instructions* in `SKILL.md`: fix the control, then delete the coaching).

## Purpose in the solution

Before writing, tell the calling agent:

- **Purpose:** what the reader must know or do after reading, in one sentence,
  and the one decision the text serves.
- **Integration:** the surface and its limits. Character or byte caps, where it
  truncates, which lines are visible before "more", whether headers and
  bullets render, which facts the surrounding product already states.
- **Proof:** the counts, the first-screen test, the Stranger pass and the
  linter run that will verify it.

## The reader contract

A person reads plain text to answer three questions, in this order:

1. **What is this?**
2. **What do I do with it?**
3. **What does it cost or require?**

Answer them in the part of the text the surface shows before any effort: the
first three lines of a store description, the first sentence of a release note,
the subject line, the first screenful of a README. Everything after that is
for the reader who has already decided to keep reading, and it is organized
for scanning, not for reading in order.

## Default workflow

1. Name the reader and the one decision. Write both down. They decide every cut.
2. List the facts first, each with its source: a verified build, a document,
   a measurement. A claim without a source does not enter the draft.
3. Choose the register from the table below. Registers have different rules
   for tense, caveats and history, and mixing them is the usual way copy goes wrong.
4. Write the first three lines against the reader contract. Rewrite them until
   a stranger could answer the three questions from those lines alone.
5. Structure the body for scanning: one idea per header, one list of parallel
   items, caveats once.
6. Cut. Apply the deletion test to every sentence: if removing it loses no
   information, remove it.
7. Measure: counts against the surface's limits, the first-screen test, the
   linter, a Stranger pass.
8. Hand over the text with its counts and the facts it rests on.

## Structure rules

- **Promise, definition, action.** Line one names the benefit in under about
  50 characters. Line two says what the thing is and where it runs. Line three
  says what to do first. Social proof, when it exists, is sentence two of the
  second paragraph. When it does not exist, the slot stays empty.
- **One idea per header.** A header is a benefit phrase of two to five words,
  set in capitals where the surface has no type hierarchy. Under it, one or
  two paragraphs of at most about 45 words each.
- **One list of parallel items.** Features, steps, options or files go in a
  single bulleted list of six to twelve items, each under twelve words, each
  starting the same way (a noun or a verb, not a mix). Two lists in a row are
  a sign the structure is wrong.
- **Price and permissions as lists, not prose.** What is free, what the
  purchase adds, what the subscription is, in bullets. One sentence after the
  list states the model: one-time or recurring.
- **Caveats once.** Requirements, limitations and privacy statements go in one
  block near the end, one line each. A caveat repeated in three sections reads
  as anxiety and costs the reader three times.
- **Never lead with a negative.** A header that says what the product lacks
  ("X: not available here") belongs in the caveats block. The same fact can
  open a section about where X *is* available.
- **Current truth, not history.** Reference text describes how the thing works
  now, in the present tense. A fixed defect gets one sentence stating what is
  true now, with at most a clause of history. Before-and-after tables,
  mechanisms and "why our tests missed it" belong in the changelog or commit.
- **A maker line, when the reader cares who made it.** One sentence, no
  adjectives: who, where, how many.
- **Stop when the content stops.** No closing summary, no restatement, no
  offer.

## Sentence rules

- One idea per sentence, about twenty words, carried by a verb. Start a new
  sentence rather than joining clauses with a semicolon or an em-dash.
- Put the topic in the subject position. When an inanimate subject takes a
  punchy transitive verb ("every export embeds the list", "the data tells
  us"), flip it: copula or passive with the topic as subject ("the list is
  embedded in every export"). Keep the active form only where the thing
  literally performs the action. This is the opposite of the usual "prefer
  active voice" advice, which is why it needs stating. Williams' *Style*
  (characters as subjects, actions as verbs) is the grounding.
- Name the actor. "The tests pass" names nobody, and "the analysis
  recommends" names a thing that cannot recommend. When an AI wrote the code and a person is the author
  of the document, the person's "I" does not claim the code. Write what the
  code does.
- Concrete nouns over category nouns. "Kaleidoscopes and flowing patterns"
  beats "visual experiences". A number beats an intensifier, and every number
  carries its unit and label, on its own line or in a table when it changes
  what the reader does.
- No flag-planting. "The part worth noting", "the key insight", "here's the
  thing" and their relatives instruct the reader how to weight the next
  sentence instead of earning it. They are always deletable. Delete them and
  move the claim to first position.
- No breathless adjectives and no false profundity. "Remarkably",
  "surprisingly", "stunning", "immersive", "seamless", "powerful" describe the
  writer's feeling. State the fact, explain why it matters,
  move on.
- Product names exactly as the project's naming document spells them, and
  platform or trademark names only in referential phrases ("for macOS", never
  "ProductMacOS").
- Register rules beat these rules. Scientific methods take the passive,
  and a hedge there is precision.

## Registers

| Register | Reader and moment | What changes |
|---|---|---|
| Store listing, product page | Deciding whether to install. Sees three lines, then scans | Reader contract in the first three lines. One feature list. Price and permissions as lists. Caveats once. No keyword stuffing, no subscription boilerplate for a one-time purchase |
| Release notes | Already a user. Wants to know what changed for them | One sentence of promise, then bullets under twelve words, benefit first. A fixed defect is one sentence of current truth |
| UI string | Mid-task. Reads a few words | Identify content, state, consequence or recovery. Never narrate a basic operation. Fix the affordance instead. Errors say what happened and what to do next |
| Explainer, technical brief | Learning how it works now | Present tense, current state, no "Update (v2.5)" blockquotes. Rewrite the section when the system changes |
| Blog post | Following a story | Keeps the thinking at the time. Changes go in a dated note at the end |
| Scientific | Reviewer | Passive in methods, hedging required, numbers with CI and effect size. The anti-slop defaults yield to the genre |
| Agent report to a person | Did not watch the work. Reads once | Lead with the outcome, and with what could not be verified. No narration of the reasoning, no names invented during the session, code and commands in fenced blocks, numbers in a table, stop when done |

## Verification

- **Counts.** Measure every field against its surface with a script, never by
  eye: characters for most text fields, bytes for fields platforms meter that
  way (App Store keywords), lines for subjects. Recount after every edit.
- **The first-screen test.** Cover everything below the fold the surface
  shows (three lines for a store description, the subject line for mail, the
  first screenful for a README) and answer the reader contract from what is
  left.
- **The deletion test.** Remove each sentence in turn. If nothing is lost,
  it stays out.
- **Read it aloud.** A sentence that needs a breath in the middle is two
  sentences.
- **The Stranger pass.** Seat the Stranger from
  [`references/jury.md`](../references/jury.md) on the text alone, brief
  withheld, and compare its three answers with the reader contract. The
  Pedant covers labels, units and numeric claims. The Squinter and Thumbnail
  do not apply to text.
- **The linter, then the read.** `python3 -m muriel.aiism <file.md>` catches
  shape tells (antithesis stacks, tricolons, anaphora, em-dash density). It
  skips single words by design and reports a flag-planting sentence as clean.
  Where the science-agent toolchain is installed, `science-agent prose-audit
  <file> --severity=info` adds the phrase rules. Canary any linter with a
  known slop sentence before trusting a clean report, then read the draft
  anyway: throat-clearing, vague declaratives and false agency are judgements
  about meaning, and no detector will make them.
  This channel quotes the tells it bans, so the phrase rules flag its own
  examples. A quoted tell is the one warning to read past.

## Anti-patterns

| Symptom | What it costs | Fix |
|---|---|---|
| A description with no bullets | The scanning reader finds nothing to land on and leaves | One feature list, one price list |
| The same caveat in three sections | Reads as anxiety and triples the reading cost | One caveats block near the end |
| A header stating what is missing | The reader meets the product's limit before its benefit | Positive header about where it exists. The limit moves to the caveats |
| Price and permissions in a paragraph | The reader cannot find what is free | Two lists and one sentence on the model |
| Adjective stacks, "experience" nouns | Says the writer's feeling, not the product | Concrete nouns, a number with its unit |
| Keyword stuffing | Reads as a search page, not a product | Keywords in the keyword field, prose for people |
| Fixed-bug post-mortem in reader-facing text | The defect becomes the project's story | One sentence of current truth |
| Flag-planting sentence | Asserts importance instead of earning it | Delete it. The claim moves to first position |
| Inanimate subject, transitive verb | Reads as machine-default and buries the topic | Topic as subject, with a copula or the passive |
| A closing summary or offer | Restates, and ends on the writer | Stop when the content stops |
| Subscription boilerplate on a one-time purchase | Legal reflex, wrong product | One sentence: one-time, not a subscription |
| Narrated operations in UI ("click to explore") | Coaching instead of affordance | Fix the control, then delete the line |

## Prior art

- Nielsen, *How Users Read on the Web* (1997): most readers scan, and text written
  for scanning measured better in his usability tests. The reader contract and
  the single-list rule follow from it.
- Krug, *Don't Make Me Think* (2000): omit needless words, which is the deletion test.
- Williams, *Style: Toward Clarity and Grace* (1990): characters as subjects
  and actions as verbs. The inanimate-subject rule is its application.
- Orwell, *Politics and the English Language* (1946): the six rules, including
  the one this channel keeps breaking on purpose ("break any of these rules
  sooner than say anything outright barbarous").
- U.S. plain-language guidelines (plainlanguage.gov): audience first, short
  sentences, headers that carry meaning, one idea per paragraph.
- hardikpandya/stop-slop (MIT): the source of the anti-slop list in `SKILL.md`,
  which this channel complements rather than repeats.
