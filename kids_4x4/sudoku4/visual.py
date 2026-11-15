"""Visual & Dad-and-Me workbook editions.

Generates two word-light, visual-heavy workbook styles (each in both numbered
and 4-color piece editions) alongside the original workbook:

1. Visual Edition (`workbook_visual.pdf`, `workbook_visual_colors.pdf`):
   - Almost wordless 3-step comic storyboards (LOOK -> BLOCK/ZAP -> PLACE!)
     on every lesson page.
   - Symbol-only puzzle headers (no puzzle numbers; each puzzle is identified
     by a nature/toy icon + visual technique theme badge(s)).

2. Dad & Me Edition (`workbook_toddler.pdf`, `workbook_toddler_colors.pdf`):
   - Top 2/3 of each lesson page is a 100% visual 3-step picture sequence +
     finger-counting piece bar for kids.
   - Bottom 1/3 is a "FOR DAD" script box with 3 short finger-pointing
     prompts ("Say & Point Together") and a playful game idea.
   - Symbol-only puzzle pages with big icons kids can name ("Sun",
     "Rocket", "Fish", "Butterfly"...).
"""

from __future__ import annotations

import math
import os

from . import grid as G
from . import logic as L
from .generate import LEVEL_BY_NUM, allowed_of, variant_of, S
from .pdf import PDF, text_width, wrap

INK = "#1d1d1f"
BOARD = "#e9e9e6"
WELL = "#ffffff"
BAR = "#26313a"
HL_UNIT = "#fff3b0"
HL_TARGET = "#b7ebc0"
HL_BAD = "#f8c4c4"
STRIKE = "#d62828"
GOOD = "#1b873f"
ACCENT_BLUE = "#1d6fd8"
ACCENT_AMBER = "#e07a00"
MARGIN = 36.0

PIECE_PALETTE = {
    1: ("#0178d4", "#004e8c", "Blue"),
    2: ("#db2134", "#8f111e", "Red"),
    3: ("#eab47f", "#9e632c", "Tan"),
    4: ("#22ab7e", "#116346", "Green"),
}

# 12 kid-friendly icons so every puzzle in a 12-puzzle set has a unique symbol
PUZZLE_ICONS = [
    ("sun", "Sun"),
    ("moon", "Moon"),
    ("star", "Star"),
    ("heart", "Heart"),
    ("clover", "Clover"),
    ("crown", "Crown"),
    ("rocket", "Rocket"),
    ("boat", "Boat"),
    ("fish", "Fish"),
    ("flower", "Flower"),
    ("tree", "Tree"),
    ("butterfly", "Butterfly"),
]


# ---------------------------------------------------------------------------
# Vector Icon & Badge Primitives
# ---------------------------------------------------------------------------

def draw_arrow(pg, x1, y1, x2, y2, color=STRIKE, width=1.8, head=5.5, dashed=False):
    """Draw a line from (x1, y1) to (x2, y2) with a filled triangular arrowhead."""
    dx, dy = x2 - x1, y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-3:
        return
    ux, uy = dx / dist, dy / dist
    px, py = -uy, ux
    pg.stroke_color(color)
    pg.fill_color(color)
    pg.line_width(width)
    if dashed:
        pg.dash(4, 2.5)
    pg.line(x1, y1, x2 - ux * head * 0.7, y2 - uy * head * 0.7)
    if dashed:
        pg.dash()
    bx, by = x2 - ux * head, y2 - uy * head
    hw = head * 0.52
    pg.polygon([(x2, y2), (bx + px * hw, by + py * hw), (bx - px * hw, by - py * hw)],
               fill=True, stroke=False)


def draw_knight_icon(pg, cx, cy, r, fill_c="#37474f", stroke_c="#ffffff", lw=0.8):
    """Draw a recognizable chess knight (horse head + mane + base) inside radius r."""
    pts = [
        (cx - r * 0.55, cy + r * 0.72),  # base bottom-left
        (cx + r * 0.55, cy + r * 0.72),  # base bottom-right
        (cx + r * 0.45, cy + r * 0.48),  # base top-right
        (cx + r * 0.25, cy + r * 0.42),  # chest
        (cx + r * 0.30, cy - r * 0.02),  # throat
        (cx + r * 0.62, cy - r * 0.12),  # lower jaw / snout bottom
        (cx + r * 0.68, cy - r * 0.32),  # nose tip
        (cx + r * 0.28, cy - r * 0.48),  # forehead
        (cx + r * 0.18, cy - r * 0.78),  # ear front
        (cx - r * 0.04, cy - r * 0.56),  # ear back
        (cx - r * 0.38, cy - r * 0.32),  # upper mane
        (cx - r * 0.48, cy + r * 0.12),  # lower mane
        (cx - r * 0.35, cy + r * 0.45),  # back base
        (cx - r * 0.55, cy + r * 0.50),  # base top-left
    ]
    pg.fill_color(fill_c)
    pg.stroke_color(stroke_c)
    pg.line_width(lw)
    pg.polygon(pts, fill=True, stroke=True)
    # eye dot
    pg.fill_color(stroke_c)
    pg.circle(cx + r * 0.20, cy - r * 0.32, max(0.8, r * 0.09), fill=True, stroke=False)


def draw_check_icon(pg, cx, cy, r, color=GOOD, lw=2.2):
    pg.stroke_color(color)
    pg.line_width(lw)
    pg.line_cap(1)
    pg.line(cx - r * 0.55, cy + r * 0.05, cx - r * 0.12, cy + r * 0.48)
    pg.line(cx - r * 0.12, cy + r * 0.48, cx + r * 0.60, cy - r * 0.45)
    pg.line_cap(0)


def draw_x_icon(pg, cx, cy, r, color=STRIKE, lw=2.0):
    pg.stroke_color(color)
    pg.line_width(lw)
    pg.line_cap(1)
    pg.line(cx - r, cy - r, cx + r, cy + r)
    pg.line(cx - r, cy + r, cx + r, cy - r)
    pg.line_cap(0)


def draw_step_badge(pg, cx, cy, r, step_no):
    """Draw a circular step icon for Storyboard panels 1 (Look), 2 (Zap/Block), 3 (Place!)."""
    if step_no == 1:
        # Blue Eye / Magnifying Glass badge
        pg.fill_color("#e3f2fd")
        pg.stroke_color(ACCENT_BLUE)
        pg.line_width(1.4)
        pg.circle(cx, cy, r, fill=True, stroke=True)
        # Eye outline + pupil
        pg.fill_color("#ffffff")
        pg.stroke_color(ACCENT_BLUE)
        pg.line_width(1.2)
        pts = [
            (cx - r * 0.62, cy),
            (cx - r * 0.28, cy - r * 0.36),
            (cx + r * 0.28, cy - r * 0.36),
            (cx + r * 0.62, cy),
            (cx + r * 0.28, cy + r * 0.36),
            (cx - r * 0.28, cy + r * 0.36),
        ]
        pg.polygon(pts, fill=True, stroke=True)
        pg.fill_color(ACCENT_BLUE)
        pg.circle(cx, cy, r * 0.22, fill=True, stroke=False)
    elif step_no == 2:
        # Red/Amber Block / Zap badge
        pg.fill_color("#ffebee")
        pg.stroke_color(STRIKE)
        pg.line_width(1.4)
        pg.circle(cx, cy, r, fill=True, stroke=True)
        draw_x_icon(pg, cx, cy, r * 0.42, color=STRIKE, lw=2.2)
    else:
        # Green Place / Checkmark badge
        pg.fill_color("#e6f4ea")
        pg.stroke_color(GOOD)
        pg.line_width(1.4)
        pg.circle(cx, cy, r, fill=True, stroke=True)
        draw_check_icon(pg, cx, cy, r * 0.65, color=GOOD, lw=2.4)


def draw_puzzle_icon(pg, cx, cy, r, idx):
    """Draw one of the 12 kid-friendly shape/nature icons at (cx, cy) within radius r."""
    kind = PUZZLE_ICONS[idx % len(PUZZLE_ICONS)][0]
    if kind == "sun":
        pg.stroke_color("#f59f00")
        pg.line_width(1.4)
        for k in range(8):
            ang = k * math.pi / 4.0
            pg.line(cx + math.cos(ang) * r * 0.58, cy + math.sin(ang) * r * 0.58,
                    cx + math.cos(ang) * r * 0.96, cy + math.sin(ang) * r * 0.96)
        pg.fill_color("#ffd43b")
        pg.stroke_color("#e67700")
        pg.line_width(1.0)
        pg.circle(cx, cy, r * 0.48, fill=True, stroke=True)
    elif kind == "moon":
        pg.fill_color("#ffd43b")
        pg.stroke_color("#d9480f")
        pg.line_width(1.0)
        pg.circle(cx, cy, r * 0.80, fill=True, stroke=True)
        pg.fill_color("#ffffff")
        pg.circle(cx + r * 0.30, cy - r * 0.18, r * 0.62, fill=True, stroke=False)
    elif kind == "star":
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5.0
            rad = r * 0.92 if k % 2 == 0 else r * 0.40
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pg.fill_color("#fcc419")
        pg.stroke_color("#d9480f")
        pg.line_width(1.0)
        pg.polygon(pts, fill=True, stroke=True)
    elif kind == "heart":
        pg.fill_color("#ff6b6b")
        pg.stroke_color("#c92a2a")
        pg.line_width(1.0)
        pg.circle(cx - r * 0.32, cy - r * 0.22, r * 0.42, fill=True, stroke=True)
        pg.circle(cx + r * 0.32, cy - r * 0.22, r * 0.42, fill=True, stroke=True)
        pg.polygon([
            (cx - r * 0.70, cy - r * 0.06),
            (cx + r * 0.70, cy - r * 0.06),
            (cx, cy + r * 0.82),
        ], fill=True, stroke=False)
        pg.line(cx - r * 0.71, cy - r * 0.04, cx, cy + r * 0.82)
        pg.line(cx + r * 0.71, cy - r * 0.04, cx, cy + r * 0.82)
    elif kind == "clover":
        pg.stroke_color("#2b8a3e")
        pg.line_width(1.4)
        pg.line(cx, cy + r * 0.1, cx + r * 0.22, cy + r * 0.88)
        pg.fill_color("#51cf66")
        pg.stroke_color("#2b8a3e")
        pg.line_width(0.9)
        for ox, oy in ((0, -0.34), (-0.34, 0.14), (0.34, 0.14)):
            pg.circle(cx + ox * r, cy + oy * r, r * 0.36, fill=True, stroke=True)
    elif kind == "crown":
        pts = [
            (cx - r * 0.78, cy + r * 0.55),
            (cx + r * 0.78, cy + r * 0.55),
            (cx + r * 0.85, cy - r * 0.45),
            (cx + r * 0.38, cy + r * 0.05),
            (cx, cy - r * 0.65),
            (cx - r * 0.38, cy + r * 0.05),
            (cx - r * 0.85, cy - r * 0.45),
        ]
        pg.fill_color("#ffd43b")
        pg.stroke_color("#e67700")
        pg.line_width(1.0)
        pg.polygon(pts, fill=True, stroke=True)
    elif kind == "rocket":
        pg.fill_color("#fa5252")
        pg.stroke_color("#c92a2a")
        pg.line_width(0.9)
        pg.polygon([(cx - r * 0.65, cy + r * 0.65), (cx - r * 0.30, cy + r * 0.15),
                    (cx - r * 0.30, cy + r * 0.65)], fill=True, stroke=True)
        pg.polygon([(cx + r * 0.65, cy + r * 0.65), (cx + r * 0.30, cy + r * 0.15),
                    (cx + r * 0.30, cy + r * 0.65)], fill=True, stroke=True)
        pg.fill_color("#e9ecef")
        pg.stroke_color("#495057")
        pg.polygon([
            (cx, cy - r * 0.88),
            (cx + r * 0.34, cy - r * 0.25),
            (cx + r * 0.34, cy + r * 0.62),
            (cx - r * 0.34, cy + r * 0.62),
            (cx - r * 0.34, cy - r * 0.25),
        ], fill=True, stroke=True)
        pg.fill_color("#339af0")
        pg.circle(cx, cy - r * 0.05, r * 0.18, fill=True, stroke=True)
    elif kind == "boat":
        pg.fill_color("#4dabf7")
        pg.stroke_color("#1864ab")
        pg.line_width(0.9)
        pg.polygon([(cx - r * 0.05, cy - r * 0.82), (cx + r * 0.68, cy + r * 0.18),
                    (cx - r * 0.05, cy + r * 0.18)], fill=True, stroke=True)
        pg.fill_color("#fcc419")
        pg.polygon([(cx - r * 0.15, cy - r * 0.62), (cx - r * 0.68, cy + r * 0.18),
                    (cx - r * 0.15, cy + r * 0.18)], fill=True, stroke=True)
        pg.fill_color("#c92a2a")
        pg.stroke_color("#862e9c")
        pg.polygon([
            (cx - r * 0.82, cy + r * 0.28),
            (cx + r * 0.82, cy + r * 0.28),
            (cx + r * 0.52, cy + r * 0.72),
            (cx - r * 0.52, cy + r * 0.72),
        ], fill=True, stroke=True)
    elif kind == "fish":
        pg.fill_color("#ff922b")
        pg.stroke_color("#d9480f")
        pg.line_width(1.0)
        pg.polygon([
            (cx + r * 0.25, cy),
            (cx + r * 0.88, cy - r * 0.52),
            (cx + r * 0.88, cy + r * 0.52),
        ], fill=True, stroke=True)
        pg.polygon([
            (cx - r * 0.88, cy),
            (cx - r * 0.35, cy - r * 0.55),
            (cx + r * 0.35, cy - r * 0.42),
            (cx + r * 0.52, cy),
            (cx + r * 0.35, cy + r * 0.42),
            (cx - r * 0.35, cy + r * 0.55),
        ], fill=True, stroke=True)
        pg.fill_color("#ffffff")
        pg.circle(cx - r * 0.42, cy - r * 0.12, r * 0.12, fill=True, stroke=False)
        pg.fill_color(INK)
        pg.circle(cx - r * 0.44, cy - r * 0.12, r * 0.06, fill=True, stroke=False)
    elif kind == "flower":
        pg.fill_color("#f783ac")
        pg.stroke_color("#a61e4d")
        pg.line_width(0.8)
        for k in range(6):
            ang = k * math.pi / 3.0
            pg.circle(cx + math.cos(ang) * r * 0.46, cy + math.sin(ang) * r * 0.46,
                      r * 0.32, fill=True, stroke=True)
        pg.fill_color("#ffd43b")
        pg.stroke_color("#e67700")
        pg.circle(cx, cy, r * 0.30, fill=True, stroke=True)
    elif kind == "tree":
        pg.fill_color("#8b5a2b")
        pg.rect(cx - r * 0.18, cy + r * 0.38, r * 0.36, r * 0.48, fill=True, stroke=False)
        pg.fill_color("#40c057")
        pg.stroke_color("#2b8a3e")
        pg.line_width(0.9)
        pg.polygon([(cx, cy - r * 0.35), (cx + r * 0.78, cy + r * 0.42),
                    (cx - r * 0.78, cy + r * 0.42)], fill=True, stroke=True)
        pg.polygon([(cx, cy - r * 0.85), (cx + r * 0.60, cy - r * 0.05),
                    (cx - r * 0.60, cy - r * 0.05)], fill=True, stroke=True)
    else:  # butterfly
        pg.fill_color("#cc5de8")
        pg.stroke_color("#862e9c")
        pg.line_width(0.9)
        for sx in (-1, 1):
            pg.circle(cx + sx * r * 0.42, cy - r * 0.26, r * 0.38, fill=True, stroke=True)
            pg.circle(cx + sx * r * 0.34, cy + r * 0.28, r * 0.30, fill=True, stroke=True)
        pg.fill_color("#343a40")
        pg.round_rect(cx - r * 0.10, cy - r * 0.58, r * 0.20, r * 1.16, r * 0.09, fill=True, stroke=False)


def draw_theme_badge(pg, cx, cy, r, key, use_colors=False):
    """Draw a compact visual badge representing one of the 10 technique themes."""
    pg.fill_color("#f8f9fa")
    pg.stroke_color("#495057")
    pg.line_width(1.1)
    pg.round_rect(cx - r, cy - r, 2 * r, 2 * r, r * 0.26, fill=True, stroke=True)
    if key == "hidden_single":
        # 2x2 mini box: 3 crossed cells + 1 bright green target cell
        s = r * 0.68
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            bx = cx + dc * s * 0.5 - s * 0.42
            by = cy + dr * s * 0.5 - s * 0.42
            is_tgt = (dr == 1 and dc == 1)
            pg.fill_color(HL_TARGET if is_tgt else HL_UNIT)
            pg.stroke_color(GOOD if is_tgt else "#adb5bd")
            pg.line_width(0.8)
            pg.rect(bx, by, s * 0.84, s * 0.84, fill=True, stroke=True)
            if is_tgt:
                pg.fill_color(GOOD)
                pg.circle(bx + s * 0.42, by + s * 0.42, s * 0.24, fill=True, stroke=False)
            else:
                draw_x_icon(pg, bx + s * 0.42, by + s * 0.42, s * 0.20, color=STRIKE, lw=1.2)
    elif key == "naked_single":
        # 3 small colored dots pointing into 1 central green cell
        pg.fill_color(HL_TARGET)
        pg.stroke_color(GOOD)
        pg.line_width(1.1)
        pg.round_rect(cx - r * 0.42, cy - r * 0.12, r * 0.84, r * 0.84, r * 0.15, fill=True, stroke=True)
        for idx_d, ox in enumerate((-0.55, 0.0, 0.55), 1):
            c_fill = PIECE_PALETTE[idx_d][0] if use_colors else "#495057"
            pg.fill_color(c_fill)
            pg.circle(cx + ox * r, cy - r * 0.55, r * 0.20, fill=True, stroke=False)
        pg.fill_color(PIECE_PALETTE[4][0] if use_colors else GOOD)
        pg.circle(cx, cy + r * 0.30, r * 0.24, fill=True, stroke=False)
    elif key == "center_marks":
        # Cell with 2 center pegs: one crossed out, one circled in green
        pg.fill_color("#ffffff")
        pg.stroke_color("#868e96")
        pg.line_width(0.9)
        pg.round_rect(cx - r * 0.72, cy - r * 0.72, r * 1.44, r * 1.44, r * 0.18, fill=True, stroke=True)
        # top-left peg (survives, green ring)
        p1x, p1y = cx - r * 0.30, cy - r * 0.30
        pg.fill_color(PIECE_PALETTE[1][0] if use_colors else "#ffffff")
        pg.stroke_color(GOOD)
        pg.line_width(1.4)
        pg.circle(p1x, p1y, r * 0.26, fill=True, stroke=True)
        # bottom-left peg (crossed out)
        p2x, p2y = cx - r * 0.30, cy + r * 0.30
        pg.fill_color(PIECE_PALETTE[3][0] if use_colors else "#ffffff")
        pg.stroke_color("#868e96")
        pg.line_width(0.8)
        pg.circle(p2x, p2y, r * 0.22, fill=True, stroke=True)
        draw_x_icon(pg, p2x, p2y, r * 0.22, color=STRIKE, lw=1.4)
    elif key == "snyder":
        # Two diagonal square corner marks in a box
        for sx, sy, alive in ((-0.42, -0.42, False), (0.42, 0.42, True)):
            px, py = cx + sx * r, cy + sy * r
            pg.fill_color(PIECE_PALETTE[1][0] if use_colors else (HL_TARGET if alive else "#ffffff"))
            pg.stroke_color(GOOD if alive else "#495057")
            pg.line_width(1.2 if alive else 0.8)
            pg.rect(px - r * 0.32, py - r * 0.32, r * 0.64, r * 0.64, fill=True, stroke=True)
            if not alive:
                draw_x_icon(pg, px, py, r * 0.26, color=STRIKE, lw=1.4)
    elif key == "pointing":
        # Two aligned corner squares shooting a laser arrow right to zap a 3rd
        for sy in (-0.38, 0.38):
            px, py = cx - r * 0.48, cy + sy * r
            pg.fill_color(PIECE_PALETTE[2][0] if use_colors else HL_TARGET)
            pg.stroke_color(GOOD)
            pg.line_width(0.9)
            pg.rect(px - r * 0.22, py - r * 0.22, r * 0.44, r * 0.44, fill=True, stroke=True)
        draw_arrow(pg, cx - r * 0.15, cy, cx + r * 0.38, cy, color=STRIKE, width=1.5, head=4.2)
        draw_x_icon(pg, cx + r * 0.56, cy, r * 0.22, color=STRIKE, lw=1.5)
    elif key == "naked_pair":
        # Two green twin cells side by side linked with an "=" bridge
        for sx in (-0.42, 0.42):
            px = cx + sx * r
            pg.fill_color(HL_TARGET)
            pg.stroke_color(GOOD)
            pg.line_width(1.0)
            pg.round_rect(px - r * 0.34, cy - r * 0.44, r * 0.68, r * 0.88, r * 0.12, fill=True, stroke=True)
            pg.fill_color(PIECE_PALETTE[1][0] if use_colors else INK)
            pg.circle(px - r * 0.13, cy - r * 0.14, r * 0.11, fill=True, stroke=False)
            pg.fill_color(PIECE_PALETTE[3][0] if use_colors else INK)
            pg.circle(px + r * 0.13, cy + r * 0.14, r * 0.11, fill=True, stroke=False)
        pg.stroke_color(GOOD)
        pg.line_width(1.6)
        pg.line(cx - r * 0.10, cy - r * 0.08, cx + r * 0.10, cy - r * 0.08)
        pg.line(cx - r * 0.10, cy + r * 0.08, cx + r * 0.10, cy + r * 0.08)
    elif key in ("xwing", "xwing_boss"):
        if key == "xwing_boss":
            # Extra red/amber emphasis border around the X-Wing badge
            pg.fill_color("#fff8e6")
            pg.stroke_color(STRIKE)
            pg.line_width(1.6)
            pg.round_rect(cx - r, cy - r, 2 * r, 2 * r, r * 0.28, fill=True, stroke=True)
        # 4 green corners + diagonal X
        pg.stroke_color(GOOD)
        pg.line_width(1.6)
        pg.line(cx - r * 0.52, cy - r * 0.52, cx + r * 0.52, cy + r * 0.52)
        pg.line(cx + r * 0.52, cy - r * 0.52, cx - r * 0.52, cy + r * 0.52)
        for sx in (-0.52, 0.52):
            for sy in (-0.52, 0.52):
                pg.fill_color(HL_TARGET)
                pg.stroke_color(GOOD)
                pg.line_width(1.0)
                pg.circle(cx + sx * r, cy + sy * r, r * 0.24, fill=True, stroke=True)
    elif key == "xwing_warn":
        # High-visibility warning badge (!) emphasizing that an X-Wing is required
        pg.fill_color("#fff3cd")
        pg.stroke_color(STRIKE)
        pg.line_width(1.4)
        pg.round_rect(cx - r, cy - r, 2 * r, 2 * r, r * 0.28, fill=True, stroke=True)
        pg.fill_color("#f59f00")
        pg.stroke_color(STRIKE)
        pg.line_width(1.1)
        tri = [(cx, cy - r * 0.68), (cx + r * 0.68, cy + r * 0.58), (cx - r * 0.68, cy + r * 0.58)]
        pg.polygon(tri, fill=True, stroke=True)
        pg.stroke_color(INK)
        pg.line_width(max(1.4, r * 0.22))
        pg.line_cap(1)
        pg.line(cx, cy - r * 0.24, cx, cy + r * 0.14)
        pg.line_cap(0)
        pg.fill_color(INK)
        pg.circle(cx, cy + r * 0.38, r * 0.11, fill=True, stroke=False)
    elif key == "jigsaw":
        # L-shaped 4-cell polyomino in warm tint with thick outline
        u = r * 0.44
        cells = [(-1, -1), (-1, 0), (-1, 1), (0, 1)]
        pg.fill_color("#f6f3e3")
        pg.stroke_color(BAR)
        pg.line_width(1.4)
        for gx, gy in cells:
            pg.rect(cx + gx * u - u * 0.2, cy + gy * u - u * 0.5, u, u, fill=True, stroke=True)
    elif key == "anti_knight":
        draw_knight_icon(pg, cx, cy, r * 0.78, fill_c="#26313a", stroke_c="#ffffff", lw=0.7)
    else:  # all_star
        draw_puzzle_icon(pg, cx, cy, r * 0.80, 2)  # gold star


def tech_badges_for_puzzle(p, level):
    """Return 1-3 theme badge keys describing the techniques used by puzzle `p`."""
    if level < 10:
        return [LEVEL_BY_NUM[level]["key"]]
    t = p.get("technique", "")
    mapping = {
        "Singles Warm-Up": ["hidden_single"],
        "Singles + Self-Pegging": ["naked_single", "center_marks"],
        "Minimal Singles": ["hidden_single", "naked_single"],
        "Center Marks": ["center_marks"],
        "Snyder Corner Marks": ["snyder"],
        "Center + Corner Combo": ["center_marks", "snyder"],
        "Jigsaw Sudoku": ["jigsaw"],
        "Anti-Knight": ["anti_knight"],
        "Pointing Pairs": ["pointing"],
        "Naked Pair": ["naked_pair"],
        "Jigsaw + Pointing": ["jigsaw", "pointing"],
        "Anti-Knight + Pointing": ["anti_knight", "pointing"],
        "Jigsaw + Naked Pair": ["jigsaw", "naked_pair"],
        "Anti-Knight + Naked Pair": ["anti_knight", "naked_pair"],
        "Jigsaw + Anti-Knight": ["jigsaw", "anti_knight"],
        "X-Wing": ["xwing_warn", "xwing_boss"],
        "Jigsaw + X-Wing": ["jigsaw", "xwing_warn", "xwing_boss"],
        "Anti-Knight + X-Wing": ["anti_knight", "xwing_warn", "xwing_boss"],
    }
    return mapping.get(t, ["all_star"])


# ---------------------------------------------------------------------------
# 3-Step Visual Storyboards + Dad & 3-Year-Old Scripts for Levels 1..10
# ---------------------------------------------------------------------------

def build_storyboard(example, level, use_colors=False, xwing_axis="row"):
    """Return a dict with:
      - 'panels': list of 3 (board_record, draw_kwargs, short_caption) tuples
      - 'formula': short visual rule phrase
      - 'dad_steps': list of 3 finger-pointing lines for Dad to say to a 3-year-old
      - 'dad_game': playful 1-line game idea for a 3-year-old
    """
    tok = (lambda d: PIECE_PALETTE[d][2]) if use_colors else str
    noun = "color" if use_colors else "number"

    if level == 1:
        # Clean teaching board for Hidden Single in top-right box:
        # Top-right box (cells 2, 3, 6, 7) needs 3 (Tan).
        # R1C1 (0) = 3 blocks row 1 (cells 2, 3). R4C3 (14) = 3 blocks col 3 (cells 2, 6).
        # Only R2C4 (7) is open!
        demo = {
            "givens": [3, 0, 0, 0,
                       0, 2, 0, 0,
                       0, 0, 0, 1,
                       0, 0, 3, 0],
            "solution": [3, 4, 1, 2,
                         1, 2, 4, 3,
                         4, 3, 2, 1,
                         2, 1, 3, 4],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {}, "center_clues": {}, "corner_clues": [], "fog_lit": None,
        }
        box = [2, 3, 6, 7]
        p1 = (demo, {"hl": {**{c: HL_UNIT for c in box}, 0: HL_TARGET, 14: HL_TARGET}},
              f"1. Box needs {tok(3)}")
        p2 = (demo, {"hl": {2: HL_BAD, 3: HL_BAD, 6: HL_BAD, 7: HL_UNIT},
                     "block_arrows": [(0, 3), (14, 2)],
                     "cell_strikes": [2, 3, 6]},
              f"2. {tok(3)} blocks 3 cells")
        p3 = (demo, {"hl": {2: HL_UNIT, 3: HL_UNIT, 6: HL_UNIT, 7: HL_TARGET},
                     "cell_strikes": [2, 3, 6],
                     "target": (7, 3)},
              f"3. Only 1 cell left -> {tok(3)}!")
        return {
            "panels": [p1, p2, p3],
            "formula": f"3 cells blocked in a box  ->  last cell gets {tok(3)}!",
            "dad_steps": [
                f"\"Put your finger on the yellow box! It needs a {tok(3)} piece.\"",
                f"\"Zoom your finger from the other {tok(3)}s! Zoom across the top (X, X) and zoom up (X)!\"",
                f"\"Where is the ONLY safe home left for {tok(3)}? Right in the green spot!\"",
            ],
            "dad_game": f"Game: \"No-Go Train!\" Drive your finger like a train from each {tok(3)} across its row and column!",
        }

    if level == 2:
        # Clean teaching board for Naked Single at R2C2 (cell 5):
        # R2C1 (4) = 1 (in row/box), R2C4 (7) = 2 (in row), R4C2 (13) = 4 (in col) -> R2C2 must be 3!
        demo = {
            "givens": [0, 0, 0, 0,
                       1, 0, 0, 2,
                       0, 0, 0, 0,
                       0, 4, 0, 0],
            "solution": [4, 2, 1, 3,
                         1, 3, 4, 2,
                         3, 1, 2, 4,
                         2, 4, 3, 1],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {}, "center_clues": {}, "corner_clues": [], "fog_lit": None,
        }
        peers_hl = {0: HL_UNIT, 1: HL_UNIT, 4: HL_UNIT, 6: HL_UNIT, 7: HL_UNIT, 9: HL_UNIT, 13: HL_UNIT, 5: HL_TARGET}
        p1 = (demo, {"hl": {5: HL_TARGET}}, "1. Point at 1 cell")
        p2 = (demo, {"hl": peers_hl, "block_arrows": [(4, 5), (7, 5), (13, 5)]},
              f"2. Sees {tok(1)}, {tok(2)}, {tok(4)}")
        p3 = (demo, {"hl": peers_hl, "target": (5, 3)},
              f"3. Missing {tok(3)} goes here!")
        return {
            "panels": [p1, p2, p3],
            "formula": f"Row + Column + Box already have 3 {noun}s  ->  4th {noun} goes in!",
            "dad_steps": [
                "\"Tap the green spot! Let's see who lives around it.\"",
                f"\"Touch them with me: I see {tok(1)}... I see {tok(2)}... and down here I see {tok(4)}!\"",
                f"\"Who is the ONLY friend missing? {tok(3)}! Put {tok(3)} in the green spot!\"",
            ],
            "dad_game": "Game: \"Roll Call!\" Touch the 4 pieces at the bottom of the page as you spot them!",
        }

    if level == 3:
        # Center Marks teaching board
        demo = {
            "givens": [0, 4, 0, 0,
                       0, 0, 2, 0,
                       0, 0, 0, 0,
                       0, 0, 0, 0],
            "solution": [2, 4, 3, 1,
                         1, 3, 2, 4,
                         4, 2, 1, 3,
                         3, 1, 4, 2],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {},
            "center_clues": {"4": [1, 3]},
            "corner_clues": [], "fog_lit": None,
        }
        vals2 = list(demo["givens"])
        vals2[12] = 3
        p1 = (demo, {"hl": {1: HL_UNIT, 6: HL_UNIT, 4: HL_TARGET},
                     "block_arrows": [(1, 4), (6, 4)]},
              f"1. Only {tok(1)} or {tok(3)} fit")
        p2 = (demo, {"hl": {12: HL_UNIT, 4: HL_TARGET}, "values": vals2,
                     "block_arrows": [(12, 4)], "strikes": [(4, 3)],
                     "peg_target": (4, 1)},
              f"2. {tok(3)} in col -> zap {tok(3)} peg")
        p3 = (demo, {"hl": {12: HL_UNIT, 4: HL_TARGET}, "values": vals2,
                     "target": (4, 1)},
              f"3. Only {tok(1)} peg left!")
        return {
            "panels": [p1, p2, p3],
            "formula": "2 little center pegs in a cell  ->  cross 1 out  ->  last peg wins!",
            "dad_steps": [
                f"\"Look inside the green spot: two little baby pegs ({tok(1)} and {tok(3)}) are waiting inside!\"",
                f"\"Look down at the bottom: big {tok(3)} moved in! Pull out the baby {tok(3)} peg!\"",
                f"\"Only baby {tok(1)} is left! Trade baby {tok(1)} for the big {tok(1)} piece!\"",
            ],
            "dad_game": "Game: \"Baby Peg Swap!\" Pull out blocked baby pegs until only 1 baby peg is left!",
        }

    if level == 4:
        # Clean, self-contained teaching board for Snyder Corner Marks:
        # - In top-right box (2, 3, 6, 7), R4C3 (14) = 1 blocks col 3 (R1C3, R2C3),
        #   so 1 can only go in R1C4 (3) or R2C4 (7) -> corner marks [1, [3, 7]].
        # - Then R1C4 (3) gets filled with 4, so 1 must go in R2C4 (7)!
        demo = {
            "givens": [0, 0, 2, 0,
                       4, 0, 0, 0,
                       0, 0, 0, 0,
                       0, 0, 1, 0],
            "solution": [1, 3, 2, 4,
                         4, 2, 3, 1,
                         2, 1, 4, 3,
                         3, 4, 1, 2],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {}, "center_clues": {},
            "corner_clues": [[1, [3, 7]]],
            "fog_lit": None,
        }
        vals2 = list(demo["givens"])
        vals2[3] = 4
        unit = [2, 3, 6, 7]
        p1 = (demo, {"hl": {**{c: HL_UNIT for c in unit}, 14: HL_TARGET},
                     "block_arrows": [(14, 2)],
                     "corner_target": (7, 1)},
              f"1. {tok(1)} in 1 of 2 corners")
        p2 = (demo, {"hl": {**{c: HL_UNIT for c in unit}, 3: HL_BAD},
                     "values": vals2,
                     "strikes": [(3, 1)],
                     "corner_target": (7, 1)},
              f"2. {tok(4)} fills 1 cell!")
        p3 = (demo, {"hl": {**{c: HL_UNIT for c in unit}, 3: HL_BAD, 7: HL_TARGET},
                     "values": vals2,
                     "strikes": [(3, 1)],
                     "target": (7, 1)},
              f"3. Other corner gets {tok(1)}!")
        return {
            "panels": [p1, p2, p3],
            "formula": "2 corner marks in a box  ->  1 cell fills up  ->  other cell gets it!",
            "dad_steps": [
                f"\"In the yellow box, touch the two little {tok(1)} squares hiding in the corners!\"",
                f"\"Uh-oh! Big {tok(4)} sat down on top of the top corner! No room for {tok(1)} there!\"",
                f"\"Where is the other little {tok(1)} corner? Put big {tok(1)} right there!\"",
            ],
            "dad_game": "Game: \"Musical Chairs!\" Two seats for one piece - when one seat is taken, take the other!",
        }

    if level == 5:
        # Clean, self-contained teaching board for Pointing Pairs:
        # - Top-right box has R1C3 = 4 and R2C3 = 3, so 2 can only go in R1C4 (3) or R2C4 (7) (both in col 4).
        # - Bottom-right box has R3C1 = 2 blocking row 3, so 2 can only go in R4C3 (14) or R4C4 (15).
        # - The two 2 corner marks in the top-right box point down column 4 and zap R4C4 (15),
        #   leaving R4C3 (14) as the only spot for 2 in the bottom-right box!
        demo = {
            "givens": [0, 0, 4, 0,
                       0, 0, 3, 0,
                       2, 0, 0, 0,
                       0, 0, 0, 0],
            "solution": [3, 2, 4, 1,
                         4, 1, 3, 2,
                         2, 4, 1, 3,
                         1, 3, 2, 4],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {}, "center_clues": {},
            "corner_clues": [[2, [3, 7]], [2, [14, 15]]],
            "fog_lit": None,
        }
        p1 = (demo, {"hl": {3: HL_TARGET, 7: HL_TARGET}},
              f"1. {tok(2)} corners in 1 col")
        p2 = (demo, {"hl": {3: HL_TARGET, 7: HL_TARGET, 11: HL_UNIT, 15: HL_BAD},
                     "block_arrows": [(7, 15)],
                     "strikes": [(15, 2)],
                     "corner_target": (14, 2)},
              f"2. Laser zaps {tok(2)} in col!")
        p3 = (demo, {"hl": {10: HL_UNIT, 11: HL_UNIT, 14: HL_TARGET, 15: HL_BAD},
                     "strikes": [(15, 2)],
                     "target": (14, 2)},
              f"3. Place {tok(2)} in other spot!")
        return {
            "panels": [p1, p2, p3],
            "formula": "2 corner marks in 1 line  ->  laser zaps that line in the next box!",
            "dad_steps": [
                f"\"Look at the green spots: both little {tok(2)}s are lined up in a straight column!\"",
                f"\"Pew! Pew! Shoot a laser beam down that column and zap the {tok(2)} in the red spot!\"",
                f"\"Now only one {tok(2)} corner is left in the bottom box - put big {tok(2)} in!\"",
            ],
            "dad_game": "Game: \"Laser Beam!\" Lay a long bar across the two corner pegs and say PEW PEW!",
        }

    if level == 6:
        # Clean, self-contained teaching board for Naked Pair in Row 1:
        # - Top-left box has R2C1 = 2 and R2C2 = 4, so both R1C1 (0) and R1C2 (1) can only be 1 or 3 (Twins!).
        # - Row 1 has R1C4 = 4, so R1C3 (2) can only be 1, 2 or 3.
        # - The [1, 3] Twins in R1C1 & R1C2 use up 1 and 3 in Row 1, so cross 1 and 3 off R1C3 -> only 2 is left!
        demo = {
            "givens": [0, 0, 0, 4,
                       2, 4, 0, 0,
                       0, 0, 0, 0,
                       0, 0, 0, 0],
            "solution": [1, 3, 2, 4,
                         2, 4, 1, 3,
                         3, 1, 4, 2,
                         4, 2, 3, 1],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False, "colors": {},
            "center_clues": {"0": [1, 3], "1": [1, 3], "2": [1, 2, 3]},
            "corner_clues": [], "fog_lit": None,
        }
        p1 = (demo, {"hl": {0: HL_TARGET, 1: HL_TARGET, 2: HL_UNIT, 3: HL_UNIT},
                     "pair_link": (0, 1)},
              f"1. Twin cells: {tok(1)} & {tok(3)}")
        p2 = (demo, {"hl": {0: HL_TARGET, 1: HL_TARGET, 2: HL_UNIT, 3: HL_UNIT},
                     "pair_link": (0, 1),
                     "strikes": [(2, 1), (2, 3)],
                     "peg_target": (2, 2)},
              f"2. Cross {tok(1)} & {tok(3)} off neighbor!")
        p3 = (demo, {"hl": {0: HL_UNIT, 1: HL_UNIT, 2: HL_TARGET, 3: HL_UNIT},
                     "pair_link": (0, 1),
                     "target": (2, 2)},
              f"3. Only {tok(2)} left -> {tok(2)}!")
        return {
            "panels": [p1, p2, p3],
            "formula": f"2 cells in a row/col/box with the SAME 2 pegs ({tok(1)}, {tok(3)})  ->  zap {tok(1)} & {tok(3)} from the rest!",
            "dad_steps": [
                f"\"Look at the top row: two green Twin spots have the exact same two pegs ({tok(1)} and {tok(3)})!\"",
                f"\"The Twins use up {tok(1)} and {tok(3)} in that row, so cross {tok(1)} and {tok(3)} off the spot next door (X)!\"",
                f"\"Look what is the ONLY peg left in that spot now: {tok(2)}! Put big {tok(2)} in!\"",
            ],
            "dad_game": "Game: \"Twin Buddies!\" Point with two fingers at the two matching Twin cells!",
        }

    if level == 7:
        s = L.solve_logic(example["givens"], variant_of(example), S,
                          record=True, allowed=allowed_of(example))[1][0]
        d = s["digit"]
        cell = s["cell"]
        unit = s.get("unit") or next(b for b in G.region_units(example["regions"]) if cell in b)
        peers = G.peers_of(variant_of(example))
        blocked = [c for c in unit if c != cell and not example["givens"][c]]
        block_arrows = []
        for bc in blocked:
            src = next((q for q in peers[bc] if example["givens"][q] == d), None)
            if src is not None:
                block_arrows.append((src, bc))
        p1 = (example, {"hl": {c: HL_UNIT for c in unit}},
              "1. Trace the 4-cell shape")
        p2 = (example, {"hl": {**{c: HL_UNIT for c in unit}, **{bc: HL_BAD for bc in blocked}},
                        "block_arrows": block_arrows,
                        "cell_strikes": blocked},
              f"2. {tok(d)} blocked in shape")
        p3 = (example, {"hl": {**{c: HL_UNIT for c in unit}, cell: HL_TARGET},
                        "cell_strikes": blocked,
                        "target": (cell, d)},
              f"3. Last spot in shape -> {tok(d)}!")
        return {
            "panels": [p1, p2, p3],
            "formula": "Every thick-outlined wobbly shape has 4 cells and needs all 4 pieces!",
            "dad_steps": [
                "\"Trace the yellow wobbly shape with your finger! Count its 4 spots: 1, 2, 3, 4!\"",
                f"\"This shape needs a {tok(d)}, but those spots are blocked (X)!\"",
                f"\"Put {tok(d)} in the only open spot inside the wobbly shape!\"",
            ],
            "dad_game": "Game: \"Build the Walls!\" Let your child snap the short bars onto the board to build the shapes first!",
        }

    if level == 8:
        # Clean teaching board for Anti-Knight:
        # Top-right box (2, 3, 6, 7) needs 1 (Blue).
        # R2C1 (4) = 1 blocks R2C3 (6) & R2C4 (7) by row AND blocks R1C3 (2) by KNIGHT JUMP!
        # So only R1C4 (3) is safe in the top-right box!
        demo = {
            "givens": [0, 0, 0, 0,
                       1, 0, 0, 0,
                       0, 0, 0, 2,
                       0, 3, 0, 0],
            "solution": [2, 3, 4, 1,
                         1, 4, 2, 3,
                         3, 1, 4, 2,
                         4, 2, 1, 3],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": True, "colors": {}, "center_clues": {}, "corner_clues": [], "fog_lit": None,
        }
        empty_b = dict(demo, givens=[0] * 16)
        kn = G.knight_neighbors(5)
        p1 = (empty_b, {"hl": {5: HL_TARGET, **{c: HL_BAD for c in kn}},
                        "knight_from": 5,
                        "knight_jumps": [(5, c) for c in kn]},
              "1. Horsie jumps 2 + 1 (L)")
        p2 = (demo, {"hl": {2: HL_BAD, 3: HL_UNIT, 6: HL_BAD, 7: HL_BAD, 4: HL_TARGET},
                     "block_arrows": [(4, 7)],
                     "knight_jumps": [(4, 2)],
                     "cell_strikes": [2, 6, 7]},
              f"2. Row + Horsie block {tok(1)}")
        p3 = (demo, {"hl": {2: HL_UNIT, 6: HL_UNIT, 7: HL_UNIT, 3: HL_TARGET},
                     "knight_jumps": [(4, 2)],
                     "cell_strikes": [2, 6, 7],
                     "target": (3, 1)},
              f"3. Safe spot gets {tok(1)}!")
        return {
            "panels": [p1, p2, p3],
            "formula": "No matching pieces a Knight's L-jump apart (2 cells one way, 1 sideways)!",
            "dad_steps": [
                "\"A horsie jumps in an L: clip-clop 1-2, and 1 to the side!\"",
                f"\"Look at {tok(1)}: it blocks its row AND horsie-jumps to block the top spot (X)!\"",
                f"\"Only one spot in the box is safe from the horsie - put {tok(1)} there!\"",
            ],
            "dad_game": "Game: \"Clip-Clop Horsie!\" Hop your finger 2 cells and 1 sideways saying 'Clip, Clop, Boing!'",
        }

    if level == 9:
        _, steps2 = L.solve_logic(example["givens"], variant_of(example), S + ("point", "npair", "xwing"),
                                  record=True, allowed=allowed_of(example))
        idx_xw = next(i for i, st in enumerate(steps2) if st["tech"] == "xwing")
        s = steps2[idx_xw]
        s_next = next(st for st in steps2[idx_xw + 1:] if "cell" in st)
        d = s["digit"]
        pattern = list(s["pattern"])
        if xwing_axis == "col" and s.get("axis") == "row":
            # Compute the dual Column X-Wing on the same candidate state!
            st_col = L.State(example["givens"], variant_of(example), allowed_of(example))
            spots = []
            for col in st_col.cols:
                sp = [k for k, c_i in enumerate(col) if not st_col.values[c_i] and d in st_col.cands[c_i]]
                spots.append(sp if len(sp) == 2 else None)
            for a_i in range(4):
                for b_i in range(a_i + 1, 4):
                    if spots[a_i] and spots[a_i] == spots[b_i]:
                        k1, k2 = spots[a_i]
                        pattern = [st_col.cols[a_i][k1], st_col.cols[a_i][k2],
                                   st_col.cols[b_i][k1], st_col.cols[b_i][k2]]
                        break
        a, b, c2, d2 = pattern
        elims = s["elims"]
        p1 = (example, {"hl": {c: HL_TARGET for c in pattern},
                        "values": s["before"]["values"]},
              f"1. {tok(d)} in 4 X-corners")
        p2 = (example, {"hl": {**{c: HL_TARGET for c in pattern}, **{c: HL_BAD for c, _ in elims}},
                        "values": s["before"]["values"],
                        "lines": [(a, d2), (b, c2)],
                        "strikes": elims,
                        "peg_target": (s_next["cell"], s_next["digit"])},
              f"2. X zaps {tok(d)} in other line!")
        p3 = (example, {"hl": {**{c: HL_UNIT for c, _ in elims}, s_next["cell"]: HL_TARGET},
                        "values": s_next["before"]["values"],
                        "strikes": elims,
                        "target": (s_next["cell"], s_next["digit"])},
              f"3. Unlocked -> place {tok(s_next['digit'])}!")
        return {
            "panels": [p1, p2, p3],
            "formula": "Works in ROWS or COLUMNS:  2 rows -> zap 2 columns   |   2 columns -> zap 2 rows!",
            "dad_steps": [
                f"\"Look at the 4 green spots: {tok(d)} only fits in those 2 spots in two rows (or two columns)!\"",
                f"\"Cross your fingers in an X! Two rows zap the columns - OR two columns zap the rows (red)!\"",
                f"\"Look at the red spot now - only {tok(s_next['digit'])} is left!\"",
            ],
            "dad_game": "Game: \"X-Wing Both Ways!\" Make a big X with two bars - works across rows OR down columns!",
        }

    # Level 10: All-Star Challenge (adding your own pegs!)
    demo10 = {
        "givens": [0, 4, 3, 0,
                   0, 3, 4, 0,
                   3, 0, 0, 0,
                   0, 2, 0, 0],
        "solution": [1, 4, 3, 2,
                     2, 3, 4, 1,
                     3, 1, 2, 4,
                     4, 2, 1, 3],
        "regions": list(G.STANDARD_REGIONS),
        "anti_knight": False, "colors": {}, "center_clues": {}, "corner_clues": [], "fog_lit": None,
    }
    p1 = (demo10, {"hl": {0: HL_UNIT, 4: HL_UNIT, 12: HL_UNIT}},
          "1. Empty cells? Grab pegs!")
    p2 = (demo10, {"hl": {0: HL_TARGET, 4: HL_TARGET, 12: HL_UNIT},
                   "cands": {0: [1, 2], 4: [1, 2], 12: [1, 4]},
                   "pair_link": (0, 4),
                   "strikes": [(12, 1)],
                   "peg_target": (12, 4)},
          f"2. {tok(1)} & {tok(2)} twins zap {tok(1)}!")
    p3 = (demo10, {"hl": {0: HL_UNIT, 4: HL_UNIT, 12: HL_TARGET},
                   "cands": {0: [1, 2], 4: [1, 2], 12: [1, 4]},
                   "target": (12, 4)},
          f"3. Only {tok(4)} left -> {tok(4)}!")
    return {
        "panels": [p1, p2, p3],
        "formula": "Put in your OWN center & corner pegs to make pairs, lasers and singles appear!",
        "dad_steps": [
            "\"No little dots printed? We get to put in our OWN baby pegs from the tray!\"",
            f"\"Put {tok(1)} and {tok(2)} pegs in the top two spots - look, we made Twin Buddies!\"",
            f"\"The twins take {tok(1)} and {tok(2)}, so the bottom spot MUST be {tok(4)}!\"",
        ],
        "dad_game": "Game: \"Peg Boss!\" Let your child be in charge of putting baby pegs into the holes!",
    }


# ---------------------------------------------------------------------------
# Visual Peg Map & Header Helpers
# ---------------------------------------------------------------------------

def draw_peg_map_strip(pg, x, y, w, h, use_colors=False):
    """Draw a visual peg-hole map card at the bottom of a lesson page."""
    pg.fill_color("#f3f4f6")
    pg.stroke_color("#d0d5dd")
    pg.line_width(0.8)
    pg.round_rect(x, y, w, h, 8, fill=True, stroke=True)

    # Mini cell diagram on the left showing the 4 spots in a 2x2 layout
    cs = h - 10
    bx = x + 12
    by = y + 5
    pg.fill_color("#ffffff")
    pg.stroke_color("#868e96")
    pg.line_width(0.8)
    pg.round_rect(bx, by, cs, cs, 4, fill=True, stroke=True)
    cx, cy = bx + cs / 2, by + cs / 2
    offsets = {1: (-0.24, -0.24), 2: (0.24, -0.24), 3: (-0.24, 0.24), 4: (0.24, 0.24)}
    for d, (ox, oy) in offsets.items():
        px, py = cx + ox * cs, cy + oy * cs
        if use_colors:
            fc, ec, _ = PIECE_PALETTE[d]
            pg.fill_color(fc)
            pg.stroke_color(ec)
            pg.line_width(0.7)
            pg.circle(px, py, cs * 0.16, fill=True, stroke=True)
        else:
            pg.fill_color("#ffffff")
            pg.stroke_color("#495057")
            pg.line_width(0.7)
            pg.circle(px, py, cs * 0.16, fill=True, stroke=True)
            pg.text_centered_in(px, py, str(d), cs * 0.24, True, INK)

    # 4 visual pills across the strip
    spots = [(1, "Top-Left"), (2, "Top-Right"), (3, "Bottom-Left"), (4, "Bottom-Right")]
    avail_w = w - (cs + 32)
    slot_w = avail_w / 4.0
    for idx_s, (d, label) in enumerate(spots):
        sx = bx + cs + 18 + idx_s * slot_w
        sy = y + h / 2
        if use_colors:
            fc, ec, name = PIECE_PALETTE[d]
            pg.fill_color(fc)
            pg.stroke_color(ec)
            pg.line_width(0.8)
            pg.circle(sx + 8, sy, 6.0, fill=True, stroke=True)
            pg.text(sx + 18, sy + 3.5, f"{name} = {label}", 9.0, True, color="#333333")
        else:
            pg.fill_color("#ffffff")
            pg.stroke_color("#495057")
            pg.line_width(0.8)
            pg.circle(sx + 8, sy, 6.5, fill=True, stroke=True)
            pg.text_centered_in(sx + 8, sy, str(d), 8.5, True, INK)
            pg.text(sx + 18, sy + 3.5, label, 9.5, True, color="#333333")


def draw_toddler_piece_bar(pg, x, y, w, h, use_colors=False, draw_swatch_fn=None):
    """Interactive 'Touch & Count the 4 Pieces!' bar for a 3-year-old."""
    pg.fill_color("#fff9db")
    pg.stroke_color("#f59f00")
    pg.line_width(1.2)
    pg.round_rect(x, y, w, h, 9, fill=True, stroke=True)
    pg.text(x + 14, y + h / 2 + 4, "Touch all 4:", 11.5, True, color="#b45309")
    start_x = x + 115
    spacing = (w - 130) / 4.0
    for idx_d, d in enumerate(G.DIGITS):
        cx = start_x + (idx_d + 0.5) * spacing
        cy = y + h / 2
        if use_colors and draw_swatch_fn:
            draw_swatch_fn(pg, cx - 18, cy, 22, d, shaded=True)
            pg.text(cx + 2, cy + 4, PIECE_PALETTE[d][2], 11.5, True, color=INK)
        else:
            pg.fill_color("#ffffff")
            pg.stroke_color("#495057")
            pg.line_width(1.0)
            pg.round_rect(cx - 13, cy - 11, 22, 22, 4, fill=True, stroke=True)
            pg.text_centered_in(cx - 2, cy, str(d), 13, True, INK)


# ---------------------------------------------------------------------------
# Page Renderers (Lesson, Symbol-Only Puzzle Pages, Cover, Answers)
# ---------------------------------------------------------------------------

def visual_lesson_page(pdf, level, example, page_no, *, use_colors=False, toddler=False,
                       draw_board_fn=None, draw_swatch_fn=None, alt_example=None):
    lv = LEVEL_BY_NUM[level]
    sb = build_storyboard(example, level, use_colors=use_colors)
    pg = pdf.new_page()
    width = pg.w - 2 * MARGIN

    # 1. Minimal Header Banner: Theme Symbol Badge + Technique Name only
    pg.fill_color("#26313a")
    pg.round_rect(MARGIN, MARGIN, width, 56, 12, fill=True, stroke=False)
    draw_theme_badge(pg, MARGIN + 30, MARGIN + 28, 20, lv["key"], use_colors=use_colors)
    pg.text(MARGIN + 62, MARGIN + 36, lv["name"], 24, True, color="#ffffff")
    if level == 9:
        pg.fill_color("#f59f00")
        pg.round_rect(pg.w - MARGIN - 108, MARGIN + 16, 92, 24, 6, fill=True, stroke=False)
        pg.text(pg.w - MARGIN - 62, MARGIN + 32, "OPTIONAL", 10.5, True, align="center", color="#1d1d1f")

    # 2. Short Visual Rule Banner
    y = MARGIN + 68
    pg.fill_color("#eef4fb")
    pg.stroke_color("#b6d4fe")
    pg.line_width(1.0)
    pg.round_rect(MARGIN, y, width, 28, 7, fill=True, stroke=True)
    pg.text(pg.w / 2, y + 18, sb["formula"], 11, True, align="center", color="#1e3a8a")

    # 3. 3-Panel Visual Storyboard (Step 1 -> Step 2 -> Step 3)
    y_panels = y + 40
    panel_gap = 16.0
    bsize = (width - 2 * panel_gap) / 3.0  # ~169 pt per board
    for idx_p, (p_rec, kw, cap) in enumerate(sb["panels"], 1):
        px = MARGIN + (idx_p - 1) * (bsize + panel_gap)
        # Step icon badge + short 3-word caption pill above board
        draw_step_badge(pg, px + 14, y_panels + 12, 11.5, idx_p)
        pg.text(px + 30, y_panels + 16, cap, 10.0, True, color=INK)
        by = y_panels + 30
        draw_board_fn(pg, px, by, bsize, p_rec, use_colors=use_colors, **kw)
        # Big arrow between Panel 1 -> 2 and Panel 2 -> 3
        if idx_p < 3:
            ax1 = px + bsize + 2.5
            ax2 = px + bsize + panel_gap - 2.5
            ay = by + bsize / 2
            draw_arrow(pg, ax1, ay, ax2, ay, color="#495057", width=2.2, head=5.5)

    y_after_boards = y_panels + 30 + bsize + 14

    if toddler:
        # 4a. Interactive "Touch all 4" bar for kids
        draw_toddler_piece_bar(pg, MARGIN, y_after_boards, width, 34,
                               use_colors=use_colors, draw_swatch_fn=draw_swatch_fn)
        y_coach = y_after_boards + 46

        # 4b. Dad's Play-by-Play Coach Box (for kids and their dads)
        box_h = pg.h - MARGIN - 24 - y_coach
        pg.fill_color("#f8fafc")
        pg.stroke_color("#94a3b8")
        pg.line_width(1.2)
        pg.round_rect(MARGIN, y_coach, width, box_h, 10, fill=True, stroke=True)

        pg.fill_color("#334155")
        pg.round_rect(MARGIN + 12, y_coach + 10, 190, 22, 5, fill=True, stroke=False)
        pg.text(MARGIN + 22, y_coach + 25, "FOR DAD (Say & Point Together)", 9.2, True, color="#ffffff")

        cy_step = y_coach + 44
        step_bgs = ["#eff6ff", "#fef2f2", "#f0fdf4"]
        step_edges = ["#bfdbfe", "#fecaca", "#bbf7d0"]
        for idx_s, line_txt in enumerate(sb["dad_steps"], 1):
            row_h = 44
            pg.fill_color(step_bgs[idx_s - 1])
            pg.stroke_color(step_edges[idx_s - 1])
            pg.line_width(0.9)
            pg.round_rect(MARGIN + 12, cy_step, width - 24, row_h, 7, fill=True, stroke=True)
            draw_step_badge(pg, MARGIN + 30, cy_step + row_h / 2, 11.5, idx_s)
            pg.paragraph(MARGIN + 50, cy_step + 8, line_txt, 11.0, width - 70,
                         bold=True, leading=1.25, color="#1e293b")
            cy_step += row_h + 10

        # Playful game idea strip inside Dad box
        pg.fill_color("#ecfdf5")
        pg.stroke_color("#6ee7b7")
        pg.line_width(0.9)
        pg.round_rect(MARGIN + 12, y_coach + box_h - 36, width - 24, 24, 6, fill=True, stroke=True)
        pg.text(MARGIN + 22, y_coach + box_h - 20, sb["dad_game"], 9.5, True, color="#065f46")
    else:
        if level == 9 and alt_example is not None:
            # Show BOTH Row X-Wing (2 rows -> zap columns) and Column X-Wing (2 cols -> zap rows) side-by-side!
            sb_col = build_storyboard(alt_example, level, use_colors=use_colors, xwing_axis="col")
            zoom_size = min(228.0, pg.h - MARGIN - 48 - y_after_boards)
            gap_x = 36.0
            total_w = 2 * zoom_size + gap_x
            zx1 = (pg.w - total_w) / 2
            zx2 = zx1 + zoom_size + gap_x
            zy = y_after_boards + 32
            pg.text(zx1 + zoom_size / 2, zy - 8, "2 Rows  ->  Zap 2 Columns", 11.5, True, align="center", color=INK)
            pg.text(zx2 + zoom_size / 2, zy - 8, "2 Columns  ->  Zap 2 Rows", 11.5, True, align="center", color=INK)
            p_rec2, kw2, _ = sb["panels"][1]
            p_col2, kw_col2, _ = sb_col["panels"][1]
            draw_board_fn(pg, zx1, zy, zoom_size, p_rec2, use_colors=use_colors, **kw2)
            draw_board_fn(pg, zx2, zy, zoom_size, p_col2, use_colors=use_colors, **kw_col2)
        else:
            # 4. In the Visual Edition: draw a single centered Close-Up Action View
            #    (no redundant text cards repeating the panel captions)
            zoom_size = min(265.0, pg.h - MARGIN - 28 - y_after_boards)
            zx = (pg.w - zoom_size) / 2
            zy = y_after_boards + 14
            p_rec2, kw2, _ = sb["panels"][1]
            p_rec3, kw3, _ = sb["panels"][2]
            merged_kw = dict(kw2)
            strike_cells = {c for c, _ in kw2.get("strikes", [])}
            if "target" in kw3 and kw3["target"][0] not in strike_cells:
                merged_kw["target"] = kw3["target"]
                merged_kw["hl"] = dict(kw2.get("hl", {}))
                merged_kw["hl"][kw3["target"][0]] = HL_TARGET
                merged_kw.pop("peg_target", None)
                merged_kw.pop("corner_target", None)
            draw_board_fn(pg, zx, zy, zoom_size, p_rec2, use_colors=use_colors, **merged_kw)

    return page_no + 1


def visual_puzzle_pages(pdf, puzzles, level, page_no, *, use_colors=False, toddler=False,
                        draw_board_fn=None, draw_header_swatches_fn=None):
    """Minimalistic puzzle pages: no titles, no rules text, no ordering icons.
    Only the 6 boards and each puzzle's functional technique/variant symbol(s).
    """
    per = 6
    for start in range(0, len(puzzles), per):
        chunk = puzzles[start:start + per]
        pg = pdf.new_page()

        top = MARGIN + 6
        cell_w = (pg.w - 2 * MARGIN) / 2
        cell_h = (pg.h - 2 * MARGIN - 6) / 3
        bsize = min(cell_h - 28, cell_w - 34, 198)

        for k, p in enumerate(chunk):
            col, row = k % 2, k // 2
            px = MARGIN + col * cell_w
            py = top + row * cell_h
            bx = px + (cell_w - bsize) / 2
            by = py + 22

            # Only the functional technique/variant symbol(s) for this puzzle
            badges = tech_badges_for_puzzle(p, level)
            for b_i, b_key in enumerate(badges):
                bcx = bx + 9 + b_i * 21
                draw_theme_badge(pg, bcx, py + 10, 8.5, b_key, use_colors=use_colors)

            draw_board_fn(pg, bx, by, bsize, p, use_colors=use_colors)
        page_no += 1
    return page_no


def visual_cover_page(pdf, data, levels, *, use_colors=False, toddler=False,
                      draw_board_fn=None, draw_swatch_fn=None):
    pg = pdf.new_page()
    pg.fill_color("#eef4fb")
    pg.stroke_color("#b6d4fe")
    pg.line_width(0.9)
    pill_w = 148
    pg.round_rect((pg.w - pill_w) / 2, 72, pill_w, 22, 11, fill=True, stroke=True)
    pg.text(pg.w / 2, 87, "DoDad Puzzles\u2122", 10.5, True, "center", "#1e3a8a")

    if toddler:
        title = "DAD & ME 4x4 SUDOKU"
        sub = "A picture-first workbook for kids and their dads"
    else:
        title = "4x4 SUDOKU" if not use_colors else "4x4 COLOR SUDOKU"
        sub = ""
    pg.text(pg.w / 2, 128 if sub else 142, title, 34, True, "center", INK)
    if sub:
        pg.text(pg.w / 2, 154, sub, 12.5, False, "center", "#444444")

    demo = next(p for p in data["puzzles"] if p["level"] == 1)
    draw_board_fn(pg, (pg.w - 195) / 2, 176, 195, demo, use_colors=use_colors)

    if use_colors and draw_swatch_fn:
        y_leg = 398
        spacing = 95
        start_x = pg.w / 2 - 1.5 * spacing
        for idx_d, d in enumerate(G.DIGITS):
            cx = start_x + idx_d * spacing
            draw_swatch_fn(pg, cx, y_leg, 18, d, shaded=True)
            pg.text(cx, y_leg + 20, PIECE_PALETTE[d][2], 10, True, "center", INK)
        y = 446
    else:
        y = 415

    # Visual Theme Symbol Directory (2 columns of 5 theme badges)
    pg.text(pg.w / 2, y, "Symbols", 13, True, "center", INK)
    y += 16
    col_w = (pg.w - 2 * MARGIN - 40) / 2
    for idx_lv, lv in enumerate(levels):
        col = idx_lv // 5
        row = idx_lv % 5
        lx = MARGIN + 20 + col * (col_w + 20)
        ly = y + row * 36
        pg.fill_color("#f8f9fa")
        pg.stroke_color("#dee2e6")
        pg.line_width(0.8)
        pg.round_rect(lx, ly, col_w, 28, 6, fill=True, stroke=True)
        draw_theme_badge(pg, lx + 16, ly + 14, 10.5, lv["key"], use_colors=use_colors)
        pg.text(lx + 34, ly + 18, lv["name"], 11, True, color="#222222")


def visual_answer_pages(pdf, puzzles, *, use_colors=False, draw_board_fn=None):
    """Minimalistic answer key matching the puzzle pages."""
    per_row, per_col = 4, 5
    per = per_row * per_col
    for start in range(0, len(puzzles), per):
        pg = pdf.new_page()
        top = MARGIN + 14
        cw = (pg.w - 2 * MARGIN) / per_row
        ch = (pg.h - 2 * MARGIN - 14) / per_col
        size = min(cw - 22, ch - 22)
        for k, p in enumerate(puzzles[start:start + per]):
            col, row = k % per_row, k // per_row
            bx = MARGIN + col * cw + (cw - size) / 2
            by = top + row * ch + 14
            badges = tech_badges_for_puzzle(p, p["level"])
            for b_i, b_key in enumerate(badges):
                draw_theme_badge(pg, bx + 7 + b_i * 15, by - 8, 6.0, b_key, use_colors=use_colors)
            draw_board_fn(pg, bx, by, size, p, show="answer", holes=False, use_colors=use_colors)


def render_visual_editions(data, levels, out_dir, *, use_colors=False,
                           draw_board_fn=None, draw_swatch_fn=None, draw_header_swatches_fn=None,
                           welcome_page_fn=None, no_lessons=False, no_cover=False):
    """Render both the Visual Edition and the Dad & Me Edition."""
    c_suf = "_colors" if use_colors else ""
    for toddler, mode_tag, title_prefix in (
        (False, "visual", "4x4 Visual Sudoku Workbook"),
        (True, "toddler", "Dad & Me 4x4 Sudoku Workbook"),
    ):
        book = PDF(title=title_prefix)
        page_no = 1
        if not no_cover:
            visual_cover_page(book, data, levels, use_colors=use_colors, toddler=toddler,
                              draw_board_fn=draw_board_fn, draw_swatch_fn=draw_swatch_fn)
            page_no += 1
            if welcome_page_fn is not None:
                page_no = welcome_page_fn(book, page_no, use_colors=use_colors, book_label=title_prefix)
        chosen = []
        for lv in levels:
            ps = [p for p in data["puzzles"] if p["level"] == lv["level"]]
            chosen += ps
            if not no_lessons:
                page_no = visual_lesson_page(
                    book, lv["level"], ps[0], page_no,
                    use_colors=use_colors, toddler=toddler,
                    draw_board_fn=draw_board_fn, draw_swatch_fn=draw_swatch_fn,
                    alt_example=ps[1] if len(ps) > 1 else None,
                )
            page_no = visual_puzzle_pages(
                book, ps, lv["level"], page_no,
                use_colors=use_colors, toddler=toddler,
                draw_board_fn=draw_board_fn, draw_header_swatches_fn=draw_header_swatches_fn,
            )
        wb_path = os.path.join(out_dir, f"workbook_{mode_tag}{c_suf}.pdf")
        book.save(wb_path)

        ans = PDF(title=f"{title_prefix} - Answers")
        visual_answer_pages(ans, chosen, use_colors=use_colors, draw_board_fn=draw_board_fn)
        ans_path = os.path.join(out_dir, f"answers_{mode_tag}{c_suf}.pdf")
        ans.save(ans_path)
        print(f"Wrote {wb_path} ({len(book.pages)} pages) and {ans_path} ({len(ans.pages)} pages)")
