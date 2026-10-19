# Scrutinizer and perceptual foundations for Muriel

Literature review and source audit · 11 October 2026

## Recommendation

Muriel should treat **active visual sampling** as a core design concern: what people can detect before looking directly, how they choose where to inspect, and what inspection enables them to recognize and do. Scrutinizer makes this concern tangible through interactive restrictions, visual diagnostics, and recorded exploration. It connects naturally to Gray’s account of information access costs and to the [Hick, Fitts, and GOMS review](interaction-models-review.md).

The design opportunity extends beyond removing clutter. Coarse structure can guide detailed inspection; stable dense arrangements can support comparison; a cheap local reference can change whether someone checks information at all. These mechanisms can motivate unfamiliar interaction forms. Muriel’s contribution is to turn them into working software and compare the resulting work, rather than enforce a conventional layout because a named law appears to endorse it.

Scrutinizer should enter Muriel as an **instrument for generating and inspecting hypotheses**, with claims tied to the appropriate evidence. A shader output, a model comparison, an OCR result, a pointer trace, and successful human work answer different questions. The inspected implementation and artifacts do not establish general psychophysical fidelity or usability benefit.

This is a focused review of 21 selected sources, including one already in the companion review, through 2025. It is not a systematic search or a claim to exhaustive coverage. The [bibliography](scrutinizer-perception.bib) and intake ledger below distinguish full or selected text from abstract-level intake. Recommendations here are design inferences, not outcomes established for Muriel. Only research documents changed; the implementation issues identified below remain follow-up work.

## How the anchors fit together

| Design question | Useful anchor | What must remain separate |
|---|---|---|
| What can guide the next inspection? | Peripheral vision, crowding, visual search | Detection, identification, and scene understanding |
| Why inspect this location now? | Task guidance and information foraging | Conspicuity, expected usefulness, and actual benefit |
| What does accessing information cost? | Gray; Fitts; restricted viewing | Eye movement, pointer movement, interface navigation, and interpretation |
| What method does the representation enable? | GOMS; external representations | Routine execution, discovery, and problem solving |
| What survives a change in focus? | Transsaccadic memory; external references | Human retention and software keeping pixels available |
| What does the tool measurement establish? | Model validation and study design | Implementation agreement, perceptual fit, and task performance |

These accounts interact without forming one additive formula. A pointer-controlled aperture changes motor costs as well as visual availability. A persistent reference changes access costs as well as memory demands. A novel grouping can change search guidance and the procedure a person adopts. Analyze those changes before assigning an improvement to a single mechanism.

## Crowding concerns recognition in context

Bouma’s letter-recognition experiments established an important distinction: a peripheral target that is recognizable alone can become difficult to identify with nearby flankers. Critical spacing grows with eccentricity in the tested conditions. The familiar fraction of eccentricity is a useful starting hypothesis, not a universal spacing constant for buttons, dashboards, or arbitrary objects. Pelli and Tillman organize evidence around an uncrowded recognition window and discuss qualifications to its generality. Detecting that something is present does not establish that its identity is available. [Bouma](https://doi.org/10.1038/226177a0), [Pelli and Tillman](https://doi.org/10.1038/nn.2187).

For Muriel, the actionable question is often **which distinctions must be available before direct inspection**. A toolbar can be discoverable as a region without every icon being identifiable from the current fixation. Conversely, a warning whose category must be recognized immediately needs more than a detectable colored patch. Evaluate the required capability, position, target–flanker arrangement, and similarity. Increasing whitespace everywhere can sacrifice useful comparisons and increase travel; enlarging a target alone may leave interference unresolved.

Scrutinizer’s density-dependent distortion is a candidate way to expose sensitivity to local structure. It does not directly implement an empirical target–flanker critical-spacing test. Its own [simulation limitations](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/docs/simulation-limitations.md) acknowledge that the intended isolated-versus-flanked recognition asymmetry has not been demonstrated. The [Wave 7c artifact](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/tests/validation/wave7c-crowding.json) includes unreadable isolated-letter baselines in relevant modes. A distorted flanked display cannot demonstrate crowding when the baseline is already unrecognizable. Displacement magnitude and OCR accuracy also remain different outcomes from human recognition.

**Useful probe.** Compare isolated and flanked targets at matched size, contrast, and eccentricity, varying spacing and grouping separately. Then test the actual interface task. A layout that passes a restricted letter task may still fail because its category structure is misleading; a useful dense arrangement may exploit learned structure absent from the letter task.

## Summary statistics offer a model of retained information

Balas and colleagues propose that peripheral representations preserve joint image statistics while losing precise local arrangements. Rosenholtz and colleagues connect this account to visual search: human discrimination of synthesized patches containing or lacking a target predicts differences among selected search conditions. The important claim is about information available under a specified representation, not that any blur or texture replacement simulates a person’s peripheral view. The visual-search study explicitly treats human discrimination as consequential rather than substituting an arbitrary classifier. [Crowding model](https://doi.org/10.1167/9.12.13), [visual-search account](https://doi.org/10.1167/12.4.14).

Freeman and Simoncelli synthesize images from pooled nonlinear responses and test discrimination between synthesized samples. That comparison matters: it does not by itself show that an original scene is indistinguishable from its synthesis. Wallis and colleagues directly examine original-versus-synthesis comparisons and find image content consequential, challenging a general claim that fixed pooling at the proposed scale produces arbitrary scene metamers. This disagreement belongs beside the model, rather than in a footnote after declaring it biologically correct. [Ventral-stream metamers](https://doi.org/10.1038/nn.2889), [content-dependent challenge](https://doi.org/10.7554/eLife.42512).

Muriel can use this lineage to ask what coarse relationships a design preserves before detail is read. Region boundaries, repeated structure, and distinctive target features are candidates to investigate. It should not label a default Scrutinizer rendering a validated Texture Tiling Model implementation, or call an output a human metamer solely because it looks plausible. Research modes, default modes, and the published models have different computations and evidence.

**Useful probe.** Compare a stable overview that preserves task structure with one that removes all nonfocused detail. Observe which region people choose next, what they infer before inspection, and whether they recover when the initial cue is wrong. If claiming perceptual equivalence, use an appropriate original-versus-rendered human discrimination task under controlled viewing. Task usefulness and perceptual equivalence are separate possible claims.

## Peripheral color depends on the stimulus and the task

Mullen and Kingdom report different eccentricity dependencies for red–green and blue–yellow cone-opponent sensitivity under controlled stimulus conditions. Hansen and colleagues demonstrate substantial peripheral color capability with appropriately sized stimuli and distinguish detection, identification, and discrimination. Together they reject a simple story that peripheral color merely disappears at a fixed angle. Size, spatial frequency, luminance contrast, and the required judgment matter. [Mullen and Kingdom](https://doi.org/10.1017/S0952523802191103), [Hansen and colleagues](https://doi.org/10.1167/9.4.26).

castleCSF models contrast detection jointly across color, area, spatiotemporal frequency, luminance, and eccentricity using consolidated datasets. This is a stronger basis for specifying conditions than one universal falloff curve, but it predicts detection of specified stimuli, not arbitrary interface comprehension or suprathreshold appearance. Bowers and colleagues’ far-peripheral threshold measurements reveal consequential extrapolation problems and retained sensitivity for large, low-frequency chromatic stimuli. Those measurements do not directly validate how saturated interface objects should look in a rendering. [castleCSF](https://doi.org/10.1167/jov.24.4.5), [far-peripheral measurements](https://doi.org/10.1167/jov.25.11.7).

For Muriel, a peripheral event can ask at least three different things: notice an event, identify its category, or discriminate two states. A large colored field could help the first while a small hue-only difference fails the third. The design should carry the distinction through its feedback and evaluation. Preserving redundant shape, position, or text cues can be useful, but these papers do not supply a universal recipe for their arrangement.

**Useful probe.** Vary size, luminance contrast, and fixation location while holding the event meaning constant. Measure detection and correct interpretation separately. Compare a localized peripheral cue with moving focus or opening a modal interruption; include the cost of disrupting the current task. Do not declare peripheral decoration inherently invisible or recommend centering all meaningful controls.

## Attention follows tasks as well as conspicuity

Itti, Koch, and Niebur’s model combines multiscale visual features to select conspicuous locations and explicitly omits top-down task control. A computed saliency map can therefore reveal a competition among visual features without predicting a particular user’s complete search. Wolfe and Horowitz describe guidance from salience, target features, scene structure, history, and value. Tatler and colleagues develop the importance of goals, learned expectations, and action in natural vision. [Saliency model](https://doi.org/10.1109/34.730558), [five guidance factors](https://doi.org/10.1038/s41562-017-0058), [natural vision](https://doi.org/10.1167/11.5.5).

Muriel should ask what the person is seeking and what they already know before interpreting a bright region as a problem. A visually quiet familiar location can be easy to find; an emphatic unfamiliar symbol can attract attention without communicating an action. Saliency and relevance are neither interchangeable nor a moral division between where eyes might and should go. Likewise, an F- or Z-shaped scanpath is not a general program that users execute on every composition.

**Useful probe.** Keep the page constant and vary the task; then keep the task constant and vary the visual treatment. Compare successful finding, wrong selections, target-absent decisions, and repeated use. A saliency-map difference can motivate that comparison. It cannot establish that an interface “fights the task” without observing the task.

## Information foraging connects guidance to access costs

Pirolli and Card analyze how people seek valuable information relative to access and processing costs, including information patches and cues to likely value. Fu and Pirolli’s SNIF-ACT applies a cognitive account to web navigation, predicting link choices and backtracking under specified tasks. Its stated limits include visual-layout insensitivity and the fact that it is not an eye-movement model. Information scent concerns the relation between a cue and the user’s goal; it is not a synonym for visual prominence or proof that every user navigates optimally. [Information foraging](https://doi.org/10.1037/0033-295X.106.4.643), [SNIF-ACT](https://doi.org/10.1080/07370020701638806).

This supplies a productive bridge to [Gray’s microstrategies](../plugins/muriel/skills/compose/references/microstrategies.md). A design changes both the expected value of inspecting somewhere and the work required to do it. A good preview can direct inspection; a cheap reference can make checking worthwhile; a stable location can support repeated access. Novel interaction grammar is justified when it changes these relations usefully, rather than merely reducing the number of visible controls.

**Useful probe.** Compare meaningful previews with decorative thumbnails, and local access with reopening a remote panel. Observe which cues people follow, whether they consult the source, and whether consultation improves decisions. Include misleading-cue cases. Faster navigation that leads to poorer evidence is not a task improvement.

## Restricted viewing is an intervention and an observable

Jansen, Blackwell, and Marriott introduced the Restricted Focus Viewer as a tool for tracking controlled access to visual material. Their experiments preserved selected high-level patterns while restricted access slowed work. Bednarik and Tukiainen compared pointer-controlled restrictions with simultaneous eye tracking in program comprehension: access switching and gaze switching differed, and restriction affected aspects of strategy even when task outcomes were similar. These studies support a useful complementary method, with task-dependent validity, rather than equating the pointer with the eyes. [RFV](https://doi.org/10.3758/BF03195497), [eye-tracking validation](https://doi.org/10.3758/BF03193158).

Scrutinizer’s pointer-controlled focus gives a record of **information the interface made available through the controller**. It does not directly record eye position, covert attention, recognition, or understanding. The manipulation also adds pointer movement and access coordination. Fitts and Gray are therefore relevant to interpreting its traces, not just to designing the underlying page. Similar completion times across conditions would not establish identical perceptual strategies.

The inspected [practitioner guide](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/docs/tutorials/usability-testing-practitioner-guide.md) and the Study Workbench guide make useful methodological distinctions: conditions need signatures, empty or corrupt captures need exclusion, and **Done is a task-end trigger rather than success**. Capture and replay support procedural inspection. Packaged-release capture readiness is separate from source-build capability and remained unverified here. The Study Workbench guide is in `scrutinizer-moderator`, which is not public.

**Useful probe.** Establish ordinary-viewing task behavior, then use a restricted condition to investigate a specific access hypothesis. Define success independently from the recording controls. Keep controller, aperture, rendering mode, memory behavior, and training explicit. If claiming correspondence with gaze, collect gaze evidence for the relevant task rather than inheriting validity from another RFV study.

## Reading and memory need their own interpretations

Rayner’s reading review describes eye movements with units and conditions that matter. A commonly reported English-reading saccade is about seven to nine **letter spaces**, not three to four words. Reading behavior also depends on text, reader, and task. E-Z Reader relates lexical processing to eye-movement control; a brief description of parafoveal preview does not derive universal label lengths, line breaks, or a rule that longer dwell proves more understanding. [Reading review](https://doi.org/10.1037/0033-2909.124.3.372), [E-Z Reader](https://doi.org/10.1037/0033-295X.105.1.125).

Irwin’s experiments distinguish limited information retained across saccades from a detailed, position-perfect visual buffer. That is a reason to separate retention from a program preserving clear screen regions. Scrutinizer’s Visual Memory can be a useful external-access manipulation: previously visited regions remain available. Its count of regions and retained radius are implementation parameters, not a demonstrated human capacity or a transsaccadic memory model. [Information integration](https://doi.org/10.1016/0010-0285(91)90015-G), [Visual Memory implementation](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/renderer/visual-memory.js#L182).

For Muriel, persistent references, pinned intermediate results, and visible work history should be evaluated as external representations. Compare revisits, reconstruction, correct decisions, and the cost of maintaining the reference. Dwell can indicate inspection, difficulty, distraction, or other processes; interpreting it requires the task and an independent outcome.

## What the current Scrutinizer evidence establishes

The source snapshot is `scrutinizer2025` at `bc68944`, read on 11 October 2026. The marketing and Study Workbench repositories supplied product and procedure context. No application session, model benchmark, or human study was rerun for this review.

| Evidence level | Appropriate check | What it cannot establish alone |
|---|---|---|
| Implementation correctness | Specified inputs produce expected outputs; units and parameter paths agree | Fidelity to human perception |
| Reference implementation agreement | Independent implementations compared on the same inputs and settings | Human recognition or useful software |
| Psychophysical fit | Relevant human thresholds or discrimination under calibrated conditions | General task benefit |
| Task performance | People successfully perform intended work, with suitable comparisons | Universal benefit across tasks, devices, or expertise |
| Generalization | Relevant variation in people, stimuli, devices, practice, and context | An unlimited design law |

### Clutter comparisons support a qualified diagnostic

The [congestion core](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/renderer/congestion-core.js#L7) documents an approximation using Oklab, local variances, and a single Gaussian scale. This differs from the original Feature Congestion computation. Its score combines per-map normalized summaries with software weights and thresholds. Rosenholtz, Li, and Nakano evaluate clutter measures against search; that supports investigating visual competition, not interpreting a product score as a percentage of human confusion. [Measuring visual clutter](https://doi.org/10.1167/7.2.17).

Two existing local comparison reports put the README’s headline correlation in context:

| Historical artifact | Configuration label | Images | Spearman rank correlation | Mean map SSIM |
|---|---|---:|---:|---:|
| 3 March 2026 (`tests/validation/results-768-fixed-sigma/comparison_report.json`) | 768-pixel maximum dimension, fixed sigma | 10 | 0.9273 | 0.5175 |
| 24 March 2026 (`tests/validation/results/comparison_report.json`) | Full-resolution report | 10 | 0.7212 | 0.5984 |

These are read artifacts, not reproduced results. They show configuration-sensitive rankings against a Python reference on a small image corpus; the configurations do not isolate a single causal difference. Rank agreement is also distinct from spatial heatmap agreement. The files are local ignored outputs, so the table preserves the inspected values even if they do not accompany a checkout.

The [CLI analyzer](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/cli/lib/analyzer.js#L94) scales sigma with effective image dimension, while the [renderer worker](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/renderer/congestion-worker.js#L130) fixes it at 2.5. Sharing helper functions therefore does not establish pipeline parity. A score change after resizing, capture changes, or a port needs a reproduced baseline before being interpreted as a design improvement. The score’s 25/50/75 boundaries and `--fail-above` gates remain project policy, not human thresholds.

### The chromatic fixture has a specific provenance problem

The [Mullen and Kingdom fixture](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/tests/validation/published-data/mullen_kingdom2002_rg_by.json#L3) labels its data as Figure 4 sensitivity ratios over eccentricity, specifies 0.5 cycles per degree, and includes 30°. In the [author PDF](https://mvr.mcgill.ca/Fred/Papers/Mullen%26Kingdom_2002.pdf), Figure 4 concerns cone-opponent purity versus cone count; the reported methods span 0–25°, and the relevant peak chromatic measurements use 0.3 cycles per degree. The fixture is invalid **as labeled**. This comparison does not individually disprove every number in it, but a validator consuming it cannot treat that labeling as reliable published-data provenance.

The [color report](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/tests/validation/reports/color-search-report.md) already records removal of unsupported Hansen naming-accuracy checks and a rendered/model agreement failure. Those qualifications should accompany any pass counts. The [system paper](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/docs/arxiv-paper/scrutinizer-system-paper.tex#L146) also describes Bowers measurements as suprathreshold, although the cited study and local data concern thresholds. Correct citation metadata is necessary but cannot validate an empirical claim or extracted dataset.

### Calibration and defaults can change the interpretation

The desktop [default configuration](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/renderer/config.js#L14) uses a 45-CSS-pixel foveal radius, whereas the [MCP capture path](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/cli/mcp/server.js#L121) defaults to 180. Neither is a universal visual angle. The [shader](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/renderer/shaders/peripheral.frag#L520) derives pixels per degree from the foveal radius. Changing that radius can therefore change both the clear region and the modeled eccentricity scale. It is not a pure window-size manipulation.

A meaningful comparison records physical display geometry, viewing distance, CSS/device pixel relationships, viewport, zoom, fixation/controller location, mode, radius, aspect ratio, and memory settings. Keep physical calibration and an adjustable comfort radius distinct in the interpretation. Biological names such as LGN, V1, and V4 can organize engineering analogies; component names do not establish neural localization or causal adequacy.

## Design experiments this opens for Muriel

These are proposed mechanisms to build and test, not prescriptions derived from a single paper. Scrutinizer can help expose their assumptions and compare access patterns; ordinary human task performance decides their practical value.

| Candidate interaction | Proposed benefit | Comparison and evidence that could reject it |
|---|---|---|
| Stable overview with local detail | Coarse structure guides the next inspection without losing context | Compare blanket hiding and ordinary viewing. Reject if region choices become less accurate or detail recovery costs dominate. |
| Dense grouped canvas | Preserve useful comparisons while differentiating task-relevant groups | Compare spacing, grouping, and target similarity separately. Reject if errors persist or novices cannot discover the organization. |
| Reference attached to the point of work | Make verification cheap enough to use | Compare reopening a separate panel. Reject if consultation does not increase, decisions do not improve, or the reference obstructs work. |
| Peripheral event cue with local explanation | Permit noticing without immediately taking over focus | Compare a modal interruption. Reject if events go unnoticed, categories are confused, or interruptions increase anyway. |
| Visible path into a practiced direct action | Let guidance teach a stable gesture or command grammar | Compare conventional controls across practice and return after nonuse. Reject if learning costs persist or recovery is poor. |
| Shared human–agent work artifact | Preserve state, evidence, and next actions for both actors | Evaluate human interpretation and agent retrieval separately. Reject if either actor loses provenance or reconstructs incompatible state. |

The last two connect back to learning, external representations, and resumption in the first review. Human peripheral limits do not describe an agent’s context handling. A shared artifact can serve both while providing different access paths: inspectable spatial organization for a person, explicit structure and provenance for an agent.

For a concrete comparison, write down the task, the unknown mechanism, the intervention, and the independent outcome first. Use the ordinary interface as a baseline and add restricted viewing only where it resolves the question. Preserve individual traces and condition signatures; distinguish failure to notice, failure to identify, misunderstanding, and a deliberate choice not to act. Measure first use and practiced use when the proposed benefit depends on learning. Select sample sizes from the intended inference and variability rather than prescribing a universal participant count.

For captures and model comparisons, record source revision, source content, viewport/zoom, rendering mode, explicit radius, controller/fixation coordinates, memory state, and analysis settings. Reproduce an existing number on its existing inputs before producing a new comparison. The [CLI documentation](https://github.com/andyed/scrutinizer2025/blob/bc68944a48c2a2c442ed9cc4fefb029b51942656/cli/README.md) distinguishes browser scoring from Electron shader capture; substituting one for the other changes what was measured.

## Proposed integration into Muriel

Keep the main skill centered on producing working artifacts. Add a compact active-vision reference that routes dense or spatial interfaces to crowding, summary statistics, task guidance, and information access. Pair each mechanism with a design question, a boundary, and a probe. Route Scrutinizer into visual inspection when its manipulation or measurement answers that question; do not make its numeric score a mandatory universal gate.

The existing [critique agent](../plugins/muriel/agents/muriel-critique.md) needs a separate revision before its scientific rules are treated as dependable:

| Current guidance | Recommended correction |
|---|---|
| Three to four words per saccade | Correct the units and scope; do not derive a universal chart-label line-break rule. |
| Longer dwell establishes more processing | Treat dwell as a trace requiring task context and independent outcomes. |
| F/Z patterns prescribe universal layouts | Treat scanpath patterns as conditional observations; inspect task, content, and experience. |
| Primary controls should sit within five degrees of fixation | Evaluate intended inspection sequences and actual display geometry; users move their eyes and controls need not all occupy one region. |
| Peripheral decoration is literally dim | Specify chromatic/luminance channel, size, frequency, eccentricity, and required judgment. |
| A named framework is required to establish a critique | Lead with the observed symptom and user consequence; use a framework when it supplies a defensible explanation. |
| Fisheye geometry makes cortical magnification explicit | Label the relationship as a design analogy and test its benefits and distortions. |

These are recommendations, not edits applied by this review. The strongest intake is a way of working: make an interaction’s assumptions visible, preserve the distinctions the science depends on, and let an inventive mechanism earn confidence through appropriate evidence.

## Source intake ledger

DOI metadata for all 21 entries was checked against Crossref with science-agent. Metadata verification confirms bibliographic identity; the reading depth below determines the scope of the substantive appraisal. Abstract-only entries do not receive a full methodological endorsement.

| Source and bibliography key | Primary text consulted | Intake depth |
|---|---|---|
| Bouma 1970 · `bouma1970` | [Publisher](https://doi.org/10.1038/226177a0) | Preview/metadata; interpretation cross-checked against Pelli and Tillman. |
| Pelli and Tillman 2008 · `pelli2008` | [Author full text and supplement](https://denispelli.com/pubs/pelli2008uncrowded-complete.pdf) | Full paper and relevant supplementary discussion. |
| Balas et al. 2009 · `balas2009` | [Primary article](https://doi.org/10.1167/9.12.13) | Abstract, indexed explanatory sections and appendix; full retrieval restricted. |
| Rosenholtz et al. 2012 · `rosenholtz2012` | [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC4032502/) | Full methods, selected results, model and limits. |
| Freeman and Simoncelli 2011 · `freeman2011` | [Author manuscript](https://www.cns.nyu.edu/pub/eero/freeman10-preprint.pdf) | Full text, including the discrimination comparison. |
| Wallis et al. 2019 · `wallis2019` | [Primary article](https://elifesciences.org/articles/42512) | Indexed abstract, results, figures, discussion and appendix; direct opening restricted. |
| Jansen et al. 2003 · `jansen2003` | [Publisher full text](https://link.springer.com/content/pdf/10.3758/BF03195497.pdf) | Full paper, experiments and methodological qualifications. |
| Bednarik and Tukiainen 2007 · `bednarik2007` | [Author full text](https://cs.uef.fi/pages/int/pub/bednarik07e.pdf) | Full methods, comparisons and limitations. |
| Rosenholtz et al. 2007 · `rosenholtz2007` | [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/18217832/) | Abstract; full retrieval failed. No detailed methods appraisal. |
| Mullen and Kingdom 2002 · `mullen2002` | [Author full text](https://mvr.mcgill.ca/Fred/Papers/Mullen%26Kingdom_2002.pdf) | Abstract, methods, scaling, relevant results and Figures 2–4. |
| Hansen et al. 2009 · `hansen2009` | [Author full text](https://www.allpsych.uni-giessen.de/hansen/publications/HansenPracejusGegenfurtner2009JVision.pdf) | Methods, detection/identification/discrimination results, Figures 2–6 and discussion. |
| Ashraf et al. 2024 · `ashraf2024` | [Author full text](https://www.cl.cam.ac.uk/research/rainbow/projects/castleCSF/castleCSF_2024.pdf) | Introduction, selected formulation and area effects, conclusions and gaps. |
| Bowers et al. 2025 · `bowers2025` | [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12439501/) | Indexed Experiment 1, model comparison and limitations; direct access intermittent. |
| Itti et al. 1998 · `itti1998` | [Journal PDF](https://hasler.ece.gatech.edu/Courses/MachineLearning/FoundationalPapers/Itti_Koch_Neiber1998.pdf) | Abstract, model, feature normalization and task-guidance scope. |
| Wolfe and Horowitz 2017 · `wolfe2017` | [Author full text](https://search.bwh.harvard.edu/new/pubs/FiveFactors_Wolfe-Horowitz_2017.pdf) | Abstract, measuring guidance and selected scene/history/value sections. |
| Tatler et al. 2011 · `tatler2011` | [Primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3134223/) | Introduction, task-related action, uncertainty/reward and conclusions. |
| Reichle et al. 1998 · `reichle1998` | [Primary abstract](https://pubmed.ncbi.nlm.nih.gov/9450374/) | Abstract and indexed opening; full original retrieval failed. |
| Rayner 1998 · `rayner1998` | [Primary record](https://pubmed.ncbi.nlm.nih.gov/9849112/), [indexed original scan](https://andrewd.ces.clemson.edu/courses/cpsc881/papers/reading/Ray98_readingSurvey.pdf) | Abstract and indexed original sections including saccade units; direct full retrieval failed. |
| Pirolli and Card 1999 · `pirolli1999` | [Author-provided manuscript](https://www.researchgate.net/profile/Stuart-Card-2/publication/229101074_Information_Foraging/links/09e41508383bc5a245000000/Information-Foraging.pdf) | Introduction and selected model discussion. |
| Fu and Pirolli 2007 · `fu2007` | [Author manuscript](https://www.peterpirolli.com/Professional/About_Me_files/FuPirolli%20HCI%20SNIF-ACT%20%28final%29.pdf) | Abstract, model introduction, application and limitations. |
| Irwin 1991 · `irwin1991` | [Publisher abstract](https://www.sciencedirect.com/science/article/pii/001002859190015G) | Indexed abstract; no full methods appraisal. |
