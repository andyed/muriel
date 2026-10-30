# Human capabilities — academic grounding in the craft

Use when an interaction or representation needs deeper cognitive grounding
than its primary channel provides. Muriel's production capabilities put that
grounding into practice. Start with the relevant academic work and the actual
task, identify the mechanism worth carrying forward, and embody it in the
software or artifact being built.

## From scholarship to interaction

Connect the source, mechanism, implementation choice, and observable outcome
inside the existing design rationale. For example:

- [Spatial composition](../channels/spatial.md) carries the focus-and-context
  and spatial-organization lineage into working layouts. Identify what position
  or peripheral context contributes to this task before choosing the geometry.
- [Visible Language](../vocabularies/visible-language.md) offers an academic
  design lineage for navigable typography and information landscapes. Treat its
  exemplars as design precedents; establish the value of a new application
  through its own use and evaluation.
- [Radial interfaces](radial-menus.md) translate interaction considerations into
  stable geometry, target acquisition, labeling, and input parity. Preserve the
  mechanism when adapting the surface to the host product.
- Distributed representations, below, provide a framework for deciding which
  relationships the display should carry and which work the person must do.
- [Gray's microstrategies and soft constraints](microstrategies.md) connect
  small interaction costs to the routines people adopt. Use this when timing,
  information access, or coordination of perception and action can change a
  design; it also provides a basis for exploring new interaction mechanisms.

Distinguish a theoretical account, an empirical result, and an academic design
precedent. Each can inform craft, with different implications for what is
already established. The relevant insight should affect what gets built.

Research also provides material for invention. A theoretical mechanism can
suggest an interaction that has no direct precedent. Treat that design as a
hypothesis worth building and testing; identify what it enables and which
learning or coordination demands change when it departs from convention.

## Frame the task before choosing a solution

Inspect the actual workflow and available user evidence. Establish only the
details that could change the decision:

- **Person and context:** relevant experience, access needs, tools, environment,
  interruptions, frequency of use, and consequences of error. Identify unknowns
  rather than inventing a persona or inferring ability from demographics.
- **Goal and activity:** what the person must notice, understand, compare,
  decide, create, perform, or learn; what success means to them.
- **Distribution of work:** what the person, software, external records, and
  other people contribute at each consequential step; include AI when present.
- **Demand and support:** where the design requires recall, search, inference,
  verification, coordination, or recovery; which existing strengths or artifacts
  can support that work.
- **Choice and evidence:** the design mechanism, predicted benefit, material
  tradeoff, and observation that could support or refute the prediction.

Keep this inside the existing Muriel synthesis or delta. A local decision may
need only a sentence; do not require a separate assessment for every control.

Before designing or changing a multi-step flow, use
[task analysis](task-analysis.md) to turn this framing into goals, methods,
selection rules, and knowledge demands.

For example, when designing a creative tool's parameter panel, compare how
people explore, compare, and return to earlier results. Persistent previews,
saved alternatives, reversible changes, and precise direct controls are
candidate mechanisms. Choose among them using the actual task and expertise
of the audience; test whether people can make and recover their intended
changes. This reasoning applies whether or not the tool has AI features.

## Select the relevant lens

These are design questions, not universal prescriptions or a scored checklist.

| Capability | Questions that can change the design |
|---|---|
| Perception and attention | What must be noticed, and when? What competes with it? Does an alert justify interrupting the current task? Is state legible through the supported sensory and input paths? |
| Memory and resumption | What must be remembered across screens or interruptions? Can persistent context, comparisons, history, or external records carry it? What helps the person resume? |
| Mental models and sensemaking | Can the person explain the current state, distinguish evidence from inference, and predict the next action? Which representation makes the important relationships inspectable? |
| Judgment and metacognition | Can the person check an answer and recognize when help is unreliable? Are alternatives, assumptions, and source evidence available at the decision point? |
| Learning and expertise | Is the goal immediate completion, skill development, or both? Which assistance supports that goal? Can experts act efficiently while learners obtain useful feedback? |
| Skilled action and creativity | Which direct controls, expressive choices, or practiced sequences matter? Where does generation help exploration, and how can the person refine and retain authorship of the result? |
| Agency and coordination | Who initiates, decides, acts, checks, and recovers? Can people redirect the system and understand handoffs, ownership, and changes made by others? |

Consider task demands together. Reducing clicks can increase verification work;
adding an explanation can increase reading without improving a decision;
automating a step can change the practice available to a learner. Treat such
effects as hypotheses to evaluate in the relevant context.

## When the interaction includes AI assistance

Use this lens only when the product includes AI. Decide whether assistance
should retrieve, suggest, generate alternatives, recommend, or act within the
project's actual capabilities and authorization rules.

Make suggestions, evidence, and completed actions distinguishable. Provide a
practical opportunity to inspect, correct, redirect, and recover. Account for
the effort and expertise required to review, the timing of proactive help, and
the person's goals for learning or direct control. Use the AI research anchors
below to inform the relevant mechanism and its evaluation.

Use [interaction contracts](interaction-contracts.md) for the resulting state,
feedback, input, and recovery behavior. Keep architecture ownership with the
calling agent.

## Evidence discipline

Separate four kinds of statement:

- **Research finding:** name and verify the primary source, task, population,
  and limits that matter to the inference.
- **Project observation:** state what was seen or measured and under which
  conditions.
- **Design hypothesis:** explain why a mechanism might help this task and what
  would change the judgment.
- **Tested outcome:** report the actual observation, comparison, and remaining
  uncertainty.

Retrieve primary research when a specific empirical claim or unfamiliar
mechanism drives the decision. Apply findings at their demonstrated scope;
explain extrapolation to a different task or population. Do not invent effect
sizes, universal memory or element-count limits, cognitive-load scores, or
claims that a particular style is psychologically optimal.

Distinguish performance, comprehension, preference, and subjective effort.
Do not infer understanding from gaze, clicks, time-on-task, or a saliency map
alone. Simulated users and agent critiques can expose candidate defects; they
do not establish how people behave.

## Match proof to the claim

Code and rendered-state checks establish implemented behavior and visible
properties. Human outcomes need relevant task evidence. Select the smallest
credible observation; do not turn every change into a formal study.

| Proposed benefit | Suitable evidence to seek |
|---|---|
| Important state is understood | Ask a person to explain the state and predict an action; observe relevant omissions or errors |
| Work is easier to resume | Exercise an interruption and return; observe context reconstruction, resumption errors, and effort |
| AI assistance improves decisions | Compare relevant unaided and assisted performance, including realistic AI errors and the ability to reject or correct them |
| Assistance supports learning | Observe later performance or transfer with appropriately reduced assistance; immediate assisted success answers a different question |
| Control and recovery are usable | Observe correction, cancellation, undo, and recovery in a realistic task; include relevant input and access needs |

Use an existing workflow or smallest viable alternative as a baseline when a
comparative claim matters. Report who participated, task conditions, what was
observed, and limits proportional to the claim. If task evidence is unavailable,
deliver the bounded design recommendation, mark the human benefit unverified,
and name the next useful observation.

## Research anchors

Use these as starting points for the named questions, not blanket endorsements
of every recommendation above:

- Zhang and Norman (1994), [*Representations in Distributed Cognitive
  Tasks*](https://doi.org/10.1207/s15516709cog1801_3): a framework for analyzing
  tasks through internal and external representations. Useful for asking what
  the display or artifact can carry instead of requiring mental reconstruction.
- Horvitz (1999), [*Principles of Mixed-Initiative User
  Interfaces*](https://www.microsoft.com/en-us/research/publication/principles-mixed-initiative-user-interfaces/):
  automation combined with direct manipulation, considering uncertain intent,
  attention, timing, and the costs of action. Use to frame allocation of work.
- Amershi et al. (2019), [*Guidelines for Human-AI
  Interaction*](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/):
  interaction guidelines evaluated with design practitioners across AI-infused
  products. Useful for expectation setting, correction, control, and adaptation;
  this validation does not prove a particular product improves human cognition.
- Buçinca, Malaya, and Gajos (2021), [*To Trust or to Think: Cognitive Forcing
  Functions Can Reduce Overreliance on AI in AI-assisted
  Decision-making*](https://arxiv.org/abs/2102.09692): their experiment found
  reduced overreliance from cognitive forcing, with subjective-rating tradeoffs
  and differing benefits by cognitive motivation. Use to motivate testing the
  tradeoff, not a universal requirement to add friction or explanations.
