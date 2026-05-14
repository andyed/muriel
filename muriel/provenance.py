"""Figure provenance — PNG tEXt chunks + JSON sidecar.

Stamp every figure with the script that produced it, the git SHA, the
input dataset (path + hash), and the H## / NB##:K## IDs it carries
forward. The metadata travels with the binary (PNG tEXt) *and* sits
next to it as JSON (greppable, machine-auditable by science-agent's
figure-audit pass).

Why both layers
---------------

PNG tEXt chunks survive copy/paste, image-board uploads, and being
emailed around. They're the binary's own answer to "where did you come
from?" — no path needed.

JSON sidecars are aggregable and grep-friendly. science-agent already
expects ``*_summary.json`` neighbours to verify caption numerics; the
``.meta.json`` sidecar here is the freshness/lineage layer above that.

Usage
-----

Most callers just want the savefig wrapper::

    from muriel.provenance import stamp_savefig

    stamp_savefig(
        fig, "scripts/output/figures/foo.png",
        script=__file__,
        h_ids=["H03"],
        nb_k_ids=["NB22:K3", "NB21:K-bbox-3"],
        dataset="AdSERP/data/cursor-approach-features-organic.json",
        figure_version="v2",      # optional, caller-defined
        notes="organic-hybrid, Δ=500ms",  # optional free text
        dpi=200,
    )

For figures already saved by another path (e.g. matplotlib already
called ``fig.savefig``), call ``stamp_existing(path, ...)`` to inject
tEXt chunks + write the sidecar after the fact.

Field semantics
---------------

- ``script_path`` — absolute path to the producer script, resolved at
  stamp time.
- ``script_sha`` — git SHA of the producer script's repository HEAD.
  Best-effort: empty string if the script is not in a git checkout.
- ``script_dirty`` — whether the script's working tree has uncommitted
  changes. ``true`` means "this figure was rendered from a dirty tree."
- ``dataset_path`` — caller-supplied. Relative or absolute, kept as
  given so it's grep-friendly against paper prose.
- ``dataset_sha256`` — hex digest of the file at ``dataset_path``,
  computed at stamp time. Empty string if the path can't be resolved.
- ``run_utc`` — ISO-8601 UTC timestamp at stamp time.
- ``h_ids`` / ``nb_k_ids`` — list[str]. The IDs this figure carries
  forward into a paper. Used by figure-freshness audits.
- ``muriel_version`` — pinned for reproducibility.
- ``schema_version`` — the provenance schema version. Bump when the
  field set changes; old sidecars stay readable.

PNG tEXt chunks store the same fields as a single JSON blob under the
keyword ``muriel:provenance``, plus a few flat keywords (``Software``,
``Source``, ``CreationTime``) for compatibility with image viewers.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo
except ImportError as _exc:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    PngInfo = None  # type: ignore[assignment]
    _PIL_IMPORT_ERR: Optional[ImportError] = _exc
else:
    _PIL_IMPORT_ERR = None

SCHEMA_VERSION = 1
TEXT_KEY = "muriel:provenance"
MURIEL_VERSION = "0.6.0"


@dataclass
class Provenance:
    """All the lineage we record per figure."""

    script_path: str
    script_sha: str
    script_dirty: bool
    dataset_path: str
    dataset_sha256: str
    run_utc: str
    h_ids: list[str] = field(default_factory=list)
    nb_k_ids: list[str] = field(default_factory=list)
    figure_version: str = ""
    notes: str = ""
    muriel_version: str = MURIEL_VERSION
    schema_version: int = SCHEMA_VERSION

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _git_sha(path: Path) -> tuple[str, bool]:
    """Return (short_sha, dirty) for the git repo containing ``path``.

    Empty string + False if not a git checkout. Best-effort: any git
    failure is silent.
    """
    if not path.exists():
        return "", False
    cwd = path.parent if path.is_file() else path
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "", False
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--", str(path)],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        ).decode()
        dirty = bool(status.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        dirty = False
    return sha, dirty


def _sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _coerce_ids(ids: Optional[Iterable[str]]) -> list[str]:
    if ids is None:
        return []
    return [str(x) for x in ids]


def build_provenance(
    *,
    script: str | os.PathLike[str],
    dataset: str | os.PathLike[str] | None = None,
    h_ids: Optional[Iterable[str]] = None,
    nb_k_ids: Optional[Iterable[str]] = None,
    figure_version: str = "",
    notes: str = "",
) -> Provenance:
    """Construct a Provenance record without writing anything."""
    script_path = Path(script).resolve()
    sha, dirty = _git_sha(script_path)

    if dataset is None:
        dataset_path = ""
        dataset_hash = ""
    else:
        dataset_p = Path(dataset)
        # Don't resolve — keep caller's spelling for grep-friendliness.
        dataset_path = str(dataset)
        # But resolve for hashing.
        dataset_hash = _sha256(dataset_p if dataset_p.is_absolute() else Path.cwd() / dataset_p)

    return Provenance(
        script_path=str(script_path),
        script_sha=sha,
        script_dirty=dirty,
        dataset_path=dataset_path,
        dataset_sha256=dataset_hash,
        run_utc=_utc_now(),
        h_ids=_coerce_ids(h_ids),
        nb_k_ids=_coerce_ids(nb_k_ids),
        figure_version=figure_version,
        notes=notes,
    )


def _png_metadata(prov: Provenance) -> "PngInfo":
    """Bundle a PngInfo with both the canonical JSON blob and a few
    flat keys for image viewers (Preview, Photoshop) that surface them.
    """
    if PngInfo is None:
        raise RuntimeError(
            "Pillow is required for PNG provenance. "
            "Install it: pip install Pillow"
        ) from _PIL_IMPORT_ERR
    info = PngInfo()
    info.add_text(TEXT_KEY, prov.to_json())
    info.add_text("Software", f"muriel {prov.muriel_version}")
    info.add_text("Source", prov.script_path)
    info.add_text("CreationTime", prov.run_utc)
    if prov.h_ids:
        info.add_text("muriel:h_ids", ",".join(prov.h_ids))
    if prov.nb_k_ids:
        info.add_text("muriel:nb_k_ids", ",".join(prov.nb_k_ids))
    return info


def _sidecar_path(figure_path: Path) -> Path:
    return figure_path.with_suffix(figure_path.suffix + ".meta.json")


def _write_sidecar(figure_path: Path, prov: Provenance) -> Path:
    sidecar = _sidecar_path(figure_path)
    sidecar.write_text(prov.to_json() + "\n")
    return sidecar


def stamp_savefig(
    fig: Any,
    path: str | os.PathLike[str],
    *,
    script: str | os.PathLike[str],
    dataset: str | os.PathLike[str] | None = None,
    h_ids: Optional[Iterable[str]] = None,
    nb_k_ids: Optional[Iterable[str]] = None,
    figure_version: str = "",
    notes: str = "",
    sidecar: bool = True,
    **savefig_kwargs: Any,
) -> Provenance:
    """Save ``fig`` to ``path`` with provenance baked in.

    For PNGs: tEXt chunks land in the binary AND a sidecar JSON is
    written next to the file. For other formats (PDF, SVG): the sidecar
    JSON is written; binary metadata is skipped (matplotlib's PDF/SVG
    metadata kwargs are format-specific and would balloon this API).
    Pass ``sidecar=False`` to suppress the sidecar.

    Returns the Provenance record.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prov = build_provenance(
        script=script,
        dataset=dataset,
        h_ids=h_ids,
        nb_k_ids=nb_k_ids,
        figure_version=figure_version,
        notes=notes,
    )
    is_png = out.suffix.lower() == ".png"
    if is_png:
        # Save normally first; matplotlib's metadata kwarg for PNG only
        # accepts strings, but we want our blob plus standard keys, so
        # we round-trip through Pillow.
        fig.savefig(out, **savefig_kwargs)
        _inject_png_text(out, prov)
    else:
        fig.savefig(out, **savefig_kwargs)

    if sidecar:
        _write_sidecar(out, prov)
    return prov


def stamp_existing(
    path: str | os.PathLike[str],
    *,
    script: str | os.PathLike[str],
    dataset: str | os.PathLike[str] | None = None,
    h_ids: Optional[Iterable[str]] = None,
    nb_k_ids: Optional[Iterable[str]] = None,
    figure_version: str = "",
    notes: str = "",
    sidecar: bool = True,
) -> Provenance:
    """Stamp a figure that's already on disk."""
    out = Path(path)
    if not out.exists():
        raise FileNotFoundError(out)
    prov = build_provenance(
        script=script,
        dataset=dataset,
        h_ids=h_ids,
        nb_k_ids=nb_k_ids,
        figure_version=figure_version,
        notes=notes,
    )
    if out.suffix.lower() == ".png":
        _inject_png_text(out, prov)
    if sidecar:
        _write_sidecar(out, prov)
    return prov


def _inject_png_text(path: Path, prov: Provenance) -> None:
    """Re-encode a PNG with provenance tEXt chunks. Lossless — Pillow
    re-emits the same pixel data.
    """
    if Image is None:
        raise RuntimeError(
            "Pillow is required for PNG provenance. "
            "Install it: pip install Pillow"
        ) from _PIL_IMPORT_ERR
    with Image.open(path) as img:
        img.load()
        img.save(path, "PNG", pnginfo=_png_metadata(prov))


def stamp_json(
    data: Any,
    path: str | os.PathLike[str],
    *,
    script: str | os.PathLike[str],
    dataset: str | os.PathLike[str] | None = None,
    h_ids: Optional[Iterable[str]] = None,
    nb_k_ids: Optional[Iterable[str]] = None,
    figure_version: str = "",
    notes: str = "",
    sidecar: bool = True,
    embed: bool = True,
    indent: int = 2,
    sort_keys: bool = True,
) -> Provenance:
    """Write ``data`` as JSON to ``path`` with provenance attached.

    Two layers, mirroring stamp_savefig:

    - **Embed** (default on, dict only): inserts a ``_provenance`` key
      into the top-level dict before serialising. If ``data`` is not a
      dict, embedding is silently skipped — sidecar still works.
    - **Sidecar**: writes ``<path>.meta.json`` next to the file.
      Authoritative; survives whether or not the consumer reads
      ``_provenance``.

    Pass ``embed=False`` if a downstream consumer can't tolerate the
    extra key (rare). Pass ``sidecar=False`` to suppress the sidecar.

    Returns the Provenance record.
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    prov = build_provenance(
        script=script,
        dataset=dataset,
        h_ids=h_ids,
        nb_k_ids=nb_k_ids,
        figure_version=figure_version,
        notes=notes,
    )
    payload: Any
    if embed and isinstance(data, dict):
        payload = {**data, "_provenance": asdict(prov)}
    else:
        payload = data
    out.write_text(json.dumps(payload, indent=indent, sort_keys=sort_keys) + "\n")
    if sidecar:
        _write_sidecar(out, prov)
    return prov


def stamp_existing_json(
    path: str | os.PathLike[str],
    *,
    script: str | os.PathLike[str],
    dataset: str | os.PathLike[str] | None = None,
    h_ids: Optional[Iterable[str]] = None,
    nb_k_ids: Optional[Iterable[str]] = None,
    figure_version: str = "",
    notes: str = "",
    sidecar: bool = True,
    embed: bool = True,
    indent: int = 2,
    sort_keys: bool = True,
) -> Provenance:
    """Stamp an already-written JSON file in place.

    Reads, optionally injects ``_provenance``, rewrites. Sidecar is the
    same as stamp_json. Use this for JSONs you can't easily reproduce
    (lost producer, REPL output) — but **prefer regenerating** so the
    SHA + timestamp reflect a real run, not a retroactive label.
    """
    out = Path(path)
    if not out.exists():
        raise FileNotFoundError(out)
    prov = build_provenance(
        script=script,
        dataset=dataset,
        h_ids=h_ids,
        nb_k_ids=nb_k_ids,
        figure_version=figure_version,
        notes=notes,
    )
    if embed:
        try:
            data = json.loads(out.read_text())
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            data["_provenance"] = asdict(prov)
            out.write_text(json.dumps(data, indent=indent, sort_keys=sort_keys) + "\n")
    if sidecar:
        _write_sidecar(out, prov)
    return prov


def read_provenance(path: str | os.PathLike[str]) -> Optional[Provenance]:
    """Read provenance from a stamped PNG (tEXt) or sidecar (.meta.json).

    Sidecar wins if both exist (it's authoritative; PNG can be
    re-saved without the sidecar getting regenerated). Returns None
    if neither carries provenance.

    Looks at, in order:
      1. ``<path>.meta.json`` sidecar
      2. PNG tEXt chunk (PNG only)
      3. ``_provenance`` top-level key (JSON only)
    """
    p = Path(path)
    sidecar = _sidecar_path(p)
    if sidecar.exists():
        raw = json.loads(sidecar.read_text())
        raw.pop("_provenance", None)
        return Provenance(**raw)
    if p.suffix.lower() == ".png" and p.exists() and Image is not None:
        with Image.open(p) as img:
            blob = img.info.get(TEXT_KEY)
            if blob:
                return Provenance(**json.loads(blob))
    if p.suffix.lower() == ".json" and p.exists():
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict):
            embedded = data.get("_provenance")
            if embedded:
                return Provenance(**embedded)
    return None


__all__ = [
    "Provenance",
    "SCHEMA_VERSION",
    "TEXT_KEY",
    "build_provenance",
    "stamp_savefig",
    "stamp_existing",
    "stamp_json",
    "stamp_existing_json",
    "read_provenance",
]
