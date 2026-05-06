"""
Colophon logo generator — MIT Press / Muriel Cooper heritage.

Muriel Cooper designed the MIT Press colophon (1962): seven vertical
bars derived from the letterforms of "mitpress", forming one of the
most iconic publishing marks in modern design. The toolkit is named
after her — the logo references that heritage directly.

This version: six vertical bars, one per letter of M·U·R·I·E·L, with
widths proportional to each letter's visual stroke mass and heights
modulated to echo the ascender/descender rhythm of the original.

MIT red on warm paper; wordmark in lowercase sans below, set tight
per Cooper's Bauhaus sensibility.

1200×630 OG size.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630

# ── Palette ───────────────────────────────────────────────────────────────
# Cooper worked across red/black/white. Options:
#   paper + MIT red          — archival feel
#   near-black + cream mark  — modern
#   MIT red bg + cream mark  — bold
# Default: cream paper, MIT red colophon, dark ink wordmark
PAPER   = (236, 226, 204)
OXBLOOD = (107,  42,  42)        # deep oxblood — bookbinder / letterpress
INK     = ( 18,  18,  18)
INK_SOFT = ( 92,  90,  82)

SANS_CANDIDATES = [
    ('/System/Library/Fonts/Helvetica.ttc', 1),   # Helvetica Bold
    ('/System/Library/Fonts/Helvetica.ttc', 0),
    ('/Library/Fonts/Arial Bold.ttf',       0),
]
SANS_LIGHT_CANDIDATES = [
    ('/System/Library/Fonts/Helvetica.ttc', 0),
    ('/System/Library/Fonts/Supplemental/Arial.ttf', 0),
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'colophon')


def _load(candidates, size):
    for p, idx in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=idx)
            except OSError:
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    continue
    return ImageFont.load_default()


def sans(size):       return _load(SANS_CANDIDATES, size)
def sans_light(size): return _load(SANS_LIGHT_CANDIDATES, size)


def measure(font, text):
    tmp = Image.new('RGB', (1, 1))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb


# ── Colophon mark ────────────────────────────────────────────────────────
# Each entry: (width_units, height_fraction, top_fraction)
# width_units  — bar thickness, proportional to letter visual mass
# height_fraction — bar height as fraction of colophon height
# top_fraction — bar top y as fraction of colophon height
# Chosen to echo Cooper's original: bars of varying weight that
# together compose the mark without spelling out the word literally.
# M-silhouette proportions: outer stems tall, middle four dip to trace
# the top of an M. `float_frac` lifts the bar's bottom above the baseline
# by that fraction of its own total drop — 0 means pinned, 1 means
# centered around the middle.
COLOPHON_BARS = [
    {'name': 'M', 'width': 30, 'h_frac': 1.00, 'float_frac': 0.00},
    {'name': 'U', 'width': 20, 'h_frac': 0.62, 'float_frac': 0.00},
    {'name': 'R', 'width': 20, 'h_frac': 0.30, 'float_frac': 0.00},
    {'name': 'I', 'width':  8, 'h_frac': 0.30, 'float_frac': 0.00},
    {'name': 'E', 'width': 16, 'h_frac': 0.62, 'float_frac': 0.00},
    {'name': 'L', 'width': 10, 'h_frac': 1.00, 'float_frac': 0.00},
]
BAR_GAP = 10


def draw_colophon(img, cx, cy, height, color, bars=None):
    """Render the colophon-style mark centered on (cx, cy)."""
    bars = bars or COLOPHON_BARS
    draw = ImageDraw.Draw(img, 'RGBA')
    total_units = sum(b['width'] for b in bars)
    target_w = int(height * 1.15)
    scale = (target_w - BAR_GAP * (len(bars) - 1)) / total_units
    x = cx - target_w // 2
    top = cy - height // 2
    bot = top + height
    for bar in bars:
        bw = int(bar['width'] * scale)
        bh = int(bar['h_frac'] * height)
        # By default bars are pinned to the bottom (baseline);
        # `float_frac` lifts the bar's bottom by that fraction of its
        # own drop (height - bh), so the bar hovers above the baseline.
        drop = height - bh
        lift = int(bar.get('float_frac', 0.0) * drop)
        by = bot - bh - lift
        draw.rectangle([x, by, x + bw, by + bh], fill=color + (255,))
        x += bw + BAR_GAP


# ── Generator ────────────────────────────────────────────────────────────
def generate(text="MURIEL",
             subtitle="scriptable visual production toolkit",
             subtitle2="for researcher-designer-engineers",
             bars=None,
             name_suffix=''):
    base = Image.new('RGBA', (W, H), PAPER + (255,))

    # Colophon up top
    colophon_h = 280
    colophon_cx, colophon_cy = W // 2, int(H * 0.36)
    draw_colophon(base, colophon_cx, colophon_cy, colophon_h, OXBLOOD,
                  bars=bars)

    # Thin red rule above the wordmark — Bauhaus/MIT Press convention
    rule_y = int(H * 0.65)
    rule_w = 380
    draw = ImageDraw.Draw(base, 'RGBA')
    draw.line([((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
              fill=OXBLOOD + (255,), width=2)

    # Wordmark: Helvetica Bold, lowercase (Cooper's modernist preference)
    wm_text = text.lower()
    wf = sans(76)
    tw, th, tbb = measure(wf, wm_text)
    wty = rule_y + 22 - tbb[1]
    wtx = (W - tw) // 2 - tbb[0]
    draw.text((wtx, wty), wm_text, fill=INK + (255,), font=wf)

    # Subtitles: Helvetica Light, lowercase
    sf1 = sans_light(22)
    sf2 = sans_light(17)
    y_after_wm = rule_y + 22 + th
    if subtitle:
        sw, sh, _ = measure(sf1, subtitle)
        draw.text(((W - sw) // 2, y_after_wm + 18), subtitle, fill=INK + (255,), font=sf1)
        y_after_wm += sh + 30
    if subtitle2:
        sw2, _, _ = measure(sf2, subtitle2)
        draw.text(((W - sw2) // 2, y_after_wm), subtitle2, fill=INK_SOFT, font=sf2)

    # Tiny credit line, bottom-left, in red — "After Muriel Cooper, 1962"
    credit_f = sans_light(11)
    credit = "after muriel cooper · mit press colophon, 1962"
    draw.text((40, H - 30), credit, fill=OXBLOOD + (220,), font=credit_f)

    # Flatten + save
    final = Image.new('RGB', (W, H), PAPER)
    final.paste(base, (0, 0), base)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, f'colophon-logo-{text.lower()}{name_suffix}.png')
    final.save(out, 'PNG')
    print(f"  → {out}")
    return out


# Floating variant — inner four bars have their bottoms lifted by
# 50% of their drop, so they hover above the baseline while their tops
# still trace the M silhouette. Outer stems stay pinned.
COLOPHON_BARS_FLOATING = [
    {'name': 'M', 'width': 30, 'h_frac': 1.00, 'float_frac': 0.00},
    {'name': 'U', 'width': 20, 'h_frac': 0.62, 'float_frac': 0.45},
    {'name': 'R', 'width': 20, 'h_frac': 0.30, 'float_frac': 0.60},
    {'name': 'I', 'width':  8, 'h_frac': 0.30, 'float_frac': 0.60},
    {'name': 'E', 'width': 16, 'h_frac': 0.62, 'float_frac': 0.45},
    {'name': 'L', 'width': 10, 'h_frac': 1.00, 'float_frac': 0.00},
]


if __name__ == '__main__':
    print(f"Generating colophon logo → {OUTPUT_DIR}\n")
    # Default: bars pinned to baseline, tops trace M silhouette
    generate(bars=COLOPHON_BARS, name_suffix='')
    # Floating variant: inner bars hover above the baseline
    generate(bars=COLOPHON_BARS_FLOATING, name_suffix='-floating')
    print("\nDone.")
