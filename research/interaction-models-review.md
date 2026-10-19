# Cognitive psychology and HCI anchors for Muriel

Literature review · 11 October 2026 · Recommendations for discussion; no skill or runtime changes made by this review.

## Recommendation

Muriel should carry a compact set of models that help designers **change the work an interaction requires**. Its production capabilities remain the substance of the skill; these anchors explain when to choose, alter, or invent an interaction, and how to tell whether it helps.

The recommended core is Hick–Hyman with its qualifications, Fitts and steering, GOMS/KLM/CPM-GOMS, Gray’s microstrategies and soft constraints, external representations, active visual sampling, learning trajectories, and interruption/resumption. The [Scrutinizer companion review](scrutinizer-perception-review.md) develops the perception, attention, and information-foraging lineage in depth. Bimanual control belongs in the relevant specialist guidance. Each reference should connect a mechanism, its scope, an actionable design question, and an observable test. An equation or famous name alone is insufficient.

| Design question | Anchor to consult | Main boundary |
|---|---|---|
| What uncertainty must someone resolve before responding? | Hick–Hyman; Liu et al.’s critique | Choice reaction is not interchangeable with search or deliberation. |
| How difficult is reaching and selecting a known target? | Fitts; MacKenzie; MacKenzie & Buxton | Geometry, input device, accuracy, and calibration matter. |
| How difficult is staying inside a constrained movement path? | Accot & Zhai | Endpoint acquisition and path steering are different tasks. |
| What procedure does practiced work require? | GOMS; KLM | The method must be known or explicitly represented. |
| Which activities actually determine completion time? | CPM-GOMS; Project Ernestine; Gray | Overlap and dependencies defeat simple action counting. |
| Why do people consult information, remember, or skip checking? | Gray & Fu; soft constraints | Local access costs can change strategy without improving overall success. |
| Can a representation remove search or inference? | Larkin & Simon; Zhang & Norman | A picture or external artifact is not automatically useful. |
| What can guide inspection, and what becomes recognizable after it? | Crowding; peripheral representations; task guidance; information foraging | Detection, recognition, controller access, gaze, and understanding are different observables. |
| What happens as the interaction becomes familiar? | Marking menus; Heathcote et al. | First use and pooled averages do not establish a learning trajectory. |
| What makes stopping and returning easier? | Trafton et al. | Preparation evidence does not directly validate every checkpoint design. |

These are different analytical lenses, not terms to add into one universal formula. The recommendations and prototype ideas below are Muriel-specific inferences; the cited studies did not evaluate Muriel.

## 1. Hick–Hyman: uncertainty, with a serious transfer problem

Hick (1952) investigated response time in learned stimulus–response tasks. Hyman (1953) extended the information account to unequal probabilities and sequential dependencies. A common expression is `RT = a + bH`, where `H = Σ pᵢ log₂(1/pᵢ)`; equiprobable alternatives yield `H = log₂(n)`. Hick’s original formulation used `log₂(n + 1)`. Coefficients are fitted, and stimulus–response compatibility and experience matter. These experiments concern responding to a stimulus, not the full cost of understanding unfamiliar alternatives. [Hick](https://doi.org/10.1080/17470215208416600), [Hyman](https://doi.org/10.1037/h0056940).

Cockburn et al. (2007) developed and evaluated a menu model combining search/decision and pointing, including changing familiarity with item locations. Liu et al. (2020) challenge the theoretical transfer of Hick’s paradigm to HCI, particularly conflation of choice reaction, visual search, and deliberative choice. A logarithmic fit is not sufficient to identify the underlying process. Muriel should preserve this disagreement: the menu model can be useful within its calibrated setting without making its Hick interpretation settled science. [Menu model](https://doi.org/10.1145/1240624.1240723), [critical review](https://doi.org/10.1145/3313831.3376878).

**Design consequence.** Ask what is unknown: command identity, location, category, meaning, or consequence. Organizing a large command surface may help; dividing it into more stages may add search, navigation, and recovery. The papers do not supply a universal seven-option threshold.

**Invention to test.** Compare a broad, organized command surface with progressive disclosure. Compare adaptive emphasis with adaptive relocation. Record display onset, movement onset, selection, correction, and total task success across repeated use. Separate uncertainty reduction from faster pointing; do not infer a cognitive mechanism from total time alone.

## 2. Fitts: acquisition geometry and speed–accuracy tradeoffs

Fitts (1954) modeled movement under amplitude and accuracy constraints. MacKenzie’s 1992 review covers the HCI evidence, formulations, effective target width, and methodological problems in comparing devices and studies. A useful HCI form is `MT = a + b log₂(D/W + 1)`, with distance `D`, target width `W`, and fitted coefficients. It predicts a specified acquisition task; it does not include discovering the target or deciding what to do. [Fitts](https://doi.org/10.1037/h0055392), [MacKenzie](https://doi.org/10.1207/s15327051hci0701_3).

MacKenzie and Buxton (1992) show that treating a rectangular target’s horizontal extent as its width regardless of approach can give poor predictions. Their experiment compares alternative width definitions. This matters for text, wedges, narrow controls, and novel geometry: target area alone does not establish acquisition difficulty. Their fitted coefficients are properties of the tested conditions, not values to transplant into modern interfaces. [Two-dimensional tasks](https://doi.org/10.1145/142750.142794).

**Design consequence.** Examine start location, approach, selectable region, neighboring targets, and error/correction cost. Keep minimum hit-area policies distinct from performance predictions. Neither a 40-pixel floor nor a 44-pixel preference is a result derived from Fitts’s equation.

**Invention to test.** Prototype enlarged invisible hit regions, local command placement, or directional controls while preserving unambiguous selection. Compare movement time and endpoint errors over representative start positions, devices, and users. Estimate coefficients or use clearly labeled relative geometry hypotheses; do not publish precise millisecond savings from borrowed constants.

## 3. Steering: the path can be the difficulty

Accot and Zhai (1997) studied goal passing and steering through straight, narrowing, and spiral tunnels. Their path model relates time to `∫ ds/W(s)`; for constant width, a common fitted form is `T = a + bL/W`. Long narrow passages impose constraints that endpoint-only analysis misses. They also discuss limits, including saturation at large widths and limitations of the simple models. [Steering paper](https://doi.org/10.1145/258549.258760).

**Design consequence.** Inspect submenu transitions, constrained drag routes, and other interactions that require staying inside a corridor. Enlarging the final target can leave a narrow passage unchanged.

**Invention to test.** Compare wider transitions, alternative routes, or a mechanism that removes the corridor requirement. Observe path exits, retries, completion time, and accidental activations. An unconstrained drag is not automatically a steering task; curved or unfamiliar gestures require evidence appropriate to their geometry.

## 4. GOMS: model the method, then choose the right grain

GOMS represents goals, operators, methods, and selection rules. The original KLM estimates **error-free execution of a specified routine method by a skilled user**, using physical actions, mental preparation, and system waiting. Card et al. (1980) explicitly distinguish this from acquiring the task and identify other performance goals. Treating every screen transition as one mental operator, or estimating creative problem solving by counting keystrokes, exceeds that scope. [KLM](https://doi.org/10.1145/358886.358895).

John and Kieras’s paired 1996 papers distinguish the variants and their design uses. Choose the least elaborate model that resolves the question. [Comparison](https://doi.org/10.1145/235833.236054), [design applications](https://doi.org/10.1145/235833.236050).

| Variant | Useful question | Important limit |
|---|---|---|
| KLM | How do two specified, largely serial execution methods compare? | Does not discover the method or model general problem solving. |
| CMN-GOMS | Which subgoals, methods, and selection rules structure routine work? | Requires the relevant procedural knowledge to be represented. |
| NGOMSL | How do method structure, consistency, and procedure learning compare? | Learning estimates concern represented procedures, assuming operators are already known; they do not predict learning an entirely new input technique. |
| CPM-GOMS | How do perceptual, cognitive, and motor activities overlap, and what is critical? | More detail is useful only when the parallelism matters and dependencies are defensible. |

Published operator times are estimates, not universal cognitive constants. Vary plausible parameters and methods before trusting a small predicted difference. Replacing a pointing operator with an appropriate calibrated Fitts estimate can be useful; adding a separate decision term already covered by a mental operator can double-count work.

Project Ernestine supplies an important field example: CPM-GOMS predicted that a proposed telephone-operator workstation would be slower, contrary to expectations, and the field data supported that direction. Aggregate accuracy was stronger than prediction for individual call categories. This is evidence for modeling skilled routine work and its dependencies, not a guarantee for every task or worker. [Gray, John, and Atwood](https://doi.org/10.1207/s15327051hci0803_3).

**Invention to test.** Model the procedure a proposed interaction enables, not just its visible controls. A composite action, different command grammar, or change in information availability may remove a subgoal. Compare methods with observed traces, including alternatives people actually choose. Keep errors, understanding, learning, expressiveness, and fatigue as separate outcomes rather than assigning invented time penalties to all of them.

## 5. Gray: microstrategies, overlap, and soft constraints

Gray and Boehm-Davis’s 2000 paper shows why small changes in perceptual, cognitive, and motor coordination can alter interactive routines. Predictability and overlap matter; removing an action need not shorten the critical path. Their controlled task and their separate, small prototype observations have different evidential strength. The latter generate useful diagnoses, not general causal proofs. [Milliseconds Matter](https://doi.org/10.1037/1076-898X.6.4.322).

Gray and Fu (2004) found that people could use imperfect internal information rather than available accurate external information as access costs changed, with consequences for performance. Gray et al. (2006) developed the soft constraints account through experiments and modeling: allocation between internal and external resources can respond to the temporal costs of local routines. A locally economical strategy need not optimize the overall task. This is not a rule that people always minimize time or that external memory always helps. [Soft constraints and imperfect information](https://doi.org/10.1207/s15516709cog2803_3), [resource-allocation account](https://doi.org/10.1037/0033-295X.113.3.461).

**Design consequence.** Make essential information cheap to inspect at the moment of use. Look for reconstruction, repeated consultation, checking, and unproductive waiting. Verification itself can be valuable; the design aim depends on consequences and error costs.

**Invention to test.** Compare a persistent local reference with a panel people must reopen. Compare predictable and contingent next-action locations. Inspect strategy changes as well as time and accuracy. Test whether users consult the improved reference; merely making it available does not establish benefit. Muriel’s existing [microstrategies intake](../plugins/muriel/skills/compose/references/microstrategies.md) can remain the focused source treatment.

## 6. External representations: change the computation

Larkin and Simon (1987) distinguish informational equivalence from computational equivalence. In their analyses, spatial grouping and explicit relationships can change search, recognition, and inference. Advantages depend on the representation and the user’s procedures and knowledge; an arbitrary diagram is not superior to prose. [Diagram analysis](https://doi.org/10.1111/j.1551-6708.1987.tb00863.x).

Zhang and Norman (1994) analyze tasks as combined internal and external representational systems, using structured puzzle tasks. Different representations of an isomorphic problem can recruit different processes. Applying that account to collaborative software is a hypothesis to investigate, not an outcome established by those puzzles. [Distributed representations](https://doi.org/10.1207/s15516709cog1801_3).

**Design consequence.** Start with the relationship or constraint the user needs to perceive, rather than a preferred widget. Explore making dependencies, intermediate results, or allowable transformations visible and actionable. Externalizing information may change the strategy, not just reduce an undifferentiated “cognitive load.”

**Invention to test.** Compare the current representation with one that exposes the relevant structure directly. Observe search, cross-referencing, rule violations, reconstruction, backtracking, and correct inference. For tools shared by humans and AI agents, evaluate whether the artifact supports each actor’s work; do not assume human memory models describe an agent’s context handling.

## 7. Learning: fluency is a design outcome

Kurtenbach and Buxton (1994) offer a concrete example of an interaction grammar linking visible guidance with remembered marking gestures. Their two-user field case shows movement between the two forms of use. It supports studying command-specific expertise and transitions; it does not establish a universal speed benefit or a universal novice-to-expert schedule. [Marking-menu study](https://doi.org/10.1145/191666.191759).

Heathcote et al. (2000) challenge treating the power law as a universal learning function. Their examined individual series generally favored exponential/APEX alternatives, while averaging could favor an apparent power curve. This is a reason to inspect individual trajectories and competing explanations, not to replace one universal learning law with another. [Practice-function analysis](https://doi.org/10.3758/BF03212979).

**Design consequence.** A novel interaction may have an initial cost and a later advantage, or may remain difficult. Both are consequential. Familiarity is evidence relevant to adoption and transfer, not an automatic veto on invention.

**Invention to test.** Let visible assistance teach the same stable action that can later become fluent. Measure first use, repeated use, errors, help invocation, return after nonuse, and transfer. Preserve individual trajectories and infrequent-command performance. Do not judge a fluent interaction only at first exposure, or excuse persistent failure with an assumed future learning curve.

## 8. Interruption: design the return

Trafton et al. (2003) manipulated preparation opportunity before interruption in a resource-allocation task. Preparation facilitated resumption, and immediate-interruption participants also improved with practice. The intervention was an eight-second preparation interval, not a written checkpoint. Their discussion identifies environmental-cue effects as requiring direct testing. [Interruption preparation](https://doi.org/10.1016/S1071-5819(03)00023-5).

**Design consequence.** Treat suspension and resumption as part of the interaction. A long-running operation, detour, or handoff has a return cost beyond the visible wait.

**Invention to test.** Prototype preserving the pending intention, current state, and next action as distinct interventions. Measure correct first action, resumption lag, duplicated or omitted work, and the cost of creating and inspecting the aid. Human–agent handoff is a useful application to test; this experiment did not validate agent checkpoints.

## 9. Specialist anchors

Wolfe and Horowitz (2017) synthesize five influences on visual-search guidance: salience, target features, scene structure, history, and value. This qualifies advice that simply increasing prominence makes an element easier to find. Route the review into Muriel’s vision/critique guidance; it is not a predictive interface-findability formula. Test target-present and target-absent accuracy, search time, distractors, and experience. [Visual search](https://doi.org/10.1038/s41562-017-0058).

Guiard (1987) proposes differentiated roles, reference frames, and scales in skilled bimanual action. It is useful for canvas, musical, spatial, or embodied controls, but does not establish a universal left-hand/coarse, right-hand/fine prescription. Explore complementary context-setting and fine-action controls, then evaluate coordination, accuracy, training, fatigue, and workable alternatives for the intended users. [Bimanual action](https://doi.org/10.1080/00222895.1987.10735426).

## Scrutinizer and active visual sampling

The [deep companion review](scrutinizer-perception-review.md) adds 21 selected sources, including the Wolfe and Horowitz review already cited here. Its central design question is how an interaction helps someone choose where to inspect and makes useful information available through that inspection. It connects crowding and peripheral representations to task-guided search, information foraging, reading, and restricted-viewing methods.

This strengthens the bridge to Gray: an interface changes both the expected value of consulting a location and the cost of reaching and interpreting it. Stable overviews, local references, grouped dense canvases, and peripheral event cues become concrete alternatives to test. The connection supports invention without treating a rendering or model score as evidence of human task benefit.

Scrutinizer's source and existing artifacts also expose important boundaries. Pointer-controlled focus measures controlled information access rather than gaze; default capture and desktop radii differ; the clear radius also participates in the modeled eccentricity scale. Historical clutter comparisons vary with configuration, and a chromatic fixture has incorrect published-data provenance. The companion records those findings and proposed corrections to Muriel's critique guidance. It does not apply implementation fixes or rerun model validation.

## What this should change in Muriel

These are proposed follow-up edits, not changes enacted by this review.

1. **Add a compact model-selection reference.** Route a concrete design question to a model, its assumptions, and a probe. Keep the main skill focused on producing working artifacts.
2. **Add choice/acquisition and procedure references.** Keep Hick with its contemporary criticism; keep Fitts with geometry and calibration; distinguish KLM from CPM-GOMS. Reuse the existing Gray intake rather than duplicating it.
3. **Add a representations reference.** Pair Larkin/Simon and Zhang/Norman to guide invention beyond conventional widgets. Connect it to diagrams, spatial work, and interaction design.
4. **Make learning and resumption part of evaluation.** Use observation over time when the proposed benefit depends on practice; measure return and recovery when interruption is part of the task.
5. **Add active visual sampling to design synthesis.** Use the Scrutinizer companion to connect peripheral guidance, recognition, information access, and task outcomes. Keep model diagnostics distinct from human validation and revise the critique agent's unsupported reading, dwell, and peripheral-vision rules.
6. **Repair numerical claims before presenting them as science.** The [polish channel](../plugins/muriel/skills/compose/channels/polish.md) prescribes disclosure above about seven peer choices. The [diagram channel](../plugins/muriel/skills/compose/channels/diagrams.md) and [cycle helper](../muriel/tools/diagrams/cycle.py) claim that beyond eight steps no reader can hold a loop in working memory. The selected literature does not substantiate those universal thresholds. A renderer's supported range can remain an engineering constraint without claiming a human limit. Keep hit-area floors labeled as design policy rather than Fitts-derived predictions.

Suggested reusable entry structure:

> **Decision → mechanism → scope → conventional and novel alternatives → observable prediction → evidence and limitations.**

For example, a command surface could combine stable locations, visible guidance, and a direct practiced gesture. The proposal earns its place by demonstrating successful discovery, acquisition, retention, and recovery for the intended tasks. The literature motivates that experiment; it does not certify the invented interaction in advance.

Do not optimize every task for speed. Define the intended benefit—accuracy, fluency, understanding, expressive control, or another outcome—before selecting a model. A model’s inability to quantify an outcome does not make that outcome unimportant.

## Scope, verification, and source ledger

This is a purposive foundational review, not a systematic review or a complete inventory of research through 2026. Selection followed the requested Hick/Fitts/GOMS lineage, Gray’s work, and complementary mechanisms that help invent software interactions. Searches used paper titles, author/institutional repositories, publisher records, and citation-following. Twenty-two papers were retained. DOIs, titles, authors, and publication years were checked using science-agent against Crossref; that verifies identity, not empirical claims. Reading depth is recorded below. The companion [BibTeX bibliography](interaction-models.bib) supplies publication metadata.

The review combines experiments, field studies, theoretical analyses, and research syntheses; these should not be treated as interchangeable evidence. Original Hick/Hyman and Fitts intake was limited by access. Their detailed interpretation here also uses the identified later analyses. The Scrutinizer companion extends the review into information foraging and perceptual guidance. Errors, signal detection, attention under concurrent demands, and collaborative cognition remain candidates for further scoped searches.

| Key | Primary text or publication | Intake and qualification |
|---|---|---|
| `hick1952` | [Publication](https://doi.org/10.1080/17470215208416600) | Publisher abstract and indexed first-page text; located hosted PDF returned 404. |
| `hyman1953` | [Publication](https://doi.org/10.1037/h0056940) | Indexed first-page text and bibliographic record; extensions also checked in Liu et al.; hosted PDF returned 404. |
| `cockburn2007` | [Author PDF](https://www.csse.canterbury.ac.nz/~andy/papers/paper191-cockburn.pdf) | Assumptions, calibration, evaluation, and limitations. |
| `liu2020` | [Author PDF](https://perso.telecom-paristech.fr/rioul/publis/202001liugoririoulbeaudouinlafonguiard.pdf) | Full critical review. |
| `kurtenbach1994` | [Author text](https://www.billbuxton.com/MMUserLearn.html) | Application, participant scope, traces, and learning behavior. |
| `fitts1954` | [Publication](https://doi.org/10.1037/h0055392) | Indexed original opening and publication metadata; substantive HCI application checked in the two MacKenzie papers. Located course reprint required login. |
| `mackenzie1992` | [Author text](https://www.yorku.ca/mack/hci1992.html) | Formulations, effective width, device-study synthesis, and methodological qualifications. |
| `mackenziebuxton1992` | [Author text](https://www.yorku.ca/mack/CHI92.html) | Full paper, including width alternatives, experiment, and generality limits. |
| `accot1997` | [ACM conference text](https://chi1997.acm.org/proceedings/paper/ja.html) | Model, apparatus, experimental overview, and discussion/limitations. |
| `card1980` | [Journal scan](https://frankritter.com/hcdd331/cardMN80.pdf) | Task definition, operators, validation qualifications, and limits. |
| `johnkieras1996comparison` | [Author-uploaded manuscript](https://www.researchgate.net/publication/2504882_The_GOMS_family_of_user_interface_analysis_techniques_comparison_and_contrast) | Variant definitions, learning scope, overlap, and operator estimates. Page header incorrectly says 1999; manuscript and publication are 1996. |
| `johnkieras1996using` | [Publication](https://doi.org/10.1145/235833.236050) | Indexed publisher abstract; application detail primarily supported by comparison paper and Ernestine, not a full reading of this article. |
| `gray1993` | [Journal scan](https://www.lri.fr/~mbl/ENS/FundHCI/2013/papers/Gray-HCI93.pdf) | Task fit, field-trial overview, aggregate versus category prediction, and design implications. |
| `gray2000` | [Author-uploaded manuscript](https://www.researchgate.net/publication/12113709_Milliseconds_matter_An_introduction_to_microstrategies_and_to_their_use_in_describing_and_predicting_interactive_behavior) | Controlled-task methods/discussion and separate prototype observations; prior focused intake retained. |
| `grayfu2004` | [Publisher abstract](https://onlinelibrary.wiley.com/doi/abs/10.1207/s15516709cog2803_3) | Abstract-level intake only; no detailed reanalysis of methods. |
| `gray2006` | [Author-uploaded manuscript](https://www.researchgate.net/publication/6981571_The_Soft_Constraints_Hypothesis_A_Rational_Analysis_Approach_to_Resource_Allocation_for_Interactive_Behavior) | Hypotheses, selected experimental/model discussion, limits, and conclusions; prior focused intake retained. |
| `larkinsimon1987` | [Journal scan](https://mechanism.ucsd.edu/bill/teaching/F12/cs200/Readings/larkin.whyadiagramissometimesworth.1987.pdf) | Formal distinctions, search/recognition/inference, expertise, and conclusion; selected examples. Printed pages end at 99; Crossref/publisher say 100, so bibliography omits pages. |
| `zhangnorman1994` | [Author manuscript](https://worrydream.com/refs/Zhang_2004_-_Representations_in_Distributed_Cognitive_Tasks.pdf) | Framework, representational analysis, and general discussion; not all methods/results. Filename says 2004; article is 1994. Author text corrects Crossref’s “Jiaje” to Jiajie. |
| `heathcote2000` | [Preprint](https://users.cs.northwestern.edu/~paritosh/papers/KIP/power-law-repealed.pdf) | Publisher abstract, preprint framing, individual functions, averaging, and competing fits. |
| `trafton2003` | [Author PDF](https://gregtrafton.com/papers/preparing.to.resume.pdf) | Methods, preparation coding, resumption, practice qualification, and discussion. |
| `wolfehorowitz2017` | [Author PDF](https://search.bwh.harvard.edu/new/pubs/FiveFactors_Wolfe-Horowitz_2017.pdf) | Review abstract, efficiency definition, and selected history/scene/value sections. |
| `guiard1987` | [Author-linked article](https://www.lri.fr/~mbl/ENS/FONDIHM/2013/papers/Guiard-JMB87.pdf) | Slightly edited author version: model overview, scale contrast, and precedence. |
