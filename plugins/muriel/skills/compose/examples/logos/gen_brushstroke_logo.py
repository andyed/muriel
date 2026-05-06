"""
Brushstroke / chop logo generator — Direction D.

Single elegant M rendered like a traditional maker's chop: warm gold
glyph on near-black, ink-splatter accents, serif wordmark below.
Minimal scaffolding; lets the mark breathe.

1200×630 OG size.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, random

W, H = 1200, 630

# ── Palette ───────────────────────────────────────────────────────────────
BG = (12, 10, 14)            # near-black with a whisper of warmth
GOLD = (226, 176, 84)         # warm brushed gold
GOLD_BRIGHT = (246, 206, 110)
GOLD_DIM = (142, 108, 48)
CREAM = (238, 232, 210)

EMBLEM_FONT_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc',  2),  # Bodoni Bold
    ('/System/Library/Fonts/Supplemental/Rockwell.ttc',   2),
    ('/System/Library/Fonts/Times.ttc',                   1),
]
WORDMARK_FONT_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc',  0),  # Bodoni Book
    ('/System/Library/Fonts/Times.ttc',                   0),
    ('/System/Library/Fonts/Supplemental/Georgia.ttf',    0),
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'brushstroke')


# ── Font helpers ──────────────────────────────────────────────────────────
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


def emblem_font(size): return _load(EMBLEM_FONT_CANDIDATES, size)
def wordmark_font(size): return _load(WORDMARK_FONT_CANDIDATES, size)


def measure(font, text):
    tmp = Image.new('RGB', (1, 1))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb


# ── Brush-like ink render ─────────────────────────────────────────────────
def draw_inked_letter(letter, cx, cy, font, color, displacement=2):
    """Render a letter with slight displacement-layered copies to mimic
    hand-brushed ink edges. Returns RGBA layer."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), letter, font=font)
    lw, lh = bb[2] - bb[0], bb[3] - bb[1]
    x = cx - lw // 2 - bb[0]
    y = cy - lh // 2 - bb[1]

    # Build an edge-softened inkprint by overlaying 4 slightly displaced
    # semi-transparent renders, then one bright sharp pass on top.
    rng = random.Random(sum(ord(c) for c in letter))
    for _ in range(4):
        dx = rng.randint(-displacement, displacement)
        dy = rng.randint(-displacement, displacement)
        d.text((x + dx, y + dy), letter, fill=(*color, 110), font=font)
    d.text((x, y), letter, fill=(*color, 255), font=font)
    return layer, (x + bb[0], y + bb[1], x + bb[2], y + bb[3])


def add_ink_splatter(img, center, radius_range, accent, seed):
    """Scatter small gold specks around a center point — ink-splatter accent."""
    draw = ImageDraw.Draw(img)
    rng = random.Random(seed)
    cx, cy = center
    r_min, r_max = radius_range
    for _ in range(28):
        # Polar scatter, biased outward
        r = rng.uniform(r_min, r_max)
        theta = rng.uniform(0, 6.2832)
        x = cx + int(r * (rng.random() ** 0.5) * (1 if rng.random() > 0.5 else -1) * 0 + r * (2 * rng.random() - 1) * 0.6)
        # simpler scatter:
        x = cx + int(r * (rng.random() * 2 - 1))
        y = cy + int(r * (rng.random() * 2 - 1))
        size = rng.choice([1, 1, 2, 2, 3, 5])
        alpha = rng.randint(120, 220)
        color = accent if size <= 2 else tuple(min(255, c + 20) for c in accent)
        draw.ellipse([x - size, y - size, x + size, y + size],
                     fill=(*color, alpha))


def draw_brush_bar(img, cx, y, width, accent, height=3):
    """Horizontal gold bar — calligraphic punctuation below the wordmark."""
    draw = ImageDraw.Draw(img, 'RGBA')
    x1, x2 = cx - width // 2, cx + width // 2
    # Solid bar with tapered ends
    for step in range(height):
        a = int(230 * (1 - step / height))
        draw.line([(x1 + 4, y + step), (x2 - 4, y + step)], fill=(*accent, a), width=1)
    # Small end dots
    r = 3
    draw.ellipse([x1 - r, y - r + height // 2, x1 + r, y + r + height // 2], fill=(*accent, 230))
    draw.ellipse([x2 - r, y - r + height // 2, x2 + r, y + r + height // 2], fill=(*accent, 230))


# ── Composer ──────────────────────────────────────────────────────────────
def generate(text="MURIEL",
             subtitle="SCRIPTABLE VISUAL PRODUCTION TOOLKIT",
             subtitle2="FOR RESEARCHER-DESIGNER-ENGINEERS"):
    base = Image.new('RGBA', (W, H), BG + (255,))

    # Very subtle paper grain via random noise layer
    grain = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    rng = random.Random(13)
    for _ in range(4000):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        a = rng.randint(3, 10)
        gd.point((x, y), fill=(255, 240, 220, a))
    base = Image.alpha_composite(base, grain)

    # ── Emblem (big M) ──────────────────────────────────────────────────
    letter = text[0]
    ef = emblem_font(360)
    emblem_cx, emblem_cy = W // 2, int(H * 0.36)

    # Soft glow halo first (background bloom)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    bb = gd.textbbox((0, 0), letter, font=ef)
    gx = emblem_cx - (bb[2] - bb[0]) // 2 - bb[0]
    gy = emblem_cy - (bb[3] - bb[1]) // 2 - bb[1]
    gd.text((gx, gy), letter, fill=(*GOLD, 90), font=ef)
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    base = Image.alpha_composite(base, glow)

    # Inked letter with displacement softening
    inked, ebbox = draw_inked_letter(letter, emblem_cx, emblem_cy, ef, GOLD, displacement=3)
    base = Image.alpha_composite(base, inked)

    # Bright highlight pass (hint of sheen)
    sheen_src = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen_src)
    sd.text((gx, gy - 2), letter, fill=(*GOLD_BRIGHT, 110), font=ef)
    # Mask sheen to only top half of the letter
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rectangle([0, 0, W, emblem_cy], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(12))
    sheen_src.putalpha(ImageChops.multiply(sheen_src.split()[3], mask))
    base = Image.alpha_composite(base, sheen_src)

    # ── Ink splatters flanking the M ────────────────────────────────────
    splat_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    add_ink_splatter(splat_layer, (ebbox[0] - 60, emblem_cy), (20, 140), GOLD, 1)
    add_ink_splatter(splat_layer, (ebbox[2] + 60, emblem_cy), (20, 140), GOLD, 2)
    base = Image.alpha_composite(base, splat_layer)

    # ── Brush bar below the emblem ──────────────────────────────────────
    bar_y = ebbox[3] + 28
    draw_brush_bar(base, W // 2, bar_y, 240, GOLD_BRIGHT)

    # ── Wordmark ────────────────────────────────────────────────────────
    wf = wordmark_font(70)
    tw, th, tbb = measure(wf, text)
    tx = (W - tw) // 2 - tbb[0]
    ty = bar_y + 24 - tbb[1]
    ImageDraw.Draw(base).text((tx, ty), text, fill=(*CREAM, 245), font=wf)

    # ── Subtitles ───────────────────────────────────────────────────────
    sf1 = wordmark_font(22)
    sf2 = wordmark_font(18)
    tbx2 = ty + th
    if subtitle:
        sw, sh, _ = measure(sf1, subtitle)
        ImageDraw.Draw(base).text(((W - sw) // 2, tbx2 + 16), subtitle, fill=(180, 170, 150), font=sf1)
        tbx2 += sh + 28
    if subtitle2:
        sw2, _, _ = measure(sf2, subtitle2)
        ImageDraw.Draw(base).text(((W - sw2) // 2, tbx2), subtitle2, fill=(140, 130, 112), font=sf2)

    # Flatten and save
    final = Image.new('RGB', (W, H), BG)
    final.paste(base, (0, 0), base)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, f'brushstroke-logo-{text.lower()}.png')
    final.save(out, 'PNG')
    print(f"  → {out}")
    return out


if __name__ == '__main__':
    print(f"Generating brushstroke logo → {OUTPUT_DIR}\n")
    generate()
    print("\nDone.")
