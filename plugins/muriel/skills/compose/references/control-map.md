# Control map — every control's home, in every state, before anyone judges

A control map lists every settled state an interactive UI can reach and,
for each, every control on screen with its box. It answers one question
by arithmetic: **does each control live in one place?** Run it before a
jury sits on interactive UI, and before showing the owner.

Part of the [muriel](../SKILL.md) skill. Tool:
[`muriel.control_map`](../../../../../muriel/control_map.py).

## Why it exists

On 2026-11-05 a Spinodal UI went through three jury rounds in under an
hour: Walker, Squinter, Thumbnail, Loupe, Stranger. It passed. Seventy
minutes later the owner wrote: "the big problem is that we keep spawning
buttons in different and random places… It needs a consistent and groovy
interaction." The fix that followed was literally named "the lamp map,
fixed homes for every control."

The jury did not miss it through carelessness. Each Walker sitting walks
one journey; within one journey the next action mostly stayed put. The
wandering was *across* journeys: the close button sat in one place when
the pie was open and another when a tool was held, the heat readout in
three. Round 2's Walker did see "the heat readout moves," rated it LOW,
and the chair recorded it as a split. A small move rated by eye reads as
small. A census reports it as a second home, and a second home is the
defect.

## When to build one

- Any UI with controls that appear, hide, or change with state: corner
  menus, auto-hiding chrome, tool palettes, radial menus, panels.
- Before seating a [jury](jury.md) on that UI. The census is stipulated
  fact; see [jury.md § Jurisdiction](jury.md#jurisdiction).
- Again after any change that adds a state or a control.

Skip it for a single static screen; there is nothing to compare.

## Building it

1. **Name the controls.** Put `data-control="<stable id>"` on every
   control the person operates. The id is the control's identity across
   states, so the same button gets the same id wherever it renders.
2. **List the states.** Every settled screen the person can reach: rest,
   controls awake, each panel open, each tool active, each mode, the
   music beat mid-pulse, the demo-expired notice. A state missing from
   the list is a state the census cannot see.
3. **Harvest.** Drive each state with the host's own harness and record
   every `[data-control]` box (snippet in the module docstring). One
   viewport per map; run the shipping phone viewport first.
4. **Declare intended moves.** A control meant to move — a readout that
   follows the finger, a handle that rides the rim — goes under `moves`
   with a one-line reason. The reason is what the Walker later judges.
5. **Name the subject.** Under `protected`, the region the product
   exists to show: the lamp, the canvas, the photo.

```bash
python -m muriel control-map ui-map.json        # exit 1 if anything wanders
python -m muriel control-map ui-map.json --json
```

## Reading it

| Output | Meaning | Who acts |
|---|---|---|
| **WANDERS** | An undeclared control has two or more homes. | Fix before any panel. Not a jury question. |
| **declared** | A control moves with a stated reason. | The Walker rules whether the reason holds. |
| **new position in 'state'** | That state puts a control where nothing has been. Each one is a new place the person must learn to look. | Designer: can it reuse an existing home? |
| **distinct homes** | Size of the layout's position vocabulary. Fewer is calmer; compare it between options. | Stipulated into a direction-selection sitting. |
| **covers N% of subject** | Controls over the protected region, per state. | Fact for the owner's taste call: covering the subject has to be worth it. |

Tolerance defaults to 4% of the shorter viewport side, at least 12 px
(16 px on a 390 × 844 phone). Set `tolerance` in the map to change it;
record why.

## What it does not judge

- Whether a declared move carries meaning. That is the Walker's.
- Whether covering the subject is worth it. That is the owner's call,
  helped by the coverage number; see
  [jury.md § What no seat holds](jury.md#what-no-seat-holds).
- Motion under the hand during a transition. Capture a state mid-pulse
  (a music beat, a breathing toggle) to catch a control that jumps; the
  census only sees the states it is given.
