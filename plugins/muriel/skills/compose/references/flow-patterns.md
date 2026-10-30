# Flow patterns — known sequence failures and their fixes

Failures that only show across two or more states of a flow, each with what to
look for, the fix, its basis, and how well it is established. Used by the
[Walker](jury.md#the-roster) as a second pass after its walk, and by anyone
auditing a flow against [continuity across states](interaction-contracts.md#continuity-across-states).

For single-state conventions (focus rings, loading buttons, error wording),
query the corpus that ships with muriel:

```sh
python -m muriel uipromax guidelines --query "<term>"
```

Muriel's rules override corpus rows. Row 31, for example, dims disabled
controls with opacity, which breaks the 8:1 text floor.

## Status

- **standard** — a published guideline or specification says it.
- **rule** — a muriel rule, not yet seen in a sitting.
- **candidate** — seen once in a sitting or user report; the fix is not yet
  confirmed.
- **confirmed** — seen, fixed, and the fix verified in a later capture.

**How the list changes.** The chair edits it, never a seat. A candidate becomes
confirmed when the ledger records its finding as `hit` (fixed, and the
re-render shows it gone). A candidate whose findings are struck as `noise` in
two sittings is removed. A new candidate needs a finding with frame and
manifest evidence. Note the date and sitting for every change.

**Is the pass earning its place?** Ballots tag each finding `source: walk` or
`source: pattern`. If several sittings go by with the pattern pass adding
nothing the walk did not already find, cut it.

## Patterns

### P1 Moving target

- **Across frames:** the next action sits somewhere new in each state.
- **Fix:** one action area for the goal, stable across idle, working, ready,
  failure, and return. If a target must move, the move should carry meaning.
- **Basis:** muriel continuity rules.
- **Status:** confirmed. User report, 2026-10-29 (Protoplasm export). The fix
  was verified in the 2026-10-29 Walker sitting: one slot, 0 px shift across
  10 frames.

### P2 Relabel under the finger

- **Across frames:** one button changes to a different or opposite action in
  place (Record → Cancel, Cancel → Download), with nothing to absorb a tap
  aimed at the old label. Focus may jump onto the new action.
- **Fix:** ignore activation for a short window after any relabel, whether the
  system or the person caused it, and move focus only after that window. Do
  not let a completion that lands between pointer-down and pointer-up trigger
  the new action.
- **Basis:** WCAG 2.2 SC 2.5.2 Pointer Cancellation asks that activation
  complete on the up-event so a person can abort. A relabel between down and up
  defeats that, because the change cannot be seen in time (muriel's
  application). uipromax row 32: no repeated activation while processing.
- **Status:** candidate. 2026-10-29 export sitting, W1 and W4.

### P3 One indicator, two quantities

- **Across frames:** the same bar or number reports one thing in one state
  (playback position) and another in the next (job progress).
- **Fix:** one indicator per quantity, each labelled. A control that seeks is
  not an indicator that reports work.
- **Basis:** Apple Human Interface Guidelines, Progress indicators, which
  treats them as reporting a task's progress (determinate when its extent is
  known). Reading that as "one indicator per quantity" is muriel's application,
  not Apple's wording.
- **Status:** confirmed. User report, 2026-10-29. The fix (two labelled bars)
  was verified in the 2026-10-29 sitting.

### P4 Relayed handoff

- **Across frames:** the person must press a button for a stage that nothing
  about their intent decides (Prepare, Process, Continue).
- **Fix:** run the stage automatically. Keep a review step only if it protects
  a real choice, and if it is a product question, send it to a split.
- **Basis:** cognitive walkthrough question 1 (Wharton et al., 1994): would the
  person be trying to achieve this effect at all?
- **Status:** confirmed. User report, 2026-10-29. Automatic preparation was
  verified in the 2026-10-29 sitting.

### P5 Stale result offered as current

- **Across frames:** the settings change while work runs, and the result for
  the old settings becomes the current download or replaces the ready action.
- **Fix:** tag each result with the revision that produced it. Only the current
  revision becomes the result; late or cancelled work is discarded.
- **Basis:** muriel continuity rules.
- **Status:** rule.

### P6 Focus lost on relabel

- **Across frames:** the focused control is hidden or replaced, and focus falls
  to the page body although the next action is in the same place.
- **Fix:** move focus to the control that now occupies the slot (after the P2
  window).
- **Basis:** WCAG 2.2 SC 2.4.3 Focus Order.
- **Status:** candidate. 2026-10-29 export sitting, W8.

### P7 Raw system text in the status line

- **Across frames:** an exception name or error object appears as the status
  ("AbortError: Cancelled"), often after a step that succeeded.
- **Fix:** map known errors to plain language, and keep background cancellations
  out of the visible status. When the status line is a live region, the raw
  text is also announced.
- **Basis:** uipromax row 33 (clear error messages); WCAG 2.2 SC 4.1.3 Status
  Messages for how the line is announced.
- **Status:** candidate. 2026-10-29 export sitting, W5.

### P8 Output differs from the chosen moment

- **Across frames:** the person framed or chose something, but the delivered
  output starts, crops, or ends somewhere else (a loop excerpt that starts
  seconds after the held moment).
- **Fix:** honor the choice, or say plainly before commit what the output keeps.
  Check the delivered file, not only the preview.
- **Basis:** the Preview pattern in Tidwell's *Designing Interfaces* (show the
  result before committing); task correctness as a separate success criterion
  ([task analysis](task-analysis.md#frame-the-activity)).
- **Status:** candidate. 2026-10-29 export sitting, W3.

### P9 Placeholder reads as another control

- **Across frames:** an empty or disabled control sits where a different
  control's label leads the eye (a playback slider under a "Focus" heading
  because a sticky footer covers the real slider), or its label changes while
  it stays empty.
- **Fix:** hide controls that have nothing to act on, and keep sticky regions
  from covering the content above them.
- **Basis:** muriel continuity rules.
- **Status:** candidate. 2026-10-29 export sitting, W9.

### P10 Cancel loses the work

- **Across frames:** cancelling a long step discards what came before it (the
  take, the entered data), or leaves no route forward.
- **Fix:** cancel stops only the running step; keep the work and offer the step
  again.
- **Basis:** the Cancelability pattern in Tidwell's *Designing Interfaces*;
  muriel's "protect the user's work".
- **Status:** standard. The fix held in the 2026-10-29 sitting: "Cancelled.
  Your scene is still here."

### P11 Ready is not delivered

- **Across frames:** the journey ends at "ready" or "download started", with no
  evidence of the output where the person will look for it.
- **Fix:** check the output at its destination, and tell the person where it
  went.
- **Basis:** muriel continuity rules.
- **Status:** rule. In the 2026-10-29 sitting, W10 recorded it as a journey
  limit.

### P12 Choice offered after the expensive step

- **Across frames:** an option that changes the output appears only after the
  output has been built, so choosing it repeats the work and opens a
  cancel-and-retry branch.
- **Fix:** offer the choice before the work starts, or build the alternatives
  together when it is cheap.
- **Basis:** [task analysis](task-analysis.md#model-goals-and-methods): put the
  deciding information where the choice happens.
- **Status:** candidate. 2026-10-29 export sitting, W7.

## Sources

- W3C (2023). *Web Content Accessibility Guidelines (WCAG) 2.2*. Success
  criteria 2.4.3, 2.5.2, 4.1.3. https://www.w3.org/TR/WCAG22/
- Apple. *Human Interface Guidelines: Progress indicators*.
  https://developer.apple.com/design/human-interface-guidelines/progress-indicators
- Tidwell, J., Brewer, C., and Valencia, A. (2020). *Designing Interfaces*
  (3rd ed.). O'Reilly. Patterns: Preview, Cancelability.
- Wharton, C., Rieman, J., Lewis, C., and Polson, P. (1994). The cognitive
  walkthrough method: A practitioner's guide. In *Usability Inspection
  Methods*. Wiley.
- `muriel.uipromax` ux-guidelines, rows 31–33 (MIT, ui-ux-pro-max-skill).
