# muriel across AI agent harnesses

Plan for shipping muriel as a skill on every major AI coding harness, not just Claude Code. Mirrors [pbakaus/impeccable](https://github.com/pbakaus/impeccable)'s eleven-harness packaging matrix — that repo has already done the discovery work and proven that a single canonical `SKILL.md` can land in every ecosystem with thin per-harness shims.

## Status today

| Harness | Status | Install path |
|---|---|---|
| Claude Code | **shipped** | `/plugin install muriel@andyed-muriel` (plugin marketplace) or `./install.sh` (dev) |
| Codex CLI | **broadcast landed, unverified** | reads `.agents/skills/muriel/` natively (symlink to canonical, in-repo) |
| Cursor / Gemini CLI / GitHub Copilot / OpenCode / Pi | **broadcast landed, unverified** | each reads `.agents/skills/muriel/` as an alternate path; native dir (`.cursor/skills/muriel/` etc.) is a P1 task |
| Kiro / Qoder / Rovo Dev / Trae | **not yet** | no convergent broadcast path; per-harness manifests in P1 |

The canonical SKILL.md at `plugins/muriel/skills/compose/SKILL.md` already uses the [Agent Skills](https://github.com/anthropics/claude-code/blob/main/docs/skills.md) format — it's portable, the question is purely packaging.

## Target matrix

Eleven harnesses, three install patterns. The `.agents/skills/` convention is the convergent broadcast directory that closes most of the gap with one symlink.

| Harness | Native dir | Reads `.agents/skills/` | Reads `.claude/skills/` |
|---|---|---|---|
| Claude Code | `.claude/skills/` | — | (self) |
| Codex CLI | `.agents/skills/` | (self) | — |
| Cursor | `.cursor/skills/` | ✓ alt | ✓ alt |
| Gemini CLI | `.gemini/skills/` | ✓ alt | — |
| GitHub Copilot | `.github/skills/` | ✓ alt | ✓ alt |
| Kiro | `.kiro/skills/` | — | — |
| OpenCode | `.opencode/skills/` | ✓ alt | ✓ alt |
| Pi | `.pi/skills/` | ✓ alt | — |
| Qoder | `.qoder/skills/` (+ `~/.qoder/skills/`) | — | — |
| Rovo Dev | `.rovodev/skills/` (+ `~/.rovodev/skills/`) | — | — |
| Trae | `.trae/skills/` / `.trae-cn/skills/` | TBD | — |

## Strategy

**One canonical source, three install paths.** The repo already has the canonical layout under `plugins/muriel/`. The goal is to make every other harness install from the same source files via either a symlink, a generator, or a thin harness-specific manifest.

```
plugins/muriel/skills/compose/   ← canonical SKILL.md + channels/ + vocabularies/ + examples/
plugins/muriel/agents/           ← muriel-critique.md
.claude-plugin/marketplace.json  ← Claude Code plugin manifest (exists)
.agents/skills/muriel  ──→ plugins/muriel/skills/compose  (P0, LANDED — symlink)
.cursor-plugin/                  ← (P1, NEW) Cursor-specific manifest
.gemini-plugin/                  ← (P1, NEW) Gemini-specific manifest
…
```

### P0 — `.agents/skills/muriel/` broadcast (landed)

The repo now ships a symlink at `.agents/skills/muriel` pointing to `plugins/muriel/skills/compose` (the canonical SKILL.md + channels/ + vocabularies/ + examples/). Git tracks it as a symlink (mode `120000`), not as a copy — one source of truth, no duplication.

```
.agents/skills/muriel  →  ../../plugins/muriel/skills/compose
```

That single path is read **natively** by Codex CLI and as an **alternate** by Cursor, Gemini CLI, GitHub Copilot, OpenCode, and Pi — six of the ten non-Claude harnesses gain a working install with zero additional packaging.

**Per-harness verification — TBD.** The symlink is in place; whether each harness actually loads muriel through it is unverified. Verification needs each harness installed and exercised once:

- [ ] **Codex CLI** — `.agents/skills/` is the native skills dir; expect zero-config pickup.
- [ ] **Cursor** — needs the `agents.skills.paths` config or equivalent to add `.agents/skills` as an alternate. Document the config snippet here once tested.
- [ ] **Gemini CLI** — same pattern; verify alternate-path config.
- [ ] **GitHub Copilot** — agent mode reads `.github/skills/` natively; verify `.agents/skills/` is also discovered (impeccable's HARNESSES.md says yes, but verify).
- [ ] **OpenCode** — verify the alternate path is picked up.
- [ ] **Pi** — verify the alternate path is picked up.

For each verified harness, add a `## Get muriel running on <harness>` recipe block below: the exact config snippet (if any), how to invoke muriel from a session, and any caveats. Until verified, treat the broadcast as best-effort.

**Critique-agent placement is deferred to P1.** The plan originally had `.agents/skills/muriel-critique.md` (a single file inside `skills/`), but no harness has a documented convention for sub-agent definitions inside the skills dir. Claude Code reads agents from `.claude/agents/` (already covered by the plugin install); other harnesses' sub-agent surfaces vary. Document per-harness in P1 once we know what each accepts.

### P1 — per-harness manifests (Cursor, Gemini, Kiro, Qoder, Rovo Dev, Trae)

For harnesses that need a project-local plugin manifest beyond raw `SKILL.md`, generate one per harness:

- `.cursor-plugin/cursor-plugin.json` — Cursor's plugin spec (mirror the muriel keys from `.claude-plugin/marketplace.json`, plus Cursor-specific fields if any)
- `.gemini-plugin/manifest.yaml` — Gemini CLI's manifest format
- `.kiro/plugins/muriel.json` — Kiro's per-skill manifest
- `.qoder/plugins/muriel.toml`, `.rovodev/plugins/muriel.yaml`, `.trae/plugins/muriel.json`

A small generator script (`scripts/build-harness-manifests.py`) produces all of these from one source-of-truth metadata file (`harness-metadata.toml` — name, description, license, keywords, allowed-tools, dependencies), so a `version` bump only touches one file.

### P1 — installer extension

```
./install.sh                    # current behaviour (Claude Code dev install)
./install.sh --harness cursor   # symlink canonical into ~/.cursor/skills/muriel/
./install.sh --harness gemini   # …
./install.sh --harness all      # every harness present on this machine
./install.sh --list             # which harnesses are detected on this machine
```

Discovery: look for the well-known config dirs in `$HOME` (`~/.cursor/`, `~/.gemini/`, `~/.codex/`, etc.) and only offer harnesses that are actually installed. Never write to a harness's user-level dir without explicit consent.

### P2 — bidirectional helpers + frontmatter universalism

- **SKILL.md frontmatter audit.** Today muriel's frontmatter carries `name` + `description` only. The universal Agent Skills spec is now `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Add the missing fields without breaking Claude Code's parser.
- **Python dependency story.** muriel's Python channels (raster, science, gaze, infographics, …) assume `pip install -e .` worked. Some non-Claude harnesses run in containers without a Python env — document `pip install muriel` (PyPI) as the prerequisite per harness. Heavily Python-dependent channels degrade gracefully when the package is absent (SKILL.md already says so).
- **Agent loading.** `muriel-critique` is a sub-agent in Claude Code's sense. Cursor / Gemini / others have different sub-agent models. Document per-harness whether `muriel-critique` can be dispatched (and how) or must be invoked as a regular skill.
- **Marketplace listings.** Where each harness has a marketplace, submit muriel: Cursor's plugin gallery, OpenCode's catalog, etc. Track in this file as a checklist.

## Open questions

1. **`.agents/skills/` standardisation drift.** The directory is becoming a convergent open spec but no single body owns it. Watch for breaking changes; pin to the version impeccable ships against.
2. **Plugin marketplaces vs. raw symlinks.** Some harnesses want a marketplace manifest (Claude Code's `.claude-plugin/marketplace.json` model); others want a per-project `.<harness>/skills/<name>/` drop. Decide whether muriel publishes to each marketplace or stays symlink-distributed.
3. **Critique agent portability.** Test whether the `muriel-critique` subagent format loads in non-Claude harnesses. If not, ship an LLM-agnostic fallback prompt that any harness can invoke as a regular skill.
4. **License clarity.** muriel is MIT, impeccable is Apache-2.0. No conflict at use-site but cite both clearly in non-Claude harnesses where licensing surfaces differently (e.g., enterprise installs).

## Phasing

- **P0 (one PR).** Add the `.agents/` symlink, verify six harnesses pick it up, document recipes per harness in this file.
- **P1 (subsequent PRs).** Per-harness manifest generator, installer `--harness` flag, harness-detection.
- **P2 (rolling).** Frontmatter universalism, marketplace submissions, critique-agent portability, ongoing harness-drift watch.

## Related prior art

- **[pbakaus/impeccable](https://github.com/pbakaus/impeccable)** — the canonical example of cross-harness packaging for an Agent Skills payload. Their `HARNESSES.md` is the model for this document; their `.agents/skills/` convention is the model for the P0 broadcast directory.
- **[Anthropic's Agent Skills spec](https://github.com/anthropics/claude-code/blob/main/docs/skills.md)** — the frontmatter universe that all eleven harnesses converge on.
