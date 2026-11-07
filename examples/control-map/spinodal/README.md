# Spinodal control map, staging 7d95b56 (2026-11-07)

First run of `muriel control-map` on a real product. `harvest-control-map.mjs`
serves a Spinodal build, boots with `?warm=1&tour=0`, and records every visible
control in `#ui` (skipping `.sr-only`, ids scoped by panel) in these states:
rest, revealed, revealed mid-beat, then each revealed control activated once.
It is Spinodal-specific (boot hooks, reveal tap); copy the shape, not the file.

```bash
node harvest-control-map.mjs <dist> <out> 390x844,touch 1470x956,mouse
python -m muriel control-map map-1470x956.json
```

| Viewport | States | Controls | Homes | Result |
|---|---|---|---|---|
| 390 × 844 touch | 11 | 25 | 22 | PASS |
| 1470 × 956 mouse | 23 | 43 | 38 | FAIL: the Room panel's 5 controls have 2 homes, 990 px apart |

On desktop the Room panel opens under the Mic mode segment (left) or under the
Room rail button (right), depending on which one was pressed
(`desktop-after-mic.png`, `desktop-after-room.png`). On the phone each panel
opens on the side opposite its button (`phone-after-mic.png`,
`phone-after-lamp.png`); the census does not see that, because each control
still has one home.
