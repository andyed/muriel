"""
muriel.dimensions — common screen-size footprints as importable constants.

Code-side companion to ``channels/dimensions.md`` in the muriel repo.
Every table in that file has matching constants here so scripts don't
hardcode magic numbers.

Types
-----

- ``Size(width, height)`` — a NamedTuple with ``.aspect_ratio``,
  ``.aspect_label``, ``.scale()``. String form is ``width×height``.
- ``Device(name, physical, css, scale_factor, family)`` — a device with
  both physical and CSS-pixel sizes.
- ``PaperSize(name, width_in, height_in, width_mm, height_mm)`` — a
  paper size with ``.px_at(dpi)``, ``.px_300dpi``, ``.px_600dpi``.

Module-level constants
----------------------

Social cards, web embeds, video, viewports, paper, academic column
widths, favicon/app-icon sizes. See the markdown file for the full
rationale behind each number.

Registry + lookup
-----------------

Every ``Size`` is also registered in ``REGISTRY`` under a dotted name.
Use ``lookup('twitter.instream')`` for ad-hoc programmatic access, or
import the constants by name for common idioms::

    from muriel.dimensions import TWITTER_INSTREAM, OG_CARD, VIDEO_1080P

    cvs_w, cvs_h = TWITTER_INSTREAM          # → (1600, 900)
    OG_CARD.aspect_ratio                     # → 1.9047619...
    OG_CARD.aspect_label                     # → '1.91:1'
    OG_CARD.scale(2)                         # → Size(2400, 1260)  (retina upload)

    from muriel.dimensions import device
    device('iphone-15-pro').physical          # → Size(1179, 2556)
    device('iphone-15-pro').css              # → Size(393, 852)

    from muriel.dimensions import A4
    A4.px_300dpi                              # → Size(2481, 3507)
    A4.px_at(150)                             # → Size(1240, 1753)

    from muriel.dimensions import figsize_for
    figsize_for('chi', columns=1)             # → (3.33, 2.0)
    figsize_for('ieee', columns=2, aspect=0.5)  # → (7.16, 3.58)

CLI
---

Run the module directly to print the full registry as a table::

    python -m muriel.dimensions
"""

from __future__ import annotations

from typing import NamedTuple

__all__ = [
    # types
    "Size", "Device", "PaperSize",
    # social + web embeds
    "TWITTER_INSTREAM", "TWITTER_SUMMARY",
    "OG_CARD", "LINKEDIN_SHARE", "SUBSTACK_FEATURED",
    "YOUTUBE_THUMBNAIL",
    "INSTAGRAM_SQUARE", "INSTAGRAM_PORTRAIT", "INSTAGRAM_STORY",
    "TIKTOK", "PINTEREST_STANDARD",
    # video
    "VIDEO_1080P", "VIDEO_4K_UHD", "VIDEO_8K_UHD",
    "VIDEO_VERTICAL", "VIDEO_SQUARE", "VIDEO_DCI_4K", "VIDEO_720P",
    # web viewports
    "VIEWPORT_MOBILE_SMALL", "VIEWPORT_MOBILE_STANDARD", "VIEWPORT_MOBILE_LARGE",
    "VIEWPORT_TABLET_PORTRAIT", "VIEWPORT_TABLET_LANDSCAPE",
    "VIEWPORT_TABLET_PRO",
    "VIEWPORT_LAPTOP", "VIEWPORT_LAPTOP_LARGE",
    "VIEWPORT_DESKTOP_FHD", "VIEWPORT_DESKTOP_QHD", "VIEWPORT_DESKTOP_4K",
    "VIEWPORT_ULTRAWIDE_21_9", "VIEWPORT_ULTRAWIDE_32_9",
    "RESPONSIVE_TIER_LIST",
    # paper
    "US_LETTER", "US_LEGAL", "A3", "A4", "A5",
    # academic column widths (inches)
    "CHI_SINGLE_COL_IN", "CHI_DOUBLE_COL_IN",
    "IEEE_SINGLE_COL_IN", "IEEE_DOUBLE_COL_IN",
    "PNAS_SINGLE_COL_IN", "PNAS_DOUBLE_COL_IN",
    "NATURE_SINGLE_COL_IN", "NATURE_DOUBLE_COL_IN",
    "LNCS_COL_IN",
    # favicons + app icons
    "FAVICON_SIZES", "FAVICON_MASKABLE_SIZE",
    "IOS_APP_ICON_MASTER", "IOS_APP_ICON_SIZES",
    "ANDROID_ADAPTIVE_DP", "ANDROID_ADAPTIVE_SAFE_ZONE_DP", "ANDROID_ADAPTIVE_PX",
    # helpers
    "inches_to_px", "mm_to_px", "figsize_for",
    # devices
    "DEVICES", "device",
    # registry
    "REGISTRY", "lookup",
]


# ─── Types ───────────────────────────────────────────────────────────────

class Size(NamedTuple):
    """
    A 2D pixel size ``(width, height)``.

    Convenience properties:
      - ``aspect_ratio``  — float, width / height
      - ``aspect_label``  — short string like ``'16:9'``, ``'1.91:1'``, ``'1:1'``

    Methods:
      - ``scale(factor)`` — return a new Size scaled by a float factor

    The ``__str__`` form uses the ``×`` (U+00D7 multiplication sign), matching
    the naming convention in ``channels/dimensions.md``.
    """
    width: int
    height: int

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    @property
    def aspect_label(self) -> str:
        ar = self.aspect_ratio
        # Common named aspects, in priority order
        named: tuple[tuple[float, str], ...] = (
            (16 / 9,    "16:9"),
            (9 / 16,    "9:16"),
            (16 / 10,   "16:10"),    # MacBook / ChromeBook class
            (10 / 16,   "10:16"),
            (4 / 3,     "4:3"),
            (3 / 4,     "3:4"),
            (1.0,       "1:1"),
            (21 / 9,    "21:9"),
            (9 / 21,    "9:21"),
            (32 / 9,    "32:9"),
            (4 / 5,     "4:5"),
            (2 / 3,     "2:3"),
            (3 / 2,     "3:2"),
            (1.91,      "1.91:1"),   # Open Graph family
            (19.5 / 9,  "~19.5:9"),  # modern iPhone landscape
            (9 / 19.5,  "~9:19.5"),  # modern iPhone portrait
        )
        for target, label in named:
            if abs(ar - target) < 0.015:
                return label
        # Fall back to a numeric ratio
        return f"{ar:.2f}:1"

    def scale(self, factor: float) -> "Size":
        """Return a new Size with each dimension rounded after scaling by factor."""
        return Size(round(self.width * factor), round(self.height * factor))

    def __str__(self) -> str:
        return f"{self.width}×{self.height}"


class Device(NamedTuple):
    """
    A physical device with both physical-pixel and CSS-pixel sizes.

    ``scale_factor`` is the physical/CSS ratio (2 for retina, 3 for
    super-retina, 1 for non-scaled TVs / desktops).

    ``family`` is a loose category tag: ``'apple'``, ``'android'``,
    ``'firetv'``, ``'apple-tv'``. Useful for filtering ``DEVICES``.
    """
    name: str
    physical: Size
    css: Size
    scale_factor: int
    family: str

    @property
    def aspect_ratio(self) -> float:
        return self.physical.aspect_ratio

    @property
    def aspect_label(self) -> str:
        return self.physical.aspect_label


class PaperSize(NamedTuple):
    """
    A paper size in inches and millimeters with DPI → pixel helpers.

    ``px_300dpi`` and ``px_600dpi`` are properties for common print DPIs.
    ``px_at(dpi)`` computes for an arbitrary DPI.
    """
    name: str
    width_in: float
    height_in: float
    width_mm: int
    height_mm: int

    @property
    def px_300dpi(self) -> Size:
        return self.px_at(300)

    @property
    def px_600dpi(self) -> Size:
        return self.px_at(600)

    def px_at(self, dpi: int) -> Size:
        return Size(round(self.width_in * dpi), round(self.height_in * dpi))


# ─── Conversion helpers ──────────────────────────────────────────────────

def inches_to_px(inches: float, dpi: int = 300) -> int:
    """Convert inches to pixels at a given DPI (default 300 for print)."""
    return round(inches * dpi)


def mm_to_px(mm: float, dpi: int = 300) -> int:
    """Convert millimeters to pixels at a given DPI (default 300 for print)."""
    return round(mm / 25.4 * dpi)


# ─── Social cards & web embeds ───────────────────────────────────────────

TWITTER_INSTREAM  = Size(1600, 900)    # 16:9, full-bleed preview, no crop on desktop
TWITTER_SUMMARY   = Size(1200, 628)    # 1.91:1, summary card
OG_CARD           = Size(1200, 630)    # Open Graph default
LINKEDIN_SHARE    = Size(1200, 627)    # effectively OG
SUBSTACK_FEATURED = Size(1200, 630)    # hero image above the post title
YOUTUBE_THUMBNAIL = Size(1280, 720)    # 16:9, max 2 MB
INSTAGRAM_SQUARE  = Size(1080, 1080)   # 1:1, legacy default
INSTAGRAM_PORTRAIT = Size(1080, 1350)  # 4:5, modern feed default
INSTAGRAM_STORY   = Size(1080, 1920)   # 9:16, also Reels
TIKTOK            = Size(1080, 1920)   # 9:16
PINTEREST_STANDARD = Size(1000, 1500)  # 2:3


# ─── Video ───────────────────────────────────────────────────────────────

VIDEO_1080P    = Size(1920, 1080)   # the default
VIDEO_4K_UHD   = Size(3840, 2160)   # 4× pixel count of 1080p
VIDEO_8K_UHD   = Size(7680, 4320)   # rare but useful for downscale headroom
VIDEO_VERTICAL = Size(1080, 1920)   # 9:16 Reels/Shorts/TikTok
VIDEO_SQUARE   = Size(1080, 1080)   # Instagram feed video
VIDEO_DCI_4K   = Size(4096, 2160)   # Cinema DCI (theatrical)
VIDEO_720P     = Size(1280, 720)    # legacy / fallback


# ─── Web viewport tiers (CSS pixels) ─────────────────────────────────────

VIEWPORT_MOBILE_SMALL     = Size(375, 667)    # iPhone SE floor
VIEWPORT_MOBILE_STANDARD  = Size(390, 844)    # iPhone 14/15
VIEWPORT_MOBILE_LARGE     = Size(430, 932)    # iPhone 15 Pro Max, Pixel 8 Pro
VIEWPORT_TABLET_PORTRAIT  = Size(820, 1180)   # iPad 10.9"
VIEWPORT_TABLET_LANDSCAPE = Size(1180, 820)   # iPad rotated
VIEWPORT_TABLET_PRO       = Size(1024, 1366)  # iPad Pro 12.9"
VIEWPORT_LAPTOP           = Size(1280, 800)   # MacBook Air 13"
VIEWPORT_LAPTOP_LARGE     = Size(1440, 900)   # common dev default
VIEWPORT_DESKTOP_FHD      = Size(1920, 1080)  # most common desktop
VIEWPORT_DESKTOP_QHD      = Size(2560, 1440)  # external monitor
VIEWPORT_DESKTOP_4K       = Size(3840, 2160)  # top of the market
VIEWPORT_ULTRAWIDE_21_9   = Size(2560, 1080)  # gaming ultrawide
VIEWPORT_ULTRAWIDE_32_9   = Size(3840, 1080)  # dual-monitor-replacement

#: Minimum recommended responsive-capture tier set for Playwright sweeps.
#: Matches the guidance in ``channels/dimensions.md``.
RESPONSIVE_TIER_LIST: tuple[Size, ...] = (
    VIEWPORT_MOBILE_STANDARD,   # 390 — mobile
    VIEWPORT_TABLET_PORTRAIT,   # 820 — tablet
    VIEWPORT_LAPTOP,            # 1280 — laptop
    VIEWPORT_DESKTOP_FHD,       # 1920 — desktop
)


# ─── Paper sizes ─────────────────────────────────────────────────────────

US_LETTER = PaperSize("US Letter", 8.5,  11.00, 216, 279)
US_LEGAL  = PaperSize("US Legal",  8.5,  14.00, 216, 356)
A3        = PaperSize("A3",       11.69, 16.54, 297, 420)
A4        = PaperSize("A4",        8.27, 11.69, 210, 297)
A5        = PaperSize("A5",        5.83,  8.27, 148, 210)


# ─── Academic column widths (inches) ─────────────────────────────────────

# ACM / CHI / IUI (current acmart template)
CHI_SINGLE_COL_IN  = 3.33
CHI_DOUBLE_COL_IN  = 7.00

# IEEE two-column template
IEEE_SINGLE_COL_IN = 3.50
IEEE_DOUBLE_COL_IN = 7.16

# PNAS
PNAS_SINGLE_COL_IN = 3.42
PNAS_DOUBLE_COL_IN = 7.00

# Nature (narrow format)
NATURE_SINGLE_COL_IN = 3.54
NATURE_DOUBLE_COL_IN = 7.28

# Springer LNCS — single column only
LNCS_COL_IN = 4.80


# Map venue short names to (single, double) column-width pairs.
# LNCS is single-column-only, so both entries point at the same value.
_VENUES: dict[str, tuple[float, float]] = {
    "chi":    (CHI_SINGLE_COL_IN,    CHI_DOUBLE_COL_IN),
    "acm":    (CHI_SINGLE_COL_IN,    CHI_DOUBLE_COL_IN),
    "iui":    (CHI_SINGLE_COL_IN,    CHI_DOUBLE_COL_IN),
    "ieee":   (IEEE_SINGLE_COL_IN,   IEEE_DOUBLE_COL_IN),
    "pnas":   (PNAS_SINGLE_COL_IN,   PNAS_DOUBLE_COL_IN),
    "nature": (NATURE_SINGLE_COL_IN, NATURE_DOUBLE_COL_IN),
    "lncs":   (LNCS_COL_IN,          LNCS_COL_IN),
}


def figsize_for(
    venue: str, columns: int = 1, aspect: float = 0.6,
) -> tuple[float, float]:
    """
    Return a ``(width_in, height_in)`` tuple for matplotlib's ``figsize=``
    that targets an academic venue and column count.

    Parameters
    ----------
    venue : str
        Venue short name. Known values (case-insensitive):
        ``'chi'``, ``'acm'``, ``'iui'`` (same template),
        ``'ieee'``, ``'pnas'``, ``'nature'``, ``'lncs'``.
    columns : int
        1 for single-column (the default — tight figures that live beside
        body text), 2 for double-column / full-width figures that span both
        columns.
    aspect : float
        height / width ratio. Default 0.6 (typical for small multiples).
        Use 0.5 for wider time series, 0.75 for bar charts with legend
        padding, 0.618 for the golden ratio, 1.0 for square.

    Returns
    -------
    (width_in, height_in) : tuple[float, float]
        Suitable for ``plt.subplots(figsize=figsize_for('chi', 1))``.

    Raises
    ------
    ValueError
        If ``venue`` is unknown.

    Examples
    --------
    >>> figsize_for('chi', 1)
    (3.33, 2.0)
    >>> figsize_for('ieee', 2, aspect=0.5)
    (7.16, 3.58)
    >>> figsize_for('nature', 1, aspect=0.618)
    (3.54, 2.19)
    """
    key = venue.lower()
    if key not in _VENUES:
        raise ValueError(
            f"unknown venue: {venue!r}. Known: {sorted(_VENUES)}"
        )
    single, double = _VENUES[key]
    width = double if columns >= 2 else single
    height = round(width * aspect, 2)
    return (width, height)


# ─── Favicon + app icon sizes ────────────────────────────────────────────

#: Web favicon ship-list. All PNG. Include a ``_maskable`` variant of 512
#: for PWAs (separate asset with full-bleed safe zone).
FAVICON_SIZES: tuple[int, ...] = (16, 32, 48, 180, 192, 512)

#: PWA maskable icon size. Requires the central ~80% be meaningful content.
FAVICON_MASKABLE_SIZE: int = 512

#: Master size for iOS app icon. All smaller sizes generate from this.
IOS_APP_ICON_MASTER: int = 1024

#: Full iOS app icon size set to ship.
IOS_APP_ICON_SIZES: tuple[int, ...] = (
    1024, 180, 167, 152, 120, 87, 80, 60, 58, 40, 29, 20,
)

#: Android adaptive icon total size in dp.
ANDROID_ADAPTIVE_DP: int = 108

#: Android adaptive icon safe-zone size (central region containing content).
ANDROID_ADAPTIVE_SAFE_ZONE_DP: int = 72

#: Android adaptive icon at xxxhdpi (4x). 108 dp × 4 = 432 px.
ANDROID_ADAPTIVE_PX: int = 432


# ─── Device displays ─────────────────────────────────────────────────────

DEVICES: dict[str, Device] = {
    # Apple iPhone
    "iphone-15-pro":     Device("iPhone 15 Pro",       Size(1179, 2556), Size(393, 852), 3, "apple"),
    "iphone-15-pro-max": Device("iPhone 15 Pro Max",   Size(1290, 2796), Size(430, 932), 3, "apple"),
    "iphone-15":         Device("iPhone 15 / 14",      Size(1170, 2532), Size(390, 844), 3, "apple"),
    "iphone-se":         Device("iPhone SE",           Size(750,  1334), Size(375, 667), 2, "apple"),
    # Apple iPad
    "ipad-pro-129":      Device("iPad Pro 12.9\"",     Size(2048, 2732), Size(1024, 1366), 2, "apple"),
    "ipad-pro-11":       Device("iPad Pro 11\"",       Size(1668, 2388), Size(834, 1194), 2, "apple"),
    "ipad":              Device("iPad 10.9\"",         Size(1640, 2360), Size(820, 1180), 2, "apple"),
    # Apple Mac
    "mba-13":            Device("MacBook Air 13\"",    Size(2560, 1664), Size(1280, 832), 2, "apple"),
    "mbp-14":            Device("MacBook Pro 14\"",    Size(3024, 1964), Size(1512, 982), 2, "apple"),
    "mbp-16":            Device("MacBook Pro 16\"",    Size(3456, 2234), Size(1728, 1117), 2, "apple"),
    "studio-display":    Device("Studio Display 27\"", Size(5120, 2880), Size(2560, 1440), 2, "apple"),
    "pro-display-xdr":   Device("Pro Display XDR 32\"", Size(6016, 3384), Size(3008, 1692), 2, "apple"),
    "imac-24":           Device("iMac 24\"",           Size(4480, 2520), Size(2240, 1260), 2, "apple"),
    # TV / streaming
    "apple-tv-4k":       Device("Apple TV 4K",         Size(3840, 2160), Size(1920, 1080), 2, "apple-tv"),
    "firetv-hd":         Device("Fire TV (standard)",  Size(1920, 1080), Size(1920, 1080), 1, "firetv"),
    "firetv-4k":         Device("Fire TV 4K",          Size(3840, 2160), Size(3840, 2160), 1, "firetv"),
    # Android
    "pixel-8-pro":       Device("Pixel 8 Pro",         Size(1344, 2992), Size(448, 998), 3, "android"),
}


def device(name: str) -> Device:
    """
    Look up a device by hyphenated short name.

    >>> device('iphone-15-pro').physical
    Size(width=1179, height=2556)
    >>> device('iphone-15-pro').css
    Size(width=393, height=852)
    >>> device('iphone-15-pro').scale_factor
    3

    Raises
    ------
    KeyError
        If ``name`` is not in ``DEVICES``.
    """
    if name not in DEVICES:
        raise KeyError(
            f"unknown device: {name!r}. Known: {sorted(DEVICES)}"
        )
    return DEVICES[name]


# ─── Registry for dotted-name lookup ─────────────────────────────────────

REGISTRY: dict[str, Size] = {
    # Social
    "twitter.instream":   TWITTER_INSTREAM,
    "twitter.summary":    TWITTER_SUMMARY,
    "x.instream":         TWITTER_INSTREAM,   # alias
    "x.summary":          TWITTER_SUMMARY,    # alias
    "og.card":            OG_CARD,
    "linkedin.share":     LINKEDIN_SHARE,
    "substack.featured":  SUBSTACK_FEATURED,
    "youtube.thumbnail":  YOUTUBE_THUMBNAIL,
    "instagram.square":   INSTAGRAM_SQUARE,
    "instagram.portrait": INSTAGRAM_PORTRAIT,
    "instagram.story":    INSTAGRAM_STORY,
    "instagram.reels":    INSTAGRAM_STORY,    # same dimensions
    "tiktok":             TIKTOK,
    "pinterest.standard": PINTEREST_STANDARD,
    # Video
    "video.1080p":   VIDEO_1080P,
    "video.4k":      VIDEO_4K_UHD,
    "video.8k":      VIDEO_8K_UHD,
    "video.vertical": VIDEO_VERTICAL,
    "video.square":  VIDEO_SQUARE,
    "video.dci.4k":  VIDEO_DCI_4K,
    "video.720p":    VIDEO_720P,
    # Viewports
    "viewport.mobile.small":     VIEWPORT_MOBILE_SMALL,
    "viewport.mobile.standard":  VIEWPORT_MOBILE_STANDARD,
    "viewport.mobile.large":     VIEWPORT_MOBILE_LARGE,
    "viewport.tablet.portrait":  VIEWPORT_TABLET_PORTRAIT,
    "viewport.tablet.landscape": VIEWPORT_TABLET_LANDSCAPE,
    "viewport.tablet.pro":       VIEWPORT_TABLET_PRO,
    "viewport.laptop":           VIEWPORT_LAPTOP,
    "viewport.laptop.large":     VIEWPORT_LAPTOP_LARGE,
    "viewport.desktop.fhd":      VIEWPORT_DESKTOP_FHD,
    "viewport.desktop.qhd":      VIEWPORT_DESKTOP_QHD,
    "viewport.desktop.4k":       VIEWPORT_DESKTOP_4K,
    "viewport.ultrawide.21x9":   VIEWPORT_ULTRAWIDE_21_9,
    "viewport.ultrawide.32x9":   VIEWPORT_ULTRAWIDE_32_9,
}


def lookup(name: str) -> Size:
    """
    Look up a ``Size`` by dotted name from ``REGISTRY``.

    >>> lookup('twitter.instream')
    Size(width=1600, height=900)
    >>> lookup('og.card').aspect_label
    '1.91:1'

    Raises
    ------
    KeyError
        If ``name`` is not in ``REGISTRY``.
    """
    if name not in REGISTRY:
        raise KeyError(
            f"{name!r} not in registry. Known: {sorted(REGISTRY.keys())}"
        )
    return REGISTRY[name]


# ─── CLI self-test ──────────────────────────────────────────────────────

def _main(argv=None) -> int:
    """Print the full registry + device list as a sanity check."""
    print("\n── muriel.dimensions — registry ──")
    print(f"{'Name':<30} {'Size':<12} {'Aspect'}")
    print("─" * 58)
    for name in sorted(REGISTRY):
        size = REGISTRY[name]
        print(f"{name:<30} {str(size):<12} {size.aspect_label}")

    print("\n── devices ──")
    print(f"{'Key':<20} {'Name':<24} {'Physical':<12} {'CSS':<12} {'×':<3}")
    print("─" * 74)
    for key in sorted(DEVICES):
        d = DEVICES[key]
        print(f"{key:<20} {d.name:<24} {str(d.physical):<12} {str(d.css):<12} {d.scale_factor}×")

    print("\n── paper sizes ──")
    print(f"{'Name':<12} {'Inches':<14} {'Millimeters':<14} {'300 DPI':<14} {'600 DPI':<14}")
    print("─" * 70)
    for p in (US_LETTER, US_LEGAL, A3, A4, A5):
        ins = f"{p.width_in}×{p.height_in}"
        mms = f"{p.width_mm}×{p.height_mm}"
        print(f"{p.name:<12} {ins:<14} {mms:<14} {str(p.px_300dpi):<14} {str(p.px_600dpi):<14}")

    print("\n── academic figsize examples (width, height in inches) ──")
    for venue in ("chi", "ieee", "pnas", "nature"):
        single = figsize_for(venue, 1)
        double = figsize_for(venue, 2)
        print(f"  {venue:<6} single {single}  double {double}")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
