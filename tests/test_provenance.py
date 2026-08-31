"""
Tests for muriel.provenance — the only module other repositories import.

Seven scripts in attentional-foraging call ``stamp_json`` / ``stamp_savefig``
across a repo boundary, and until 2026-08-31 nothing here covered any of it: a
renamed function or a changed field set would have shipped green. Two of these
tests exist for defects that actually occurred rather than for defects that
might:

* ``test_version_is_not_hardcoded`` — ``MURIEL_VERSION`` was pinned at "0.6.0"
  while the package moved to 0.14.0, so 22 research sidecars record a producing
  version that did not produce them.
* ``test_public_api_surface`` — the cross-repo import contract, pinned by name.

Standard library only (unittest, no pytest dependency), matching the rest of
the suite.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from muriel import provenance as prov_mod
from muriel.provenance import (
    MURIEL_VERSION,
    SCHEMA_VERSION,
    Provenance,
    build_provenance,
    read_provenance,
    stamp_json,
)


class TestVersionSource(unittest.TestCase):
    def test_version_is_not_hardcoded(self):
        """The stamp must report the version that is actually running."""
        from muriel._version import get_version

        self.assertEqual(MURIEL_VERSION, get_version())

    def test_version_agrees_with_package(self):
        import muriel

        self.assertEqual(MURIEL_VERSION, muriel.__version__)

    def test_version_is_resolved_not_sentinel(self):
        """A checkout must resolve a real version, not fall through to the sentinel."""
        self.assertNotEqual(MURIEL_VERSION, "0+unknown")
        self.assertRegex(MURIEL_VERSION, r"^\d+\.\d+")

    def test_schema_version_stays_pinned(self):
        """SCHEMA_VERSION is the field that IS deliberately constant.

        Bumping it is a real decision — old sidecars must stay readable — so it
        is pinned here to make the bump deliberate rather than incidental.
        """
        self.assertEqual(SCHEMA_VERSION, 1)


class TestJsonRoundTrip(unittest.TestCase):
    def test_stamp_json_writes_data_and_sidecar(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "summary.json"
            payload = {"auc": 0.847, "n": 2764}
            stamp_json(payload, out, script=__file__, figure_version="v1",
                       nb_k_ids=["NB22:K3", "NB21:K-bbox-3"])

            # The written file carries the caller's payload untouched plus an
            # embedded `_provenance` block; the sidecar holds the same record
            # flat. Both layers exist so the lineage survives a file being
            # copied away from its sidecar.
            written = json.loads(out.read_text())
            for k, v in payload.items():
                self.assertEqual(written[k], v, f"payload key {k!r} was altered")
            self.assertIn("_provenance", written)
            self.assertEqual(written["_provenance"]["muriel_version"], MURIEL_VERSION)

            sidecar = out.with_suffix(out.suffix + ".meta.json")
            self.assertTrue(sidecar.exists(), "sidecar was not written")
            meta = json.loads(sidecar.read_text())
            self.assertEqual(meta["muriel_version"], MURIEL_VERSION)
            self.assertEqual(meta["schema_version"], SCHEMA_VERSION)
            self.assertEqual(meta["nb_k_ids"], ["NB22:K3", "NB21:K-bbox-3"])
            self.assertEqual(meta["figure_version"], "v1")

    def test_read_provenance_recovers_the_record(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "summary.json"
            stamp_json({"x": 1}, out, script=__file__, notes="round-trip")

            got = read_provenance(out)
            self.assertIsNotNone(got, "read_provenance returned None for a stamped file")
            self.assertEqual(got.notes, "round-trip")
            self.assertEqual(got.muriel_version, MURIEL_VERSION)
            self.assertTrue(got.run_utc, "run_utc must be populated")

    def test_read_provenance_returns_none_when_unstamped(self):
        with tempfile.TemporaryDirectory() as td:
            plain = Path(td) / "plain.json"
            plain.write_text('{"x": 1}')
            self.assertIsNone(read_provenance(plain))

    def test_dataset_hash_is_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            data = Path(td) / "input.json"
            data.write_text('{"rows": 3}')
            out = Path(td) / "summary.json"
            stamp_json({"ok": True}, out, script=__file__, dataset=data)

            meta = json.loads(out.with_suffix(out.suffix + ".meta.json").read_text())
            self.assertEqual(len(meta["dataset_sha256"]), 64,
                             "dataset_sha256 must be a full sha256 hex digest")
            self.assertEqual(meta["dataset_path"], str(data),
                             "dataset_path keeps the caller's spelling for grep")

    def test_missing_dataset_hashes_to_empty_not_error(self):
        """A dataset path that cannot be resolved degrades, it does not raise."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "summary.json"
            stamp_json({"ok": True}, out, script=__file__,
                       dataset=Path(td) / "does-not-exist.json")
            meta = json.loads(out.with_suffix(out.suffix + ".meta.json").read_text())
            self.assertEqual(meta["dataset_sha256"], "")


class TestBuildProvenance(unittest.TestCase):
    def test_builds_without_writing(self):
        p = build_provenance(script=__file__, h_ids=["H03"], nb_k_ids=["NB22:K3"])
        self.assertIsInstance(p, Provenance)
        self.assertEqual(p.h_ids, ["H03"])
        self.assertEqual(p.muriel_version, MURIEL_VERSION)

    def test_ids_are_coerced_to_strings(self):
        p = build_provenance(script=__file__, h_ids=(x for x in ["H1", "H2"]))
        self.assertEqual(p.h_ids, ["H1", "H2"], "generators must be materialised")


class TestPublicApiSurface(unittest.TestCase):
    """The cross-repo import contract.

    attentional-foraging/scripts imports these by name across a repo boundary
    with no version pin between them. Renaming one is a breaking change and
    should fail here, not in a research script three weeks later.
    """

    REQUIRED = (
        "stamp_json",
        "stamp_savefig",
        "stamp_existing",
        "stamp_existing_json",
        "read_provenance",
        "build_provenance",
        "Provenance",
        "SCHEMA_VERSION",
        "MURIEL_VERSION",
        "TEXT_KEY",
    )

    def test_names_are_exported(self):
        for name in self.REQUIRED:
            with self.subTest(name=name):
                self.assertTrue(hasattr(prov_mod, name),
                                f"muriel.provenance.{name} is imported by other repos")


if __name__ == "__main__":
    unittest.main()
