"""
Tests for channel front-matter loading — the gate layer described in
``channels/SCHEMA.md``.

This file exists because the loader was silently dead. ``_load_channel_meta``
resolved ``<repo-root>/channels/<name>.md``, but the channel docs live at
``plugins/muriel/skills/compose/channels/``. There is no ``channels/`` at repo
root in any layout, so every lookup returned ``{}``, every declared gate was
inert, and nothing failed — a dead path that reports success is invisible
without a test that asserts the payload is non-empty.

Three claims:

  * Every channel doc carrying front-matter actually loads. Not "the loader
    returns a dict" — the dict has to have the channel's own name in it.
  * The declared values are in the SCHEMA.md enums. A typo'd ``status`` or a
    mis-spelled ``audience`` degrades to no-gate rather than erroring, so it
    has to be caught here or not at all.
  * ``MURIEL_CHANNELS_DIR`` overrides the search, which is what makes the
    resolution order testable at all.

Standard library only (unittest, no pytest dependency).
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from muriel.critique import _load_channel_meta, _parse_frontmatter, channel_dirs

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL = REPO_ROOT / "plugins" / "muriel" / "skills" / "compose" / "channels"

# SCHEMA.md enums.
STATUSES = {"active", "partial-mvp", "queued"}
REQUIREMENT = {"required", "optional", "none"}
OUTPUT_KINDS = {"svg", "png", "jpg", "pdf", "html", "css", "js", "tsx",
                "mp4", "gif", "txt"}
REGISTERS = {"paper", "blog", "social", "app", "interactive", "terminal",
             "presentation", "editorial"}


def _channel_docs() -> list[Path]:
    """Every channel doc except SCHEMA.md, which documents the format
    rather than using it."""
    return sorted(p for p in CANONICAL.glob("*.md") if p.stem != "SCHEMA")


def _has_frontmatter(path: Path) -> bool:
    return path.read_text(encoding="utf-8").startswith("---")


class ChannelDirsTests(unittest.TestCase):

    def test_canonical_dir_is_searched_and_exists(self):
        """The dev-checkout path must be in the search list and must be real.
        This is the assertion the original bug would have failed."""
        self.assertTrue(CANONICAL.is_dir(), f"{CANONICAL} missing")
        self.assertIn(CANONICAL, [d.resolve() for d in channel_dirs()])

    def test_env_override_replaces_the_search(self):
        prior = os.environ.get("MURIEL_CHANNELS_DIR")
        os.environ["MURIEL_CHANNELS_DIR"] = "/nonexistent/channels"
        try:
            self.assertEqual(channel_dirs(), [Path("/nonexistent/channels")])
            # An override pointing nowhere degrades to no gates, not an error.
            self.assertEqual(_load_channel_meta("web"), {})
        finally:
            if prior is None:
                del os.environ["MURIEL_CHANNELS_DIR"]
            else:
                os.environ["MURIEL_CHANNELS_DIR"] = prior


class ChannelMetaTests(unittest.TestCase):

    def test_every_frontmatter_channel_loads(self):
        """The regression guard. A channel that declares front-matter must
        come back through the loader with content."""
        declared = [p for p in _channel_docs() if _has_frontmatter(p)]
        self.assertTrue(declared, "no channel docs carry front-matter")
        for path in declared:
            with self.subTest(channel=path.stem):
                meta = _load_channel_meta(path.stem)
                self.assertTrue(meta, f"{path.stem} front-matter did not load")
                self.assertEqual(meta.get("channel"), path.stem,
                                 "`channel:` must match the filename")

    def test_declared_values_are_in_schema_enums(self):
        for path in _channel_docs():
            if not _has_frontmatter(path):
                continue
            meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
            with self.subTest(channel=path.stem):
                self.assertIn(meta.get("status"), STATUSES)
                requires = meta.get("requires") or {}
                for key in ("brand", "audience"):
                    if key in requires:
                        self.assertIn(requires[key], REQUIREMENT)
                output = meta.get("output") or {}
                for kind in output.get("kinds", []):
                    self.assertIn(kind, OUTPUT_KINDS)
                for register in output.get("registers", []):
                    self.assertIn(register, REGISTERS)

    def test_peer_channels_point_at_real_channels(self):
        names = {p.stem for p in _channel_docs()}
        for path in _channel_docs():
            if not _has_frontmatter(path):
                continue
            meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
            for peer in meta.get("peer_channels", []):
                with self.subTest(channel=path.stem, peer=peer):
                    self.assertIn(peer, names)

    def test_missing_channel_degrades_quietly(self):
        self.assertEqual(_load_channel_meta("no-such-channel"), {})


if __name__ == "__main__":
    unittest.main()
