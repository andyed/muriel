# Motion craft — staging, expression, and continuity

Use when motion needs an authored character, several elements must communicate
one change, or prepared imagery follows live input. Load from the polish,
interactive, or video channel; a routine transition needs only its existing
recipe. This reference informs design within the host's current animation stack.

## Keep the clock and the contract

[Polish rules](polish-rules.md#motion-scope-what-the-binary-governs),
`muriel.motion`, and the host's compliant brand tokens remain authoritative:
utility transitions stay at or below 100 ms, cinematic transitions at or above
1500 ms. Keep the existing hold, spring, and press distinctions, sequence
budgets, easing directions, scale limits, and reduced-motion policies. This
reference adds no timing bands or exemptions. Do not stretch routine feedback
into the cinematic bucket to accommodate a borrowed recipe.

Use [interaction contracts](interaction-contracts.md) for state ownership,
acknowledgment, cancellation, and recovery. Animation completion must not imply
an operation succeeded. Expressive motion must preserve access to controls and
the host's actual state.

## Give motion a specific job

Name what the viewer should notice: an object's destination, a relationship,
a changed status, a material transformation, or a deliberate expressive moment.
Then choose a property and path that carry that meaning. A moving object can
retain its identity across a layout change; a reveal can expose a relationship;
a settled pose can make a result available for inspection.

For expressive work, translate a few words from the brief into concrete choices
within the existing rules: restrained displacement, a consistent origin,
controlled arcs, coordinated arrival, or a distinctive resting pose. Reuse
those choices for related actions. Brand character can live in geometry,
amplitude, and composition while the timing tokens stay fixed. Follow the
host's easing semantics; do not replace them with a universal signature curve.

Treat associations such as curved movement suggesting warmth as design
hypotheses to inspect in context. Do not assign a stock personality to an entire
product category or claim a motion recipe reliably produces an emotion.

## Choreograph relationships

- Stage the meaningful change around one focal action. Supporting movement is
  optional and should make that action easier to follow; a quiet background is
  a valid composition. Keep Muriel's one load-bearing motion per interaction.
- Derive origins and destinations from relationships: a panel from its trigger,
  an item toward its new location, a detail from its parent. Preserve stable
  anchors where the viewer needs to compare before and after.
- Sequence by dependency or reading order when that relationship matters.
  Elements expressing one event may arrive together. Do not stagger every list
  or impose a screen-fraction rule on how many elements may move.
- Use anticipation or follow-through only where it earns its place. A narrative
  reveal may benefit from preparation and settlement; a repeated command needs
  immediate acknowledgment. Optional secondary cues must obey the same timing,
  scale, and spring rules and must not delay access to the result.
- Let the result settle into a readable state. Keep important labels and values
  available for comparison; preserve text contrast instead of dimming unrelated
  content to manufacture emphasis. Judge a repeated interaction after repeated
  use, when surprise has worn off.

## Separate input, playback, and material

For interactive media, resolve these choices independently in the existing
interaction contract. Page layout or a file extension does not decide them.

| Choice | Design question |
|---|---|
| Input | Which pointer, scroll, touch, keyboard, data, or application-state change drives it? |
| Playback | Does input continuously select a frame, select a transition that plays, or start/stop autonomous playback? |
| State space | Is the material a bounded progression, a cycle, independent states, or genuinely two-dimensional variation? |
| Composition | Does the scene belong inside the media, or must the subject combine with the host page? |

Continuous control should retain its correspondence with input. A transition
selected by input needs an explicit interruption policy: retarget, queue, or
ignore for a stated task reason. When reversal is supported, continue from the
currently visible position rather than restarting a clip. Do not add cosmetic
lag to direct manipulation; any scheduled settling follows the existing motion
policy. A horizontal sweep cannot also represent independent vertical variation.

Keep product state in its canonical owner. A media manifest may describe frames,
segment boundaries, and mappings to existing state IDs; it must not become a
second application state machine. Derive media times from the processed output
and update them when trimming or re-encoding changes the sequence.

## Make the material hold together

Use native transforms or procedural rendering for changes they can express
faithfully. Prepared media is useful when pose, occlusion, material, or structure
changes require authored frames. Generated imagery used to explain a real
mechanism needs reference checks for that mechanism as well as visual continuity.

For a media sequence:

- Record what must stay consistent about subject identity, proportions, anchor,
  lighting, and background ownership. Inspect adjoining frames after processing;
  continuity depends on the displayed result, not just compatible prompts or
  planned poses.
- For a generated chain, use the accepted output endpoint as the next segment's
  starting reference when the production tool supports it. Check the resulting
  join again; matching input images alone cannot establish a seamless output.
- Choose delivery using real display dimensions, pixel density, decoded memory,
  and access pattern. An atlas can suit frequent random access; video can suit a
  longer progression. Measure seek and reversal behavior on the target device.
- Complete one representative segment in the actual host before producing a
  larger set. Include its transition to rest and, for interactive work, input
  reversal and the static alternative. Fix wrong subject structure or movement
  in the source material.

Keep existing generation providers, renderers, and media tools. These ideas do
not require installing either upstream skill or adopting its service defaults.

## Inspect the experience

Select checks that match the work:

- At normal speed, can the intended change and its destination be followed?
  Inspect sequence boundaries as well as isolated attractive frames.
- Exercise rapid reversal, interruption, repeated input, and keyboard/touch
  equivalents. Check that old playback cannot overwrite a newer state.
- Repeat common actions: does choreography become waiting, distraction, or an
  obstacle to comparison? Simplify the sequence within the existing timing rules.
- Check narrow layouts, actual display size, initial loading, media failure,
  and reduced motion. Disable continuous input-driven animation when the chosen
  fallback is static; turning off easing alone still allows frame changes.
- Preserve the complete current state in the accessible alternative. Explanatory
  figures retain Muriel's complete final frame for reduced motion, no-JS, print,
  and static export. Keep essential information outside motion-only cues.

Rendered and interaction checks establish artifact behavior. Claims about
comprehension, workload, or emotional response need appropriate human evidence.

## Sources and adaptation

Craft inspiration, reviewed 2026-10-16; these are design precedents rather than
empirical authority for numerical limits. The guidance above is written for
Muriel; no upstream code, media, or dependencies are included.

- **LottieFiles motion-design-skill:**
  [motion identity](https://github.com/LottieFiles/motion-design-skill/blob/main/skills/motion-design/director/motion-personality.md),
  [choreography](https://github.com/LottieFiles/motion-design-skill/blob/main/skills/motion-design/director/choreography.md),
  and [quality review](https://github.com/LottieFiles/motion-design-skill/blob/main/skills/motion-design/reference/quality-checklist.md)
  inform expressive consistency, staging, and repeated-use inspection. Its
  [core prescriptions](https://github.com/LottieFiles/motion-design-skill/blob/main/skills/motion-design/SKILL.md)
  for duration bands, mandatory motion layers, overshoot, opacity combinations,
  and screen-fraction limits are not adopted.
- **oil-motion:**
  [runtime semantics](https://github.com/oil-oil/oil-motion/blob/main/references/runtime.md),
  [delivery selection](https://github.com/oil-oil/oil-motion/blob/main/references/delivery-selection.md),
  and [production workflow](https://github.com/oil-oil/oil-motion/blob/main/SKILL.md)
  inform independent input/playback choices, continuity checks, resource-aware
  delivery, and a representative pilot. Muriel keeps the host's canonical state,
  production tooling, accessibility contract, and timing rules.
