"""
muriel.doctor — install / extras / cache health check.

Run this before opening a support issue. It reports:

  * muriel version and Python version
  * which optional extras are installed (probed without importing them)
  * which model weights are cached on disk
  * the install command for any missing extra

Nothing here imports heavyweight libs — ``find_spec`` only tells us the
module exists, without paying the import cost. Fast enough to run at
skill-invocation time (<50ms cold).

Usage
-----

::

    muriel doctor
    muriel doctor --json            # machine-readable
"""

from __future__ import annotations

import json
import os
import sys
from importlib import util as _ilu
from pathlib import Path
from typing import Optional, Sequence

from muriel import __version__
from muriel.detectors import EXTRAS


def _installed(module_name: str) -> bool:
    return _ilu.find_spec(module_name) is not None


def _dir_size(p: Path) -> int:
    if not p.exists():
        return 0
    total = 0
    for dirpath, _, filenames in os.walk(p):
        for f in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return total


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB"):
        n /= 1024.0
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
    return f"{n:.1f} GB"


def collect() -> dict:
    """Gather the doctor report as a plain dict (CLI + JSON share this)."""
    from muriel.detectors import saliency as _sal

    extras_status = {}
    for name, info in EXTRAS.items():
        module = info["module"]
        extras_status[name] = {
            "module": module,
            "installed": _installed(module),
            "purpose": info["purpose"],
            "install_hint": f"pip install 'muriel[{name}]'",
        }

    # EasyOCR model cache lives under ~/.EasyOCR.
    easyocr_cache = Path.home() / ".EasyOCR"
    # MediaPipe bundles its own weights — no user-facing cache.
    caches = {
        "easyocr": {
            "path": str(easyocr_cache),
            "exists": easyocr_cache.exists(),
            "size": _fmt_bytes(_dir_size(easyocr_cache)),
        },
        "saliency": {
            "path": str(_sal.cached_model_path()),
            "exists": _sal.is_warmed(),
            "size": _fmt_bytes(_dir_size(_sal.cached_model_path().parent)),
        },
    }

    return {
        "muriel_version": __version__,
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "platform": sys.platform,
        "extras": extras_status,
        "caches": caches,
    }


def _print_human(report: dict) -> None:
    print(f"muriel {report['muriel_version']}  (Python {report['python_version']}, {report['platform']})")
    print(f"  → {report['python_executable']}")
    print()
    print("Extras")
    width = max(len(name) for name in report["extras"])
    for name, info in report["extras"].items():
        mark = "✓" if info["installed"] else "·"
        colour = "" if info["installed"] else ""
        status = "installed" if info["installed"] else "not installed"
        print(f"  {mark}  {name:<{width}}   [{info['module']:<12}] {status}")
        if not info["installed"]:
            print(f"       {info['install_hint']}")
        print(f"       {info['purpose']}")
    print()
    print("Model cache")
    for name, c in report["caches"].items():
        mark = "✓" if c["exists"] else "·"
        status = f"{c['size']}" if c["exists"] else "(not warmed)"
        print(f"  {mark}  {name:<10} {status}")
        print(f"       {c['path']}")
    print()
    missing = [n for n, v in report["extras"].items() if not v["installed"]]
    if missing:
        print(f"To enable all detectors: pip install 'muriel[{','.join(missing)}]'")
        print("After installing, run:    muriel warmup")
    else:
        warmups_needed = [n for n, c in report["caches"].items() if not c["exists"]]
        if warmups_needed:
            print(f"All extras installed. Warm caches: muriel warmup --{' --'.join(warmups_needed)}")
        else:
            print("All extras installed and caches warm. Ready.")


def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="muriel doctor",
        description="Report muriel install state, extras, and model caches.",
    )
    ap.add_argument("--json", action="store_true",
                    help="Emit report as JSON instead of human-readable text.")
    args = ap.parse_args(argv)

    report = collect()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
