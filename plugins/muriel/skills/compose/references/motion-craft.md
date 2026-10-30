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

## Keep procedural light continuous

For shader and canvas effects that run inside an illustration or interface,
such as fire, glow, water, caustics, lamp light, smoke or sparks. A shader can
change any pixel in one frame, so continuity has to be designed in. Each rule
below answers a defect found in review of anatomy's shader figures (see
[Sources](#sources-and-adaptation)), and each one read as a cut.

- **Every uniform rides an envelope.** Nothing steps in a single frame. A
  one-shot event has an attack that leaves zero at zero slope and a decay. A
  level follows a critically damped follower, so it does not overshoot its
  target. These are `spring`-kind motion in `muriel.motion`: the time comes
  from the parameters, so validate those (`validate_spring`), and keep repeated
  flashes within `validate_flash_rate`. This section adds no durations.
- **Drive a phase change from one physical quantity.** Derive colour,
  brightness and size from a single state (pressure, temperature, energy)
  moving on its follower, so a change of phase is a crossfade. Two terms
  where one dies as the other grows read as a colour switch. If that state
  moves fast, give hue its own slower follower, and check that brightness
  does not dip and recover inside a flash: that is a cut hidden by the flash.
- **A fade-out only fades.** On a dark ground brightness only falls; on paper
  ink only thins. `mix(a, b, t)` with `b < a` climbs again as `t` decays, so
  freeze the peak when the fade starts and scale it only by quantities that
  fall. Two envelopes multiplied together can rise mid-fade when one is still
  growing: freeze the growing one first.
- **Every term reaches zero before any boundary.** That covers an `if`, a
  bounding volume, a plane, the edge of a noise cell and the canvas edge.
  Soften with `smoothstep`, and check that the outermost rows and columns of
  the canvas read exactly 0. Cell noise only looks inside its own cell, so a
  feature's offset, wobble, radius and tail must stay under half a cell, or
  the 3 × 3 neighbourhood must be sampled. Angular noise built on `atan` has a
  seam along one angle; sample noise of the direction vector instead.
- **Effects live in the scene's coordinates.** Build shader positions from the
  same camera or projection as the SVG or DOM layer, so a reflection on a
  floor registers with the floor's lines and a glow sized in world units stays
  the right size when the figure scales. When an effect sits both behind and in
  front of a part, stack a back layer, the canvas and a front layer instead of
  faking depth in one canvas.
- **Tonemap, never clamp, then dither.** A clamp flattens a bright core into a
  plateau. After tonemapping, add about ±1 LSB of animated noise, gated so empty
  pixels stay exactly 0. Without it, large soft gradients band into 8-bit steps.

**On a light ground, design the colour the page should show and solve for the
ink.** Screen blending over white is white, and no pixel can be brighter than
the paper, so light reads through saturation and a darker physical ground
(soot, deep water, shadow). A dark-theme glow that is darkened for paper reads
as a stain. Write the ramp from energy to the colour seen over the page, then
invert normal compositing over white, which shows `rgb + (1 − a)`:

```glsl
vec4 inkFor(vec3 seen, float cover) {
  vec3 absorbed = 1. - seen;
  float a = max(max(absorbed.r, max(absorbed.g, absorbed.b)), cover);
  return vec4(vec3(a) - absorbed, a);
}
```

`cover` is an alpha floor at the hot end. Without it a near-white core is
near-transparent and the lines behind it show through, so the core reads as a
hole instead of light. Give each kind of light its own ink (emission, light
falling on a surface, haze, sparks) and composite them back to front. Summing
the energies first and inking the sum gives everything one hue and loses the
pale core. Fade the finished ink once, never term by term: fading each term
before inking lets the pale core arrive ahead of its saturated body, and first
light goes pale, then dark.

Draw only while an effect is active and on screen, and cap the device pixel
ratio. Under reduced motion, show one representative steady state with time
frozen and no event envelopes. The illustration must still read with WebGL
unavailable.

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
- For a shader, slow every transition to about 5% speed and lay its frames
  out as a contact sheet. A pop is a jump between adjacent frames that the
  physical quantity did not make. Log one scalar per frame (mean luminance,
  total ink, or peak channel) through each transition and require it to move
  in the same direction as the quantity driving it. Crop the canvas edges at
  8–16× to confirm every term reaches 0 before them.
- Preserve the complete current state in the accessible alternative. Explanatory
  figures retain Muriel's complete final frame for reduced motion, no-JS, print,
  and static export. Keep essential information outside motion-only cues.

Rendered and interaction checks establish artifact behavior. Claims about
comprehension, workload, or emotional response need appropriate human evidence.

## Sources and adaptation

Craft inspiration, reviewed 2026-10-16 and 2026-10-24; these are design
precedents rather than empirical authority for numerical limits. The guidance
above is written for Muriel; no upstream code, media, or dependencies are
included.

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
- **anatomy:**
  [WebGL inside the drawing](https://github.com/wheresryan22/anatomy/blob/main/references/webgl.md)
  (sections 7 and 8, and the shader checks in
  [verify](https://github.com/wheresryan22/anatomy/blob/main/references/verify.md))
  informs the procedural-light rules: envelopes on every uniform, crossfades
  driven by one physical quantity, terms that reach zero before every
  boundary, ink solved from the colour paper should show, one ink per kind of
  light, and the slowed contact sheet. Its specific attack and decay times,
  device-ratio cap and per-figure ramps are not adopted; Muriel's timing comes
  from `muriel.motion`. The `inkFor` inversion is a three-line identity of
  normal compositing, restated here.
