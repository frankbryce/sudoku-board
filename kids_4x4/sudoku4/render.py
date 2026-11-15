"""Render puzzles.json into printable PDFs.

    python3 -m sudoku4.render                 # workbook.pdf + answers.pdf
    python3 -m sudoku4.render --levels 1 2 3  # just some levels
    python3 -m sudoku4.render --no-lessons    # puzzle pages only

Puzzle pages hold 6 puzzles per US-letter (8.5 x 11 in) sheet.  The board is
drawn as a simplified top-down view of the physical board: cell wells, thick
region bars, main pieces for clues, and center/corner peg positions
(1 = top-left, 2 = top-right, 3 = bottom-left, 4 = bottom-right).
"""

from __future__ import annotations

import argparse
import json
import os

from . import grid as G
from . import logic as L
from .generate import LEVEL_BY_NUM, allowed_of, variant_of, S
from .lessons import LESSONS, LESSONS_COLORS
from .pdf import PDF, text_width, wrap
from .visual import draw_arrow, draw_knight_icon, draw_theme_badge, draw_x_icon, render_visual_editions

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

INK = "#1d1d1f"
BOARD = "#e9e9e6"
WELL = "#ffffff"
WELL_EDGE = "#b9b9b4"
BAR = "#26313a"
PIECE = "#d9dee4"
PIECE_EDGE = "#8d97a1"
FAINT = "#d4d4d0"
FOG = "#a9adb1"
FOG_HATCH = "#8c9095"
HL_UNIT = "#fff3b0"
HL_TARGET = "#b7ebc0"
HL_BAD = "#f8c4c4"
STRIKE = "#d62828"
GOOD = "#1b873f"

# 4 Sharpie Creative Marker piece colors (from photo, left-to-right):
# 1 = Blue, 2 = Red, 3 = Tan, 4 = Green
PIECE_PALETTE = {
    1: ("#0178d4", "#004e8c", "Blue"),
    2: ("#db2134", "#8f111e", "Red"),
    3: ("#eab47f", "#9e632c", "Tan"),
    4: ("#22ab7e", "#116346", "Green"),
}

# colour-group palette for Level 8 in numbered mode (pastel fill, strong edge, symbol)
COLOR_STYLE = [
    ("#f9c6c9", "#d62839", "circle", "RED"),
    ("#bfe1ff", "#1f6fd1", "square", "BLUE"),
    ("#c9efc4", "#2b9348", "triangle", "GREEN"),
    ("#ffe0a8", "#e07a00", "diamond", "ORANGE"),
]

# mystery-group palette for Level 8 in color-piece mode (distinct from piece colors)
MYSTERY_STYLE_COLORS = [
    ("#ede2f7", "#6b3fa0", "circle", "CIRCLE"),
    ("#dff0f2", "#2b6f78", "square", "SQUARE"),
    ("#f2e8dc", "#7a5c3c", "triangle", "TRIANGLE"),
    ("#e4e6eb", "#495057", "diamond", "DIAMOND"),
]

COLOR_LEVEL_HINTS = {
    1: "Look at one row, column or box. Is there only ONE cell left where a color can go?",
    2: "Look at one empty cell. Its row, column and box already use 3 colors - the 4th one goes here!",
    3: "When a cell's row, column and box already use 2 colors, peg the 2 colors left in the center. Pull a peg out when its color appears in that row, column or box!",
    4: "A small color square in a corner means: inside this box, that color is in one of the corner-marked cells.",
    5: "If a box's corner marks for a color sit in one line, that color is zapped from the rest of that line.",
    6: "Two cells in a row, column or box with the SAME two center marks own those colors. Nobody else there can use them.",
    7: "The boxes are funny shapes! Each thick-outlined shape still needs all 4 colors.",
    8: "Normal rules, PLUS: the same color can never be a chess knight's jump apart (2 one way, 1 the other).",
    9: "Optional boss move! Works in rows OR columns: if a color fits in only 2 cells across 2 rows (lined up in 2 columns), zap it from the rest of those columns - or 2 columns zapping 2 rows!",
    10: "60 puzzles of increasing difficulty mixing every technique! The final 12 puzzles at the end require an X-Wing (marked with a warning symbol).",
}
REGION_TINTS = ["#ffffff", "#ecebe6", "#f6f3e3", "#e5ebee"]

# 2x2 peg positions for digits 1..4 (fractions of the cell)
CENTER_POS = {1: (-0.15, -0.15), 2: (0.15, -0.15), 3: (-0.15, 0.15), 4: (0.15, 0.15)}
CORNER_POS = {1: (-0.31, -0.31), 2: (0.31, -0.31), 3: (-0.31, 0.31), 4: (0.31, 0.31)}


# ---------------------------------------------------------------------------
# Board drawing
# ---------------------------------------------------------------------------

def _shape(pg, kind, cx, cy, r, fill=True, stroke=True):
    if kind == "circle":
        pg.circle(cx, cy, r, fill, stroke)
    elif kind == "square":
        pg.rect(cx - r * 0.85, cy - r * 0.85, r * 1.7, r * 1.7, fill, stroke)
    elif kind == "triangle":
        pg.polygon([(cx, cy - r), (cx + r * 0.95, cy + r * 0.75), (cx - r * 0.95, cy + r * 0.75)], fill, stroke)
    else:
        pg.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill, stroke)


def _draw_color_piece_swatch(pg, cx, cy, w, d, shaded=True):
    fill_c, edge_c, _ = PIECE_PALETTE[d]
    if shaded:
        pg.fill_color("#f3f4f6")
        pg.stroke_color("#6c757d")
        pg.line_width(0.75)
        pg.round_rect(cx - w / 2, cy - w / 2, w, w, w * 0.16, fill=True, stroke=True)
        pw = w * 0.76
    else:
        pw = w * 0.72
    pg.fill_color(fill_c)
    pg.stroke_color(edge_c)
    pg.line_width(0.85)
    pg.round_rect(cx - pw / 2, cy - pw / 2, pw, pw, pw * 0.2, fill=True, stroke=True)


def draw_board(pg, x, y, size, p, *, show="puzzle", hl=None, cands=None, strikes=None,
               target=None, peg_target=None, holes=True, values=None, lines=None,
               knight_from=None, use_colors=False, cell_strikes=None, block_arrows=None,
               corner_target=None, pair_link=None, knight_jumps=None):
    """Draw one 4x4 board with its top-left at (x, y).

    show        'puzzle' (clues only) or 'answer' (solution; clues shaded)
    hl          {cell: fill colour} highlight for cell wells
    cands       {cell: [digits]} small center-mark digits to draw (lesson diagrams)
    strikes     [(cell, digit)] small red digits crossed out
    target      (cell, digit) green answer digit / piece
    peg_target  (cell, digit) green highlight ring around a surviving center peg
    values      16-list overriding which placed digits to show (lesson diagrams)
    lines       [(cellA, cellB)] green connector lines (X-Wing)
    use_colors  True = draw 4 marker colors instead of digits 1..4
    """
    hl = hl or {}
    cands = cands or {}
    strikes = strikes or []
    pad = size * 0.045
    cs = (size - 2 * pad) / 4.0           # cell pitch
    gx, gy = x + pad, y + pad
    regions = p["regions"]
    colors = {int(k): v for k, v in p.get("colors", {}).items()}
    center = {int(k): v for k, v in p.get("center_clues", {}).items()}
    corner = {}
    for d, cells in p.get("corner_clues", []):
        for c in cells:
            corner.setdefault(c, []).append(d)
    fog_lit = p.get("fog_lit")
    jigsaw = regions != G.STANDARD_REGIONS
    group_style = MYSTERY_STYLE_COLORS if use_colors else COLOR_STYLE

    def cxy(i):
        r, c = G.rc(i)
        return gx + (c + 0.5) * cs, gy + (r + 0.5) * cs

    # board base
    pg.line_width(0.8)
    pg.stroke_color("#9a9a94")
    pg.fill_color(BOARD)
    pg.round_rect(x, y, size, size, size * 0.035, fill=True, stroke=True)

    # cell wells
    inset = cs * 0.075
    for i in G.CELLS:
        r, c = G.rc(i)
        wx, wy = gx + c * cs + inset, gy + r * cs + inset
        fill = WELL
        if jigsaw:
            fill = REGION_TINTS[regions[i] % len(REGION_TINTS)]
        if i in colors and show == "puzzle":
            fill = group_style[colors[i]][0]
        if i in hl:
            fill = hl[i]
        pg.fill_color(fill)
        pg.stroke_color(WELL_EDGE)
        pg.line_width(0.6)
        pg.round_rect(wx, wy, cs - 2 * inset, cs - 2 * inset, cs * 0.09, fill=True, stroke=True)

    # faint peg holes (only in cells with nothing printed in them)
    if holes:
        pg.fill_color(FAINT)
        for i in G.CELLS:
            busy = (p["givens"][i] or i in center or (values and values[i])
                    or show == "answer" or (fog_lit is not None and i not in fog_lit))
            if busy:
                continue
            cx, cy = cxy(i)
            for d in G.DIGITS:
                if i not in corner or d not in corner[i]:
                    ox, oy = CORNER_POS[d]
                    pg.circle(cx + ox * cs, cy + oy * cs, cs * 0.028, fill=True, stroke=False)
                if not cands.get(i):
                    ox, oy = CENTER_POS[d]
                    pg.circle(cx + ox * cs, cy + oy * cs, cs * 0.022, fill=True, stroke=False)

    # colour symbols (B&W-printer friendly, and mystery shapes in color mode)
    if show == "puzzle":
        for i, col in colors.items():
            cx, cy = cxy(i)
            fillc, edge, kind, _ = group_style[col]
            pg.fill_color(edge)
            pg.stroke_color(edge)
            pg.line_width(0.6)
            _shape(pg, kind, cx + cs * 0.3, cy - cs * 0.3, cs * 0.085 if use_colors else cs * 0.075)

    # region bars (thick lines between regions + perimeter)
    pg.stroke_color(BAR)
    pg.line_width(max(1.6, cs * 0.075))
    pg.line_cap(1)
    for r in range(4):
        for c in range(4):
            i = G.idx(r, c)
            x0, y0 = gx + c * cs, gy + r * cs
            if c == 3 or regions[i] != regions[G.idx(r, c + 1)]:
                pg.line(x0 + cs, y0, x0 + cs, y0 + cs)
            if r == 3 or regions[i] != regions[G.idx(r + 1, c)]:
                pg.line(x0, y0 + cs, x0 + cs, y0 + cs)
            if c == 0:
                pg.line(x0, y0, x0, y0 + cs)
            if r == 0:
                pg.line(x0, y0, x0 + cs, y0)
    # thin grid lines between ordinary neighbours
    pg.line_width(0.5)
    pg.stroke_color("#c8c8c2")
    for r in range(4):
        for c in range(4):
            i = G.idx(r, c)
            x0, y0 = gx + c * cs, gy + r * cs
            if c < 3 and regions[i] == regions[G.idx(r, c + 1)]:
                pg.line(x0 + cs, y0 + cs * 0.15, x0 + cs, y0 + cs * 0.85)
            if r < 3 and regions[i] == regions[G.idx(r + 1, c)]:
                pg.line(x0 + cs * 0.15, y0 + cs, x0 + cs * 0.85, y0 + cs)
    pg.line_cap(0)

    # fog
    if fog_lit is not None and show == "puzzle":
        for i in G.CELLS:
            if i in fog_lit:
                continue
            r, c = G.rc(i)
            wx, wy = gx + c * cs + inset * 0.6, gy + r * cs + inset * 0.6
            w = cs - 1.2 * inset
            pg.fill_color(FOG)
            pg.stroke_color(FOG_HATCH)
            pg.line_width(0.6)
            pg.round_rect(wx, wy, w, w, cs * 0.09, fill=True, stroke=True)
            pg.line_width(0.5)
            for k in range(1, 6):
                t = k / 6.0
                pg.line(wx + w * t, wy + w * 0.06, wx + w * 0.06, wy + w * t)
                pg.line(wx + w * (1 - 0.06), wy + w * t, wx + w * t, wy + w * (1 - 0.06))

    # main pieces (clues) and digits / colors
    def piece(i, d, shaded=True, color=INK):
        cx, cy = cxy(i)
        if use_colors:
            _draw_color_piece_swatch(pg, cx, cy, cs * 0.64, d, shaded=shaded)
        else:
            if shaded:
                w = cs * 0.62
                pg.fill_color(PIECE)
                pg.stroke_color(PIECE_EDGE)
                pg.line_width(0.7)
                pg.round_rect(cx - w / 2, cy - w / 2, w, w, cs * 0.1, fill=True, stroke=True)
            pg.text_centered_in(cx, cy, str(d), cs * 0.46, True, color)

    for i in G.CELLS:
        hidden_by_fog = fog_lit is not None and i not in fog_lit and show == "puzzle"
        if show == "answer":
            if p["givens"][i]:
                piece(i, p["solution"][i], True)
            else:
                piece(i, p["solution"][i], False, "#55606a")
        elif values is not None:
            if values[i]:
                piece(i, values[i], bool(p["givens"][i]), INK if p["givens"][i] else "#3f6db3")
        elif p["givens"][i] and not hidden_by_fog:
            piece(i, p["givens"][i], True)

    # printed pencil clues
    small = cs * 0.2
    if show == "puzzle":
        for i, ds in center.items():
            if (values is not None and values[i]) or (target and target[0] == i):
                continue
            cx, cy = cxy(i)
            for d in ds:
                ox, oy = CENTER_POS[d]
                if use_colors:
                    fill_c, edge_c, _ = PIECE_PALETTE[d]
                    pg.fill_color(fill_c)
                    pg.stroke_color(edge_c)
                    pg.line_width(0.75)
                    pg.circle(cx + ox * cs, cy + oy * cs, cs * 0.115, fill=True, stroke=True)
                else:
                    pg.fill_color("#ffffff")
                    pg.stroke_color("#5a6570")
                    pg.line_width(0.6)
                    pg.circle(cx + ox * cs, cy + oy * cs, cs * 0.115, fill=True, stroke=True)
                    pg.text_centered_in(cx + ox * cs, cy + oy * cs, str(d), small, True, INK)
        for i, ds in corner.items():
            if (values is not None and values[i] and not any(si == i for si, _ in strikes)) or (target and target[0] == i):
                continue
            cx, cy = cxy(i)
            for d in ds:
                ox, oy = CORNER_POS[d]
                px, py = cx + ox * cs, cy + oy * cs
                if use_colors:
                    fill_c, edge_c, _ = PIECE_PALETTE[d]
                    pg.fill_color(fill_c)
                    pg.stroke_color(edge_c)
                    pg.line_width(0.75)
                    pg.rect(px - cs * 0.1, py - cs * 0.1, cs * 0.2, cs * 0.2, fill=True, stroke=True)
                else:
                    pg.fill_color("#ffffff")
                    pg.stroke_color("#5a6570")
                    pg.line_width(0.6)
                    pg.rect(px - cs * 0.1, py - cs * 0.1, cs * 0.2, cs * 0.2, fill=True, stroke=True)
                    pg.text_centered_in(px, py, str(d), small, True, INK)

    # lesson overlays
    for i, ds in cands.items():
        if target and target[0] == i:
            continue
        cx, cy = cxy(i)
        for d in ds:
            ox, oy = CENTER_POS[d]
            if use_colors:
                fill_c, edge_c, _ = PIECE_PALETTE[d]
                pg.fill_color(fill_c)
                pg.stroke_color(edge_c)
                pg.line_width(0.65)
                pg.circle(cx + ox * cs, cy + oy * cs, cs * 0.095, fill=True, stroke=True)
            else:
                pg.text_centered_in(cx + ox * cs, cy + oy * cs, str(d), small, False, "#3f6db3")
    for i, d in strikes:
        if target and target[0] == i:
            continue
        cx, cy = cxy(i)
        is_corner = i in corner and d in corner[i]
        pos = CORNER_POS if is_corner else CENTER_POS
        ox, oy = pos[d]
        px, py = cx + ox * cs, cy + oy * cs
        if use_colors:
            already_drawn = ((i in center and d in center[i])
                             or (i in corner and d in corner[i])
                             or (cands.get(i) and d in cands[i]))
            if not already_drawn:
                fill_c, edge_c, _ = PIECE_PALETTE[d]
                pg.fill_color(fill_c)
                pg.stroke_color(edge_c)
                pg.line_width(0.65)
                if is_corner:
                    pg.rect(px - cs * 0.09, py - cs * 0.09, cs * 0.18, cs * 0.18, fill=True, stroke=True)
                else:
                    pg.circle(px, py, cs * 0.095, fill=True, stroke=True)
            r = cs * 0.105
            pg.stroke_color("#ffffff")
            pg.line_width(2.2)
            pg.line(px - r, py - r, px + r, py + r)
            pg.line(px - r, py + r, px + r, py - r)
            pg.stroke_color(INK)
            pg.line_width(1.2)
            pg.line(px - r, py - r, px + r, py + r)
            pg.line(px - r, py + r, px + r, py - r)
        else:
            if not cands.get(i) or d not in cands[i]:
                pg.text_centered_in(px, py, str(d), small, True, STRIKE)
            pg.stroke_color(STRIKE)
            pg.line_width(1.4)
            r = cs * 0.09
            pg.line(px - r, py - r, px + r, py + r)
            pg.line(px - r, py + r, px + r, py - r)
    if lines:
        pg.stroke_color(GOOD)
        pg.line_width(1.6)
        pg.dash(4, 3)
        for a, b in lines:
            (ax, ay), (bx, by) = cxy(a), cxy(b)
            pg.line(ax, ay, bx, by)
        pg.dash()
    if pair_link is not None:
        a, b = pair_link
        (ax, ay), (bx, by) = cxy(a), cxy(b)
        pg.stroke_color(GOOD)
        pg.line_width(2.0)
        pg.dash(3, 2.5)
        pg.line(ax, ay, bx, by)
        pg.dash()
    if block_arrows:
        for a, b in block_arrows:
            (ax, ay), (bx, by) = cxy(a), cxy(b)
            dx, dy = bx - ax, by - ay
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 1e-3:
                ux, uy = dx / dist, dy / dist
                start_x = ax + ux * (cs * 0.34)
                start_y = ay + uy * (cs * 0.34)
                end_x = bx - ux * (cs * 0.24)
                end_y = by - uy * (cs * 0.24)
                draw_arrow(pg, start_x, start_y, end_x, end_y,
                           color=STRIKE, width=1.4, head=4.2, dashed=True)
    if cell_strikes:
        for i in cell_strikes:
            cx, cy = cxy(i)
            draw_x_icon(pg, cx, cy, cs * 0.21, color=STRIKE, lw=2.0)
    if knight_jumps:
        for a, b in knight_jumps:
            ra, ca = G.rc(a)
            rb, cb = G.rc(b)
            (ax, ay), (bx, by) = cxy(a), cxy(b)
            # 2 steps along the longer delta, then 1 step perpendicular
            if abs(rb - ra) == 2:
                ex, ey = ax, by
            else:
                ex, ey = bx, ay
            pg.stroke_color("#d9480f")
            pg.line_width(1.8)
            pg.line_cap(1)
            pg.line(ax, ay, ex, ey)
            pg.line_cap(0)
            dx, dy = bx - ex, by - ey
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 1e-3:
                ux, uy = dx / dist, dy / dist
                end_x = bx - ux * (cs * 0.22)
                end_y = by - uy * (cs * 0.22)
                draw_arrow(pg, ex, ey, end_x, end_y, color="#d9480f", width=1.8, head=4.6)
    if knight_from is not None:
        cx, cy = cxy(knight_from)
        draw_knight_icon(pg, cx, cy, cs * 0.33, fill_c="#26313a", stroke_c="#ffffff")
    if target is not None:
        i, d = target
        cx, cy = cxy(i)
        if use_colors and d:
            _draw_color_piece_swatch(pg, cx, cy, cs * 0.56, d, shaded=False)
        pg.stroke_color(GOOD)
        pg.line_width(2.0)
        pg.circle(cx, cy, cs * 0.36, fill=False, stroke=True)
        if d and not use_colors:
            pg.text_centered_in(cx, cy, str(d), cs * 0.46, True, GOOD)
    if peg_target is not None:
        i, d = peg_target
        cx, cy = cxy(i)
        ox, oy = CENTER_POS[d]
        px, py = cx + ox * cs, cy + oy * cs
        pg.stroke_color(GOOD)
        pg.line_width(2.2)
        pg.circle(px, py, cs * 0.16, fill=False, stroke=True)
    if corner_target is not None:
        i, d = corner_target
        cx, cy = cxy(i)
        ox, oy = CORNER_POS[d]
        px, py = cx + ox * cs, cy + oy * cs
        pg.stroke_color(GOOD)
        pg.line_width(2.2)
        pg.circle(px, py, cs * 0.16, fill=False, stroke=True)


# ---------------------------------------------------------------------------
# Page layouts
# ---------------------------------------------------------------------------

MARGIN = 36.0


def footer(pg, text):
    pg.text(pg.w / 2, pg.h - 20, text, 8, False, "center", "#777777")


def checkbox(pg, x, y, s=9):
    pg.stroke_color("#777777")
    pg.line_width(0.7)
    pg.rect(x, y, s, s, fill=False, stroke=True)


def _draw_header_color_swatches(pg, right_x, y_baseline):
    """Draw 'Fill each row, column and box with' followed by the 4 color piece icons."""
    sw = 10.5
    gap = 4.0
    total_sw = 4 * sw + 3 * gap
    sx0 = right_x - total_sw
    pg.text(sx0 - 6, y_baseline, "Fill each row, column and box with",
            8.5, False, "right", "#555555")
    for idx_d, d in enumerate(G.DIGITS):
        cx = sx0 + idx_d * (sw + gap) + sw / 2
        cy = y_baseline - 3.2
        _draw_color_piece_swatch(pg, cx, cy, sw, d, shaded=False)


def puzzle_pages(pdf, puzzles, level, page_no, use_colors=False):
    lv = LEVEL_BY_NUM[level]
    hint_text = COLOR_LEVEL_HINTS[level] if use_colors else lv["hint"]
    per = 6
    for start in range(0, len(puzzles), per):
        chunk = puzzles[start:start + per]
        pg = pdf.new_page()
        # header
        pg.text(MARGIN, MARGIN + 14, f"Level {level}: {lv['name']}", 17, True, color=INK)
        if use_colors:
            _draw_header_color_swatches(pg, pg.w - MARGIN, MARGIN + 14)
        else:
            pg.text(pg.w - MARGIN, MARGIN + 14, "Fill each row, column and box with 1 2 3 4",
                    8.5, False, "right", "#555555")
        yb = MARGIN + 20
        for ln in wrap(hint_text, 9.5, pg.w - 2 * MARGIN):
            yb += 12
            pg.text(MARGIN, yb, ln, 9.5, False, color="#333333")
        pg.stroke_color("#bbbbbb")
        pg.line_width(0.6)
        pg.line(MARGIN, yb + 7, pg.w - MARGIN, yb + 7)
        top = yb + 14
        cell_w = (pg.w - 2 * MARGIN) / 2
        cell_h = (pg.h - MARGIN - 18 - top) / 3
        bsize = min(cell_h - 34, cell_w - 40, 186)
        for k, p in enumerate(chunk):
            col, row = k % 2, k // 2
            px = MARGIN + col * cell_w
            py = top + row * cell_h
            bx = px + (cell_w - bsize) / 2
            by = py + 20
            pg.text(bx, py + 14, f"Puzzle {p['level']}.{p['number']:02d}", 11, True, color=INK)
            extra = []
            if level == 10 and p.get("technique"):
                extra.append(p["technique"])
            if p.get("anti_knight") and "Anti-Knight" not in " ".join(extra):
                extra.append("+ no knight-jump repeats")
            if p.get("colors"):
                extra.append("same shape = same color" if use_colors else "same color = same number")
            if extra:
                if level == 10 and "X-Wing" in p.get("technique", ""):
                    draw_theme_badge(pg, bx + bsize - 22, py + 11, 6.5, "xwing_warn", use_colors=use_colors)
                    draw_theme_badge(pg, bx + bsize - 7, py + 11, 6.5, "xwing_boss", use_colors=use_colors)
                    pg.text(bx + bsize - 32, py + 14, "  ".join(extra), 7.5, True, "right", STRIKE)
                else:
                    pg.text(bx + bsize, py + 14, "  ".join(extra), 7.5, False, "right", "#555555")
            checkbox(pg, bx + bsize - 9, by + bsize + 4)
            pg.text(bx + bsize - 13, by + bsize + 12, "solved!", 7.5, False, "right", "#777777")
            draw_board(pg, bx, by, bsize, p, use_colors=use_colors)
        book_label = "4x4 Color Sudoku Workbook" if use_colors else "4x4 Sudoku Workbook"
        footer(pg, f"{book_label}  -  page {page_no}")
        page_no += 1
    return page_no


def _first_step(p, techs, want, record=True, pred=None):
    ok, steps = L.solve_logic(p["givens"], variant_of(p), techs, record=record, allowed=allowed_of(p))
    for s in steps:
        if s["tech"] in want and (pred is None or pred(s)):
            return s
    return steps[0] if steps else None


def lesson_example(p, level, use_colors=False):
    """Return (draw kwargs, caption) for the lesson diagram of `level`."""
    rcname = lambda i: f"row {G.rc(i)[0] + 1}, column {G.rc(i)[1] + 1}"
    tok = (lambda d: PIECE_PALETTE[d][2]) if use_colors else str
    noun = "color" if use_colors else "number"
    if level == 1:
        demo_p = {
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
        hl = {2: HL_BAD, 3: HL_BAD, 6: HL_BAD, 7: HL_TARGET, 0: HL_UNIT, 14: HL_UNIT}
        cap = (f"The top-right box needs {tok(3)}. The {tok(3)} in row 1, column 1 blocks row 1 "
               f"and the {tok(3)} in row 4, column 3 blocks column 3 (X), leaving only row 2, column 4!")
        return {"_p": demo_p, "hl": hl, "block_arrows": [(0, 3), (14, 2)],
                "cell_strikes": [2, 3, 6], "target": (7, 3)}, cap
    if level == 2:
        demo_p = {
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
        hl = {0: HL_UNIT, 1: HL_UNIT, 4: HL_UNIT, 6: HL_UNIT, 7: HL_UNIT, 9: HL_UNIT, 13: HL_UNIT, 5: HL_TARGET}
        cap = (f"Look at row 2, column 2 (green): its row, column and box already have "
               f"{tok(1)}, {tok(2)} and {tok(4)}. The only {noun} left is {tok(3)}!")
        return {"_p": demo_p, "hl": hl, "block_arrows": [(4, 5), (7, 5), (13, 5)],
                "target": (5, 3)}, cap
    if level == 3:
        # Clean, self-contained teaching board for Center Marks:
        # - R1C2 has 4 (Green) in the top-left box, R2C3 has 2 (Red) in row 2
        #   -> so R2C1 (green cell) is narrowed down to center marks 1 & 3 (Blue & Tan).
        # - R4C1 in column 1 has 3 (Tan), which crosses out the 3 (Tan) center mark in R2C1,
        #   leaving only 1 (Blue)!
        demo_p = {
            "givens": [0, 4, 0, 0,
                       0, 0, 2, 0,
                       0, 0, 0, 0,
                       0, 0, 0, 0],
            "solution": [2, 4, 3, 1,
                         1, 3, 2, 4,
                         4, 2, 1, 3,
                         3, 1, 4, 2],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False,
            "colors": {},
            "center_clues": {"4": [1, 3]},
            "corner_clues": [],
            "fog_lit": None,
        }
        vals = list(demo_p["givens"])
        vals[12] = 3  # R4C1 placed as 3 (Tan) in column 1
        hl = {1: HL_UNIT, 6: HL_UNIT, 12: HL_UNIT, 4: HL_TARGET}
        cap = (f"1. Why does the green cell (row 2, column 1) have {tok(1)} and {tok(3)} center "
               f"marks? Because {tok(4)} is already in its box (row 1, column 2) and {tok(2)} is "
               f"already in row 2 (row 2, column 3), leaving only {tok(1)} or {tok(3)}.  "
               f"2. Now look down column 1 at row 4, column 1: {tok(3)} is placed there, so cross "
               f"out the {tok(3)} center mark (X).  "
               f"3. Only {tok(1)} is left (circled in green), so place {tok(1)} here!")
        return {"_p": demo_p, "hl": hl, "values": vals,
                "strikes": [(4, 3)], "peg_target": (4, 1)}, cap
    if level == 4:
        # Clean, self-contained teaching board for Snyder Corner Marks:
        # - In the top-right box (2, 3, 6, 7), R4C3 (14) = 1 blocks column 3 (R1C3, R2C3),
        #   so 1 in the top-right box can only go in R1C4 (3) or R2C4 (7) -> corner marks [1, [3, 7]].
        # - Then R1C4 (3) gets filled with 4 (since R1C3 = 2 and R2C1 = 4 blocks row 2),
        #   so 1 must go in the other corner-marked cell, R2C4 (7)!
        demo_p = {
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
        vals = list(demo_p["givens"])
        vals[3] = 4
        hl = {2: HL_UNIT, 3: HL_BAD, 6: HL_UNIT, 7: HL_TARGET, 14: HL_UNIT}
        cap = (f"Because {tok(1)} in row 4, column 3 blocks column 3, {tok(1)} in the top-right box "
               f"can only go in row 1, column 4 or row 2, column 4 (the two corner marks). "
               f"Once row 1, column 4 fills up with {tok(4)}, {tok(1)} must go in row 2, column 4!")
        return {"_p": demo_p, "hl": hl, "values": vals, "target": (7, 1),
                "strikes": [(3, 1)]}, cap
    if level == 5:
        # Clean, self-contained teaching board for Pointing Pairs:
        # - Top-right box has R1C3 = 4 and R2C3 = 3, so 2 can only go in R1C4 (3) or R2C4 (7) (both in col 4).
        # - Bottom-right box has R3C1 = 2 blocking row 3, so 2 can only go in R4C3 (14) or R4C4 (15).
        # - The two 2 corner marks in the top-right box point down column 4 and zap R4C4 (15),
        #   leaving R4C3 (14) as the only spot for 2 in the bottom-right box!
        demo_p = {
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
        hl = {3: HL_TARGET, 7: HL_TARGET, 11: HL_UNIT, 15: HL_BAD, 14: HL_UNIT}
        cap = (f"In the top-right box, the two {tok(2)} corner marks (green) sit in column 4, so {tok(2)} "
               f"in that box must go in column 4. Shoot a laser down column 4 to cross out the {tok(2)} "
               f"corner mark in row 4, column 4 (red) - leaving row 4, column 3 (circled) as the only spot for {tok(2)}!")
        return {"_p": demo_p, "hl": hl, "block_arrows": [(7, 15)],
                "strikes": [(15, 2)], "corner_target": (14, 2)}, cap
    if level == 6:
        # Clean, self-contained teaching board for Naked Pair in Row 1:
        # - Top-left box has R2C1 = 2 and R2C2 = 4, so both R1C1 (0) and R1C2 (1) can only be 1 or 3 (Twins!).
        # - Row 1 has R1C4 = 4, so R1C3 (2) can only be 1, 2 or 3.
        # - The [1, 3] Twins in R1C1 & R1C2 use up 1 and 3 in Row 1, so cross 1 and 3 off R1C3 -> only 2 is left!
        demo_p = {
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
        hl = {0: HL_TARGET, 1: HL_TARGET, 2: HL_UNIT, 3: HL_UNIT}
        cap = (f"In row 1, the two green twin cells (row 1, column 1 and row 1, column 2) can only be "
               f"{tok(1)} or {tok(3)} (since {tok(2)} and {tok(4)} are already in their box). Between them "
               f"they use up {tok(1)} and {tok(3)} in row 1, so cross {tok(1)} and {tok(3)} off row 1, column 3 "
               f"(yellow) - leaving only {tok(2)} (circled)!")
        return {"_p": demo_p, "hl": hl, "pair_link": (0, 1),
                "strikes": [(2, 1), (2, 3)], "peg_target": (2, 2)}, cap
    if level == 7:
        s = _first_step(p, ("hs_box", "hs_line", "ns"), ("hs_box", "hs_line"))
        unit = s.get("unit", [])
        peers = G.peers_of(variant_of(p))
        blocked = [c for c in unit if c != s["cell"] and not p["givens"][c]]
        block_arrows = []
        for bc in blocked:
            src = next((q for q in peers[bc] if p["givens"][q] == s["digit"]), None)
            if src is not None:
                block_arrows.append((src, bc))
        hl = {c: HL_UNIT for c in unit}
        for bc in blocked:
            hl[bc] = HL_BAD
        hl[s["cell"]] = HL_TARGET
        cap = (f"In the yellow wobbly shape, {tok(s['digit'])} is blocked from the two red cells (X), "
               f"so it goes in {rcname(s['cell'])}.")
        return {"hl": hl, "values": s["before"]["values"], "block_arrows": block_arrows,
                "cell_strikes": blocked, "target": (s["cell"], s["digit"])}, cap
    if level == 8:
        i = 5
        kn = G.knight_neighbors(i)
        hl = {c: HL_BAD for c in kn}
        hl[i] = HL_TARGET
        q = dict(p, givens=[0] * 16, center_clues={}, corner_clues=[], colors={})
        return {"hl": hl, "knight_from": i, "knight_jumps": [(i, c) for c in kn], "_p": q}, (
            f"The knight jumps in an L (2 cells one way, 1 sideways). Whatever {noun} sits on "
            f"the green cell can't also be on any of the 4 red cells.")
    if level == 9:
        s = _first_step(p, S + ("point", "npair", "xwing"), ("xwing",))
        d = s["digit"]
        hl = {c: HL_TARGET for c in s["pattern"]}
        for c, _ in s["elims"]:
            hl[c] = HL_BAD
        cands = {i: ds for i, ds in enumerate(s["before"]["cands"])
                 if ds and str(i) not in p["center_clues"]}
        a, b, c2, d2 = s["pattern"]
        lines_word = "rows" if s["axis"] == "row" else "columns"
        other = "columns" if s["axis"] == "row" else "rows"
        cap = (f"In two {lines_word}, {tok(d)} fits only in the green corner cells of the X. One {tok(d)} goes "
               f"on each diagonal, so {tok(d)} is zapped from the rest of those {other} (red) - leaving only "
               f"{tok(4)} (circled) in row 2, column 2! (Works the same way when two {other} lock two {lines_word}!)")
        return {"hl": hl, "values": s["before"]["values"], "strikes": s["elims"], "cands": cands,
                "lines": [(a, d2), (b, c2)], "peg_target": (5, 4)}, cap
    if level == 10:
        demo_p = {
            "givens": [0, 4, 3, 0,
                       0, 3, 4, 0,
                       3, 0, 0, 0,
                       0, 2, 0, 0],
            "solution": [1, 4, 3, 2,
                         2, 3, 4, 1,
                         3, 1, 2, 4,
                         4, 2, 1, 3],
            "regions": list(G.STANDARD_REGIONS),
            "anti_knight": False,
            "colors": {},
            "center_clues": {},
            "corner_clues": [],
            "fog_lit": None,
        }
        cands = {0: [1, 2], 4: [1, 2], 12: [1, 4]}
        hl = {0: HL_UNIT, 4: HL_UNIT, 12: HL_TARGET}
        cap = (f"No marks printed? Add your OWN pegs! In column 1, row 1 and row 2 can only be "
               f"{tok(1)} or {tok(2)}. Your pegs show {tok(1)} and {tok(2)} are used up there, "
               f"so cross {tok(1)} off row 4, column 1 (green) - it must be {tok(4)}!")
        return {"_p": demo_p, "hl": hl, "cands": cands, "pair_link": (0, 4),
                "strikes": [(12, 1)], "peg_target": (12, 4)}, cap
    return {}, ""


def _draw_peg_spots_legend(pg, y_baseline, use_colors=False):
    if not use_colors:
        pg.text(MARGIN, y_baseline,
                "Peg spots in every cell:  1 top-left   2 top-right   3 bottom-left   4 bottom-right",
                9, False, color="#555555")
        return
    pg.text(MARGIN, y_baseline, "Peg spots in every cell:", 9, False, color="#555555")
    x = MARGIN + text_width("Peg spots in every cell:   ", 9, False)
    spots = [(1, "top-left"), (2, "top-right"), (3, "bottom-left"), (4, "bottom-right")]
    for d, pos_label in spots:
        fill_c, edge_c, name = PIECE_PALETTE[d]
        pg.fill_color(fill_c)
        pg.stroke_color(edge_c)
        pg.line_width(0.75)
        pg.circle(x + 4, y_baseline - 3.2, 4.2, fill=True, stroke=True)
        label = f"{name} {pos_label}"
        pg.text(x + 11, y_baseline, label, 9, False, color="#444444")
        x += 11 + text_width(label, 9, False) + 16


def lesson_page(pdf, level, example, page_no, use_colors=False):
    lv = LEVEL_BY_NUM[level]
    les = (LESSONS_COLORS if use_colors else LESSONS)[level]
    pg = pdf.new_page()
    pg.fill_color("#26313a")
    pg.round_rect(MARGIN, MARGIN, pg.w - 2 * MARGIN, 60, 10, fill=True, stroke=False)
    pg.text(MARGIN + 18, MARGIN + 25, f"LEVEL {level}  -  NEW TECHNIQUE", 10, True, color="#cfd8dc")
    pg.text(MARGIN + 18, MARGIN + 49, lv["name"], 26, True, color="#ffffff")
    y = MARGIN + 88
    width = pg.w - 2 * MARGIN
    for head, key in (("What it means", "what"), ("On the board", "board"), ("Dad tip", "dad")):
        pg.text(MARGIN, y, head, 13, True, color=INK)
        y = pg.paragraph(MARGIN, y + 2, les[key], 11, width, leading=1.32, color="#222222") + 14
    # example diagram
    kw, cap = lesson_example(example, level, use_colors=use_colors)
    p = kw.pop("_p", example)
    size = 250
    bx = (pg.w - size) / 2
    pg.text(MARGIN, y + 4, "Example", 13, True, color=INK)
    by = y + 14
    draw_board(pg, bx, by, size, p, use_colors=use_colors, **kw)
    y = by + size + 6
    y = pg.paragraph(MARGIN + 30, y, cap, 11, width - 60, leading=1.3, color="#222222")
    book_label = "4x4 Color Sudoku Workbook" if use_colors else "4x4 Sudoku Workbook"
    footer(pg, f"{book_label}  -  page {page_no}")
    return page_no + 1


def cover_page(pdf, data, levels, use_colors=False):
    pg = pdf.new_page()
    pg.fill_color("#eef4fb")
    pg.stroke_color("#b6d4fe")
    pg.line_width(0.9)
    pill_w = 148
    pg.round_rect((pg.w - pill_w) / 2, 78, pill_w, 22, 11, fill=True, stroke=True)
    pg.text(pg.w / 2, 93, "DoDad Puzzles\u2122", 10.5, True, "center", "#1e3a8a")

    title = "4x4 COLOR SUDOKU" if use_colors else "4x4 SUDOKU"
    pg.text(pg.w / 2, 145 if use_colors else 150, title, 40 if use_colors else 44, True, "center", INK)
    pg.text(pg.w / 2, 180 if use_colors else 185,
            "A step-by-step technique workbook for kids (and their dads)", 13,
            False, "center", "#444444")
    demo = next(p for p in data["puzzles"] if p["level"] == 1)
    draw_board(pg, (pg.w - 200) / 2, 200 if use_colors else 215, 200, demo, use_colors=use_colors)
    if use_colors:
        y_leg = 424
        sw = 18
        spacing = 95
        start_x = pg.w / 2 - 1.5 * spacing
        for idx_d, d in enumerate(G.DIGITS):
            cx = start_x + idx_d * spacing
            _draw_color_piece_swatch(pg, cx, y_leg, sw, d, shaded=True)
            pg.text(cx, y_leg + 20, PIECE_PALETTE[d][2], 10, True, "center", INK)
        y = 468
    else:
        y = 460
    pg.text(MARGIN + 60, y, "Levels", 14, True, color=INK)
    step_y = 18 if use_colors else 19
    for lv in levels:
        y += step_y
        n = sum(1 for p in data["puzzles"] if p["level"] == lv["level"])
        pg.text(MARGIN + 60, y, f"{lv['level']:>2}.  {lv['name']}", 11.5, False, color="#222222")
        pg.text(pg.w - MARGIN - 60, y, f"{n} puzzles", 10, False, "right", "#666666")
    ans_file = "answers_colors.pdf" if use_colors else "answers.pdf"
    footer(pg, f"DoDad Puzzles\u2122  \u2022  Generated puzzle set (seed {data['seed']}). Answers are in {ans_file}.")


def welcome_page(pdf, page_no, use_colors=False, book_label=None):
    """Render the motivation & welcome page after the title page and before Level 1.

    Written at a clean 3rd-4th grade reading level with no em-dashes or LLM cliches,
    and with subtle easter eggs tucked naturally into the text for curious kids to find.
    """
    pg = pdf.new_page()
    width = pg.w - 2 * MARGIN
    piece_noun = "color" if use_colors else "number"
    pieces_noun = "colors" if use_colors else "numbers"
    sample_q1 = "What colors are already in this row?" if use_colors else "What numbers are already in this row?"
    sample_q2 = "Where else could Blue go?" if use_colors else "Where else could 3 go?"

    # Top Header Banner
    pg.fill_color("#26313a")
    pg.round_rect(MARGIN, 28, width, 46, 9, fill=True, stroke=False)
    pg.text(MARGIN + 14, 45, "DODAD PUZZLES\u2122  \u2022  WHERE PLAY BUILDS BIG BRAINS", 8.5, True, color="#cfd8dc")
    pg.text(MARGIN + 14, 65, "Welcome to Sudoku: Your Quest Starts Here", 18.5, True, color="#ffffff")

    y = 82

    # -----------------------------------------------------------------------
    # 1. TOP SECTION: FOR KIDS (Quest to Outsmart Dad)
    # -----------------------------------------------------------------------
    kid_box_h = 126
    pg.fill_color("#fffbeb")
    pg.stroke_color("#f59e0b")
    pg.line_width(1.0)
    pg.round_rect(MARGIN, y, width, kid_box_h, 8, fill=True, stroke=True)

    pg.fill_color("#d97706")
    pg.round_rect(MARGIN + 10, y + 7, 198, 17, 4, fill=True, stroke=False)
    pg.text(MARGIN + 18, y + 18.5, "FOR KIDS: YOUR QUEST STARTS HERE", 8.5, True, color="#ffffff")

    yk = y + 27
    yk = pg.rich_paragraph(
        MARGIN + 10, yk,
        [
            ("Every Sudoku puzzle is a tiny mystery, and you are the detective. As you play through this book, you will learn real logic tricks for one big mission:", False, False, "#1d1d1f"),
            ("getting smarter than your Dad.", True, False, "#b45309"),
        ],
        8.8, width - 20, leading=1.22,
    ) + 3.5
    yk = pg.rich_paragraph(
        MARGIN + 10, yk,
        [
            ("Fair warning: there is zero chance he is going to let you win.", True, False, "#1d1d1f"),
            ("You will have to play hard and work right beside him. You will get stuck sometimes, and you will make mistakes. That is part of the deal, and we Dads believe in you completely. Finish this book to become an official", False, False, "#1d1d1f"),
            ("DoDad Graduate.", True, False, "#1d1d1f"),
        ],
        8.8, width - 20, leading=1.22,
    ) + 3.5
    pg.rich_paragraph(
        MARGIN + 10, yk,
        [
            ("Ready? Turn the page and go kick some butt.", True, False, "#b45309"),
            ("(Whatever you do, definitely DO NOT keep reading the grown-up parts below to spy on Dad\u2019s secret playbook. That would be totally unfair.)", False, True, "#78350f"),
        ],
        8.7, width - 20, leading=1.20,
    )

    y += kid_box_h + 9

    # -----------------------------------------------------------------------
    # 2. UPPER-MIDDLE SECTION: HOW TO PLAY (Basic Rules + Subtle Easter Egg)
    # -----------------------------------------------------------------------
    pg.text(MARGIN, y + 10, "How to Play (Basic Rules)", 11.5, True, color=INK)
    y += 13

    y = pg.rich_paragraph(
        MARGIN, y,
        [
            ("Note:", True, False, "#1e3a8a"),
            ("These rules are here for Dad to read out loud. But if you are the kid of a DoDad and you are reading this yourself, make sure Dad knows you are already one step ahead of him. (Whisper the secret code word \u201cPINEAPPLE\u201d to see if he is even paying attention.)", False, True, "#1e3a8a"),
        ],
        8.6, width, leading=1.20,
    ) + 3.5

    rules_bullets = [
        ("Rows, Columns, and Boxes:",
         f"Every board has rows going across, columns going up and down, and thick-lined boxes. A puzzle is solved when one big peg of each {piece_noun} is in every row, every column, and every box, with no repeats."),
        ("From 2\u00d72 Boxes to \u201cChaos\u201d:",
         "Most early puzzles use neat 2\u00d72 boxes. Later in the book, those boxes twist into funny shapes called Chaos Sudoku, or add chess knight jumps. The same main rule still works, and you will build up to them one step at a time."),
        ("Pencil Pegs (The Secret Weapon):",
         f"The tiny pegs are called pencil pegs. When you are not sure which {piece_noun} goes in a space yet, pop tiny pegs into the little holes to keep track of which {pieces_noun} could still fit there."),
        ("The DoDad Twist:",
         f"On some puzzles, the board starts with tiny pencil pegs already in place as clues. That is a special DoDad Sudoku rule you won\u2019t find in the Sunday newspaper."),
    ]
    for b_title, b_body in rules_bullets:
        pg.fill_color("#1d6fd8")
        pg.circle(MARGIN + 4, y + 6.5, 2.0, fill=True, stroke=False)
        y = pg.rich_paragraph(
            MARGIN + 11, y,
            [(b_title, True, False, INK), (b_body, False, False, "#222222")],
            8.6, width - 11, leading=1.20,
        ) + 2.5

    y += 5

    # -----------------------------------------------------------------------
    # 3. LOWER-MIDDLE SECTION: MOTIVATING TEXT FOR ADULTS (Why Play & Logic)
    # -----------------------------------------------------------------------
    adult_box_h = 98
    pg.fill_color("#eff6ff")
    pg.stroke_color("#93c5fd")
    pg.line_width(0.9)
    pg.round_rect(MARGIN, y, width, adult_box_h, 8, fill=True, stroke=True)

    pg.text(MARGIN + 10, y + 14.5, "Why Play, Math, and Logic", 10.5, True, color="#1e3a8a")
    ya = y + 18
    ya = pg.rich_paragraph(
        MARGIN + 10, ya,
        [
            ("Play is how kids learn best, and curiosity is the first step.", True, False, "#1e293b"),
            ("When you test an idea, spot a pattern, and figure out why a piece belongs in a single spot, you are thinking like a mathematician without ever feeling like you are doing homework.", False, False, "#1e293b"),
        ],
        8.6, width - 20, leading=1.21,
    ) + 3
    pg.rich_paragraph(
        MARGIN + 10, ya,
        [
            ("In a busy house, quiet and focused time together is rare.", False, False, "#1e293b"),
            ("DoDad Puzzles\u2122", True, False, "#1e293b"),
            ("was built to make it easier for Dads to spend real, quality time with their kids. Clear math and logic rules give the two of you a calm place to slow down and figure things out side by side. (Wait. If you are a kid and you just read the boring parent box too, tap your nose twice. Your detective skills are officially getting scary.)", False, False, "#1e293b"),
        ],
        8.6, width - 20, leading=1.21,
    )

    y += adult_box_h + 8

    # -----------------------------------------------------------------------
    # 4. BOTTOM SECTION: ADVICE FOR DADS (+ Camouflaged Kid Easter Egg)
    # -----------------------------------------------------------------------
    dad_box_h = 208
    pg.fill_color("#f8fafc")
    pg.stroke_color("#64748b")
    pg.line_width(1.0)
    pg.round_rect(MARGIN, y, width, dad_box_h, 8, fill=True, stroke=True)

    pg.fill_color("#334155")
    pg.round_rect(MARGIN + 10, y + 7, 206, 17, 4, fill=True, stroke=False)
    pg.text(MARGIN + 18, y + 18.5, "FOR DADS: HOW TO WIN BY LOSING", 8.5, True, color="#ffffff")

    yd = y + 27
    yd = pg.rich_paragraph(
        MARGIN + 10, yd,
        [
            ("Every DoDad Puzzles\u2122 set has one goal:", False, False, "#1e293b"),
            ("getting your kids smarter than you are.", True, False, "#0f172a"),
            ("You do that through focused attention. Their brains will learn faster than yours, and that is a beautiful thing.", False, False, "#1e293b"),
            ("Your time and attention is the best thing you can give your kids.", True, False, "#0f172a"),
            ("Pull up a chair and share this board until the day they solve a puzzle faster than you can. The moment that happens, you win. Maybe they can even do the taxes next year.", False, False, "#1e293b"),
        ],
        8.6, width - 20, leading=1.20,
    ) + 4

    pg.text(MARGIN + 10, yd + 9, "To get there, how you play matters:", 8.9, True, color="#0f172a")
    yd += 12

    dad_bullets = [
        ("Step back and let them stumble.",
         "When they put a peg in the wrong spot, hold back. Spotting and fixing their own mistake is how their brain grows."),
        ("Give as little help as possible.",
         f"When they ask for a hint, don\u2019t give the answer. Ask a question instead: \u201c{sample_q1}\u201d or \u201c{sample_q2}\u201d"),
        ("Keep a straight face.",
         "Hold on. If you are a kid and you are reading this right now, stop and make sure your dad knows you are smarter than they are! Look up and tell him: \u201cI just read your secret instructions, Dad. You\u2019re going down.\u201d"),
        ("Celebrate the breakthroughs.",
         "Kids are curious and wired to make their dads happy and proud. When they crack a tough step, make sure they know they crushed it."),
        ("Once your child knows the rules, let them drive.",
         "Put them in charge of the pegs, follow their lead, and enjoy the ride together."),
    ]
    for d_title, d_body in dad_bullets:
        pg.fill_color("#1b873f")
        pg.circle(MARGIN + 14, yd + 6.5, 2.0, fill=True, stroke=False)
        yd = pg.rich_paragraph(
            MARGIN + 21, yd,
            [(d_title, True, False, "#0f172a"), (d_body, False, False, "#1e293b")],
            8.5, width - 31, leading=1.20,
        ) + 2.5

    y += dad_box_h + 7

    # Keep Growing Together sign-off strip
    pg.rich_paragraph(
        MARGIN + 4, y,
        [
            ("Keep Growing Together:", True, False, INK),
            ("This set is just the first in a growing series of", False, False, "#444444"),
            ("DoDad Puzzles\u2122", True, False, INK),
            ("missions. Visit", False, False, "#444444"),
            ("dodadpuzzles.com", True, False, "#1d6fd8"),
            ("for new puzzle quests and upcoming releases. (If a kid made it all the way to the very last line on this page, Dad automatically owes you first pick of the pegs. Sorry, Dad, rules are rules.)", False, False, "#444444"),
        ],
        8.3, width - 8, leading=1.19,
    )

    if book_label is None:
        book_label = "4x4 Color Sudoku Workbook" if use_colors else "4x4 Sudoku Workbook"
    footer(pg, f"{book_label}  -  page {page_no}")
    return page_no + 1


def answer_pages(pdf, puzzles, use_colors=False):
    per_row, per_col = 4, 5
    per = per_row * per_col
    for start in range(0, len(puzzles), per):
        pg = pdf.new_page()
        pg.text(MARGIN, MARGIN + 12, "Answer Key", 16, True, color=INK)
        legend = ("outer tile rim = printed clue"
                  if use_colors else
                  "shaded = printed clue")
        pg.text(pg.w - MARGIN, MARGIN + 12, legend, 8, False, "right", "#555555")
        top = MARGIN + 26
        cw = (pg.w - 2 * MARGIN) / per_row
        ch = (pg.h - MARGIN - 20 - top) / per_col
        size = min(cw - 22, ch - 22)
        for k, p in enumerate(puzzles[start:start + per]):
            col, row = k % per_row, k // per_row
            bx = MARGIN + col * cw + (cw - size) / 2
            by = top + row * ch + 14
            pg.text(bx, by - 4, f"{p['level']}.{p['number']:02d}  {p['technique']}", 7.5, True, color=INK)
            draw_board(pg, bx, by, size, p, show="answer", holes=False, use_colors=use_colors)
        book_label = "4x4 Color Sudoku Workbook" if use_colors else "4x4 Sudoku Workbook"
        footer(pg, f"{book_label}  -  answers")


def render_set(data, levels, out_dir, *, no_lessons=False, no_cover=False, use_colors=False):
    suffix = "_colors" if use_colors else ""
    title_base = "4x4 Color Sudoku Workbook" if use_colors else "4x4 Sudoku Workbook"
    book = PDF(title=title_base)
    page_no = 1
    if not no_cover:
        cover_page(book, data, levels, use_colors=use_colors)
        page_no += 1
        page_no = welcome_page(book, page_no, use_colors=use_colors, book_label=title_base)
    chosen = []
    for lv in levels:
        ps = [p for p in data["puzzles"] if p["level"] == lv["level"]]
        chosen += ps
        if not no_lessons:
            page_no = lesson_page(book, lv["level"], ps[0], page_no, use_colors=use_colors)
        page_no = puzzle_pages(book, ps, lv["level"], page_no, use_colors=use_colors)
    wb = os.path.join(out_dir, f"workbook{suffix}.pdf")
    book.save(wb)

    ans = PDF(title=f"{title_base} - Answers")
    answer_pages(ans, chosen, use_colors=use_colors)
    ap_path = os.path.join(out_dir, f"answers{suffix}.pdf")
    ans.save(ap_path)
    print(f"Wrote {wb} ({len(book.pages)} pages) and {ap_path} ({len(ans.pages)} pages)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puzzles", default=os.path.join(ROOT, "puzzles", "puzzles.json"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--levels", type=int, nargs="*", help="only these level numbers")
    ap.add_argument("--no-lessons", action="store_true", help="skip the lesson page before each level")
    ap.add_argument("--no-cover", action="store_true")
    ap.add_argument("--colors", action="store_true", help="only render the color-piece workbook")
    ap.add_argument("--numbers", action="store_true", help="only render the numbered workbook")
    args = ap.parse_args()

    with open(args.puzzles) as f:
        data = json.load(f)
    for p in data["puzzles"]:
        p["corner_clues"] = [[d, list(c)] for d, c in p["corner_clues"]]
    levels = [lv for lv in data["levels"] if not args.levels or lv["level"] in args.levels]
    os.makedirs(args.out_dir, exist_ok=True)

    modes = []
    if args.colors and not args.numbers:
        modes = [True]
    elif args.numbers and not args.colors:
        modes = [False]
    else:
        modes = [False, True]

    for use_colors in modes:
        render_set(data, levels, args.out_dir,
                   no_lessons=args.no_lessons, no_cover=args.no_cover, use_colors=use_colors)
        render_visual_editions(
            data, levels, args.out_dir,
            use_colors=use_colors,
            draw_board_fn=draw_board,
            draw_swatch_fn=_draw_color_piece_swatch,
            draw_header_swatches_fn=_draw_header_color_swatches,
            welcome_page_fn=welcome_page,
            no_lessons=args.no_lessons,
            no_cover=args.no_cover,
        )


if __name__ == "__main__":
    main()

