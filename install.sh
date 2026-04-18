#!/usr/bin/env bash
# muriel install helper — symlinks muriel into ~/.claude/skills/ and the
# critique agent into ~/.claude/agents/.
#
# Safe to re-run; skips what already exists.

set -euo pipefail

SRC="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DST="$HOME/.claude/skills/muriel"
AGENT_DST="$HOME/.claude/agents/muriel-critique.md"

echo "muriel — install helper"
echo "source: $SRC"

# ── Skill mount ────────────────────────────────────────────────────────
mkdir -p "$HOME/.claude/skills"
if [ -L "$SKILL_DST" ] || [ -d "$SKILL_DST" ]; then
  echo "✓ $SKILL_DST already exists — leaving alone"
else
  ln -s "$SRC" "$SKILL_DST"
  echo "✓ linked $SRC → $SKILL_DST"
fi

# ── Critique agent ─────────────────────────────────────────────────────
mkdir -p "$HOME/.claude/agents"
if [ -L "$AGENT_DST" ] || [ -f "$AGENT_DST" ]; then
  echo "✓ $AGENT_DST already exists — leaving alone"
else
  ln -s "$SRC/agents/muriel-critique.md" "$AGENT_DST"
  echo "✓ linked $SRC/agents/muriel-critique.md → $AGENT_DST"
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
