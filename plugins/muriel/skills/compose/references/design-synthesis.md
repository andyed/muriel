---
reference: design-synthesis
status: active
requires:
  human_visible_decision: required
output:
  kinds: [design-thesis, option-comparison, leverage-map, experiment, decision-trace]
  registers: [app, game, web, native, editorial, data-product]
---

# Design synthesis — choose what earns implementation

Use this reference when the human-visible direction is not settled. Frame the
decision, explore materially different mechanisms, find shared leverage, choose
with explicit tradeoffs, and shape the smallest useful proof before polishing
the surface.

Do not use this reference as a license to own product truth, domain balance, or
code architecture. The calling agent retains those responsibilities. Muriel
makes the visible design decision coherent, legible, adaptable, and observable.

## Contents

1. [Load gate](#load-gate)
2. [Adaptive depth](#adaptive-depth)
3. [Synthesis loop](#synthesis-loop)
4. [Creative perturbation](#creative-perturbation)
5. [Leverage and synergy](#leverage-and-synergy)
6. [Choosing without false precision](#choosing-without-false-precision)
7. [Shape the investment](#shape-the-investment)
8. [Observable rationale](#observable-rationale)
9. [Proof and anti-patterns](#proof-and-anti-patterns)

## Load gate

Load before the primary visual channel when the task asks one or more of:

- what or why to build before how to render it;
- how a new feature, mode, gameplay grammar, information architecture, or
  interaction concept should work;
- which of several plausible directions deserves implementation;
- how one investment can create several independent benefits through shared
  state, rules, information flows, or production paths;
- how to break an ambiguous direction into a bounded, testable slice;
- how to preserve useful future choices without building a speculative platform.

Do not load for a local correctness, accessibility, typography, spacing, or
surface fix whose desired behavior is already settled. Do not load for
backend-only work. A necessary single-reason fix does not need a manufactured
strategy narrative.

## Adaptive depth

Choose the minimum sufficient ceremony. Base depth on uncertainty,
reversibility, blast radius, and evidence gaps. Do not average these into a
decorative score.

| Mode | Use when | Required output |
|---|---|---|
| **Direct** | A known pattern fits; impact is local, reversible, and supported by evidence | Decision, integration, proof |
| **Compare** | Several defensible answers exist; expertise or cross-cutting tradeoffs matter | Question, 2–4 options, criteria, leverage, decision, proof |
| **Probe** | The effect depends on real use or emergent behavior; analysis cannot predict the winner | Competing hypotheses or slices, safe-to-fail bounds, signals, expand/stop conditions |

State the selected mode and why in the Muriel entry contract. Change modes when
new evidence changes the nature of the decision. Do not keep a task in Probe
after a pattern has stabilized, or force Compare when one option clearly meets
the constraints and the others do not.

Route to Probe when the decisive criterion can only be learned through real use,
play, comprehension, or emergent system behavior. The presence of several named
options does not make the task Compare; QOC can organize options inside a Probe.
Use Compare only when existing evidence and analysis can credibly select the
direction.

Treat urgent chaotic incidents as the calling agent's operational problem, not
as a Muriel ideation exercise. Stabilize first; synthesize the human-visible
recovery later.

## Synthesis loop

Run only the stages required by the selected mode:

```text
Frame → Route → Explore → [Provoke] → Connect → Choose → Shape → Observe
```

### 1. Frame

Record:

- **Outcome** — the user or audience change the work should cause.
- **Focal decision** — one question whose answer changes implementation.
- **Product truth** — locked behavior, domain facts, and authority boundaries.
- **Canonical integration** — existing state, component, service, registry, or
  production path that may carry the choice.
- **Evidence** — observed artifact behavior, research, tests, traces, or user
  input already available.
- **Assumptions** — plausible claims not yet established.
- **Unknowns** — gaps that could reverse the decision.

Keep facts, assumptions, and concepts visibly separate. Do not let a fluent
concept silently become project truth.

### 2. Route

Select Direct, Compare, or Probe. Name the factor that set the depth. Prefer a
small proof over a long analysis when real use is the only credible source of
evidence.

### 3. Explore

Generate mechanisms, not cosmetic variants. Include a baseline or smallest
change when it is viable. Each option must differ in state, rules, information
flow, interaction, composition, or user leverage—not merely in naming or skin.

Do not fill an option quota. Two real alternatives are better than four padded
ones. Preserve surprising concepts long enough to test their mechanism, but do
not protect novelty from product constraints.

### Optional: Provoke

Do not draw a provocation by default. Load
[`creative-provocations.md`](creative-provocations.md) when:

- the first options are variations of one hidden assumption;
- the exploration changes labels, styling, or intensity but not the mechanism;
- a favored direction has become too coherent to question;
- a Compare or Probe has stalled without producing a discriminating move; or
- the user explicitly asks to brainstorm, get unstuck, or seek an oblique angle.

Use one fitted transformation first. Use at most three when breadth is the
purpose. Record what assumption each challenged and what changed. A provocation
earns a place in the option set only after it returns through product truth,
constraints, evidence, and canonical integration.

### 4. Connect

Look for one shared mechanism that creates several benefits. Check canonical
state, information flows, feedback loops, rules, and goals before proposing a
new abstraction. Ask:

- What immediate user-visible problem does the investment solve?
- What existing inconsistency or duplication does the same mechanism remove?
- What does it make easier to learn, test, explain, or verify?
- Which named, plausible next use can adopt it without another parallel model?
- Which future choices remain available without being implemented now?

Then run the leverage and synergy tests below.

### 5. Choose

Use Questions, Options, and Criteria as a compact design-space record. Mark how
each option **supports**, **conflicts with**, or remains **unknown against** each
criterion. Add evidence beside the judgment.

Apply hard constraints before tradeoffs. Eliminate an option that violates
product truth, accessibility, safety, canonical ownership, or the task boundary;
do not let strengths elsewhere compensate for a fatal weakness.

### 6. Shape

Turn the choice into a thin slice with explicit exclusions, integration, and
proof. Distinguish enabling work required by the slice from infrastructure that
would only benefit hypothetical future work.

### 7. Observe

Emit a public rationale summary at the depth required by the mode. Record
evidence, options, assumptions, decisions, and proof—not private chain-of-thought
or a chronological transcript of every idea.

## Leverage and synergy

Use a lightweight leverage ladder:

1. **Parameter or surface** — copy, timing, color, number, local layout.
2. **Information or feedback** — what becomes visible, when, and to whom.
3. **Rule or canonical state** — permissions, transitions, incentives,
   constraints, ownership.
4. **Goal or mental model** — what the system teaches the user to pursue or
   understand.

Prefer the highest justified intervention, not the highest imaginable one. A
surface fix is correct when the underlying model is already right. A new skin is
not a new grammar when the same trigger, stakes, choices, and recovery remain.

Call an investment synergistic only when:

- one named mechanism directly causes at least two benefits;
- each benefit remains valuable if another disappears;
- the benefits share implementation, state, rules, or evidence—not merely a
  release milestone;
- at least one benefit is immediate;
- any reuse claim names a plausible near-term consumer;
- the shared mechanism reduces total complexity or creates justified
  optionality.

Treat optionality as the right, not the obligation, to take a later action. Do
not implement the later action to prove the option exists. Prefer a narrow seam,
stable contract, or canonical field over a general platform with no current
consumer.

Permit single-reason investments when the reason is sufficient: correctness,
accessibility, safety, legal truth, or a locked product requirement does not need
reason inflation.

## Choosing without false precision

Start with qualitative QOC:

| Field | Required answer |
|---|---|
| Question | What decision changes implementation? |
| Options | What materially different mechanisms could answer it? |
| Criteria | What outcomes, constraints, risks, and evidence distinguish them? |
| Judgment | Supports, conflicts, or unknown—with evidence |
| Decision | Which option, at what confidence and status? |

Common criteria include user value, product truth, strategic anticipation,
mechanical or perceptual distinctness, canonical integration, accessibility,
cost, risk, reversibility, learning value, and proof quality. Select only criteria
that can change the decision.

Do not use default numeric weights. Use a weighted or multi-criteria matrix only
when several live options remain after hard constraints, stakeholders genuinely
value criteria differently, and the scales can be explained. Treat the result as
decision support, not an automatic answer. Run a sensitivity check before
trusting a narrow winner.

## Shape the investment

Write a design thesis:

- **Decision** — the mechanism to build or test.
- **Immediate value** — the first user-visible outcome.
- **Independent reasons** — the other benefits that pass the independence test.
- **Shared leverage** — the canonical mechanism producing those benefits.
- **Tradeoffs** — what becomes harder, costlier, or less flexible.
- **Thin slice** — the smallest complete experience that tests the thesis.
- **Enablers** — only the shared work the thin slice actually requires.
- **Excluded** — adjacent work deliberately left out.
- **Proof** — observable signals, rendered states, exercised paths, or tests.
- **Options preserved** — later actions enabled but not implemented.

For Probe mode, define two or more safe-to-fail probes only when they can teach
different things. For each probe specify:

- hypothesis and uncertainty;
- bounded scope and downside;
- sensor or observation method;
- success, stop, and expansion signals;
- decision the result will inform.

## Observable rationale

Treat one Muriel consultation as a design trace. Treat Frame, Explore, Choose,
and Shape as conceptual spans; treat an assumption change, option rejection,
scope change, or proof result as an event; link related earlier decisions; and
mark the decision **proposed**, **accepted**, **proven**, or **superseded**.

When a provocation was used, also record its stable id or transformation family,
the assumption it challenged, the option delta it caused, and whether that delta
was kept, adapted, or dropped. Do not record a private reasoning transcript.

Always expose a concise human-readable summary. Use only the fields required by
the mode:

```text
Muriel synthesis
Decision ID: <stable task-local id when persistence matters>
Mode: direct | compare | probe — <why>
Question: <focal decision>
Evidence: <facts and inspected sources>
Options: <material alternatives; omit in Direct>
Provocation: <id/family → assumption → option delta → disposition; omit if unused>
Criteria: <decision-changing criteria; omit in Direct>
Leverage: <shared mechanism and independent benefits>
Assumptions: <unknowns plus tests>
Decision: <choice, confidence, proposed|accepted|proven|superseded>
Thin slice: <bounded implementation or probe>
Integration: <canonical state/component/production path>
Proof: <signals, tests, renders, or exercised paths>
Links: <prior decision ids or artifacts when relevant>
```

A Compare or Probe response without the labeled mode, focal question, decision,
integration, and proof is incomplete even when its recommendation is sound.
Direct work that did not pass the load gate does not need a synthesis block.

Minimum observable content by mode:

- **Compare:** mode, question, evidence, options, criteria, leverage, decision,
  integration, and proof.
- **Probe:** all Compare fields plus assumptions, bounded probe, observable
  signals, expand/stop conditions, and decision status.

Keep the labeled core stable, but allow closely related content to share a field:
criteria may sit beside option judgments, the decisive uncertainty may sit in
Mode, and integration may be repeated only in the Muriel delta. Do not emit an
empty label or duplicate prose merely to satisfy the template.

Do not fabricate fields to make the trace look complete. Mark unknowns honestly.
Do not expose private reasoning. The observable object is the decision space,
supporting evidence, selected direction, and learning history.

Persist a machine-readable trace only when the calling environment already has
an authorized event-log or decision-record sink, or the user requests one. Keep
the event shape small and versioned:

```json
{"kind":"muriel.design","version":1,"decisionId":"…","phase":"frame|explore|choose|shape|proof","mode":"direct|compare|probe","status":"proposed|accepted|proven|superseded","summary":"…","evidence":["…"],"links":["…"]}
```

Do not add a telemetry dependency merely to emit this record. A later logger can
reuse the same shape without changing the reasoning contract.

## Proof and anti-patterns

Judge synthesis by whether it changes a material decision and produces better
evidence, not by the number of options, criteria, or trace events.

Before handoff, check:

- [ ] The mode matches uncertainty and stakes.
- [ ] Options differ mechanically or structurally, not only cosmetically.
- [ ] Any provocation names the challenged assumption, option delta, and
  keep/adapt/drop disposition.
- [ ] Product truth and authority boundaries remain explicit.
- [ ] Every synergy claim names one shared mechanism and independent benefits.
- [ ] Speculative reuse has a named near-term consumer or is omitted.
- [ ] The thin slice can disconfirm the design thesis.
- [ ] Proof measures user-visible behavior or comprehension, not copy variance.
- [ ] The rationale marks assumptions and can be superseded without erasure.

Do not ship synthesis that:

- expands scope to manufacture synergy;
- turns every decision into a workshop or weighted matrix;
- presents a bundle of features as one shared investment;
- confuses canonical integration with proof that the existing UI carrier is
  correct;
- treats distinct titles, artwork, or options as proof of distinct behavior;
- records polished conclusions without their evidence or uncertainty;
- preserves a chosen decision by deleting rejected alternatives or prior status;
- uses observability as a pretext to expose private chain-of-thought.

## Framework lineage and Muriel adaptation

Adapt this reference from:

- the [Design Council's Systemic Design
  Framework](https://www.designcouncil.org.uk/resources/systemic-design-framework/)
  and Double Diamond cadence—diverge, converge, reframe, connect, and continue;
- [Cynefin](https://thecynefin.co/about-us/about-cynefin-framework/)'s
  context-sensitive distinction between routine, analyzable, and emergent work;
- MacLean, Young, Bellotti, and Moran's [Questions, Options, and
  Criteria](https://doi.org/10.1080/07370024.1991.9667168) design rationale;
- Donella Meadows's [leverage
  points](https://donellameadows.org/archives/leverage-points-places-to-intervene-in-a-system/),
  especially information flows, feedback, rules, and goals;
- the CMU SEI's [real-options treatment of architectural
  patterns](https://www.sei.cmu.edu/library/quality-attribute-based-economic-valuation-of-architectural-patterns/)
  as the right, not obligation, to take later actions;
- lightweight [architecture decision
  records](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
  and [trace/span/event/link/status](https://opentelemetry.io/docs/concepts/signals/traces/)
  observability semantics.

Muriel deliberately keeps the composite smaller than any source framework. Use
one adaptive router, one synthesis loop, qualitative comparison by default, one
thin-slice proof, and one public rationale record.
