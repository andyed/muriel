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

SRC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLUGIN_SKILL_SRC="$SRC/plugins/muriel/skills/compose"
PLUGIN_AGENT_SRC="$SRC/plugins/muriel/agents/muriel-critique.md"
SKILL_DST="$HOME/.claude/skills/muriel"
AGENT_DST="$HOME/.claude/agents/muriel-critique.md"
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
if [ ! -d "$PLUGIN_SKILL_SRC" ] || [ ! -f "$PLUGIN_AGENT_SRC" ]; then
  echo "✗ Expected plugin layout missing."
  echo "  PLUGIN_SKILL_SRC=$PLUGIN_SKILL_SRC"
  echo "  PLUGIN_AGENT_SRC=$PLUGIN_AGENT_SRC"
  echo "  Are you on a branch where the plugin migration has landed?"
  exit 1
fi

# ── Skill mount ────────────────────────────────────────────────────────
mkdir -p "$HOME/.claude/skills"
if [ -L "$SKILL_DST" ] || [ -d "$SKILL_DST" ]; then
  echo "✓ $SKILL_DST already exists — leaving alone"
else
  ln -s "$PLUGIN_SKILL_SRC" "$SKILL_DST"
  echo "✓ linked $PLUGIN_SKILL_SRC → $SKILL_DST"
fi

# ── Critique agent ─────────────────────────────────────────────────────
mkdir -p "$HOME/.claude/agents"
if [ -L "$AGENT_DST" ] || [ -f "$AGENT_DST" ]; then
  echo "✓ $AGENT_DST already exists — leaving alone"
else
  ln -s "$PLUGIN_AGENT_SRC" "$AGENT_DST"
  echo "✓ linked $PLUGIN_AGENT_SRC → $AGENT_DST"
fi

# ── Python package (optional, editable) ────────────────────────────────
if command -v pip >/dev/null 2>&1; then
  read -r -p "Install muriel Python package with 'pip install -e' (y/N)? " yn
  case "$yn" in
    [Yy]*) pip install -e "$SRC" && echo "✓ pip install -e complete" ;;
    *)     echo "✗ skipping pip install (install later with: pip install -e $SRC)" ;;
  esac
else
  echo "✗ pip not found on PATH — skipping Python install"
fi

echo ""
echo "done. Invoke /muriel from a Claude Code session."
