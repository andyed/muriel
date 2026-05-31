"""Render the Muriel animated colophon as a GIF for GitHub README use.

Ports the constraint solver from the interactive HTML to Python. Renders
one 9-second breath cycle (all bars share period=9.0 so the GIF loops
cleanly), preceded by a 1.5s pause on the canonical H pose.

Output:
    output/colophon/muriel-logo-animated.gif  (loops 5×)

Tunables at the top of the file.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Output ──────────────────────────────────────────────────────────────
OUT_DIR = Path(__file__).resolve().parent / "output" / "colophon"

# ── Canvas ──────────────────────────────────────────────────────────────
W, H = 900, 473
SCALE = W / 1200.0

# ── Palettes ────────────────────────────────────────────────────────────
# Graphite committed. Dark mode inverts lightness while keeping the warm
# hue family — same object, different room.
PALETTES = {
    "light": {
        "paper":    "#E8E2D0",
        "mark":     "#3A3530",
        "ink":      "#121212",
        "ink_soft": "#5C5852",
    },
    "dark": {
        "paper":    "#1F1A14",
        "mark":     "#E0D4BC",
        "ink":      "#E8E2D0",
        "ink_soft": "#A89E88",
    },
}

# ── Geometry (same as interactive) ──────────────────────────────────────
CX, CY_TOP = 600, 90
MARK_H = 280
BAR_GAP = 10
WIDTHS = [30, 20, 20, 8, 16, 10]
SCALE_W = 4.4
WIDTHS_PX = [round(w * SCALE_W) for w in WIDTHS]
BOTTOM_Y = CY_TOP + MARK_H
INNER_BASE_TOTAL = WIDTHS_PX[1] + WIDTHS_PX[2] + WIDTHS_PX[3] + WIDTHS_PX[4]
OUTER_MAX_H_FRAC = 0.88
OUTER_MAX_H = round(MARK_H * OUTER_MAX_H_FRAC)

# ── Constraint-solver state (= interactive defaults, graphite) ──────────
STATE = {
    "aShallow": 0.78, "aDeep": 0.55, "aFloat": 0.45,
    "bShallow": 0.55, "bDeep": 0.22, "bFloat": 0.60,
    "elastic": 0.42, "snap": 0.35,
    "shiftBase": 0, "vFloor": 40,
}
PHASES  = [0.0, 1.4, 3.1, 0.7]           # per-bar phase offsets (seconds)
PERIOD  = 9.0                             # single period for clean GIF loop

# ── Animation shape — pose slideshow, not smooth motion ────────────────
# 12 poses total, each held ~750ms; the first pose is held longer as a
# "canonical" pause. Reads as discrete constraint-solver snapshots rather
# than continuous breath. Frame count kept small so adjacent poses are
# always visibly different (no "4 identical frames then a jump" effect).
N_FRAMES = 12
POSE_MS = 750               # duration of each pose frame
PAUSE_MS = 1600             # first frame held longer (canonical)
LOOP_DURATION = PERIOD      # one full breath cycle sampled by the frames
GIF_LOOPS = 5

# The time within the 9.0s cycle where the "H-like" pose lives.
H_POSE_TIME = 0.0


# ── Solver (ported from interactive) ────────────────────────────────────
def shaped_sine(phase: float, snap: float) -> float:
    s = math.sin(phase)
    if snap <= 0:
        return s
    k = 1 / (1 + 3 * snap)
    return math.copysign(abs(s) ** k, s)


def inner_breath(i: int, t_sec: float) -> float:
    """Returns bar i's height fraction (i in [1..4]) at time t."""
    is_a = (i == 1 or i == 4)
    shallow = STATE["aShallow"] if is_a else STATE["bShallow"]
    deep    = STATE["aDeep"]    if is_a else STATE["bDeep"]
    phase_off = PHASES[i - 1]
    phase = ((t_sec + phase_off) / PERIOD) * math.pi * 2
    u = (shaped_sine(phase, STATE["snap"]) + 1) / 2
    return shallow + (deep - shallow) * u


def heights_at(t_sec: float) -> list[float]:
    return [1.0,
            inner_breath(1, t_sec), inner_breath(2, t_sec),
            inner_breath(3, t_sec), inner_breath(4, t_sec),
            1.0]


def width_mult_for(i: int, h_frac: float) -> float:
    if i == 0 or i == 5:
        return 1.0
    is_a = (i == 1 or i == 4)
    base = (STATE["aShallow"] + STATE["aDeep"]) / 2 if is_a \
         else (STATE["bShallow"] + STATE["bDeep"]) / 2
    mult = math.sqrt(base / max(0.05, h_frac))
    min_m = 1 - STATE["elastic"]
    max_m = 1 + STATE["elastic"]
    return max(min_m, min(max_m, mult))


def layout_bars(t_sec: float):
    """Returns list of (x, y, w, h) tuples in native 1200×630 coords."""
    hs = heights_at(t_sec)

    # 1) per-bar desired widths
    desired = [WIDTHS_PX[i] * width_mult_for(i, hs[i]) for i in range(6)]
    # 2) fixed-inner-total width constraint
    inner_sum = desired[1] + desired[2] + desired[3] + desired[4]
    inner_scale = INNER_BASE_TOTAL / max(0.01, inner_sum)
    widths = [WIDTHS_PX[i] if i in (0, 5) else round(desired[i] * inner_scale)
              for i in range(6)]
    post_round = widths[1] + widths[2] + widths[3] + widths[4]
    widths[2] += INNER_BASE_TOTAL - post_round

    # 3) inner bar positions (pre-vFloor)
    inner_heights = []
    inner_lifts = []
    inner_tops = []
    inner_bots = []
    for i in range(1, 5):
        h = round(hs[i] * MARK_H)
        drop = MARK_H - h
        fl = STATE["aFloat"] if i in (1, 4) else STATE["bFloat"]
        lift = round(drop * fl)
        inner_heights.append(h)
        inner_lifts.append(lift)
        inner_tops.append(BOTTOM_Y - h - lift)
        inner_bots.append(BOTTOM_Y - lift)

    # 4) M-guard: both center bars dip below the taller of bars 1 & 4
    v_floor = STATE["vFloor"]
    if v_floor > 0:
        tallest_pair_a = min(inner_tops[0], inner_tops[3])
        needed = tallest_pair_a + v_floor
        for ii in (1, 2):  # center bars (bar 2, bar 3)
            if inner_tops[ii] < needed:
                shrink = needed - inner_tops[ii]
                inner_heights[ii] = max(4, inner_heights[ii] - shrink)
                inner_tops[ii] = inner_bots[ii] - inner_heights[ii]

    tallest_inner_top = min(inner_tops)
    lowest_inner_bot = max(inner_bots)

    # 5) lay out with fixed total footprint
    total_w = sum(widths) + BAR_GAP * (len(widths) - 1)
    x = CX - total_w / 2
    bars = []
    for i in range(6):
        if i == 0:
            y = max(tallest_inner_top + STATE["shiftBase"], BOTTOM_Y - OUTER_MAX_H)
            h = BOTTOM_Y - y
        elif i == 5:
            bottom = lowest_inner_bot - STATE["shiftBase"]
            h = min(OUTER_MAX_H, bottom - (BOTTOM_Y - MARK_H))
            y = bottom - h
        else:
            ii = i - 1
            h = inner_heights[ii]
            y = inner_tops[ii]
        bars.append((x, y, widths[i], h))
        x += widths[i] + BAR_GAP
    return bars


# ── Rendering ───────────────────────────────────────────────────────────
FONT_PATHS = [
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial Bold.ttf',
]


def _font(size, bold=True):
    for p in FONT_PATHS:
        if os.path.exists(p):
            idx = 1 if (bold and p.endswith('.ttc')) else 0
            try:
                return ImageFont.truetype(p, size, index=idx)
            except OSError:
                continue
    return ImageFont.load_default()


def render_frame(t_sec: float, pal: dict) -> Image.Image:
    """Render the animated mark at time t_sec into `pal` colors."""
    bars = layout_bars(t_sec)
    img = Image.new("RGB", (W, H), pal["paper"])
    draw = ImageDraw.Draw(img)

    for (x, y, w, h) in bars:
        x2 = round(x * SCALE)
        y2 = round(y * SCALE)
        w2 = round(w * SCALE)
        h2 = round(h * SCALE)
        draw.rectangle([x2, y2, x2 + w2, y2 + h2], fill=pal["mark"])

    draw.line([(round(400 * SCALE), round(410 * SCALE)),
               (round(800 * SCALE), round(410 * SCALE))], fill=pal["mark"], width=2)

    wf = _font(round(76 * SCALE), bold=True)
    wm = "muriel"
    bb = draw.textbbox((0, 0), wm, font=wf)
    wmw = bb[2] - bb[0]
    draw.text(((W - wmw) // 2, round(490 * SCALE) - (bb[3] - bb[1])),
              wm, fill=pal["ink"], font=wf)

    sf1 = _font(round(22 * SCALE), bold=False)
    s1 = "scriptable visual production toolkit"
    bb1 = draw.textbbox((0, 0), s1, font=sf1)
    s1w = bb1[2] - bb1[0]
    draw.text(((W - s1w) // 2, round(532 * SCALE) - (bb1[3] - bb1[1])),
              s1, fill=pal["ink"], font=sf1)

    sf2 = _font(round(17 * SCALE), bold=False)
    s2 = "for researcher-designer-engineers"
    bb2 = draw.textbbox((0, 0), s2, font=sf2)
    s2w = bb2[2] - bb2[0]
    draw.text(((W - s2w) // 2, round(558 * SCALE) - (bb2[3] - bb2[1])),
              s2, fill=pal["ink_soft"], font=sf2)

    return img


def build_gif(mode: str) -> Path:
    pal = PALETTES[mode]
    suffix = "" if mode == "light" else f"-{mode}"
    out_path = OUT_DIR / f"muriel-logo-animated{suffix}.gif"

    frames = [render_frame(H_POSE_TIME, pal)]
    durations = [PAUSE_MS]
    for i in range(1, N_FRAMES):
        t = (i / N_FRAMES) * LOOP_DURATION
        frames.append(render_frame(t, pal))
        durations.append(POSE_MS)

    frames[0].save(
        out_path,
        save_all=True, append_images=frames[1:],
        duration=durations, loop=GIF_LOOPS,
        optimize=True, disposal=2,
    )
    size_kb = out_path.stat().st_size / 1024
    print(f"  → {out_path} ({size_kb:.0f} KB, {mode})")
    return out_path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {N_FRAMES}-pose slideshow GIF ({GIF_LOOPS} loops) — light + dark...")
    build_gif("light")
    build_gif("dark")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
