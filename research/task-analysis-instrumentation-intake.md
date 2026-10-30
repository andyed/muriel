# Task modeling and task-aware instrumentation

Intake: 30 October 2026 UTC. Operational extension of the existing
[interaction-models review](interaction-models-review.md), whose GOMS section
already supplied the theoretical foundation. This intake accompanies the new
[task-analysis reference](../plugins/muriel/skills/compose/references/task-analysis.md).

## Why this extension

The design opportunity is to connect goals, alternative methods, selection
rules, and required knowledge to the evidence used to verify a complete task.
The prior runtime routing emphasized microstrategies; the research review alone
did not supply this operational connection.

Andy identifies Hilbert and Redmiles as foundational to his work. Uzilla also
explicitly cites their taxonomy. The resulting Muriel direction joins
procedural modeling with task-aware observation: model what a design asks the
person to do, record what can actually be observed, and revise the model when
the two diverge. This is a design synthesis, not a claim that these papers
validated Muriel or today's product interfaces.

## Source ledger

| Source | Intake and supported use | Qualification |
|---|---|---|
| Card, Moran, Newell (1980), *The keystroke-level model for user performance time with interactive systems* | [Journal scan](https://frankritter.com/hcdd331/cardMN80.pdf); execution scope and operator construction; existing review intake retained | Error-free skilled execution of a specified method, not general task acquisition |
| John, Kieras (1996), *Using GOMS for user interface design and evaluation: Which technique?* | [Full article](https://people.eecs.berkeley.edu/~jfc/hcc/courseSP05/lecs/Cognitive%20Models/p287-john.pdf), especially §§1–2 and design cases | Extends the older review's abstract-only intake for this article; engineering predictions are legitimate conditional evidence |
| John, Kieras (1996), *The GOMS family of user interface analysis techniques: Comparison and contrast* | Existing review's inspected author manuscript and bibliography | Author-hosted PDF fetch timed out in this intake; no claim of a fresh full-text reading |
| Hilbert, Redmiles (2000), *Extracting usability information from user interface events* | [Author manuscript](https://ics.uci.edu/~dfredmil/publications/J006-HR00.pdf), §§3.2–3.4, 4.2, 4.5.5; selection, abstraction, recoding, context and sequence comparison | Manuscript pagination 1–38 differs from journal pagination; conceptual survey, not validation of a particular interface |
| Edmonds (2003), *Uzilla: A new tool for Web usability testing* | [Article](https://link.springer.com/content/pdf/10.3758/BF03202542.pdf), especially pp. 194–196 and 198; task definitions, browser/page identity, reference traces and interpretation | Multiple optimal paths and synchronization with video/observer/eye data were proposed extensions, not implemented features claimed here |
| Edmonds, White, Morris, Drucker (2007), *Instrumenting the Dynamic Web* | [Author-hosted article](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/edmondsjwe2007.pdf), §§4.2, 5, 7; dynamic state, structural identity, task-boundary uncertainty | Unassigned visitors do not establish participant intentions; hover interpretations and an overshoot proposal remain hypotheses |

The first five publication records were checked against Crossref on the intake
date. John/Kieras subtitle text follows the article titles; Crossref returns the
main title separately. New bibliography entries are in
[task-observation.bib](task-observation.bib); existing GOMS entries remain in
[interaction-models.bib](interaction-models.bib), without duplication.

For the 2007 article, the PDF, publisher contents, and volume author index give
244–260; the Microsoft publication record and issue abstract give 243–260.
The bibliography uses 244–260 and records the discrepancy. No DOI was established
for that article in the primary records checked.

## What the new guidance contributes

The runtime references separate goal analysis, formal model selection,
observation transformations, worked cases, and an evaluation protocol. Their
templates, current-product examples, async revision rules, and agent-evaluation
conditions are Muriel applications. They are not results reported in the papers.

The local Cartographer review and Protoplasm export review provide motivating
cases, including misses requiring user correction and disagreement between AI
review lenses. Neither supplies a controlled comparison of GOMS guidance,
measured workload reduction, or human acceptance of the revised workflow.
The export implementation agent's proposed repair remains distinct from
independently verified behavior at the time of case intake.

The next discriminating experiment separates baseline guidance, explicit
retrieval of existing guidance, new method analysis, and stronger journey
verification. This tests whether the additional method contributes beyond
attention, instructions, or verification effort. See the runtime
[evaluation protocol](../plugins/muriel/skills/compose/references/task-analysis-evaluation.md).

## Revision after independent review (29 October 2026, local time)

An independent review re-read John and Kieras (1996, "Which technique?"),
Card, Moran, and Newell (1980), the Hilbert and Redmiles technical report,
Uzilla, and *Instrumenting the Dynamic Web*. Every section and page pointer
above held. Changes made:

- **GOMS table.** All four variants estimate execution time; CMN-GOMS and
  NGOMSL also predict operator sequences, and NGOMSL represents what must be
  remembered. The earlier table implied only KLM and CPM-GOMS gave time.
- **Project Ernestine** added to the runtime GOMS reference. It was already in
  [interaction-models-review.md](interaction-models-review.md) but not
  available where design decisions are made.
- **Cognitive walkthrough** (Wharton et al., 1994) named, with its four
  questions. John and Kieras limit GOMS to routine skill and point to the
  walkthrough for first use.
- **Continuity checks moved** into interaction contracts: the next action
  stays put, one indicator per quantity, results carry their revision, ready
  is not delivered. They had lived only in task analysis, which an agent
  implementing a "settled" flow would not load.
- **Walker seat** added to the jury: the only seat given the task and the
  ordered frames. The export flow passed three single-frame seats.
- **Case 2 diagnosis corrected.** Interaction contracts already asked which
  branches reflect real user decisions; the export miss was mainly retrieval
  and verification, not missing theory.
- **Evidence governance** moved out of task analysis into the evaluation file.
  The cases were rewritten as forward analyses.
- **Forward exercises reclassified.** The October synthetic trace reused the
  examples in task observation almost item for item, and the archive task
  mirrored the source-review pseudocode. They show the guidance can be
  followed, not that it transfers.
