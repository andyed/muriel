# Channel front-matter schema

Each `channels/*.md` doc may carry a YAML front-matter block at the very top — between two `---` delimiter lines — that declares what the channel is, what it needs, and what it produces. The block is **optional** today; channels without it work as before. When present, `muriel.critique` reads it and applies channel-specific gates.

The schema is intentionally minimal. Add a key only when at least one tool would meaningfully consume it.

## Why

Two failure modes the schema addresses:

1. **Reinventing channel utilities.** A channel that should call `muriel.matplotlibrc_light.rcparams()` instead reaches for raw `matplotlib.rcParams[...] = ...`. The fix is to surface the channel's expected reads in machine-readable form so a critique pass can grep for the bypass.
2. **Audience-leak.** A channel that ships to an external audience (paper, blog) needs the `--audience` denylist to run. Today this is convention; the schema makes it a gate when `requires.audience: required`.

## The schema

```yaml
---
channel: <slug>            # matches the file basename
status: active             # active | partial-mvp | queued

requires:
  brand: optional          # required | optional | none
  audience: optional       # required | optional | none
  reads:                   # importable utilities the channel uses, not reinvents
    - muriel.contrast
    - muriel.dimensions

output:
  kinds: [svg, pdf]        # file types this channel produces
  registers: [paper, blog] # where artifacts are read

peer_channels:             # cross-links — sister channels, primitive layers
  - infographics
  - svg
---
```

### Field reference

| Key | Type | Required | Purpose |
|---|---|---|---|
| `channel` | string | yes | Slug, must match the filename (drop the `.md`). |
| `status` | enum | yes | One of `active` (shipped + maintained), `partial-mvp` (some primitives shipped, more queued), `queued` (doc-only roadmap). |
| `requires.brand` | enum | no | `required` → critique fails without a loaded brand. `optional` → use brand if loaded. `none` → channel does not consume brand tokens. |
| `requires.audience` | enum | no | `required` → critique fails without `--audience`. `optional` → audit if passed. `none` → no audience filter. |
| `requires.reads` | list[string] | no | Importable muriel utilities the channel must use rather than reinvent. Critique can grep the rendered code for telltale bypasses. |
| `output.kinds` | list[enum] | no | `svg`, `png`, `jpg`, `pdf`, `html`, `mp4`, `gif`, `txt`. Drives default checkers (e.g. SVG → contrast audit). |
| `output.registers` | list[enum] | no | `paper`, `blog`, `social`, `app`, `terminal`, `presentation`, `editorial`. Used to suggest the right rcparams/dimension target. |
| `peer_channels` | list[string] | no | Sibling channels — primitive layers below, composition layers above, sister channels at the same tier. |

### Status semantics

- `active` — every primitive listed in the channel doc has shipped; further work is extension, not catch-up.
- `partial-mvp` — the channel doc is the spec, some primitives have shipped, the rest are queued in `TODO.md`. The `Status` column in the channel's catalog table indicates which.
- `queued` — doc-only, no implementation yet. Roadmap surface.

### When a key is omitted

| Omitted key | Default behavior |
|---|---|
| `requires.brand` | Treated as `optional`. |
| `requires.audience` | Treated as `optional`. |
| `requires.reads` | No grep gate runs. |
| `output.kinds` | Critique applies whatever checkers the artifact's file extension implies. |
| `output.registers` | No rcparams suggestion. |
| `peer_channels` | No cross-link table generation. |

## Adoption status

Tracked in `TODO.md`. Front-matter is shipped on a subset of channels today; rolling out across the rest is queued, not blocked. Channels without front-matter remain valid; nothing breaks.

## Why YAML, not TOML

Markdown convention. Editors highlight YAML front-matter between `---` delimiters automatically. `muriel` has zero required dependencies, so the parser is a small hand-rolled subset (no PyYAML import) sufficient for this bounded schema.
