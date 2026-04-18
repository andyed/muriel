"""
Circuit-board wireframe logo generator.
1200×630 OG images: dark background, PCB traces, wireframe letterforms.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os, random

W, H = 1200, 630
BG = (26, 26, 46)

FONT_PATHS = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
    '/System/Library/Fonts/SFCompact.ttf',
]

# Emblem font candidates as (path, face_index) tuples — chosen for
# fat slab-serif or heavy display-serif weight so there's visible
# interior space for the PCB pattern.
EMBLEM_FONT_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Rockwell.ttc',   2),  # Rockwell Bold (slab)
    ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc',  2),  # Bodoni 72 Bold (display)
    ('/System/Library/Fonts/Supplemental/Arial Black.ttf', 0),
]

LOGOS = [
    {
        "text": "MURIEL",
        "subtitle": "SCRIPTABLE VISUAL PRODUCTION TOOLKIT",
        "subtitle2": "FOR RESEARCHER-DESIGNER-ENGINEERS",
        "accent": (212, 168, 67),
    },
    {
        "text": "PSYCHODELI",
        "subtitle": "GENERATIVE ART ENGINE",
        "accent": (180, 100, 255),
    },
    {
        "text": "SCRUTINIZER",
        "subtitle": "FOVEATED VISION SIMULATOR",
        "accent": (100, 200, 180),
    },
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'circuit-logos')


# ── Font helpers ────────────────────────────────────────────────────────────

def find_font(size, bold=True):
    for p in FONT_PATHS:
        if os.path.exists(p):
            idx = 1 if (bold and p.endswith('.ttc')) else 0
            return ImageFont.truetype(p, size, index=idx)
    return ImageFont.load_default()


def find_emblem_font(size):
    """Find a fat serif/slab font for the emblem letter."""
    for p, idx in EMBLEM_FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=idx)
            except OSError:
                try:
                    return ImageFont.truetype(p, size)
                except OSError:
                    continue
    return find_font(size, bold=True)


def measure(font, text):
    """Return (w, h, raw_bbox) using a throw-away canvas."""
    tmp = Image.new('RGB', (1, 1))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def auto_fit_font(text, max_w, base_size, bold=True):
    font = find_font(base_size, bold)
    w, _, _ = measure(font, text)
    if w > max_w:
        font = find_font(int(base_size * max_w / w), bold)
    return font


# ── Contrast helpers ────────────────────────────────────────────────────────

def _linearize(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return 0.2126 * _linearize(rgb[0]) + 0.7152 * _linearize(rgb[1]) + 0.0722 * _linearize(rgb[2])


def contrast_ratio(fg, bg):
    l1, l2 = luminance(fg), luminance(bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def ensure_contrast(accent, bg, min_ratio=10.0):
    """Uniformly brighten accent until contrast >= min_ratio vs bg."""
    r, g, b = accent
    for boost in range(0, 130, 2):
        c = (min(255, r + boost), min(255, g + boost), min(255, b + boost))
        if contrast_ratio(c, bg) >= min_ratio:
            return c
    return (min(255, r + 128), min(255, g + 128), min(255, b + 128))


# ── Layer builders ──────────────────────────────────────────────────────────

def add_grid(img, accent):
    """Faint PCB substrate grid lines drawn directly onto img."""
    draw = ImageDraw.Draw(img)
    gc = tuple(max(0, int(c * 0.13)) for c in accent)
    for x in range(0, W, 40):
        draw.line([(x, 0), (x, H)], fill=gc, width=1)
    for y in range(0, H, 40):
        draw.line([(0, y), (W, y)], fill=gc, width=1)


def add_circuit_traces(img, tbx, accent, seed_str):
    """L-shaped PCB traces + via nodes drawn directly onto img."""
    draw = ImageDraw.Draw(img)
    rng = random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(seed_str)))

    tc = tuple(int(c * 0.45) for c in accent)  # dim trace color
    nc = accent                                  # node fill (full accent)

    x1, y1, x2, y2 = tbx
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

    def clamp(x, y):
        return max(10, min(W - 10, x)), max(10, min(H - 10, y))

    vias = []
    # Top band (above text)
    for _ in range(10):
        vias.append(clamp(rng.randint(20, W - 20), rng.randint(12, max(12, y1 - 8))))
    # Bottom band
    for _ in range(10):
        vias.append(clamp(rng.randint(20, W - 20), rng.randint(min(H - 12, y2 + 8), H - 12)))
    # Left side
    for _ in range(5):
        vias.append(clamp(rng.randint(10, max(10, x1 - 8)), rng.randint(12, H - 12)))
    # Right side
    for _ in range(5):
        vias.append(clamp(rng.randint(min(W - 10, x2 + 8), W - 10), rng.randint(12, H - 12)))
    # Anchors radiating from text bbox corners / midpoints
    for ax, ay in [(x1, y1), (x2, y1), (x1, y2), (x2, y2),
                   (cx, y1), (cx, y2), (x1, cy), (x2, cy)]:
        dx, dy = ax - cx, ay - cy
        ex = ax + int(dx * rng.uniform(0.25, 0.65)) + rng.randint(-15, 15)
        ey = ay + int(dy * rng.uniform(0.25, 0.65)) + rng.randint(-15, 15)
        vias.append(clamp(ax, ay))
        vias.append(clamp(ex, ey))
    # Full-canvas scatter
    for _ in range(8):
        vias.append(clamp(rng.randint(10, W - 10), rng.randint(10, H - 10)))

    # Connect each via to its 2 nearest neighbours with L-shaped traces
    drawn = set()
    for i, (px, py) in enumerate(vias):
        nearest = sorted((abs(px - qx) + abs(py - qy), j)
                         for j, (qx, qy) in enumerate(vias) if j != i)
        for _, j in nearest[:2]:
            key = (min(i, j), max(i, j))
            if key in drawn:
                continue
            drawn.add(key)
            qx, qy = vias[j]
            draw.line([(px, py), (qx, py)], fill=tc, width=1)  # horizontal
            draw.line([(qx, py), (qx, qy)], fill=tc, width=1)  # vertical
            br = 3
            draw.ellipse([qx - br, py - br, qx + br, py + br], fill=nc)

    # Via nodes at each point
    for px, py in vias:
        r = rng.choice([3, 4, 5])
        draw.ellipse([px - r, py - r, px + r, py + r], fill=nc)
        draw.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], outline=tc, width=1)


def make_glow(text, tx, ty, font, accent, radius, alpha):
    """RGBA layer: solid text Gaussian-blurred to create glow halo."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((tx, ty), text, fill=(*accent, alpha), font=font)
    return layer.filter(ImageFilter.GaussianBlur(radius))


def make_wireframe(text, tx, ty, font, accent, stroke_w):
    """RGBA layer: transparent-fill text with accent-colored stroke outline."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (tx, ty), text,
        fill=(0, 0, 0, 0),
        font=font,
        stroke_width=stroke_w,
        stroke_fill=(*accent, 255),
    )
    return layer


def make_emblem(letter, cx, cy, font, accent, stroke_w=5):
    """Build the decorative emblem letter with interior PCB pattern.

    Returns an RGBA layer with:
      - Cross-hatch grid clipped to the letterform
      - Glowing nodes at selected interior grid intersections
      - Gold stroke outline
      - Soft glow halo behind the letter
    """
    # 1) Solid-fill mask of the letter (white on black) for clipping.
    tmp = Image.new('L', (W, H), 0)
    dtmp = ImageDraw.Draw(tmp)
    bb = dtmp.textbbox((0, 0), letter, font=font)
    lw, lh = bb[2] - bb[0], bb[3] - bb[1]
    ex = cx - lw // 2 - bb[0]
    ey = cy - lh // 2 - bb[1]
    dtmp.text((ex, ey), letter, fill=255, font=font)
    mask = tmp  # L-mode

    # 2) Interior PCB: cross-hatch grid + nodes drawn onto an RGBA canvas,
    #    then masked to the letterform.
    interior = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dint = ImageDraw.Draw(interior)
    grid_color = tuple(int(c * 0.55) for c in accent) + (180,)
    node_color = (*accent, 255)
    bright = tuple(min(255, c + 40) for c in accent) + (255,)

    # Bbox of the filled letter in canvas coords for grid bounds.
    lx1, ly1 = ex + bb[0], ey + bb[1]
    lx2, ly2 = ex + bb[2], ey + bb[3]

    # Vertical grid lines
    for x in range(lx1, lx2, 14):
        dint.line([(x, ly1), (x, ly2)], fill=grid_color, width=1)
    # Horizontal grid lines
    for y in range(ly1, ly2, 14):
        dint.line([(lx1, y), (lx2, y)], fill=grid_color, width=1)
    # Diagonal grid lines (sparser — gives the cross-hatch feel)
    for off in range(-lh, lw, 28):
        dint.line([(lx1 + off, ly1), (lx1 + off + lh, ly2)], fill=grid_color, width=1)
    for off in range(0, lw + lh, 28):
        dint.line([(lx1 + off, ly1), (lx1 + off - lh, ly2)], fill=grid_color, width=1)

    # Fewer, brighter nodes — collect candidate grid intersections, subsample,
    # then connect them with L-shaped traces to feel like real PCB routing
    # rather than a uniform grid.
    rng = random.Random(sum(ord(c) for c in letter) + 777)
    candidates = [(x, y) for x in range(lx1, lx2, 14) for y in range(ly1, ly2, 14)]
    rng.shuffle(candidates)
    n_nodes = max(5, min(10, len(candidates) // 14))
    nodes = candidates[:n_nodes]

    # L-shaped traces connecting each node to its nearest neighbour
    trace_color = tuple(int(c * 0.70) for c in accent) + (230,)
    for i, (px, py) in enumerate(nodes):
        nearest = sorted(
            (abs(px - qx) + abs(py - qy), j)
            for j, (qx, qy) in enumerate(nodes) if j != i
        )
        for _, j in nearest[:1]:
            qx, qy = nodes[j]
            dint.line([(px, py), (qx, py)], fill=trace_color, width=2)
            dint.line([(qx, py), (qx, qy)], fill=trace_color, width=2)

    # Bright node dots on top of the traces
    for i, (x, y) in enumerate(nodes):
        r = rng.choice([4, 5, 6])
        dint.ellipse([x - r, y - r, x + r, y + r], fill=bright)
        dint.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3],
                     outline=(*accent, 220), width=2)

    # Clip interior to the letterform.
    interior.putalpha(ImageChops.multiply(interior.split()[3], mask))

    # 3) Outline stroke — rendered by drawing the letter with stroke_width.
    outline = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(outline).text(
        (ex, ey), letter,
        fill=(0, 0, 0, 0), font=font,
        stroke_width=stroke_w, stroke_fill=(*accent, 255),
    )

    # 4) Soft glow halo.
    glow_src = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow_src).text((ex, ey), letter, fill=(*accent, 110), font=font)
    glow = glow_src.filter(ImageFilter.GaussianBlur(22))

    inner_glow_src = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(inner_glow_src).text((ex, ey), letter, fill=(*accent, 80), font=font)
    inner_glow = inner_glow_src.filter(ImageFilter.GaussianBlur(7))

    # Compose glow + interior + outline (bottom → top)
    emblem = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    emblem = Image.alpha_composite(emblem, glow)
    emblem = Image.alpha_composite(emblem, inner_glow)
    emblem = Image.alpha_composite(emblem, interior)
    emblem = Image.alpha_composite(emblem, outline)
    return emblem, (lx1, ly1, lx2, ly2)


# ── Generator ───────────────────────────────────────────────────────────────

def generate_logo(logo_def):
    text     = logo_def['text']
    subtitle  = logo_def.get('subtitle', '')
    subtitle2 = logo_def.get('subtitle2', '')
    cream     = (238, 232, 210)

    # Enforce contrast — target 10:1 for headroom against glow-brightened BG
    accent = ensure_contrast(logo_def['accent'], BG, min_ratio=10.0)
    cr = contrast_ratio(accent, BG)
    cr_cream = contrast_ratio(cream, BG)
    boosted = ' (boosted)' if accent != logo_def['accent'] else ''
    print(f"  [{text}] accent {accent}{boosted} → {cr:.2f}:1 | cream → {cr_cream:.2f}:1")
    assert cr >= 8.0,       f"accent contrast {cr:.2f} < 8.0"
    assert cr_cream >= 8.0, f"cream contrast {cr_cream:.2f} < 8.0"

    # Fonts — emblem big at top, wordmark smaller below, subtitles bottom
    emblem_letter = text[0]
    emblem_font = find_emblem_font(320)
    ebb = measure(emblem_font, emblem_letter)
    emblem_h = ebb[1]

    title_font = auto_fit_font(text, int(W * 0.55), 96, bold=True)
    tw, th, tbb = measure(title_font, text)

    sub_font  = auto_fit_font(subtitle,  int(W * 0.60), 22, bold=False) if subtitle  else None
    sub2_font = auto_fit_font(subtitle2, int(W * 0.55), 18, bold=False) if subtitle2 else None

    sub_h  = measure(sub_font,  subtitle)[1]  if sub_font  and subtitle  else 0
    sub2_h = measure(sub2_font, subtitle2)[1] if sub2_font and subtitle2 else 0

    # Layout: emblem · gap · wordmark · gap · subtitle · small gap · subtitle2
    gap_emblem = 24
    gap1, gap2 = 14, 8
    total_h = emblem_h + gap_emblem + th + (gap1 + sub_h if sub_h else 0) + (gap2 + sub2_h if sub2_h else 0)

    top = (H - total_h) // 2
    emblem_cx = W // 2
    emblem_cy = top + emblem_h // 2

    # Wordmark positioned directly under the emblem
    desired_top = top + emblem_h + gap_emblem
    ty = desired_top - tbb[1]
    tx = (W - tw) // 2 - tbb[0]
    tbx = (tx + tbb[0], ty + tbb[1], tx + tbb[2], ty + tbb[3])

    # ── Compose layers ───────────────────────────────────────────────────────
    base = Image.new('RGBA', (W, H), BG + (255,))
    add_grid(base, accent)

    # Route traces around the combined emblem+wordmark region
    emblem_bbox_canvas = (emblem_cx - ebb[0] // 2 - 40, emblem_cy - emblem_h // 2,
                         emblem_cx + ebb[0] // 2 + 40, emblem_cy + emblem_h // 2)
    combined_bbox = (
        min(emblem_bbox_canvas[0], tbx[0]),
        emblem_bbox_canvas[1],
        max(emblem_bbox_canvas[2], tbx[2]),
        tbx[3],
    )
    add_circuit_traces(base, combined_bbox, accent, text)

    # Emblem layer (glow + interior PCB + outline) — stroke bumped for presence
    emblem_layer, emblem_text_bbox = make_emblem(
        emblem_letter, emblem_cx, emblem_cy, emblem_font, accent,
        stroke_w=max(5, int(emblem_h * 0.018)),
    )
    base = Image.alpha_composite(base, emblem_layer)

    # Wordmark glow + outline
    base = Image.alpha_composite(base, make_glow(text, tx, ty, title_font, accent, 14, 140))
    base = Image.alpha_composite(base, make_glow(text, tx, ty, title_font, accent,  5,  85))
    stroke_w = max(2, th // 48)
    base = Image.alpha_composite(base, make_wireframe(text, tx, ty, title_font, accent, stroke_w))

    # ── Overlay draw (on top of all compositing) ─────────────────────────────
    draw = ImageDraw.Draw(base)

    # Bright accent nodes at text bbox corners
    bright = tuple(min(255, c + 55) for c in accent)
    bx1, by1, bx2, by2 = tbx
    for px, py in [(bx1, by1), (bx2, by1), (bx1, by2), (bx2, by2),
                   ((bx1 + bx2) // 2, by1), ((bx1 + bx2) // 2, by2)]:
        r = 5
        draw.ellipse([px - r, py - r, px + r, py + r], fill=bright)
        draw.ellipse([px - r - 2, py - r - 2, px + r + 2, py + r + 2], outline=accent, width=1)

    # Subtitles
    sub_y = desired_top + th + gap1
    if sub_font and subtitle:
        sw = measure(sub_font, subtitle)[0]
        draw.text(((W - sw) // 2, sub_y), subtitle, fill=cream, font=sub_font)
        sub_y += sub_h + gap2
    if sub2_font and subtitle2:
        sw2 = measure(sub2_font, subtitle2)[0]
        dim = tuple(int(c * 0.82) for c in cream)   # slightly dimmer, still >> 8:1
        draw.text(((W - sw2) // 2, sub_y), subtitle2, fill=dim, font=sub2_font)

    # ── Flatten and save ─────────────────────────────────────────────────────
    final = Image.new('RGB', (W, H), BG)
    final.paste(base, (0, 0), base)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f'circuit-logo-{text.lower()}.png')
    final.save(out_path, 'PNG')
    print(f"  → {out_path}")
    return out_path


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print(f"Generating circuit logos → {OUTPUT_DIR}\n")
    for logo in LOGOS:
        generate_logo(logo)
    print("\nDone.")
