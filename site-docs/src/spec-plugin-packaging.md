# Spec: Package muriel as a Claude Code plugin

**Audience:** muriel maintainer / coding agent working in this repo.
**Status:** draft, ready to implement.
**Reference:** <https://code.claude.com/docs/en/plugins>,
<https://code.claude.com/docs/en/plugin-marketplaces>,
<https://code.claude.com/docs/en/plugins-reference>. Anything in this spec
that disagrees with those pages, the docs win — re-check the docs before
implementing.

---

## 1. Problem

Today's install path is `git clone … && bash install.sh`, which symlinks the
repo into `~/.claude/skills/muriel` and the critique into
`~/.claude/agents/muriel-critique.md`. That works if you have a shell, know
where to clone, and trust a script. It does **not** match how Claude Code
users expect to install things in 2026: `/plugin marketplace add <repo>`
followed by `/plugin install <plugin>`. The friction is real — even the
author shipped the existing install path and still had to hand-hack the
symlink targets on a fresh machine because the resolved paths confused the
loader (the install.sh-derived `~/.claude/skills/muriel` symlink did not line
up with what Claude Code expected at install time).

The plugin/marketplace surface is the right shape:

- discoverable from inside Claude Code (no terminal context-switch),
- versioned (the user knows what they have),
- removable (`/plugin uninstall`),
- safe to update (Claude Code refreshes from the marketplace; no shell
  scripts editing user dotfiles).

## 2. Goal

A user running Claude Code can install muriel with two commands:

```
/plugin marketplace add andyed/muriel
/plugin install muriel@andyed-muriel
```

That should give them:

- A `/muriel:<skill>` slash skill (see §6 on the namespace decision — the
  exact invocation depends on which skill folder name we settle on).
- The `muriel-critique` subagent available to the `Agent` tool.
- No conflict with a previous `bash install.sh` install on the same box (see
  §8 dual-install).

## 3. Plugin shape (canonical, from the docs)

A plugin directory:

```
<plugin-root>/
  .claude-plugin/
    plugin.json            # manifest — REQUIRED
  skills/
    <skill-name>/
      SKILL.md             # YAML frontmatter + body
      …                    # additional files the skill references
  agents/
    <agent>.md             # subagent definition
  commands/                # legacy flat-md skills; don't use for new plugins
  hooks/hooks.json         # event handlers (out of scope for v0)
  .mcp.json                # MCP servers (out of scope for v0)
```

**Common mistake (called out in the docs):** do not put `skills/`,
`agents/`, `commands/`, or `hooks/` inside `.claude-plugin/`. Only
`plugin.json` lives in `.claude-plugin/`. Everything else sits at the plugin
root.

A **marketplace** is a repo with `.claude-plugin/marketplace.json` at the
repo root. A repo can be its own marketplace.

A plugin's `name` field becomes the slash-skill namespace prefix, e.g. a
plugin named `muriel` containing a skill folder `compose/` is invoked as
`/muriel:compose`. **Plugin skills are always namespaced; this is non-
negotiable.** Standalone `.claude/skills/muriel/` is the only path that
yields the bare `/muriel` invocation, and that is the existing install path,
not the plugin path.

## 4. Repo layout — three options

### Option A — Root-as-plugin

Make the muriel repo itself the plugin root: move `SKILL.md` to
`skills/muriel/SKILL.md` (or whatever folder name §6 picks), put
`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` at root,
keep `agents/muriel-critique.md` at root.

Pros: simplest layout; plugin loader reads root paths directly. Cons:
top-level `skills/` and `agents/` collide visually with the existing
top-level `muriel/` Python package, `tools/`, `render_assets/`, `examples/`.
Migrating is one big mass move. No room for a sibling plugin later without
restructuring again.

### Option B — Plugins-subdir (recommended)

Match the layout the docs themselves use in the marketplace walkthrough
(<https://code.claude.com/docs/en/plugin-marketplaces#walkthrough-create-a-local-marketplace>):

```
.claude-plugin/marketplace.json           # repo root marketplace catalog
plugins/muriel/
  .claude-plugin/plugin.json
  skills/<skill-folder>/
    SKILL.md                              # canonical SKILL location
    channels/ vocabularies/ style-guides/ dimensions/ brands/
    templates/ examples/ scenarios/ assets/
  agents/
    muriel-critique.md                    # canonical agent location
```

The Python package, install.sh, README, docs, and other top-level dirs are
untouched. The marketplace lives at repo root where Claude Code expects it.
Adding a future plugin (e.g. a slash-command pack) drops in as
`plugins/muriel-tools/`.

Within Option B, **the SKILL.md and agent file are canonical at the
plugins/muriel/ paths**; the legacy `install.sh` symlinks point *to* those
new paths. Symlinks-in-git are fragile on Windows checkouts and the docs
explicitly warn that plugins are copied to a cache (see §3 footnote at
<https://code.claude.com/docs/en/plugin-marketplaces#how-plugins-are-installed>),
so a checked-in symlink from `plugins/muriel/skills/muriel/SKILL.md` →
`../../../../SKILL.md` would not survive the cache copy. Move the files,
update internal references, accept the churn.

### Option C — Separate plugin repo

`andyed/muriel-plugin` as a thin marketplace repo that vendors `andyed/muriel`
via git submodule or release-time copy.

Pros: decouples plugin distribution from main-repo cadence. Cons: doubles
maintenance, splits issues, defeats "one repo, one source of truth."

### Recommendation

**Option B.** It mirrors the doc walkthrough, preserves the existing Python
package and install.sh untouched, and keeps all files in one repo and one PR.

## 5. Manifest templates

Field names verified against
<https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema> and
<https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema>.
Re-check before committing — that page is the source of truth.

### `.claude-plugin/marketplace.json` (repo root)

```json
{
  "name": "andyed-muriel",
  "owner": {
    "name": "Andy Edmonds"
  },
  "description": "Andy Edmonds' Claude Code plugins.",
  "metadata": {
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "muriel",
      "source": "muriel",
      "description": "Multi-channel visual production skill — raster, SVG, web, interactive, video, terminal, density viz, gaze, science, infographics, diagrams. 8:1 contrast minimum enforced; brand tokens active at render time.",
      "homepage": "https://github.com/andyed/muriel",
      "license": "MIT",
      "category": "design",
      "keywords": ["visual", "design", "svg", "infographic", "science", "gaze", "brand", "contrast"]
    }
  ]
}
```

Notes:

- `name` is the marketplace identifier users see in `muriel@andyed-muriel`.
  Kebab-case, no spaces. Avoid Anthropic's reserved names (the docs list
  them).
- `metadata.pluginRoot: "./plugins"` lets each plugin entry use a short
  `"source": "muriel"` instead of `"source": "./plugins/muriel"`. It's a
  cosmetic win, drop it if multi-plugin layout is uncertain.
- `version` is **deliberately omitted** from the plugin entry. Per
  <https://code.claude.com/docs/en/plugin-marketplaces#version-resolution-and-release-channels>,
  omitting `version` falls back to the git commit SHA, so every push is a new
  version and users get updates automatically. We can add explicit semver
  later when we want to gate updates.

### `plugins/muriel/.claude-plugin/plugin.json`

```json
{
  "name": "muriel",
  "description": "Multi-channel visual production skill with brand-token enforcement and 8:1 contrast minimum.",
  "author": {
    "name": "Andy Edmonds"
  },
  "homepage": "https://github.com/andyed/muriel",
  "license": "MIT"
}
```

Notes:

- Default skill / agent locations (`skills/`, `agents/`) are picked up
  automatically — no need to declare them in the manifest.
- `version` is again deliberately omitted; the marketplace resolves to the
  commit SHA. **Do not set `version` in both `plugin.json` and the
  marketplace entry** — the docs warn that `plugin.json` silently wins, which
  has burned others.
- `name` here is the plugin identifier and the slash-skill namespace prefix.
  Keep it `muriel`.

## 6. The `/muriel:<skill>` namespace decision

Plugin skills are namespaced as `/<plugin-name>:<skill-folder-name>`. With
plugin name `muriel` and a skill folder named `muriel`, the invocation is
`/muriel:muriel` — ugly, but accurate.

Three options for the **skill folder name** inside `plugins/muriel/skills/`.
This is independent of repo layout (§4):

1. **`muriel/`** — invocation becomes `/muriel:muriel`. Clear lineage with
   the standalone install. Visually awkward.
2. **`compose/`** — invocation `/muriel:compose`. Maps to the verb the skill
   actually performs (compose a visual artifact under brand constraints).
   Cleaner read; small UX migration cost for the few existing standalone-
   install users.
3. **`start/`** or **`index/`** — invocation `/muriel:start`. Generic, less
   information-bearing.

**Recommendation: option 2 (`compose/`).** The standalone install at
`~/.claude/skills/muriel/` continues to give `/muriel` for users on the
legacy path; the plugin path gives `/muriel:compose`. Future siblings (e.g.
`/muriel:critique` wrapping the agent — see §10) drop in cleanly.

If keeping perfect parity with the standalone `/muriel` is more important
than verb-clarity, take option 1 and accept `/muriel:muriel`.

## 7. SKILL.md frontmatter

The current `SKILL.md` has `user-invocable: true` in its frontmatter. The
plugins doc shows two frontmatter keys explicitly: `description` (required)
and `disable-model-invocation` (optional, default false — i.e., model can
invoke unless this is set).

Action: keep `description`. Drop `user-invocable`; if the maintainer
confirms it is silently ignored by the plugin loader, leave it removed; if it
turns out to gate something, add a line back. Test step 1 in §9 is the place
to verify.

## 8. `install.sh` updates

Goal: legacy clone-and-run keeps working for *developers* working in the
repo. End-user installs go through the plugin path.

Required edits:

1. **Update symlink targets** to the new canonical paths under
   `plugins/muriel/`:
   - `~/.claude/skills/muriel` → `$SRC/plugins/muriel/skills/<skill-folder>`
     (the `<skill-folder>` chosen in §6).
   - `~/.claude/agents/muriel-critique.md` →
     `$SRC/plugins/muriel/agents/muriel-critique.md`
2. **Detect existing plugin install.** Before symlinking, check for a
   muriel entry in Claude Code's plugin cache. Per
   <https://code.claude.com/docs/en/plugin-marketplaces#plugin-sources> the
   cache lives at `~/.claude/plugins/cache`. If
   `~/.claude/plugins/cache/andyed-muriel/muriel/` (or any subdir matching
   that pattern) exists, refuse and print:

   ```
   muriel is already installed via /plugin install. Skipping legacy symlink.
   To switch to the dev-checkout install, first run:
     /plugin uninstall muriel@andyed-muriel
   ```

   The exact directory layout under `cache/` should be confirmed by running
   `/plugin install` once on a clean box and inspecting the tree.
3. **Add a banner** at the top of the script noting the plugin path is the
   recommended end-user install method, with the two `/plugin …` commands
   from §2.
4. **Keep the editable `pip install -e`** prompt — that is for hacking on
   `muriel/critique.py` and the Python tools, unrelated to plugin install.

The script remains supported for the dev workflow, but the README, the
plugin doc, and the homepage should lead with `/plugin marketplace add`.

## 9. Test plan

Five steps. Run on a clean macOS box, or in a fresh checkout that has never
installed muriel before. Step 0 is pre-flight.

0. **Validate.** From the repo root after the layout migration:
   ```
   claude plugin validate .
   ```
   Catches malformed JSON, missing required fields, duplicate plugin names,
   bad relative paths. **Pass:** no errors, only acceptable warnings.

1. **Local plugin-dir load (no marketplace).** Before pushing anything:
   ```
   claude --plugin-dir ./plugins/muriel
   ```
   Inside that session:
   - Run `/help` and confirm the muriel skill appears under its namespace
     (e.g. `/muriel:compose`).
   - Invoke the skill with a trivial probe and confirm the response cites
     the 8:1 contrast rule from `SKILL.md` (smoke test that SKILL.md loaded
     and frontmatter parsed).
   - Open the `Agent` tool's subagent picker and confirm `muriel-critique`
     is listed.
   - Run `/reload-plugins` after touching a file to confirm dev workflow.

2. **Marketplace add.** Push the branch to GitHub, then:
   ```
   /plugin marketplace add andyed/muriel
   ```
   Verify with `/plugin marketplace list` that `andyed-muriel` appears and
   lists `muriel` in its catalog. **If this fails:** re-run
   `claude plugin validate .` and check `marketplace.json` syntax with `jq`.

3. **Install + content reachability.** From a fresh Claude Code session:
   ```
   /plugin install muriel@andyed-muriel
   ```
   Then:
   - Confirm the namespaced skill is invocable.
   - Ask the skill to open `channels/svg.md` (or any file `SKILL.md`
     references) and verify relative-path resolution still works inside the
     cached install at `~/.claude/plugins/cache/andyed-muriel/muriel/`. This
     is the most likely place a layout migration silently breaks: any
     reference in `SKILL.md` that points at a file outside
     `plugins/muriel/skills/<skill-folder>/` is broken because the cache
     only copies the plugin root subtree.
   - Confirm the `muriel-critique` agent is loaded and runnable.

4. **Dual-install conflict.** With the plugin installed, run
   `bash install.sh` from a clone of the repo. Confirm the script's new
   detection (§8 step 2) refuses cleanly with the suggested
   `/plugin uninstall` message. Then reverse: with `install.sh` symlinks in
   place, run `/plugin install`. Document Claude Code's behavior:
   - (a) plugin install wins and the legacy symlink is shadowed;
   - (b) Claude Code warns about the conflict; or
   - (c) only one is loaded with deterministic precedence.
   Outcome (a) or (c) means the install.sh detection is the only guard
   needed; outcome (b) means we can drop that detection.

5. **Uninstall + reinstall.**
   ```
   /plugin uninstall muriel@andyed-muriel
   /plugin install muriel@andyed-muriel
   ```
   Verify the namespaced skill disappears between the two and reappears
   after. Confirms there's no orphan state in `~/.claude/plugins/cache/`.

## 10. Out of scope (follow-ups, not blockers)

- **Public marketplace catalog.** Submission to Anthropic's official
  marketplace at <https://claude.ai/settings/plugins/submit> or
  <https://platform.claude.com/plugins/submit>. The
  `/plugin marketplace add andyed/muriel` path works directly off GitHub
  today; submission is a discovery upgrade, not a prerequisite.
- **Slash commands wrapping the critique agent.** A `/muriel:critique`
  slash skill that routes to the `muriel-critique` subagent with brand
  context preloaded, instead of the current "invoke `Agent` manually"
  workflow. Drops into `plugins/muriel/skills/critique/SKILL.md` later.
- **Hooks.** The plugin format supports `hooks/hooks.json` (nested-by-event
  schema — see the known-pitfall note in MEMORY:
  `reference_claude_code_plugin_hooks_schema`). Candidates: pre-commit
  "ran muriel-critique on changed visual artifacts," post-render "log to
  research-log.jsonl." Not v0.
- **`${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`.** When hooks or
  MCP servers ship in a future revision, they must reference plugin files
  via `${CLAUDE_PLUGIN_ROOT}` (not relative paths) because the plugin runs
  from the cache, not from the original checkout. Persistent state goes in
  `${CLAUDE_PLUGIN_DATA}`.
- **Multi-plugin split.** If muriel ever wants to ship a leaner core skill
  separate from the full channel encyclopedia, the `plugins/` subdir from
  §4 Option B accommodates that as a sibling directory.
- **`extraKnownMarketplaces` for the muriel-plus-friends bundle.** If we
  ever want a "trust Andy's stuff by default" `.claude/settings.json`
  fragment that prompts users to add the marketplace on project trust, that
  belongs in a separate spec.
