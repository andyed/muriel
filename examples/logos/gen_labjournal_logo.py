"""
Lab-journal logo generator — Direction C.

Moleskine / engineer's-notebook aesthetic: warm cream paper with
faint graph grid, large serif M drafted with margin annotations
(rulers, measurement callouts, protractor arcs). Targets the
"researcher-designer-engineers" audience directly.

1200×630 OG size.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random

W, H = 1200, 630

# ── Palette ───────────────────────────────────────────────────────────────
PAPER = (232, 220, 196)          # warm cream
PAPER_SHADOW = (212, 196, 164)   # for subtle page-edge shade
GRID_MAJOR = (188, 170, 132)
GRID_MINOR = (214, 200, 172)
INK = (31, 42, 53)               # fountain-pen navy
INK_SOFT = (72, 84, 96)
GRAPHITE = (120, 108, 88)        # pencil annotations
RED_MARGIN = (160, 59, 59)       # margin red

EMBLEM_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc',  2),  # Bodoni Bold
    ('/System/Library/Fonts/Times.ttc',                   1),
    ('/System/Library/Fonts/Supplemental/Georgia Bold.ttf', 0),
]
WORDMARK_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc',  0),
    ('/System/Library/Fonts/Times.ttc',                   0),
    ('/System/Library/Fonts/Supplemental/Georgia.ttf',    0),
]
MONO_CANDIDATES = [
    ('/System/Library/Fonts/Supplemental/Courier New.ttf', 0),
    ('/System/Library/Fonts/SFNSMono.ttf',                 0),
    ('/System/Library/Fonts/Menlo.ttc',                    0),
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'labjournal')


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


def emblem_font(size): return _load(EMBLEM_CANDIDATES, size)
def wordmark_font(size): return _load(WORDMARK_CANDIDATES, size)
def mono_font(size):     return _load(MONO_CANDIDATES, size)


def measure(font, text):
    tmp = Image.new('RGB', (1, 1))
    d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb


# ── Paper substrate ───────────────────────────────────────────────────────
def draw_paper(img):
    d = ImageDraw.Draw(img, 'RGBA')
    # Graph grid — minor every 20px, major every 100px
    for x in range(0, W, 20):
        d.line([(x, 0), (x, H)], fill=GRID_MINOR + (200,), width=1)
    for y in range(0, H, 20):
        d.line([(0, y), (W, y)], fill=GRID_MINOR + (200,), width=1)
    for x in range(0, W, 100):
        d.line([(x, 0), (x, H)], fill=GRID_MAJOR + (230,), width=1)
    for y in range(0, H, 100):
        d.line([(0, y), (W, y)], fill=GRID_MAJOR + (230,), width=1)

    # Red margin rule (left)
    d.line([(72, 0), (72, H)], fill=RED_MARGIN + (200,), width=2)

    # Subtle paper grain — fine noise
    grain = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    rng = random.Random(7)
    for _ in range(5000):
        x, y = rng.randint(0, W - 1), rng.randint(0, H - 1)
        a = rng.randint(6, 16)
        gd.point((x, y), fill=(90, 70, 40, a))
    img.alpha_composite(grain)

    # Page-edge vignette (slightly darker corners)
    vignette = Image.new('L', (W, H), 255)
    vd = ImageDraw.Draw(vignette)
    for r in range(140, 0, -20):
        vd.rectangle([W // 2 - W // 2, H // 2 - H // 2,
                      W // 2 + W // 2, H // 2 + H // 2], outline=0)
    vignette = vignette.filter(ImageFilter.GaussianBlur(60))


# ── Annotation helpers ───────────────────────────────────────────────────
def draw_ruler_ticks(img, x, y1, y2, step=20, major=100, side='left'):
    """Vertical ruler ticks running from (x, y1) to (x, y2)."""
    d = ImageDraw.Draw(img, 'RGBA')
    f = mono_font(11)
    for y in range(y1, y2 + 1, step):
        is_major = (y - y1) % major == 0
        length = 10 if is_major else 5
        x1 = x - length if side == 'left' else x
        x2 = x if side == 'left' else x + length
        d.line([(x1, y), (x2, y)], fill=GRAPHITE + (220,), width=1)
        if is_major:
            label = f"{(y - y1) // 10}"
            tw, th, _ = measure(f, label)
            tx = x - length - tw - 4 if side == 'left' else x + length + 4
            d.text((tx, y - th // 2), label, fill=GRAPHITE, font=f)


def draw_measure_line(img, p1, p2, label, offset=14):
    """Dashed measurement line from p1 to p2 with a label midway."""
    d = ImageDraw.Draw(img, 'RGBA')
    x1, y1 = p1; x2, y2 = p2
    # Dashed line
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0: return
    ux, uy = dx / length, dy / length
    dash = 6
    pos = 0
    while pos < length:
        sx = x1 + ux * pos
        sy = y1 + uy * pos
        ex = x1 + ux * min(pos + dash, length)
        ey = y1 + uy * min(pos + dash, length)
        d.line([(sx, sy), (ex, ey)], fill=GRAPHITE + (220,), width=1)
        pos += dash * 2
    # Arrowhead notches at both ends (small perpendicular ticks)
    nx, ny = -uy * 4, ux * 4
    d.line([(x1 - nx, y1 - ny), (x1 + nx, y1 + ny)], fill=GRAPHITE + (220,), width=1)
    d.line([(x2 - nx, y2 - ny), (x2 + nx, y2 + ny)], fill=GRAPHITE + (220,), width=1)
    # Label at midpoint, offset perpendicular
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    lx, ly = mx + (-uy) * offset, my + ux * offset
    f = mono_font(13)
    tw, th, _ = measure(f, label)
    d.rectangle([lx - tw / 2 - 4, ly - th / 2 - 2, lx + tw / 2 + 4, ly + th / 2 + 2],
                fill=PAPER + (230,))
    d.text((lx - tw / 2, ly - th / 2), label, fill=GRAPHITE, font=f)


def draw_protractor(img, cx, cy, radius, start_deg, end_deg, label=None):
    """Dashed arc segment, like a protractor measurement."""
    d = ImageDraw.Draw(img, 'RGBA')
    # Full-circle arc via polygon segments
    for a in range(int(start_deg), int(end_deg), 4):
        a1 = math.radians(a)
        a2 = math.radians(a + 2)
        x1 = cx + radius * math.cos(a1); y1 = cy + radius * math.sin(a1)
        x2 = cx + radius * math.cos(a2); y2 = cy + radius * math.sin(a2)
        d.line([(x1, y1), (x2, y2)], fill=GRAPHITE + (200,), width=1)
    # End radii
    for a_deg in (start_deg, end_deg):
        a = math.radians(a_deg)
        d.line([(cx, cy), (cx + radius * math.cos(a), cy + radius * math.sin(a))],
               fill=GRAPHITE + (180,), width=1)
    if label:
        a_mid = math.radians((start_deg + end_deg) / 2)
        lx = cx + (radius + 18) * math.cos(a_mid)
        ly = cy + (radius + 18) * math.sin(a_mid)
        f = mono_font(12)
        tw, th, _ = measure(f, label)
        d.text((lx - tw / 2, ly - th / 2), label, fill=GRAPHITE, font=f)


def draw_margin_note(img, x, y, text, color=RED_MARGIN):
    """Handwritten-style note in the margin."""
    d = ImageDraw.Draw(img, 'RGBA')
    f = mono_font(14)
    for i, line in enumerate(text.split('\n')):
        d.text((x, y + i * 18), line, fill=color, font=f)


# ── Generator ─────────────────────────────────────────────────────────────
def generate(text="MURIEL",
             subtitle="Scriptable Visual Production Toolkit",
             subtitle2="for researcher-designer-engineers"):
    base = Image.new('RGBA', (W, H), PAPER + (255,))
    draw_paper(base)

    # Emblem M — serif, centered
    letter = text[0]
    ef = emblem_font(380)
    bb_em = None
    # Measure
    tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dtmp = ImageDraw.Draw(tmp)
    bb_em = dtmp.textbbox((0, 0), letter, font=ef)
    ew, eh = bb_em[2] - bb_em[0], bb_em[3] - bb_em[1]
    emblem_cx = int(W * 0.42)
    emblem_cy = int(H * 0.44)
    ex = emblem_cx - ew // 2 - bb_em[0]
    ey = emblem_cy - eh // 2 - bb_em[1]

    # Paint the letter solid dark ink
    dbase = ImageDraw.Draw(base, 'RGBA')
    dbase.text((ex, ey), letter, fill=INK + (255,), font=ef)

    # Emblem glyph bounding box in canvas coords
    gx1, gy1 = ex + bb_em[0], ey + bb_em[1]
    gx2, gy2 = ex + bb_em[2], ey + bb_em[3]

    # ── Annotations ─────────────────────────────────────────────────────
    # Ruler along right edge of canvas
    draw_ruler_ticks(base, W - 40, 60, H - 60, step=20, major=100, side='right')

    # Horizontal "height" measurement to the right of the M
    draw_measure_line(base, (gx2 + 30, gy1), (gx2 + 30, gy2), f"h={gy2 - gy1}px")
    # Vertical "width" measurement below the M
    draw_measure_line(base, (gx1, gy2 + 28), (gx2, gy2 + 28), f"w={gx2 - gx1}px")

    # Protractor arc at top-left serif corner
    draw_protractor(base, gx1 + 8, gy1 + 8, 48, 270, 360, label="90°")

    # Diagonal callout from top-right of M
    dcall = ImageDraw.Draw(base, 'RGBA')
    dcall.line([(gx2 - 4, gy1 + 8), (gx2 + 70, gy1 - 36)],
               fill=GRAPHITE + (220,), width=1)
    dcall.line([(gx2 + 70, gy1 - 36), (gx2 + 150, gy1 - 36)],
               fill=GRAPHITE + (220,), width=1)
    f = mono_font(12)
    dcall.text((gx2 + 76, gy1 - 54), "apex / serif", fill=GRAPHITE, font=f)

    # Margin note (red)
    draw_margin_note(base, 84, 40, "fig. 1\nM — muriel\nworking title")

    # ── Wordmark ────────────────────────────────────────────────────────
    wf = wordmark_font(72)
    wbb = dbase.textbbox((0, 0), text, font=wf)
    wtw = wbb[2] - wbb[0]
    wty = gy2 + 68
    wtx = emblem_cx - wtw // 2 - wbb[0]
    dbase.text((wtx, wty), text, fill=INK + (255,), font=wf)

    # ── Subtitles in italic-ish serif ───────────────────────────────────
    sf1 = wordmark_font(24)
    sf2 = wordmark_font(18)
    sbx = emblem_cx
    if subtitle:
        sw, sh, _ = measure(sf1, subtitle)
        dbase.text((sbx - sw // 2, wty + wbb[3] + 18),
                   subtitle, fill=INK_SOFT, font=sf1)
        wty += wbb[3] + sh + 32
    if subtitle2:
        sw2, _, _ = measure(sf2, subtitle2)
        dbase.text((sbx - sw2 // 2, wty),
                   subtitle2, fill=GRAPHITE, font=sf2)

    # Flatten + save
    final = Image.new('RGB', (W, H), PAPER)
    final.paste(base, (0, 0), base)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, f'labjournal-logo-{text.lower()}.png')
    final.save(out, 'PNG')
    print(f"  → {out}")
    return out


if __name__ == '__main__':
    print(f"Generating lab-journal logo → {OUTPUT_DIR}\n")
    generate()
    print("\nDone.")
