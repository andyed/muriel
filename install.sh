#!/usr/bin/env bash
# muriel install helper — for DEVELOPERS working on this repo.
#
# Most users should install via Claude Code's plugin system instead:
#   /plugin marketplace add andyed/muriel
#   /plugin install muriel@andyed-muriel
#
# This script symlinks the dev checkout into ~/.claude/skills/ + ~/.claude/agents/
# so changes to channels/ etc. show up immediately without a /plugin update.
# Safe to re-run; skips what already exists. Refuses if the plugin install is
# already present, to avoid double-loading the same skill.

set -euo pipefail

SKIP_PYTHON=0
REPAIR=0
for arg in "$@"; do
  case "$arg" in
    --no-python) SKIP_PYTHON=1 ;;
    --repair)    REPAIR=1 ;;
    -h|--help)
      echo "usage: install.sh [--repair] [--no-python]"
      echo "  --repair      move a legacy non-symlink mount aside and replace it"
      echo "                with a single directory symlink"
      echo "  --no-python   skip the editable pip install (packaging/CI contexts"
      echo "                that install the wheel themselves)"
      echo
      echo "env: PYTHON=/path/to/python   interpreter to install into (default: python3)"
      exit 0
      ;;
    *) echo "unknown argument: $arg (try --help)" >&2; exit 2 ;;
  esac
done

SRC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN_SKILL_SRC="$SRC/plugins/muriel/skills/compose"
PLUGIN_AGENT_SRC="$SRC/plugins/muriel/agents"
SKILL_DST="$HOME/.claude/skills/muriel"
AGENT_DST_DIR="$HOME/.claude/agents"
AGENT_DST="$AGENT_DST_DIR/muriel"
PLUGIN_CACHE_HINT="$HOME/.claude/plugins/cache/andyed-muriel"

echo "muriel — dev install helper"
echo "source: $SRC"
echo
echo "End-user install path (recommended for non-developers):"
echo "  /plugin marketplace add andyed/muriel"
echo "  /plugin install muriel@andyed-muriel"
echo

# ── Refuse if plugin install is already present ────────────────────────
if [ -d "$PLUGIN_CACHE_HINT" ]; then
  echo "✗ muriel appears to be installed via /plugin install ($PLUGIN_CACHE_HINT)."
  echo "  Skipping legacy symlink to avoid double-loading."
  echo "  To switch to the dev-checkout install, first run:"
  echo "    /plugin uninstall muriel@andyed-muriel"
  exit 0
fi

# ── Sanity-check the plugin tree ──────────────────────────────────────
if [ ! -d "$PLUGIN_SKILL_SRC" ] || [ ! -d "$PLUGIN_AGENT_SRC" ]; then
  echo "✗ Expected plugin layout missing."
  echo "  PLUGIN_SKILL_SRC=$PLUGIN_SKILL_SRC"
  echo "  PLUGIN_AGENT_SRC=$PLUGIN_AGENT_SRC"
  echo "  Are you on a branch where the plugin migration has landed?"
  exit 1
fi

# ── Mount helper ───────────────────────────────────────────────────────
# Both mounts are ONE directory symlink each. That is the only shape that
# cannot rot: a new channel, reference, or jury seat appears in the live
# install the moment it lands in the checkout, with no re-run.
#
# The previous per-file agent loop and the older per-item skill mount both
# failed the same way. They only ever *added*, and their existence check
# was `[ -L "$dst" ] || [ -d "$dst" ]` — true for a DANGLING symlink and
# true for a stale directory — so a mount that pointed at a pre-migration
# path printed "already exists, leaving alone" forever. Observed in the
# wild: `~/.claude/agents/muriel-critique.md` still aimed at the
# pre-plugin `muriel/agents/` path and resolved to nothing, and a skill
# mount assembled item-by-item never gained `references/`, so every deep
# reference SKILL.md links was unreachable.
#
# So: verify where a mount actually points, not merely that something is
# there. Repoint what we own; never silently delete what we do not.
NEEDS_REPAIR=0

mount_dir() {
  mount_src="$1"; mount_dst="$2"; mount_label="$3"

  if [ -L "$mount_dst" ]; then
    mount_cur="$( readlink "$mount_dst" )"
    if [ "$mount_cur" = "$mount_src" ]; then
      echo "✓ $mount_label already linked correctly"
      return 0
    fi
    # A symlink at our own mount point is ours to manage. Repoint it —
    # this is the dangling-after-a-refactor case and it must self-heal.
    rm "$mount_dst"
    ln -s "$mount_src" "$mount_dst"
    echo "✓ $mount_label repointed (was: $mount_cur)"
    return 0
  fi

  if [ -e "$mount_dst" ]; then
    # A real file or directory. Legacy per-item mount, or something the
    # user put there. Either way we do not delete it without being told.
    if [ "$REPAIR" -eq 1 ]; then
      mount_bak="$mount_dst.bak-$( date +%Y%m%d%H%M%S )"
      mv "$mount_dst" "$mount_bak"
      ln -s "$mount_src" "$mount_dst"
      echo "✓ $mount_label replaced (previous contents moved to $mount_bak)"
    else
      echo "✗ $mount_label exists and is not a symlink to this checkout:"
      echo "    $mount_dst"
      echo "  This is the legacy per-item mount. It does not pick up"
      echo "  directories added later, so deep references and new jury"
      echo "  seats stay invisible. Re-run with --repair to move it aside"
      echo "  and replace it with a single directory symlink."
      NEEDS_REPAIR=1
    fi
    return 0
  fi

  ln -s "$mount_src" "$mount_dst"
  echo "✓ linked $mount_src → $mount_dst"
}

# ── Skill mount ────────────────────────────────────────────────────────
mkdir -p "$HOME/.claude/skills"
mount_dir "$PLUGIN_SKILL_SRC" "$SKILL_DST" "skill"

# ── Agent mount ────────────────────────────────────────────────────────
# Claude Code scans ~/.claude/agents/ recursively and takes a subagent's
# identity from its `name:` frontmatter, not its path, so one directory
# symlink registers muriel-critique and all five jury seats — and every
# seat added later. ~/.claude/agents/ is a shared namespace, so we mount
# a muriel/ subdirectory inside it rather than the directory itself.
mkdir -p "$AGENT_DST_DIR"
mount_dir "$PLUGIN_AGENT_SRC" "$AGENT_DST" "agents"

# Retire the per-file symlinks the old loop left behind. Only ours — a
# symlink is ours if it resolves into this checkout. Anything else, and
# any real file, is left untouched.
for stale in "$AGENT_DST_DIR"/muriel-*.md; do
  [ -L "$stale" ] || continue
  case "$( readlink "$stale" )" in
    "$SRC"/*)
      rm "$stale"
      echo "✓ retired legacy per-file link $( basename "$stale" )"
      ;;
  esac
done

# ── Python package (editable, default yes) ─────────────────────────────
#
# This used to prompt (y/N), defaulting to no, and the default is what people
# took: as of 2026-08-31 no editable install had ever been made on the author's
# machine. Two consequences, both silent.
#
# 1. Consumers reach the package by absolute `sys.path.insert` instead. Six such
#    inserts exist in attentional-foraging/scripts, and they broke for three
#    weeks in August when the skill mount was repointed at the plugin's skill
#    directory — which is not a package root.
# 2. The repo root is a PEP 420 implicit namespace package named `muriel`, so
#    from a parent directory `import muriel` SUCCEEDS and yields an empty
#    module. That defeats `try: import muriel / except ImportError` guards and
#    turns a path error into a silent wrong answer.
#
# An editable install closes both: it puts a real `muriel` on sys.path with
# priority over the namespace shadow, and it makes `importlib.metadata` the
# version source the provenance stamp reads. Skippable with --no-python for
# packaging or CI contexts that install the wheel themselves.
#
# Install via `<interpreter> -m pip`, never bare `pip`. On a machine with
# pyenv, Homebrew and venvs in play these disagree: on the author's laptop
# `pip` is pyenv 3.10 while `python3` is Homebrew 3.14, so bare `pip` installed
# muriel into an interpreter the jury agents never run, and
# `python -m muriel.squint` kept failing with the install apparently done.
# Override with PYTHON=/path/to/python.
PY_FAILED=0
PYBIN="${PYTHON:-python3}"
if [ "${SKIP_PYTHON:-0}" = "1" ]; then
  echo "✗ skipping Python install (--no-python)"
elif ! command -v "$PYBIN" >/dev/null 2>&1; then
  echo "✗ interpreter '$PYBIN' not found — skipping Python install"
  echo "  set PYTHON=/path/to/python and re-run"
elif ! "$PYBIN" -m pip --version >/dev/null 2>&1; then
  echo "✗ $PYBIN has no pip — skipping Python install"
  echo "  install with uv instead:  uv pip install -e $SRC --python $PYBIN"
else
  echo "Python target: $("$PYBIN" -c 'import sys,platform; print(platform.python_version(), "at", sys.executable)')"
  read -r -p "Install muriel Python package with 'pip install -e' (Y/n)? " yn
  case "$yn" in
    [Nn]*)
      echo "! skipped — muriel.provenance will not be importable without a"
      echo "  sys.path hack, and 'import muriel' from a parent directory will"
      echo "  resolve to an empty namespace package. Install later with:"
      echo "    $PYBIN -m pip install -e $SRC"
      ;;
    *)
      # Homebrew/system pythons are PEP 668 "externally managed" and refuse a
      # plain install. Retry into the USER site, which never touches the
      # managed tree — that is the combination pip itself recommends when
      # overriding, and it is trivially reversible with `pip uninstall muriel`.
      # Without this fallback the default path fails on every Homebrew machine.
      if "$PYBIN" -m pip install -e "$SRC" 2>/tmp/muriel-pip-err.$$; then
        echo "✓ pip install -e complete"
        rm -f /tmp/muriel-pip-err.$$
      elif grep -q "externally-managed-environment" /tmp/muriel-pip-err.$$ 2>/dev/null; then
        echo "  (interpreter is externally managed — retrying into your user site)"
        if "$PYBIN" -m pip install -e "$SRC" --user --break-system-packages; then
          echo "✓ pip install -e complete (user site; system tree untouched)"
        else
          echo "! pip install failed — muriel.provenance stays unimportable."
          echo "  Options:"
          echo "    • install into a venv:  $PYBIN -m venv .venv && .venv/bin/pip install -e $SRC"
          echo "    • or with uv:           uv pip install -e $SRC --python $PYBIN"
          PY_FAILED=1
        fi
        rm -f /tmp/muriel-pip-err.$$
      else
        echo "! pip install -e failed — muriel.provenance stays unimportable."
        sed 's/^/    /' /tmp/muriel-pip-err.$$ | tail -5
        echo "  Retry with: $PYBIN -m pip install -e $SRC"
        rm -f /tmp/muriel-pip-err.$$
        PY_FAILED=1
      fi
      ;;
  esac
fi

echo ""
if [ "$PY_FAILED" -eq 1 ]; then
  echo "! Python package not installed — muriel.provenance is unimportable and"
  echo "  the jury seats that call muriel.squint will fail. Skills/agents are"
  echo "  mounted regardless; fix the install with one of the options above."
  exit 1
fi
if [ "$NEEDS_REPAIR" -eq 1 ]; then
  echo "! Install incomplete — a legacy mount is still in place."
  echo "  Re-run with:  $0 --repair"
  exit 1
fi
echo "done. Invoke /muriel from a Claude Code session."
echo "Jury seats available as subagent_type: muriel-squinter, muriel-thumbnail,"
echo "muriel-stranger, muriel-forger, muriel-pedant (plus muriel-critique)."
