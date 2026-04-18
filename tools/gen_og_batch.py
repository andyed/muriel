"""
Batch OG social preview generator.
Generates 1280x640 GitHub social preview images for multiple projects.
Each project gets a unique accent color and visual motif.

Output: assets/github-social-1280x640.png in each project directory.
"""

from PIL import Image, ImageDraw, ImageFont
import os, math

# ── Shared ─────────────────────────────────────────────────────────────────
BG = (10, 10, 15)
TEXT_CREAM = (230, 228, 210)
W, H = 1280, 640

FONT_PATHS = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/System/Library/Fonts/SFCompact.ttf',
    '/Library/Fonts/Arial Bold.ttf',
    '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
]

DEV = os.path.expanduser('~/Documents/dev')

def find_font(size, bold=True):
    for p in FONT_PATHS:
        if os.path.exists(p):
            idx = 1 if (bold and p.endswith('.ttc')) else 0
            return ImageFont.truetype(p, size, index=idx)
    return ImageFont.load_default()

def luminance(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg, bg):
    l1, l2 = luminance(fg), luminance(bg)
    if l1 < l2: l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)

def draw_text_centered(draw, text, y, font, fill, glow_color=None, glow_r=2):
    """Draw centered text with optional glow."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if glow_color:
        for dx in range(-glow_r, glow_r + 1):
            for dy in range(-glow_r, glow_r + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, fill=glow_color, font=font)
    draw.text((x, y), text, fill=fill, font=font)
    return tw

def auto_fit_font(draw, text, max_width, base_size, bold=True):
    """Find font size that fits within max_width."""
    font = find_font(base_size, bold)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    if tw > max_width:
        new_size = int(base_size * max_width / tw)
        font = find_font(new_size, bold)
    return font


# ── Project definitions ────────────────────────────────────────────────────

PROJECTS = [
    {
        'name': 'Scrutinizer',
        'subtitle': 'foveated vision simulator',
        'accent': (220, 170, 50),       # warm amber — vision/eye
        'accent_dim': (140, 108, 32),
        'dir': 'scrutinizer-repo/scrutinizer2025',
        'motif': 'foveal_rings',
    },
    {
        'name': 'Session Cartographer',
        'subtitle': 'session memory for humans and agents',
        'accent': (210, 130, 140),      # dusty rose/coral
        'accent_dim': (140, 85, 92),
        'dir': 'session-cartographer',
        'motif': 'timeline_bars',
    },
    {
        'name': 'Fisheye Menu',
        'subtitle': 'luxuriously usable cascading menus',
        'accent': (80, 200, 120),       # green — interaction/Fitts
        'accent_dim': (50, 125, 75),
        'dir': 'fisheye-menu',
        'motif': 'fisheye_items',
    },
    {
        'name': 'Science Agent',
        'subtitle': 'catches AI-confabulated citations',
        'accent': (220, 120, 70),       # warm red-orange — warnings
        'accent_dim': (140, 76, 44),
        'dir': 'science-agent',
        'motif': 'citation_marks',
    },
    {
        'name': 'Fascist Language Analyzer',
        'subtitle': "Eco's Ur-Fascism traits in Project 2025",
        'accent': (230, 90, 90),        # brighter red — political analysis
        'accent_dim': (160, 60, 60),
        'dir': 'fascist-language-analyzer',
        'motif': 'trait_bars',
    },
    {
        'name': 'Camerastein',
        'subtitle': 'camera body signal detection via MediaPipe',
        'accent': (100, 180, 230),      # cool blue — camera/vision
        'accent_dim': (65, 115, 150),
        'dir': 'camerastein',
        'motif': 'body_landmarks',
    },
]


# ── Motif renderers ────────────────────────────────────────────────────────

def _aspect_color_dark(ratio, fade=1.0):
    """Aspect ratio → fill color for dark theme.
    1.0 = teal (isotropic), >1.3 = desaturated warm (stretched).
    No red — stays in the teal-to-muted-sand range. fade dims for edge falloff."""
    t = min(1.0, max(0.0, (ratio - 1.0) / 0.3))
    # Teal (isotropic) → desaturated sand (stretched)
    r = int((25 + 30 * t) * fade)
    g = int((60 - 15 * t) * fade)
    b = int((70 - 30 * t) * fade)
    return (r, g, b)


def draw_foveal_rings_large(draw, accent, accent_dim):
    """FOVI isotropic cortical grid — ported from fig-fovi-geometry.html.
    CMF_A=2.78°, 30 rings, adaptive spoke count. Filled cells colored by
    aspect ratio: teal=isotropic, amber=stretched. Alternating ring offsets
    break the 3:00 seam."""
    cx, cy = W // 2, H // 2
    line_color = (80, 190, 210)

    CMF_A = 2.78
    N_RINGS = 30
    R_MAX = 15.0
    SCALE = 320 / R_MAX

    # Ring geometry — exact port of JS
    rings_data = []
    w_min = math.log(CMF_A)
    w_max = math.log(R_MAX + CMF_A)
    w_step = (w_max - w_min) / (N_RINGS - 1)
    for i in range(N_RINGS):
        w = w_min + i * w_step
        r = math.exp(w) - CMF_A
        if i == 0:
            dr = (math.exp(w_min + w_step) - CMF_A) - r
        elif i == N_RINGS - 1:
            dr = r - (math.exp(w_min + (i - 1) * w_step) - CMF_A)
        else:
            r_prev = math.exp(w_min + (i - 1) * w_step) - CMF_A
            r_next = math.exp(w_min + (i + 1) * w_step) - CMF_A
            dr = (r_next - r_prev) / 2
        spokes = 1 if i == 0 else max(4, int(2 * math.pi * r / dr))
        rings_data.append({'r': r, 'dr': dr, 'spokes': spokes})

    # Ring boundaries
    bounds = []
    for i in range(N_RINGS):
        if i == 0:
            r_inner = 0
            r_outer = (rings_data[0]['r'] + rings_data[1]['r']) / 2
        elif i == N_RINGS - 1:
            r_inner = (rings_data[i - 1]['r'] + rings_data[i]['r']) / 2
            r_outer = R_MAX
        else:
            r_inner = (rings_data[i - 1]['r'] + rings_data[i]['r']) / 2
            r_outer = (rings_data[i]['r'] + rings_data[i + 1]['r']) / 2
        bounds.append((r_inner, r_outer))

    # Draw filled cells — matching drawIsoGeometry from JS
    # Line color backed off from full brightness — grid supports text, doesn't compete
    line_color_base = (50, 130, 150)

    for i in range(1, N_RINGS):
        r_inner, r_outer = bounds[i]
        ri_px = r_inner * SCALE
        ro_px = r_outer * SCALE
        spokes = rings_data[i]['spokes']
        d_theta = 2 * math.pi / spokes

        # Aspect ratio for this ring
        r_mid = (r_inner + r_outer) / 2
        tangential = r_mid * d_theta
        radial = r_outer - r_inner
        aspect = tangential / radial if radial > 0 else 1.0

        # Fade out outer 30% of rings — no hard edge
        ring_frac = i / (N_RINGS - 1)
        edge_fade = 1.0 if ring_frac < 0.7 else max(0.0, 1.0 - (ring_frac - 0.7) / 0.3)

        fill_color = _aspect_color_dark(aspect, fade=edge_fade)
        ring_line = tuple(int(c * edge_fade) for c in line_color_base)
        # Skip drawing if fully faded
        if edge_fade < 0.05:
            continue

        # Offset alternating rings by half-spoke to break 3:00 seam
        offset = (d_theta / 2) if (i % 2 == 1) else 0

        for s in range(spokes):
            t0 = s * d_theta + offset
            t1 = (s + 1) * d_theta + offset

            pts = []
            n_arc = max(4, int((t1 - t0) / 0.12))
            for k in range(n_arc + 1):
                t = t0 + (t1 - t0) * k / n_arc
                pts.append((cx + ro_px * math.cos(t), cy + ro_px * math.sin(t)))
            for k in range(n_arc, -1, -1):
                t = t0 + (t1 - t0) * k / n_arc
                pts.append((cx + ri_px * math.cos(t), cy + ri_px * math.sin(t)))

            draw.polygon(pts, outline=ring_line, fill=fill_color)

    # Foveal dot
    fov_r = max(4, int(bounds[0][1] * SCALE))
    draw.ellipse([cx - fov_r, cy - fov_r, cx + fov_r, cy + fov_r],
                 outline=line_color_base, fill=_aspect_color_dark(1.0), width=2)


def draw_foveal_rings(draw, accent, accent_dim):
    """Isotropic cortical grid — log-spaced rings with adaptive spoke counts.
    Approximates FOVI geometry: w(r) = log(r + a), spokes ∝ 2πr/dr."""
    cx, cy = W // 2, H // 2 + 40
    a = 12  # cortical magnification constant (in pixels, scaled for OG image)
    n_rings = 9
    max_r = 280
    # Compute ring radii via cortical magnification
    w_min = math.log(0 + a)
    w_max = math.log(max_r + a)
    w_step = (w_max - w_min) / n_rings
    radii = [math.exp(w_min + i * w_step) - a for i in range(1, n_rings + 1)]
    prev_r = 0
    for i, r in enumerate(radii):
        r = int(r)
        dr = r - prev_r
        # Adaptive spoke count — isotropic: angular spacing ≈ radial spacing
        n_spokes = max(6, int(2 * math.pi * r / max(dr, 1)))
        # Fade outer rings
        fade = max(0.15, 1.0 - i / (n_rings + 2))
        ring_color = tuple(int(c * fade) for c in accent_dim)
        # Draw ring
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ring_color, width=1)
        # Draw spokes from prev_r to r
        for s in range(n_spokes):
            angle = 2 * math.pi * s / n_spokes
            x1 = cx + int(prev_r * math.cos(angle))
            y1 = cy + int(prev_r * math.sin(angle))
            x2 = cx + int(r * math.cos(angle))
            y2 = cy + int(r * math.sin(angle))
            spoke_color = tuple(int(c * fade * 0.7) for c in accent_dim)
            draw.line([(x1, y1), (x2, y2)], fill=spoke_color, width=1)
        prev_r = r


def draw_timeline_bars(draw, accent, accent_dim):
    """Horizontal timeline bars — session lanes."""
    import random
    rng = random.Random(42)
    y_base = 440
    for lane in range(5):
        y = y_base + lane * 30
        # Draw 3-6 segments per lane
        x = 180
        for _ in range(rng.randint(3, 6)):
            seg_w = rng.randint(40, 160)
            fade = rng.randint(15, 35)
            color = tuple(int(c * fade / 40) for c in accent_dim)
            draw.rounded_rectangle([x, y, x + seg_w, y + 16], radius=3, fill=color)
            x += seg_w + rng.randint(10, 30)
            if x > 1100:
                break


def draw_fisheye_items(draw, accent, accent_dim):
    """Stacked items with size magnification in the center — Fitts's Law."""
    cx = W // 2
    y_base = 420
    items = 11
    mid = items // 2
    for i in range(items):
        dist = abs(i - mid)
        # Size decreases with distance from center
        h = max(8, int(32 - dist * 4.5))
        w = max(60, int(260 - dist * 35))
        fade = max(10, int(35 - dist * 5))
        color = tuple(int(c * fade / 40) for c in accent_dim)
        x = cx - w // 2
        y = y_base
        draw.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=color)
        y_base += h + 4


def draw_citation_marks(draw, accent, accent_dim):
    """Scattered citation brackets with OK/FAIL verification markers."""
    import random
    rng = random.Random(99)
    cite_font = find_font(22, bold=True)
    status_font = find_font(16, bold=True)
    citations = ['[1]', '[2]', '[3]', '[4]', '[5]', '[6]', '[7]', '[8]']
    statuses =  ['OK',  'OK',  'FAIL','OK',  'FAIL','OK',  'OK',  'FAIL']
    positions = [(160, 440), (340, 480), (520, 450), (700, 500),
                 (850, 440), (980, 470), (400, 520), (760, 530)]
    for cite, status, (x, y) in zip(citations, statuses, positions):
        x += rng.randint(-10, 10)
        y += rng.randint(-10, 10)
        # Citations at moderate visibility
        cite_color = tuple(int(c * 0.6) for c in accent)
        draw.text((x, y), cite, fill=cite_color, font=cite_font)
        # Status labels: green OK, red FAIL
        bbox = draw.textbbox((0, 0), cite, font=cite_font)
        sx = x + (bbox[2] - bbox[0]) + 6
        if status == 'OK':
            draw.text((sx, y + 3), status, fill=(80, 200, 120), font=status_font)
        else:
            draw.text((sx, y + 3), status, fill=(220, 70, 70), font=status_font)


def draw_trait_bars(draw, accent, accent_dim):
    """Horizontal bars of varying length — rhetorical trait frequencies."""
    import random
    rng = random.Random(77)
    font_sm = find_font(15, bold=True)
    traits = ['cult of tradition', 'fear of difference', 'obsession with a plot',
              'selective populism', 'newspeak', 'machismo', 'ur-fascism']
    y_base = 410
    for i, trait in enumerate(traits):
        y = y_base + i * 28
        bar_w = rng.randint(120, 500)
        fade = rng.randint(30, 50)
        color = tuple(min(255, int(c * fade / 40)) for c in accent_dim)
        draw.rounded_rectangle([200, y, 200 + bar_w, y + 16], radius=3, fill=color)
        # Labels at full accent — must be readable at small size
        draw.text((200 + bar_w + 10, y - 1), trait, fill=accent, font=font_sm)


def draw_body_landmarks(draw, accent, accent_dim):
    """Stick figure with landmark dots — MediaPipe pose skeleton."""
    cx = W // 2
    # Simplified pose skeleton — head, torso, arms, legs
    # Centered vertically in the canvas so head isn't clipped by title
    oy = H // 2 + 20  # vertically centered, nudged slightly down
    scale = 1.2
    def p(x, y):
        return (cx + int(x * scale), oy + int(y * scale))

    joints = {
        'head': p(0, -120),
        'neck': p(0, -90),
        'l_shoulder': p(-45, -80),
        'r_shoulder': p(45, -80),
        'l_elbow': p(-80, -120),
        'r_elbow': p(80, -115),
        'l_wrist': p(-105, -155),
        'r_wrist': p(110, -148),
        'l_hip': p(-25, 10),
        'r_hip': p(25, 10),
        'l_knee': p(-35, 70),
        'r_knee': p(30, 75),
        'l_ankle': p(-40, 130),
        'r_ankle': p(25, 135),
    }
    bones = [
        ('head', 'neck'), ('neck', 'l_shoulder'), ('neck', 'r_shoulder'),
        ('l_shoulder', 'l_elbow'), ('l_elbow', 'l_wrist'),
        ('r_shoulder', 'r_elbow'), ('r_elbow', 'r_wrist'),
        ('neck', 'l_hip'), ('neck', 'r_hip'),
        ('l_hip', 'l_knee'), ('l_knee', 'l_ankle'),
        ('r_hip', 'r_knee'), ('r_knee', 'r_ankle'),
        ('l_hip', 'r_hip'),
    ]
    # Draw bones
    bone_color = tuple(int(c * 0.5) for c in accent)
    for a, b in bones:
        draw.line([joints[a], joints[b]], fill=bone_color, width=2)
    # Draw landmark dots
    dot_r = 4
    for name, (jx, jy) in joints.items():
        draw.ellipse([jx - dot_r, jy - dot_r, jx + dot_r, jy + dot_r],
                     fill=accent, outline=None)
    # Head circle
    hx, hy = joints['head']
    draw.ellipse([hx - 12, hy - 12, hx + 12, hy + 12],
                 outline=accent, fill=None, width=2)


MOTIF_FUNCS = {
    'foveal_rings': draw_foveal_rings,
    'timeline_bars': draw_timeline_bars,
    'fisheye_items': draw_fisheye_items,
    'citation_marks': draw_citation_marks,
    'trait_bars': draw_trait_bars,
    'body_landmarks': draw_body_landmarks,
}


# ── Generator ──────────────────────────────────────────────────────────────

def generate_og(project):
    name = project['name']
    subtitle = project['subtitle']
    accent = project['accent']
    accent_dim = project['accent_dim']
    motif = project['motif']
    out_dir = os.path.join(DEV, project['dir'], 'assets')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'github-social-1280x640.png')

    img = Image.new('RGBA', (W, H), BG + (255,))
    draw = ImageDraw.Draw(img)

    # Subtle grid dots
    for gx in range(40, W, 80):
        for gy in range(40, H, 80):
            dx = abs(gx - W / 2) / (W / 2)
            dy = abs(gy - H / 2) / (H / 2)
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0.5:
                alpha = max(0, int(18 * (1 - (dist - 0.5) / 0.5)))
                if alpha > 0:
                    color = tuple(int(c * alpha / 18) for c in accent_dim)
                    draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=color)

    # For Scrutinizer: draw cortical grid large and centered behind everything
    if motif == 'foveal_rings':
        draw_foveal_rings_large(draw, accent, accent_dim)

    # Draw motif (background decoration) — skip for Scrutinizer (already drawn large)
    if motif != 'foveal_rings':
        MOTIF_FUNCS[motif](draw, accent, accent_dim)

    # Title
    title_font = auto_fit_font(draw, name, int(W * 0.8), 96, bold=True)
    title_bbox = draw.textbbox((0, 0), name, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]

    # Subtitle
    sub_font = auto_fit_font(draw, subtitle, int(W * 0.7), 32, bold=False)
    sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_h = sub_bbox[3] - sub_bbox[1]

    # Vertical layout: center title+subtitle in canvas
    gap = 20
    total_h = title_h + gap + sub_h
    y_start = (H - total_h) // 2 - 20

    # Title glow + text — heavier glow on busy backgrounds
    glow = tuple(int(c * 0.3) for c in accent)
    glow_bg = (10, 10, 15)  # match BG for knockout effect behind text
    draw_text_centered(draw, name, y_start, title_font, accent,
                       glow_color=glow_bg, glow_r=4)
    draw_text_centered(draw, name, y_start, title_font, accent,
                       glow_color=glow, glow_r=3)

    # Subtitle — cream on dark glow for readability over busy grid
    sub_color = TEXT_CREAM
    draw_text_centered(draw, subtitle, y_start + title_h + gap, sub_font, sub_color,
                       glow_color=glow_bg, glow_r=3)

    # Flatten to RGB
    final = Image.new('RGB', (W, H), BG)
    final.paste(img, (0, 0), img)

    # Contrast check
    ratio = contrast_ratio(accent, BG)
    status = 'PASS' if ratio >= 3.0 else 'FAIL'
    print(f"  {name}: contrast {ratio:.1f}:1 {status}")

    final.save(out_path, 'PNG')
    print(f"  Saved: {out_path}")
    return out_path


# ── Main ───────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("Generating OG social previews...\n")
    paths = []
    for proj in PROJECTS:
        path = generate_og(proj)
        paths.append(path)
    print(f"\nDone. {len(paths)} images generated.")
