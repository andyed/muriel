"""
muriel.capture — Playwright viewport-sweep screenshot helper.

Thin wrapper around Playwright that takes a URL and a list of viewport
tiers and produces one PNG per tier, named by the convention in
``channels/dimensions.md``.

Answers the question: "what does my page look like at mobile / tablet /
laptop / desktop?" — in one command, with fonts loaded, correct color
scheme, retina scale, and no hand-configuration of Playwright per site.

Pulls tier data from ``muriel.dimensions`` so named tiers
(``'mobile'``, ``'tablet'``, ``'laptop'``, ``'desktop'``) stay in sync
with the canonical viewport constants and nothing here hardcodes
pixel counts.

Usage (programmatic)
--------------------

::

    from muriel.capture import capture_responsive

    paths = capture_responsive(
        url="https://example.com/",
        output_dir="captures/",
    )
    # → [
    #     'captures/andyed-github-io-marginalia-mobile-390x844.png',
    #     'captures/andyed-github-io-marginalia-tablet-820x1180.png',
    #     'captures/andyed-github-io-marginalia-laptop-1280x800.png',
    #     'captures/andyed-github-io-marginalia-desktop-1920x1080.png',
    # ]

Custom tier list, forced color scheme, single-element clip:

::

    capture_responsive(
        url="https://example.com/examples/us-constitution.html",
        tiers=["mobile-large", "tablet-pro", "desktop-qhd"],
        color_scheme="dark",
        selector="main",
        slug="constitution",
    )

Usage (CLI)
-----------

::

    python -m muriel.capture https://example.com
    python -m muriel.capture https://example.com --tiers mobile tablet laptop desktop
    python -m muriel.capture https://example.com --dir captures/ --slug homepage
    python -m muriel.capture https://example.com --dark
    python -m muriel.capture https://example.com --selector '.hero' --slug hero
    python -m muriel.capture https://example.com --full-page

Exit status:

- ``0`` — every capture succeeded
- ``1`` — one or more tiers failed (e.g., timeout, element not found)
- ``2`` — usage error, or Playwright / chromium not installed

Dependencies
------------

Playwright is an **optional** dependency — this module is importable
without it, but ``capture_responsive()`` will raise a clean
``ImportError`` with install instructions on first call. To enable::

    pip install playwright
    playwright install chromium

Font preloading
---------------

The module waits for ``document.fonts.ready`` before screenshotting by
default. This fixes the font-flash bug where webfonts load *during* the
capture and the first tier comes out with fallback metrics — the same
bug documented under ``channels/web.md``. Disable via
``wait_for_fonts=False`` when you know the site has no webfonts and
need speed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional, Sequence, Union
from urllib.parse import urlparse

from .dimensions import (
    RESPONSIVE_TIER_LIST,
    Size,
    VIEWPORT_DESKTOP_4K,
    VIEWPORT_DESKTOP_FHD,
    VIEWPORT_DESKTOP_QHD,
    VIEWPORT_LAPTOP,
    VIEWPORT_LAPTOP_LARGE,
    VIEWPORT_MOBILE_LARGE,
    VIEWPORT_MOBILE_SMALL,
    VIEWPORT_MOBILE_STANDARD,
    VIEWPORT_TABLET_LANDSCAPE,
    VIEWPORT_TABLET_PORTRAIT,
    VIEWPORT_TABLET_PRO,
    VIEWPORT_ULTRAWIDE_21_9,
    VIEWPORT_ULTRAWIDE_32_9,
)

__all__ = [
    "NAMED_TIERS",
    "DEFAULT_TIERS",
    "CaptureError",
    "capture_responsive",
    "resolve_tiers",
    "slug_from_url",
]


# ─── Tier names ──────────────────────────────────────────────────────────

#: Short-name → Size mapping for responsive sweeps. Stays in sync with
#: ``muriel.dimensions`` so the viewport constants have a single
#: source of truth.
NAMED_TIERS: dict[str, Size] = {
    "mobile-small":     VIEWPORT_MOBILE_SMALL,       # iPhone SE
    "mobile":           VIEWPORT_MOBILE_STANDARD,    # iPhone 14/15
    "mobile-large":     VIEWPORT_MOBILE_LARGE,       # iPhone 15 Pro Max
    "tablet":           VIEWPORT_TABLET_PORTRAIT,    # iPad 10.9 portrait
    "tablet-landscape": VIEWPORT_TABLET_LANDSCAPE,
    "tablet-pro":       VIEWPORT_TABLET_PRO,         # iPad Pro 12.9
    "laptop":           VIEWPORT_LAPTOP,             # MBA 13 CSS
    "laptop-large":     VIEWPORT_LAPTOP_LARGE,
    "desktop":          VIEWPORT_DESKTOP_FHD,        # 1920×1080
    "desktop-qhd":      VIEWPORT_DESKTOP_QHD,        # 2560×1440
    "desktop-4k":       VIEWPORT_DESKTOP_4K,         # 3840×2160
    "ultrawide":        VIEWPORT_ULTRAWIDE_21_9,
    "ultrawide-32":     VIEWPORT_ULTRAWIDE_32_9,
}

#: Default sweep — four tiers matching ``dimensions.RESPONSIVE_TIER_LIST``.
DEFAULT_TIERS: tuple[str, ...] = ("mobile", "tablet", "laptop", "desktop")


# ─── Errors ──────────────────────────────────────────────────────────────

class CaptureError(RuntimeError):
    """Raised when a capture operation fails at Playwright level."""


# ─── Resolution helpers ──────────────────────────────────────────────────

def resolve_tiers(
    tiers: Optional[Sequence[Union[str, Size]]] = None,
) -> list[tuple[str, Size]]:
    """
    Normalize a tier list to a list of ``(name, Size)`` pairs.

    Accepts:

    - ``None`` → defaults to ``DEFAULT_TIERS``
    - a sequence of short-name strings (looked up in ``NAMED_TIERS``)
    - a sequence of ``Size`` tuples (names derived as ``'custom-WxH'``)
    - a mixed sequence of both

    Raises
    ------
    ValueError
        If a string is not in ``NAMED_TIERS``.
    TypeError
        If an element is neither ``str`` nor ``Size``.
    """
    if tiers is None:
        tiers = DEFAULT_TIERS
    result: list[tuple[str, Size]] = []
    for t in tiers:
        if isinstance(t, str):
            if t not in NAMED_TIERS:
                raise ValueError(
                    f"unknown tier name: {t!r}. "
                    f"Known: {sorted(NAMED_TIERS)}"
                )
            result.append((t, NAMED_TIERS[t]))
        elif isinstance(t, Size):
            result.append((f"custom-{t.width}x{t.height}", t))
        else:
            raise TypeError(
                f"tier must be str or Size, got {type(t).__name__}: {t!r}"
            )
    return result


def slug_from_url(url: str) -> str:
    """
    Derive a filesystem-safe slug from a URL.

    Lowercased, non-alphanumeric characters collapsed to single hyphens,
    leading/trailing hyphens stripped. File-extension suffixes like
    ``.html`` / ``.php`` are removed so slugs for ``page.html`` and
    ``page`` collide (usually what you want).

    >>> slug_from_url('https://example.com/')
    'andyed-github-io-marginalia'
    >>> slug_from_url('https://example.com/path/to/page.html')
    'example-com-path-to-page'
    >>> slug_from_url('file:///tmp/demo.html')
    'tmp-demo'
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path
    # For file:// URLs without a netloc, use the path
    if not host and path:
        host = ""
    path = path.rstrip("/")
    path = re.sub(r"\.(html?|php|asp|aspx)$", "", path, flags=re.IGNORECASE)
    combined = f"{host}{path}"
    slug = re.sub(r"[^a-z0-9]+", "-", combined.lower())
    slug = slug.strip("-")
    return slug or "capture"


# ─── Main capture ────────────────────────────────────────────────────────

def capture_responsive(
    url: str,
    tiers: Optional[Sequence[Union[str, Size]]] = None,
    output_dir: Union[str, Path] = ".",
    slug: Optional[str] = None,
    device_scale_factor: int = 2,
    color_scheme: Optional[str] = None,
    full_page: bool = False,
    wait_for_fonts: bool = True,
    network_idle: bool = True,
    selector: Optional[str] = None,
    timeout_ms: int = 30000,
    verbose: bool = True,
) -> list[Path]:
    """
    Capture a URL at every tier and return the paths of the PNGs written.

    Parameters
    ----------
    url : str
        URL or ``file://`` path to capture.
    tiers : sequence of str or Size, optional
        Tier names (from ``NAMED_TIERS``) or explicit ``Size`` tuples.
        Defaults to ``DEFAULT_TIERS`` — ``('mobile', 'tablet', 'laptop',
        'desktop')``.
    output_dir : str or Path
        Directory to write PNGs. Created if it doesn't exist.
    slug : str, optional
        Filesystem-safe identifier for this capture. If ``None``, derived
        from the URL via ``slug_from_url()``.
    device_scale_factor : int
        Retina scale factor. Default 2. Use 1 for 1× captures, 3 for
        super-retina (physical iPhone-Pro simulation).
    color_scheme : {'dark', 'light', None}
        Force a color scheme via Playwright's ``emulate_media``. ``None``
        leaves the page's own default.
    full_page : bool
        If ``True``, capture the entire scrollable page, not just the
        viewport. Mutually exclusive with ``selector``.
    wait_for_fonts : bool
        If ``True``, wait for ``document.fonts.ready`` before screenshotting.
        Recommended unless you know the site has no webfonts.
    network_idle : bool
        If ``True``, wait for 500ms of network silence after navigation
        (``wait_until='networkidle'``). If ``False``, wait only for
        ``DOMContentLoaded`` — faster but less reliable for JS-heavy sites.
    selector : str, optional
        CSS selector to clip the screenshot to a single element.
        Mutually exclusive with ``full_page``.
    timeout_ms : int
        Per-tier timeout in milliseconds for page navigation. Default 30000.
    verbose : bool
        Print a one-line status per tier to stdout (PASS) or stderr (FAIL).

    Returns
    -------
    list[Path]
        Paths of successfully written PNGs, in tier order. Missing
        entries mean that tier failed — inspect stderr for per-tier errors.

    Raises
    ------
    ImportError
        If Playwright is not installed. Clean error with install
        instructions.
    CaptureError
        If Chromium isn't installed, or Playwright hits an unrecoverable
        error before any tier screenshot could be attempted.
    ValueError
        If ``full_page`` and ``selector`` are both set, or if a tier
        name is unknown.
    """
    try:
        from playwright.sync_api import (
            Error as PlaywrightError,
            sync_playwright,
        )
    except ImportError as exc:
        raise ImportError(
            "Playwright is not installed. Install with:\n"
            "    pip install playwright\n"
            "    playwright install chromium"
        ) from exc

    if full_page and selector:
        raise ValueError("full_page and selector are mutually exclusive")

    resolved = resolve_tiers(tiers)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if slug is None:
        slug = slug_from_url(url)

    written: list[Path] = []
    wait_until = "networkidle" if network_idle else "domcontentloaded"

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except PlaywrightError as exc:
                msg = str(exc)
                if "Executable doesn't exist" in msg or "not found" in msg.lower():
                    raise CaptureError(
                        "Chromium is not installed for Playwright. Run:\n"
                        "    playwright install chromium"
                    ) from exc
                raise CaptureError(f"Playwright launch error: {exc}") from exc

            try:
                for tier_name, size in resolved:
                    context = browser.new_context(
                        viewport={"width": size.width, "height": size.height},
                        device_scale_factor=device_scale_factor,
                    )
                    try:
                        page = context.new_page()
                        if color_scheme:
                            page.emulate_media(color_scheme=color_scheme)

                        # Navigation
                        try:
                            page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                        except PlaywrightError as exc:
                            if verbose:
                                print(
                                    f"  FAIL {tier_name:<16} {size}  "
                                    f"load failed: {exc}",
                                    file=sys.stderr,
                                )
                            continue

                        # Font readiness — the main gotcha from channels/web.md
                        if wait_for_fonts:
                            try:
                                page.evaluate("() => document.fonts.ready")
                            except PlaywrightError:
                                pass  # older browsers lack document.fonts

                        # Build the target filename
                        filename = (
                            f"{slug}-{tier_name}-{size.width}x{size.height}.png"
                        )
                        out_path = out_dir / filename

                        # Screenshot — element, viewport, or full page
                        try:
                            if selector:
                                locator = page.locator(selector)
                                locator.screenshot(path=str(out_path))
                            else:
                                page.screenshot(
                                    path=str(out_path),
                                    full_page=full_page,
                                )
                        except PlaywrightError as exc:
                            if verbose:
                                print(
                                    f"  FAIL {tier_name:<16} {size}  "
                                    f"screenshot failed: {exc}",
                                    file=sys.stderr,
                                )
                            continue

                        written.append(out_path)
                        if verbose:
                            print(
                                f"  PASS {tier_name:<16} {size}  → {out_path}"
                            )
                    finally:
                        context.close()
            finally:
                browser.close()
    except CaptureError:
        raise
    except PlaywrightError as exc:
        raise CaptureError(f"Playwright error: {exc}") from exc

    return written


# ─── CLI ─────────────────────────────────────────────────────────────────

def _main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m muriel.capture",
        description=(
            "Responsive screenshot sweep: capture a URL at mobile, tablet, "
            "laptop, and desktop viewport sizes in one command. Built on "
            "Playwright."
        ),
    )
    parser.add_argument("url", help="URL or file:// path to capture.")
    parser.add_argument(
        "--tiers", nargs="+", default=list(DEFAULT_TIERS),
        help=(
            f"Tier names to capture (default: {' '.join(DEFAULT_TIERS)}). "
            f"Known: {', '.join(sorted(NAMED_TIERS))}."
        ),
    )
    parser.add_argument(
        "--dir", "--output-dir", dest="output_dir", default=".",
        help="Output directory for PNGs. Default: current directory.",
    )
    parser.add_argument(
        "--slug", default=None,
        help="Filename slug. Default: derived from URL host + path.",
    )
    parser.add_argument(
        "--scale", type=int, default=2,
        help="Device scale factor. Default: 2 (retina).",
    )
    parser.add_argument(
        "--dark", action="store_const", const="dark", dest="color_scheme",
        help="Force dark color scheme via prefers-color-scheme emulation.",
    )
    parser.add_argument(
        "--light", action="store_const", const="light", dest="color_scheme",
        help="Force light color scheme.",
    )
    parser.add_argument(
        "--full-page", action="store_true",
        help="Capture the entire scrollable page, not just the viewport.",
    )
    parser.add_argument(
        "--selector", default=None,
        help="CSS selector to clip the screenshot to a single element.",
    )
    parser.add_argument(
        "--no-fonts", dest="wait_for_fonts", action="store_false",
        help="Skip waiting for document.fonts.ready (faster, less reliable).",
    )
    parser.add_argument(
        "--no-idle", dest="network_idle", action="store_false",
        help="Wait only for DOMContentLoaded, not network idle.",
    )
    parser.add_argument(
        "--timeout", type=int, default=30000,
        help="Per-tier navigation timeout in ms. Default: 30000.",
    )
    parser.add_argument(
        "--quiet", "-q", dest="verbose", action="store_false",
        help="Suppress per-tier status output.",
    )
    args = parser.parse_args(argv)

    if args.verbose:
        print(f"\nCapturing {args.url}")
        print(f"  tiers:    {' '.join(args.tiers)}")
        print(f"  output:   {args.output_dir}")
        print(f"  scale:    {args.scale}×")
        if args.color_scheme:
            print(f"  scheme:   {args.color_scheme}")
        if args.selector:
            print(f"  selector: {args.selector}")
        if args.full_page:
            print(f"  mode:     full page")
        print()

    try:
        written = capture_responsive(
            url=args.url,
            tiers=args.tiers,
            output_dir=args.output_dir,
            slug=args.slug,
            device_scale_factor=args.scale,
            color_scheme=args.color_scheme,
            full_page=args.full_page,
            selector=args.selector,
            wait_for_fonts=args.wait_for_fonts,
            network_idle=args.network_idle,
            timeout_ms=args.timeout,
            verbose=args.verbose,
        )
    except ImportError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 2
    except (ValueError, TypeError) as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 2
    except CaptureError as exc:
        print(f"\n{exc}", file=sys.stderr)
        return 2

    expected = len(resolve_tiers(args.tiers))
    if args.verbose:
        print(f"\n  wrote {len(written)}/{expected} files")
    return 0 if len(written) == expected else 1


if __name__ == "__main__":
    raise SystemExit(_main())
