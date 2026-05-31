"""
Bauhaus-M logo generator.

References Muriel Cooper's MIT-Press-era design sensibility via Herbert
Bayer's Universal typeface logic: the M is constructed from pure
geometric primitives — two vertical bars plus two diagonal
parallelograms forming the V-apex. No decoration, no texture; the
mark is its construction.

Palette: warm cream paper + vermilion + charcoal + mustard accent.
Bauhaus-adjacent, explicitly not MIT corporate red.

1200×630 OG size.
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 630

# ── Palette — muted archival, not primary Bauhaus ───────────────────────
# Bone ivory paper, graphite-slate mark, copper accent. Scholarly-warm
# without shouting. No red, no mustard.
PAPER   = (232, 224, 208)   # bone ivory
SLATE   = ( 45,  52,  64)   # graphite slate (dark blue-gray)
COPPER  = (184, 123,  74)   # muted copper
INK_SOFT = ( 92,  88,  82)

SANS_CANDIDATES = [
    ('/System/Library/Fonts/Helvetica.ttc', 1),
    ('/System/Library/Fonts/Helvetica.ttc', 0),
    ('/Library/Fonts/Arial Bold.ttf',       0),
]
SANS_LIGHT_CANDIDATES = [
    ('/System/Library/Fonts/Helvetica.ttc', 0),
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output', 'bauhaus')


def _load(candidates, size):
    for p, idx in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=idx)
            except OSError:
                try: return ImageFont.truetype(p, size)
                except OSError: continue
    return ImageFont.load_default()


def sans(size):       return _load(SANS_CANDIDATES, size)
def sans_light(size): return _load(SANS_LIGHT_CANDIDATES, size)


def measure(font, text):
    tmp = Image.new('RGB', (1, 1))
    bb = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1], bb


# ── M construction ───────────────────────────────────────────────────────
def draw_bauhaus_m(img, cx, cy, height, stroke_w, apex_frac=0.62,
                   diag_stroke_frac=1.0, outline_only=False, outline_w=3,
                   curved_arm='right', bow_depth=22,
                   vertical_color=SLATE, diagonal_color=SLATE):
    """Render an M from four geometric primitives:

        ██        ██      ← two vertical bars (`vertical_color`)
        █ ╲      ╱ █
        █  ╲    ╱  █      ← two diagonal parallelograms forming the
        █   ╲  ╱   █        V-apex (`diagonal_color`), meeting at
        █    ╲╱    █        y = top + apex_frac * height
        █    ╱╲    █
        █   ╱  ╲   █
        ██        ██

    `apex_frac` = 0.50 gives a deep V (apex in the middle), 0.75 gives
    a shallow V (apex near the bottom). Classic M = ~0.60–0.65.
    """
    draw = ImageDraw.Draw(img, 'RGBA')
    total_w = int(height * 0.92)            # roughly square-ish M
    L = cx - total_w // 2
    R = cx + total_w // 2
    top = cy - height // 2
    bot = cy + height // 2

    # Two vertical bars — filled or outline-only
    if outline_only:
        draw.rectangle([L, top, L + stroke_w, bot],
                       outline=vertical_color + (255,), width=outline_w)
        draw.rectangle([R - stroke_w, top, R, bot],
                       outline=vertical_color + (255,), width=outline_w)
    else:
        draw.rectangle([L, top, L + stroke_w, bot], fill=vertical_color + (255,))
        draw.rectangle([R - stroke_w, top, R, bot], fill=vertical_color + (255,))

    # Two diagonals — slimmer than verticals, starting one full stroke
    # INSIDE the vertical bars so the M reads more implied than carved.
    diag_w = max(4, int(stroke_w * diag_stroke_frac))
    apex_x = cx
    apex_y = top + int(apex_frac * height)
    # Left diagonal: top-of-stroke is one stroke_w inside the left bar
    lx_top_outer = L + stroke_w              # inner edge of left bar
    lx_top_inner = lx_top_outer + diag_w      # diag_w wide at the top
    rx_top_outer = R - stroke_w
    rx_top_inner = rx_top_outer - diag_w

    def curved_arm_polygon(top_mid, apex_mid, width, bow_vector):
        """Generate the outline polygon for a trampoline-bent arm.

        Samples a quadratic bezier from `top_mid` (midpoint of the arm's
        top edge) to `apex_mid` (midpoint at the apex), with the control
        point offset by `bow_vector`. At each sample, offsets perpendicular
        by ±width/2 to build a parallel-edge curved bar.
        """
        n = 36
        ctrl_x = (top_mid[0] + apex_mid[0]) / 2 + bow_vector[0]
        ctrl_y = (top_mid[1] + apex_mid[1]) / 2 + bow_vector[1]
        left_edge, right_edge = [], []
        for i in range(n + 1):
            t = i / n
            # Position on centerline bezier
            px = (1 - t) ** 2 * top_mid[0] + 2 * (1 - t) * t * ctrl_x + t * t * apex_mid[0]
            py = (1 - t) ** 2 * top_mid[1] + 2 * (1 - t) * t * ctrl_y + t * t * apex_mid[1]
            # Tangent (derivative of bezier)
            tx = 2 * (1 - t) * (ctrl_x - top_mid[0]) + 2 * t * (apex_mid[0] - ctrl_x)
            ty = 2 * (1 - t) * (ctrl_y - top_mid[1]) + 2 * t * (apex_mid[1] - ctrl_y)
            tl = (tx * tx + ty * ty) ** 0.5 or 1
            # Perpendicular (unit normal)
            nx, ny = -ty / tl, tx / tl
            half = width / 2
            left_edge.append((px + nx * half, py + ny * half))
            right_edge.append((px - nx * half, py - ny * half))
        # Outline polygon: left edge forward + right edge backward
        return left_edge + list(reversed(right_edge))

    def draw_arm(kind, top_outer, top_inner, apex_left, apex_right, bow_dir):
        """Render one arm. Straight = parallelogram; curved = bezier-bent bar."""
        straight_poly = [top_outer, top_inner, apex_right, apex_left]
        if curved_arm == kind:
            top_mid = ((top_outer[0] + top_inner[0]) / 2,
                       (top_outer[1] + top_inner[1]) / 2)
            apex_mid = ((apex_left[0] + apex_right[0]) / 2,
                        (apex_left[1] + apex_right[1]) / 2)
            # Bow vector: perpendicular to centerline direction × bow_depth
            # bow_dir is +1 (bow toward upper-right) or -1 (bow toward upper-left)
            # For the right arm bowing INWARD into the V, push toward upper-left;
            # for left arm bowing inward, push toward upper-right.
            dx = apex_mid[0] - top_mid[0]
            dy = apex_mid[1] - top_mid[1]
            length = (dx * dx + dy * dy) ** 0.5 or 1
            perp = (-dy / length * bow_dir, dx / length * bow_dir)
            bow_vector = (perp[0] * bow_depth, perp[1] * bow_depth)
            poly = curved_arm_polygon(top_mid, apex_mid, diag_w, bow_vector)
            if outline_only:
                draw.polygon(poly, outline=diagonal_color + (255,), width=outline_w)
            else:
                draw.polygon(poly, fill=diagonal_color + (255,))
        else:
            if outline_only:
                draw.polygon(straight_poly, outline=diagonal_color + (255,), width=outline_w)
            else:
                draw.polygon(straight_poly, fill=diagonal_color + (255,))

    apex_left = (apex_x - diag_w // 2, apex_y)
    apex_right = (apex_x + diag_w // 2, apex_y)
    # Left arm, if curved, bows INWARD (toward the V's interior = upper-right)  = +1
    # Right arm, if curved, bows INWARD (toward the V's interior = upper-left)  = -1
    draw_arm('left',  (lx_top_outer, top), (lx_top_inner, top), apex_left, apex_right, bow_dir=+1)
    draw_arm('right', (rx_top_outer, top), (rx_top_inner, top), apex_left, apex_right, bow_dir=-1)

    return (L, top, R, bot)


# ── Supporting geometry — the Bauhaus colophon accent ────────────────────
def draw_accent_circle(img, cx, cy, r, color, outline_w=0):
    """Single filled/outlined circle — Bauhaus primary-shape accent."""
    draw = ImageDraw.Draw(img, 'RGBA')
    if outline_w:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     outline=color + (255,), width=outline_w)
    else:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,))


# ── Generator ────────────────────────────────────────────────────────────
def generate(text="MURIEL",
             subtitle="scriptable visual production toolkit",
             subtitle2="for researcher-designer-engineers"):
    base = Image.new('RGBA', (W, H), PAPER + (255,))

    # Construct the M — single-color slate, thinner diagonals (55% of
    # vertical stroke) to make the V-apex feel implied rather than carved.
    m_cy = int(H * 0.35)
    m_height = 300
    stroke_w = 48
    apex_frac = 0.58
    m_bbox = draw_bauhaus_m(base, W // 2, m_cy, m_height, stroke_w,
                            apex_frac=apex_frac, diag_stroke_frac=0.55,
                            outline_only=True, outline_w=3,
                            curved_arm='right', bow_depth=22,
                            vertical_color=SLATE, diagonal_color=SLATE)

    # Copper dot mid-flight — captured 1/3 along its rebound trajectory
    # from the strike point on the curved right arm. Motion reflections
    # (ghost trail) fade back toward the strike point to show velocity.
    m_top = m_cy - m_height // 2
    apex_y_abs = m_top + int(apex_frac * m_height)
    # Strike point — midway along the right arm, bowed inward toward upper-left
    L_ = W // 2 - int(m_height * 0.92) // 2
    R_ = W // 2 + int(m_height * 0.92) // 2
    right_top  = (R_ - stroke_w - max(4, int(stroke_w * 0.55)) // 2, m_top)
    right_apex = (W // 2, apex_y_abs)
    strike_x = (right_top[0] + right_apex[0]) / 2
    strike_y = (right_top[1] + right_apex[1]) / 2
    # Offset strike inward along bow direction (perpendicular-left of arm tangent)
    dx = right_apex[0] - right_top[0]
    dy = right_apex[1] - right_top[1]
    length = (dx * dx + dy * dy) ** 0.5 or 1
    perp_inward = (dy / length, -dx / length)   # rotate +90° toward upper-left
    bow_depth = 22
    strike_x += perp_inward[0] * bow_depth
    strike_y += perp_inward[1] * bow_depth
    # Destination: dot is flying toward upper-left (rebound direction)
    dest_x = L_ + stroke_w + 28
    dest_y = m_top + 20
    # Dot at 1/3 along trajectory from strike → destination
    t = 0.33
    dot_x = strike_x + (dest_x - strike_x) * t
    dot_y = strike_y + (dest_y - strike_y) * t

    # Motion trail: 3 ghost copies fading back toward the strike point.
    # Each ghost sits ~10% further back along the trajectory, smaller and
    # more transparent — reads as a multi-exposure of the dot in flight.
    draw_ghost = ImageDraw.Draw(base, 'RGBA')
    for i in range(1, 4):
        frac = 0.10 * i             # 0.10, 0.20, 0.30 along return path
        gx = dot_x + (strike_x - dot_x) * frac
        gy = dot_y + (strike_y - dot_y) * frac
        gr = int(18 * (1 - i * 0.15))
        alpha = int(180 * (1 - i * 0.30))
        draw_ghost.ellipse([gx - gr, gy - gr, gx + gr, gy + gr],
                           fill=COPPER + (alpha,))
    # The dot itself — full opacity, full size, on top of the trail
    draw_accent_circle(base, int(dot_x), int(dot_y), 18, COPPER)

    # Thin horizontal rule — Cooper's typographic signature
    rule_y = int(H * 0.68)
    rule_w = 420
    ImageDraw.Draw(base, 'RGBA').line(
        [((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
        fill=COPPER + (255,), width=2,
    )

    # Wordmark — lowercase sans, Cooper / Bauhaus convention
    draw = ImageDraw.Draw(base, 'RGBA')
    wm_text = text.lower()
    wf = sans(84)
    tw, th, tbb = measure(wf, wm_text)
    wty = rule_y + 24 - tbb[1]
    wtx = (W - tw) // 2 - tbb[0]
    draw.text((wtx, wty), wm_text, fill=SLATE + (255,), font=wf)

    # Subtitles — light sans
    sf1 = sans_light(22)
    sf2 = sans_light(17)
    y = rule_y + 24 + th
    if subtitle:
        sw, sh, _ = measure(sf1, subtitle)
        draw.text(((W - sw) // 2, y + 20), subtitle, fill=SLATE + (255,), font=sf1)
        y += sh + 32
    if subtitle2:
        sw2, _, _ = measure(sf2, subtitle2)
        draw.text(((W - sw2) // 2, y), subtitle2, fill=INK_SOFT + (255,), font=sf2)

    # Credit line in copper, bottom-left
    credit_f = sans_light(11)
    credit = "after muriel cooper · bauhaus-bayer construction"
    draw.text((40, H - 30), credit, fill=COPPER + (220,), font=credit_f)

    # Flatten + save
    final = Image.new('RGB', (W, H), PAPER)
    final.paste(base, (0, 0), base)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, f'bauhaus-m-logo-{text.lower()}.png')
    final.save(out, 'PNG')
    print(f"  → {out}")
    return out


if __name__ == '__main__':
    print(f"Generating Bauhaus-M logo → {OUTPUT_DIR}\n")
    generate()
    print("\nDone.")
