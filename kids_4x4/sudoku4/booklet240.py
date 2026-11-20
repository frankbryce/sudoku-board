"""Generate and render the 240-puzzle Multi-Technique Progressive Pocket Booklet.

Each of the 240 puzzles is verified to require 2+ distinct Sudoku techniques
in the same puzzle, deduplicated against both itself and the main workbook
(`puzzles/puzzles.json`), and ordered progressively from easy multi-technique
warmups to boss mashups with organic variety spattered throughout.

Printed as a Half-Letter (5.5" x 8.5") small booklet:
  - Odd pages (front):  1 large puzzle per page
  - Even pages (back):  Matching Timer & Best Time speed log for that exact puzzle

Usage:
    python3 -m sudoku4.booklet240                # generate JSON (if missing) + render PDFs
    python3 -m sudoku4.booklet240 --regenerate   # force fresh 240-puzzle generation
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time

from . import grid as G
from . import logic as L
from .generate import (
    LATIN_REGIONS,
    S,
    _gen_clean_npair,
    _gen_clean_pointing,
    _gen_clean_xwing,
    allowed_of,
    gen_center_corner_combo,
    info_count,
    minimize_givens,
    new_record,
    signature,
    solves,
    unique,
    variant_of,
)
from .pdf import PDF, text_width, wrap
from .render import (
    GOOD,
    INK,
    PIECE_PALETTE,
    STRIKE,
    _draw_color_piece_swatch,
    draw_board,
)
from .visual import draw_arrow, draw_theme_badge

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

HALF_LETTER = (396.0, 612.0)  # 5.5" x 8.5" printable small booklet
BMARGIN = 26.0

# ---------------------------------------------------------------------------
# Multi-technique puzzle generators (every puzzle verified to need 2+ techs!)
# ---------------------------------------------------------------------------

def _uses_both_hs_and_ns(p):
    """True iff solving with singles strictly requires Naked Single (pure HS cannot solve it)
    AND also executes at least one Hidden Single step."""
    v = variant_of(p)
    al = allowed_of(p)
    if solves(p, ("hs_box", "hs_line")):
        return False
    ok, steps = L.solve_logic(p["givens"], v, S, allowed=al)
    if not ok:
        return False
    cnt = L.tech_counts(steps)
    return (cnt.get("hs_box", 0) + cnt.get("hs_line", 0)) >= 1 and cnt.get("ns", 0) >= 1


def gen_hs_ns_combo(rng):
    """Standard 4x4 puzzle requiring BOTH Hidden Singles and Naked Singles."""
    v = G.default_variant()
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if not _uses_both_hs_and_ns(p):
        return None
    return p


def gen_center_corner_warmup(rng):
    """Easier Center + Corner combo with 1 extra given added back for a gentle warm-up."""
    p = gen_center_corner_combo(rng)
    if p is None:
        return None
    v = variant_of(p)
    empty = [i for i in G.CELLS if not p["givens"][i]
             and i not in p["center_clues"]
             and all(i not in cs for _, cs in p["corner_clues"])]
    rng.shuffle(empty)
    for c in empty:
        q = dict(p, givens=list(p["givens"]))
        q["givens"][c] = p["solution"][c]
        if unique(q) and not unique(dict(q, center_clues={})) and not unique(dict(q, corner_clues=[])):
            ok, _ = L.solve_logic(q["givens"], v, S, allowed=allowed_of(q))
            if ok:
                return q
    return p


def gen_variant_center_corner(rng, use_jigsaw=False, use_knight=False):
    """3-technique combo: Jigsaw or Anti-Knight + Center Marks + Snyder Corner Marks."""
    layout = list(rng.choice(G.jigsaw_layouts())) if use_jigsaw else list(G.STANDARD_REGIONS)
    v = G.make_variant(regions=layout, anti_knight=use_knight)
    sol = G.random_grid(v, rng)
    boxes = G.region_units(v["regions"])
    peers = G.peers_of(v)
    p = new_record(sol, regions=layout)
    p["anti_knight"] = use_knight
    for c in rng.sample(G.CELLS, rng.choice([2, 3])):
        p["givens"][c] = sol[c]
    for b in rng.sample(boxes, 2):
        for d in rng.sample(G.DIGITS, 4):
            if any(p["givens"][x] == d for x in b):
                continue
            t = next(x for x in b if sol[x] == d)
            if p["givens"][t] or any(p["givens"][q] == d for q in peers[t]):
                continue
            diag = [o for o in b if o != t and not p["givens"][o]
                    and G.rc(o)[0] != G.rc(t)[0] and G.rc(o)[1] != G.rc(t)[1]
                    and not any(p["givens"][q] == d for q in peers[o])]
            if diag:
                p["corner_clues"].append([d, sorted([t, rng.choice(diag)])])
                break
    if not p["corner_clues"]:
        return None
    corner_cells = {c for _, cs in p["corner_clues"] for c in cs}
    empty = [i for i in G.CELLS if not p["givens"][i] and i not in corner_cells]
    rng.shuffle(empty)
    for i in empty[:rng.choice([2, 3])]:
        peer_giv = {p["givens"][q] for q in peers[i] if p["givens"][q]}
        others = [d for d in G.DIGITS if d != sol[i] and d not in peer_giv]
        if others:
            p["center_clues"][i] = sorted([sol[i], rng.choice(others)])
    if not p["center_clues"]:
        return None

    def grade(q):
        if not q["center_clues"] or not q["corner_clues"] or not unique(q):
            return False
        if unique(dict(q, center_clues={})) or unique(dict(q, corner_clues=[])):
            return False
        if use_jigsaw and unique(dict(q, regions=LATIN_REGIONS)):
            return False
        if use_knight and unique(dict(q, anti_knight=False)):
            return False
        ok, _ = L.solve_logic(q["givens"], v, S, allowed=allowed_of(q))
        return ok

    if not grade(p):
        return None
    for k in rng.sample(range(len(p["corner_clues"])), len(p["corner_clues"])):
        if k < len(p["corner_clues"]):
            q = dict(p, corner_clues=[c for j, c in enumerate(p["corner_clues"]) if j != k])
            if grade(q):
                p = q
    for c in rng.sample(list(p["center_clues"]), len(p["center_clues"])):
        q = dict(p, center_clues={k: val for k, val in p["center_clues"].items() if k != c})
        if grade(q):
            p = q
    minimize_givens(p, rng, grade)
    return p


def gen_center_hs_ns(rng, use_jigsaw=False, use_knight=False):
    """Center-mark clues combined with Jigsaw, Anti-Knight, or both."""
    layout = list(rng.choice(G.jigsaw_layouts())) if use_jigsaw else list(G.STANDARD_REGIONS)
    v = G.make_variant(regions=layout, anti_knight=use_knight)
    grids = G.all_grids(v) if (use_jigsaw and use_knight) else None
    if grids is not None:
        if not grids:
            return None
        sol = list(rng.choice(grids))
    else:
        sol = G.random_grid(v, rng)
    peers = G.peers_of(v)
    p = new_record(sol, regions=layout)
    p["anti_knight"] = use_knight
    n_giv = rng.choice([2, 3])
    for c in rng.sample(G.CELLS, n_giv):
        p["givens"][c] = sol[c]
    empty = [i for i in G.CELLS if not p["givens"][i]]
    rng.shuffle(empty)
    for i in empty[:rng.choice([2, 3, 4])]:
        peer_giv = {p["givens"][q] for q in peers[i] if p["givens"][q]}
        others = [d for d in G.DIGITS if d != sol[i] and d not in peer_giv]
        if others:
            p["center_clues"][i] = sorted([sol[i], rng.choice(others)])
    if not p["center_clues"]:
        return None

    def grade(q):
        if not q["center_clues"] or not unique(q):
            return False
        if unique(dict(q, center_clues={})):
            return False
        if use_jigsaw and unique(dict(q, regions=LATIN_REGIONS)):
            return False
        if use_knight and unique(dict(q, anti_knight=False)):
            return False
        ok, _ = L.solve_logic(q["givens"], v, S, allowed=allowed_of(q))
        return ok

    if not grade(p):
        return None
    for c in rng.sample(list(p["center_clues"]), len(p["center_clues"])):
        q = dict(p, center_clues={k: val for k, val in p["center_clues"].items() if k != c})
        if grade(q):
            p = q
    minimize_givens(p, rng, grade)
    return p


def gen_snyder_combo(rng, use_jigsaw=False, use_knight=False):
    """Snyder corner-mark clues combined with Jigsaw, Anti-Knight, or both."""
    layout = list(rng.choice(G.jigsaw_layouts())) if use_jigsaw else list(G.STANDARD_REGIONS)
    v = G.make_variant(regions=layout, anti_knight=use_knight)
    grids = G.all_grids(v) if (use_jigsaw and use_knight) else None
    if grids is not None:
        if not grids:
            return None
        sol = list(rng.choice(grids))
    else:
        sol = G.random_grid(v, rng)
    boxes = G.region_units(v["regions"])
    peers = G.peers_of(v)
    p = new_record(sol, regions=layout)
    p["anti_knight"] = use_knight
    for c in rng.sample(G.CELLS, rng.choice([2, 3])):
        p["givens"][c] = sol[c]
    for b in rng.sample(boxes, rng.choice([2, 3])):
        for d in rng.sample(G.DIGITS, 4):
            if any(p["givens"][x] == d for x in b):
                continue
            t = next(x for x in b if sol[x] == d)
            if p["givens"][t] or any(p["givens"][q] == d for q in peers[t]):
                continue
            cands = [o for o in b if o != t and not p["givens"][o]
                     and G.rc(o)[0] != G.rc(t)[0] and G.rc(o)[1] != G.rc(t)[1]
                     and not any(p["givens"][q] == d for q in peers[o])]
            if cands:
                p["corner_clues"].append([d, sorted([t, rng.choice(cands)])])
                break
    if not p["corner_clues"]:
        return None

    def grade(q):
        if not q["corner_clues"] or not unique(q):
            return False
        if unique(dict(q, corner_clues=[])):
            return False
        if use_jigsaw and unique(dict(q, regions=LATIN_REGIONS)):
            return False
        if use_knight and unique(dict(q, anti_knight=False)):
            return False
        ok, _ = L.solve_logic(q["givens"], v, S, allowed=allowed_of(q))
        return ok

    if not grade(p):
        return None
    for k in rng.sample(range(len(p["corner_clues"])), len(p["corner_clues"])):
        if k < len(p["corner_clues"]):
            q = dict(p, corner_clues=[c for j, c in enumerate(p["corner_clues"]) if j != k])
            if grade(q):
                p = q
    minimize_givens(p, rng, grade)
    return p


def gen_jigsaw_hs_ns(rng):
    """Jigsaw Sudoku requiring BOTH Hidden Singles and Naked Singles."""
    layout = list(rng.choice(G.jigsaw_layouts()))
    v = G.make_variant(regions=layout)
    sol = G.random_grid(v, rng)
    p = new_record(sol, regions=layout)
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if unique(dict(p, regions=LATIN_REGIONS)):
        return None
    if not _uses_both_hs_and_ns(p):
        return None
    return p


def gen_knight_hs_ns(rng):
    """Anti-Knight Sudoku requiring BOTH Hidden Singles and Naked Singles."""
    v = G.make_variant(anti_knight=True)
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    p["anti_knight"] = True
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if unique(dict(p, anti_knight=False)):
        return None
    if not _uses_both_hs_and_ns(p):
        return None
    return p


def gen_pointing_ns_combo(rng):
    """Pointing Pair puzzle that ALSO uses Naked Singles + Hidden Singles."""
    v = G.default_variant()
    p = _gen_clean_pointing(rng, v)
    if p is None:
        return None
    ok, steps = L.solve_logic(p["givens"], v, S + ("point",), allowed=allowed_of(p))
    if not ok:
        return None
    cnt = L.tech_counts(steps)
    if cnt.get("point", 0) < 1 or cnt.get("ns", 0) < 1:
        return None
    return p


def gen_variant_marks(rng, use_jigsaw=False, use_knight=False, need_tech="point"):
    """Jigsaw or Anti-Knight combined with Pointing Pair, Naked Pair, or X-Wing."""
    layout = list(rng.choice(G.jigsaw_layouts())) if use_jigsaw else list(G.STANDARD_REGIONS)
    v = G.make_variant(regions=layout, anti_knight=use_knight)
    if need_tech == "point":
        p = _gen_clean_pointing(rng, v)
    elif need_tech == "npair":
        p = _gen_clean_npair(rng, v)
    else:
        p = _gen_clean_xwing(rng, v)
    if p is None:
        return None
    if use_jigsaw and unique(dict(p, regions=LATIN_REGIONS)):
        return None
    if use_knight and unique(dict(p, anti_knight=False)):
        return None
    return p


def gen_jigsaw_knight(rng):
    """Jigsaw + Anti-Knight mashup."""
    layout = list(rng.choice(G.jigsaw_layouts()))
    v = G.make_variant(regions=layout, anti_knight=True)
    grids = G.all_grids(v)
    if not grids:
        return None
    sol = list(rng.choice(grids))
    p = new_record(sol, regions=layout)
    p["anti_knight"] = True
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if unique(dict(p, anti_knight=False)) or unique(dict(p, regions=G.STANDARD_REGIONS)):
        return None
    return p


# ---------------------------------------------------------------------------
# 240-Puzzle Multi-Technique Progressive Assembly
# ---------------------------------------------------------------------------

def gen_warmup_wrapper(base_fn):
    """Wrap any multi-technique generator to add 1 extra given back (while keeping all rules required)."""
    def _fn(rng):
        p = base_fn(rng)
        if p is None:
            return None
        v = variant_of(p)
        use_jigsaw = p["regions"] != list(G.STANDARD_REGIONS)
        use_knight = bool(p["anti_knight"])
        has_center = bool(p["center_clues"])
        has_corner = bool(p["corner_clues"])
        empty = [i for i in G.CELLS if not p["givens"][i]
                 and i not in p["center_clues"]
                 and all(i not in cs for _, cs in p["corner_clues"])]
        rng.shuffle(empty)
        for c in empty:
            q = dict(p, givens=list(p["givens"]))
            q["givens"][c] = p["solution"][c]
            if not unique(q):
                continue
            if has_center and unique(dict(q, center_clues={})):
                continue
            if has_corner and unique(dict(q, corner_clues=[])):
                continue
            if use_jigsaw and unique(dict(q, regions=LATIN_REGIONS)):
                continue
            if use_knight and unique(dict(q, anti_knight=False)):
                continue
            ok, _ = L.solve_logic(q["givens"], v, S, allowed=allowed_of(q))
            if ok:
                return q
        return p
    return _fn


RECIPES = [
    # (label, badges, count, base_diff, jitter_span, generator_fn)
    ("Center + Corner Warm-Up",      ["center_marks", "snyder"],                   16, 10.0, 8.0,  gen_center_corner_warmup),
    ("Jigsaw + Center Warm-Up",      ["jigsaw", "center_marks"],                    8, 14.0, 8.0,  gen_warmup_wrapper(lambda r: gen_center_hs_ns(r, use_jigsaw=True))),
    ("Knight + Snyder Warm-Up",      ["anti_knight", "snyder"],                     8, 17.0, 8.0,  gen_warmup_wrapper(lambda r: gen_snyder_combo(r, use_knight=True))),
    ("Center + Corner Marks",        ["center_marks", "snyder"],                   16, 21.0, 10.0, gen_center_corner_combo),
    ("Jigsaw + Center Marks",        ["jigsaw", "center_marks"],                   20, 30.0, 11.0, lambda r: gen_center_hs_ns(r, use_jigsaw=True)),
    ("Jigsaw + Snyder Corners",      ["jigsaw", "snyder"],                         20, 35.0, 11.0, lambda r: gen_snyder_combo(r, use_jigsaw=True)),
    ("Anti-Knight + Center Marks",   ["anti_knight", "center_marks"],              18, 40.0, 11.0, lambda r: gen_center_hs_ns(r, use_knight=True)),
    ("Anti-Knight + Snyder Corners", ["anti_knight", "snyder"],                    18, 45.0, 11.0, lambda r: gen_snyder_combo(r, use_knight=True)),
    ("Jigsaw + Center + Corner",     ["jigsaw", "center_marks", "snyder"],         16, 52.0, 11.0, lambda r: gen_variant_center_corner(r, use_jigsaw=True)),
    ("Knight + Center + Corner",     ["anti_knight", "center_marks", "snyder"],    14, 57.0, 11.0, lambda r: gen_variant_center_corner(r, use_knight=True)),
    ("Jigsaw + Pointing Pair",       ["jigsaw", "pointing"],                       18, 64.0, 10.0, lambda r: gen_variant_marks(r, use_jigsaw=True, need_tech="point")),
    ("Anti-Knight + Pointing Pair",  ["anti_knight", "pointing"],                  16, 69.0, 10.0, lambda r: gen_variant_marks(r, use_knight=True, need_tech="point")),
    ("Jigsaw + Naked Pair",          ["jigsaw", "naked_pair"],                     10, 76.0, 8.0,  lambda r: gen_variant_marks(r, use_jigsaw=True, need_tech="npair")),
    ("Anti-Knight + Naked Pair",     ["anti_knight", "naked_pair"],                 8, 80.0, 8.0,  lambda r: gen_variant_marks(r, use_knight=True, need_tech="npair")),
    ("Jigsaw + Anti-Knight",         ["jigsaw", "anti_knight"],                    12, 84.0, 7.0,  gen_jigsaw_knight),
    ("Jigsaw + Knight + Center",     ["jigsaw", "anti_knight", "center_marks"],     6, 87.0, 6.0,  lambda r: gen_center_hs_ns(r, use_jigsaw=True, use_knight=True)),
    ("Jigsaw + Knight + Snyder",     ["jigsaw", "anti_knight", "snyder"],           6, 89.0, 6.0,  lambda r: gen_snyder_combo(r, use_jigsaw=True, use_knight=True)),
    ("Jigsaw + X-Wing",              ["jigsaw", "xwing_warn", "xwing_boss"],        5, 93.0, 4.0,  lambda r: gen_variant_marks(r, use_jigsaw=True, need_tech="xwing")),
    ("Anti-Knight + X-Wing",         ["anti_knight", "xwing_warn", "xwing_boss"],   5, 96.0, 4.0,  lambda r: gen_variant_marks(r, use_knight=True, need_tech="xwing")),
]


def _stars_for_score(raw_diff: float) -> int:
    if raw_diff < 24:
        return 1
    if raw_diff < 42:
        return 2
    if raw_diff < 62:
        return 3
    if raw_diff < 82:
        return 4
    return 5


def load_existing_sigs(main_json_path: str) -> set:
    if not os.path.exists(main_json_path):
        return set()
    with open(main_json_path) as f:
        data = json.load(f)
    sigs = set()
    for p in data.get("puzzles", []):
        rec = dict(p)
        rec["center_clues"] = {int(k): v for k, v in rec.get("center_clues", {}).items()}
        rec["corner_clues"] = [[d, list(c)] for d, c in rec.get("corner_clues", [])]
        sigs.add(signature(rec))
    return sigs


def generate_240(seed: int = 2027, existing_sigs: set | None = None) -> dict:
    rng = random.Random(seed)
    seen = set(existing_sigs or ())
    all_puzzles = []
    t0 = time.time()

    for label, badges, count, base_diff, jitter_span, fn in RECIPES:
        got = []
        attempts = 0
        max_attempts = max(count * 4000, 12000)
        while len(got) < count and attempts < max_attempts:
            attempts += 1
            p = fn(rng)
            if p is None:
                continue
            sig = signature(p)
            if sig in seen:
                continue
            seen.add(sig)
            # Fewer clues/givens = slightly harder within the same recipe
            clue_penalty = max(0.0, min(6.0, (12 - info_count(p)) * 0.7))
            raw_diff = base_diff + clue_penalty
            sort_score = raw_diff + rng.uniform(-jitter_span, jitter_span)
            p["technique"] = label
            p["badges"] = list(badges)
            p["difficulty"] = round(raw_diff, 1)
            p["stars"] = _stars_for_score(raw_diff)
            p["_sort_score"] = sort_score
            got.append(p)
        print(f"  {label:<30} {len(got):3d}/{count:<3d} ({attempts} tries)")
        all_puzzles.extend(got)

    # Sort progressively harder, with organic variety spattered throughout
    all_puzzles.sort(key=lambda p: (p["_sort_score"], -sum(1 for d in p["givens"] if d)))

    # Normalize for JSON serialization
    cleaned = []
    for idx, p in enumerate(all_puzzles, 1):
        rec = {
            "number": idx,
            "technique": p["technique"],
            "badges": p["badges"],
            "difficulty": p["difficulty"],
            "stars": p["stars"],
            "givens": p["givens"],
            "solution": p["solution"],
            "regions": p["regions"],
            "anti_knight": p["anti_knight"],
            "colors": {str(k): v for k, v in p["colors"].items()},
            "center_clues": {str(k): v for k, v in p["center_clues"].items()},
            "corner_clues": [[d, list(c)] for d, c in p["corner_clues"]],
            "fog_lit": p["fog_lit"],
        }
        cleaned.append(rec)

    print(f"Generated {len(cleaned)} unique multi-technique puzzles in {time.time() - t0:.1f}s")
    return {
        "title": "DoDad Puzzles 4x4 Multi-Technique Challenge Booklet (240 Puzzles)",
        "seed": seed,
        "count": len(cleaned),
        "puzzles": cleaned,
    }


# ---------------------------------------------------------------------------
# Vector Drawing Helpers for the Small Booklet
# ---------------------------------------------------------------------------

def draw_star(pg, cx, cy, r_outer, filled=True, fill_c="#f59f00", stroke_c="#b45309"):
    import math
    r_inner = r_outer * 0.44
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        r = r_outer if k % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    pg.fill_color(fill_c if filled else "#f1f3f5")
    pg.stroke_color(stroke_c if filled else "#cbd5e1")
    pg.line_width(0.8)
    pg.polygon(pts, fill=True, stroke=True)


def draw_difficulty_stars(pg, x_right, cy, stars, r=5.2):
    """Draw 5 difficulty stars right-aligned ending at x_right."""
    gap = r * 2.35
    x0 = x_right - 4 * gap - r
    for i in range(5):
        draw_star(pg, x0 + i * gap, cy, r, filled=(i < stars))


def draw_stopwatch_icon(pg, cx, cy, r):
    """Draw a crisp vector stopwatch icon centered at (cx, cy)."""
    # Top crown button
    pg.fill_color("#b45309")
    pg.stroke_color("#78350f")
    pg.line_width(0.9)
    pg.round_rect(cx - r * 0.24, cy - r * 1.32, r * 0.48, r * 0.24, r * 0.08, fill=True, stroke=True)
    # Stem
    pg.stroke_color("#78350f")
    pg.line_width(1.6)
    pg.line(cx, cy - r * 1.08, cx, cy - r * 0.94)
    # Side pusher
    pg.line(cx + r * 0.66, cy - r * 0.68, cx + r * 0.86, cy - r * 0.88)
    # Watch body
    pg.fill_color("#ffffff")
    pg.stroke_color("#b45309")
    pg.line_width(1.8)
    pg.circle(cx, cy, r * 0.92, fill=True, stroke=True)
    # Tick marks (12, 3, 6, 9)
    pg.stroke_color("#92400e")
    pg.line_width(1.0)
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        pg.line(cx + dx * r * 0.65, cy + dy * r * 0.65, cx + dx * r * 0.80, cy + dy * r * 0.80)
    # Hands
    pg.stroke_color("#1e293b")
    pg.line_width(1.5)
    pg.line_cap(1)
    pg.line(cx, cy, cx, cy - r * 0.52)
    pg.stroke_color("#d62828")
    pg.line_width(1.2)
    pg.line(cx, cy, cx + r * 0.44, cy - r * 0.16)
    pg.line_cap(0)
    # Center pin
    pg.fill_color("#1e293b")
    pg.circle(cx, cy, r * 0.11, fill=True, stroke=False)


# ---------------------------------------------------------------------------
# Booklet Page Renderers (Half-Letter 5.5" x 8.5")
# ---------------------------------------------------------------------------

def booklet_cover_page(pdf, data, use_colors=False):
    pg = pdf.new_page()
    w, h = pg.w, pg.h

    # Brand pill
    pg.fill_color("#eef4fb")
    pg.stroke_color("#b6d4fe")
    pg.line_width(0.9)
    pill_w = 132
    pg.round_rect((w - pill_w) / 2, 38, pill_w, 20, 10, fill=True, stroke=True)
    pg.text(w / 2, 51.5, "DoDad Puzzles\u2122", 9.5, True, "center", "#1e3a8a")

    # Title
    title = "4x4 COLOR SUDOKU" if use_colors else "4x4 SUDOKU"
    pg.text(w / 2, 90, title, 25, True, "center", INK)
    pg.fill_color("#26313a")
    pg.round_rect(BMARGIN + 18, 102, w - 2 * BMARGIN - 36, 26, 7, fill=True, stroke=False)
    pg.text(w / 2, 119, "240 MULTI-TECHNIQUE CHALLENGES", 11.5, True, "center", "#ffffff")

    pg.text(w / 2, 146, "Progressively harder combos  \u2022  1 puzzle per page", 9.5, False, "center", "#444444")
    pg.text(w / 2, 160, "With a Best-Time Speed Timer on the back of every page!", 9.5, True, "center", "#b45309")

    # Sample puzzle in the middle (pick an eye-catching Jigsaw + Pointing or Center + Corner)
    sample = next((p for p in data["puzzles"] if "Jigsaw + Snyder" in p["technique"]), data["puzzles"][0])
    bsize = 178.0
    draw_board(pg, (w - bsize) / 2, 176, bsize, sample, use_colors=use_colors)

    y = 368
    if use_colors:
        spacing = 74
        start_x = w / 2 - 1.5 * spacing
        for idx_d, d in enumerate(G.DIGITS):
            cx = start_x + idx_d * spacing
            _draw_color_piece_swatch(pg, cx, y + 6, 15, d, shaded=True)
            pg.text(cx, y + 24, PIECE_PALETTE[d][2], 8.5, True, "center", INK)
        y += 38

    # Difficulty Ladder Card
    box_w = w - 2 * BMARGIN
    pg.fill_color("#f8fafc")
    pg.stroke_color("#cbd5e1")
    pg.line_width(0.9)
    pg.round_rect(BMARGIN, y, box_w, 134, 8, fill=True, stroke=True)
    pg.text(BMARGIN + 12, y + 18, "Inside This Pocket Booklet", 10.5, True, color=INK)

    tiers = [
        (1, "Warm-Up Combos", "Center+Corner & Gentle Variants"),
        (2, "Double Logic",   "Jigsaw & Anti-Knight + Marks"),
        (3, "Triple Combos",  "Jigsaw/Knight + Center + Corner"),
        (4, "Pair Lasers",    "Pointing & Naked Pair Mashups"),
        (5, "Boss Mashups",   "Jigsaw+Knight & X-Wing Combos"),
    ]
    ry = y + 34
    for stars, tname, tdesc in tiers:
        for i in range(5):
            draw_star(pg, BMARGIN + 16 + i * 10.5, ry - 3, 4.0, filled=(i < stars))
        pg.text(BMARGIN + 74, ry, tname, 8.8, True, color=INK)
        pg.text(w - BMARGIN - 10, ry, tdesc, 8.0, False, "right", "#555555")
        ry += 20

    ans_name = "answers_240_colors.pdf" if use_colors else "answers_240.pdf"
    pg.text(w / 2, h - 18, f"DoDad Puzzles\u2122  \u2022  Seed {data['seed']}  \u2022  Answers in {ans_name}",
            7.5, False, "center", "#666666")


def booklet_guide_page(pdf, use_colors=False):
    """Page 2 (back of cover): Printing instructions, timer guide, and badge legend."""
    pg = pdf.new_page()
    w, h = pg.w, pg.h
    bw = w - 2 * BMARGIN

    pg.fill_color("#26313a")
    pg.round_rect(BMARGIN, BMARGIN, bw, 40, 8, fill=True, stroke=False)
    pg.text(BMARGIN + 12, BMARGIN + 16, "HOW TO USE THIS BOOKLET", 8.0, True, color="#cfd8dc")
    pg.text(BMARGIN + 12, BMARGIN + 32, "Printing, Timing & Symbols", 14.5, True, color="#ffffff")

    y = BMARGIN + 52

    # 1. Printing card
    pg.fill_color("#eff6ff")
    pg.stroke_color("#93c5fd")
    pg.line_width(0.8)
    pg.round_rect(BMARGIN, y, bw, 94, 7, fill=True, stroke=True)
    pg.text(BMARGIN + 10, y + 16, "Printing as a Small Booklet (5.5\" x 8.5\")", 9.8, True, color="#1e3a8a")
    pg.paragraph(
        BMARGIN + 10, y + 20,
        "Print double-sided (flip on long edge) on Half-Letter paper, OR use your PDF viewer's "
        "Booklet / 2-up print mode on standard US Letter (8.5\" x 11\") in 20- to 40-page sections. "
        "Every puzzle lands on the FRONT of a page, with its matching Speed Timer & Best Time log "
        "right on the BACK!",
        8.5, bw - 20, leading=1.28, color="#1e293b",
    )
    y += 104

    # 2. Speed Timer card
    pg.fill_color("#fffbeb")
    pg.stroke_color("#f59e0b")
    pg.line_width(0.8)
    pg.round_rect(BMARGIN, y, bw, 88, 7, fill=True, stroke=True)
    draw_stopwatch_icon(pg, BMARGIN + 26, y + 44, 15)
    pg.text(BMARGIN + 50, y + 17, "Race the Clock (and Each Other!)", 9.8, True, color="#92400e")
    pg.paragraph(
        BMARGIN + 50, y + 21,
        "Start a timer when you set up the puzzle on your 4x4 board. When you place the last piece, "
        "flip the page over and write down your time! Replay any puzzle later to beat your Personal "
        "Best, or track Dad vs. Kid records.",
        8.5, bw - 60, leading=1.28, color="#451a03",
    )
    y += 100

    # 3. Technique Symbol Key
    pg.text(BMARGIN, y + 10, "Technique Symbols", 11.0, True, color=INK)
    y += 18
    symbols = [
        ("hidden_single", "Hidden Single"),
        ("naked_single",  "Naked Single"),
        ("center_marks",  "Center Marks"),
        ("snyder",        "Snyder Corners"),
        ("pointing",      "Pointing Pair"),
        ("naked_pair",    "Naked Pair"),
        ("jigsaw",        "Jigsaw Shapes"),
        ("anti_knight",   "Anti-Knight"),
        ("xwing_boss",    "X-Wing Boss"),
        ("xwing_warn",    "X-Wing Required!"),
    ]
    col_w = (bw - 12) / 2.0
    for idx, (skey, sname) in enumerate(symbols):
        col = idx // 5
        row = idx % 5
        sx = BMARGIN + col * (col_w + 12)
        sy = y + row * 34
        pg.fill_color("#f8fafc")
        pg.stroke_color("#dee2e6")
        pg.line_width(0.75)
        pg.round_rect(sx, sy, col_w, 27, 5, fill=True, stroke=True)
        draw_theme_badge(pg, sx + 15, sy + 13.5, 9.5, skey, use_colors=use_colors)
        pg.text(sx + 31, sy + 17, sname, 9.2, True, color="#222222")

    # 4. Bottom tip
    y_bot = h - 78
    pg.fill_color("#f0fdf4")
    pg.stroke_color("#86efac")
    pg.line_width(0.8)
    pg.round_rect(BMARGIN, y_bot, bw, 44, 7, fill=True, stroke=True)
    pg.paragraph(
        BMARGIN + 10, y_bot + 5,
        "Every puzzle in this booklet requires at least TWO different techniques together. "
        "Use your center and corner pencil pegs whenever a puzzle gets spicy!",
        8.4, bw - 20, leading=1.28, color="#14532d",
    )
    pg.text(w / 2, h - 18, "DoDad Puzzles\u2122  \u2022  240 Multi-Technique Challenges",
            7.5, False, "center", "#777777")


def booklet_puzzle_front_page(pdf, p, total, use_colors=False):
    """Odd page (front): 1 large puzzle centered on the Half-Letter page."""
    pg = pdf.new_page()
    w, h = pg.w, pg.h
    bw = w - 2 * BMARGIN
    num = p["number"]

    # Header row: Puzzle #NNN on left, Difficulty stars + progress on right
    pg.fill_color("#26313a")
    pg.round_rect(BMARGIN, BMARGIN, bw, 42, 8, fill=True, stroke=False)
    pg.text(BMARGIN + 14, BMARGIN + 27, f"Puzzle #{num:03d}", 17.5, True, color="#ffffff")
    draw_difficulty_stars(pg, w - BMARGIN - 12, BMARGIN + 15, p["stars"], r=5.0)
    pg.text(w - BMARGIN - 12, BMARGIN + 34, f"{num} of {total}", 8.0, False, "right", "#cbd5e1")

    # Technique badge strip
    y_strip = BMARGIN + 52
    is_xwing = "X-Wing" in p["technique"]
    pg.fill_color("#fff8e6" if is_xwing else "#f8fafc")
    pg.stroke_color(STRIKE if is_xwing else "#dee2e6")
    pg.line_width(1.0 if is_xwing else 0.8)
    pg.round_rect(BMARGIN, y_strip, bw, 32, 7, fill=True, stroke=True)

    badges = p.get("badges", [])
    bx_cur = BMARGIN + 16
    for b_key in badges:
        draw_theme_badge(pg, bx_cur, y_strip + 16, 10.0, b_key, use_colors=use_colors)
        bx_cur += 25
    pg.text(bx_cur + 2, y_strip + 20, p["technique"], 10.5, True,
            color=STRIKE if is_xwing else INK)

    # Active rule tags (if Jigsaw / Anti-Knight / X-Wing)
    tags = []
    if p["regions"] != list(G.STANDARD_REGIONS):
        tags.append("Jigsaw shapes")
    if p.get("anti_knight"):
        tags.append("No knight-jump repeats")
    if is_xwing:
        tags.append("X-Wing Boss!")
    y_board_top = y_strip + 46
    if tags:
        pg.text(w / 2, y_strip + 45, "  \u2022  ".join(tags), 8.8, True, "center",
                STRIKE if is_xwing else "#475569")
        y_board_top = y_strip + 58

    # Giant centered 4x4 board!
    bsize = 310.0
    bx = (w - bsize) / 2.0
    by = y_board_top + 6
    draw_board(pg, bx, by, bsize, p, use_colors=use_colors)

    # Bottom info & flip-over prompt
    y_bot = by + bsize + 18
    if use_colors:
        # Mini color piece reminder bar
        spacing = 68
        sx0 = w / 2 - 1.5 * spacing
        for idx_d, d in enumerate(G.DIGITS):
            cx = sx0 + idx_d * spacing
            _draw_color_piece_swatch(pg, cx - 14, y_bot, 11, d, shaded=False)
            pg.text(cx - 4, y_bot + 3.5, PIECE_PALETTE[d][2], 8.2, True, color="#444444")
        y_bot += 22

    # Solved checkbox + Flip prompt pill
    pg.fill_color("#f0fdf4")
    pg.stroke_color("#86efac")
    pg.line_width(0.85)
    pg.round_rect(BMARGIN, y_bot, bw, 30, 7, fill=True, stroke=True)

    # Checkbox
    cbx, cby = BMARGIN + 12, y_bot + 9
    pg.fill_color("#ffffff")
    pg.stroke_color(GOOD)
    pg.line_width(1.1)
    pg.rect(cbx, cby, 12, 12, fill=True, stroke=True)
    pg.text(cbx + 18, y_bot + 19, "Solved!", 9.5, True, color="#14532d")

    pg.text(w - BMARGIN - 12, y_bot + 19, "Flip page over for Timer & Best Time  ->",
            8.5, True, "right", "#15803d")

    pg.text(w / 2, h - 16, f"DoDad Puzzles\u2122  \u2022  Puzzle #{num:03d} (Front)",
            7.5, False, "center", "#777777")


def booklet_timer_back_page(pdf, p, use_colors=False):
    """Even page (back of Puzzle #N): Timer & Best Time tracker for that exact puzzle."""
    pg = pdf.new_page()
    w, h = pg.w, pg.h
    bw = w - 2 * BMARGIN
    num = p["number"]

    # Header bar matching the puzzle on the front
    pg.fill_color("#334155")
    pg.round_rect(BMARGIN, BMARGIN, bw, 40, 8, fill=True, stroke=False)
    pg.text(BMARGIN + 12, BMARGIN + 16, f"PUZZLE #{num:03d}  \u2022  SPEED LOG", 8.0, True, color="#cbd5e1")
    pg.text(BMARGIN + 12, BMARGIN + 32, "Timer & Best Time", 14.0, True, color="#ffffff")
    draw_difficulty_stars(pg, w - BMARGIN - 12, BMARGIN + 20, p["stars"], r=4.6)

    y = BMARGIN + 52

    # 1. Prominent BEST TIME Trophy Box
    best_h = 112
    pg.fill_color("#fffbeb")
    pg.stroke_color("#f59e0b")
    pg.line_width(1.3)
    pg.round_rect(BMARGIN, y, bw, best_h, 9, fill=True, stroke=True)

    # Stopwatch icon on left
    draw_stopwatch_icon(pg, BMARGIN + 38, y + 48, 22)

    pg.text(BMARGIN + 76, y + 22, "BEST TIME", 11.5, True, color="#92400e")
    pg.text(w - BMARGIN - 12, y + 22, p["technique"], 8.2, False, "right", "#92400e")

    # Big writable MM : SS digital boxes
    bx_m = BMARGIN + 76
    by_m = y + 30
    box_w_t, box_h_t = 68, 38
    pg.fill_color("#ffffff")
    pg.stroke_color("#d97706")
    pg.line_width(1.2)
    pg.round_rect(bx_m, by_m, box_w_t, box_h_t, 6, fill=True, stroke=True)
    pg.round_rect(bx_m + box_w_t + 18, by_m, box_w_t, box_h_t, 6, fill=True, stroke=True)
    pg.text(bx_m + box_w_t + 9, by_m + 27, ":", 22, True, "center", "#b45309")
    pg.text(bx_m + box_w_t / 2, by_m + box_h_t + 11, "MIN", 7.2, True, "center", "#92400e")
    pg.text(bx_m + box_w_t + 18 + box_w_t / 2, by_m + box_h_t + 11, "SEC", 7.2, True, "center", "#92400e")

    # Solver + Date line inside Best Time card
    pg.text(BMARGIN + 14, y + best_h - 11, "Holder: ________________________", 8.5, False, color="#78350f")
    pg.text(w - BMARGIN - 14, y + best_h - 11, "Date: ______________", 8.5, False, "right", "#78350f")

    y += best_h + 12

    # 2. Dad vs. Kid Best Time split strip
    split_h = 46
    half_w = (bw - 10) / 2.0
    for idx_k, (label, bg, edge, tc) in enumerate((
        ("KID'S BEST", "#eff6ff", "#93c5fd", "#1e3a8a"),
        ("DAD'S BEST", "#f8fafc", "#94a3b8", "#334155"),
    )):
        sx = BMARGIN + idx_k * (half_w + 10)
        pg.fill_color(bg)
        pg.stroke_color(edge)
        pg.line_width(0.9)
        pg.round_rect(sx, y, half_w, split_h, 7, fill=True, stroke=True)
        pg.text(sx + 10, y + 15, label, 8.2, True, color=tc)
        pg.fill_color("#ffffff")
        pg.stroke_color(edge)
        pg.line_width(0.8)
        pg.round_rect(sx + 10, y + 21, half_w - 20, 18, 4, fill=True, stroke=True)
        pg.text(sx + half_w / 2, y + 33.5, ":     ", 11, True, "center", "#94a3b8")

    y += split_h + 14

    # 3. Timed Attempts Log Table (8 rows)
    pg.text(BMARGIN, y + 10, "Timed Runs Log", 10.5, True, color=INK)
    pg.text(w - BMARGIN, y + 10, "Beat your time on a rematch!", 8.0, False, "right", "#64748b")
    y += 16

    cols = [
        ("Run", 32),
        ("Date", 74),
        ("Solver", 94),
        ("Time (m:ss)", 86),
        ("Best?", 58),
    ]
    # Header row
    hdr_h = 22
    row_h = 26
    n_rows = 8
    pg.fill_color("#e2e8f0")
    pg.stroke_color("#94a3b8")
    pg.line_width(0.8)
    pg.round_rect(BMARGIN, y, bw, hdr_h, 4, fill=True, stroke=True)
    cx = BMARGIN
    for cname, cw in cols:
        pg.text(cx + cw / 2, y + 14.5, cname, 8.2, True, "center", "#1e293b")
        cx += cw
    y_tbl = y + hdr_h

    for r_i in range(n_rows):
        ry = y_tbl + r_i * row_h
        pg.fill_color("#ffffff" if r_i % 2 == 0 else "#f8fafc")
        pg.stroke_color("#cbd5e1")
        pg.line_width(0.6)
        pg.rect(BMARGIN, ry, bw, row_h, fill=True, stroke=True)
        # Vertical dividers
        cx = BMARGIN
        for c_idx, (_, cw) in enumerate(cols):
            if c_idx > 0:
                pg.line(cx, ry, cx, ry + row_h)
            cx += cw
        # Run number
        pg.text(BMARGIN + 16, ry + 16.5, f"#{r_i + 1}", 8.5, True, "center", "#64748b")
        # Colon guide in Time column
        time_x = BMARGIN + 32 + 74 + 94 + 43
        pg.text(time_x, ry + 16.5, ":", 10.0, True, "center", "#cbd5e1")
        # Checkbox in Best? column
        chk_x = BMARGIN + 32 + 74 + 94 + 86 + 24
        pg.fill_color("#ffffff")
        pg.stroke_color("#94a3b8")
        pg.line_width(0.8)
        pg.rect(chk_x, ry + 8, 10, 10, fill=True, stroke=True)

    y_notes = y_tbl + n_rows * row_h + 14

    # 4. Quick Notes strip
    pg.text(BMARGIN, y_notes + 8, "Notes / Trickiest Step:", 8.5, True, color="#475569")
    pg.stroke_color("#cbd5e1")
    pg.line_width(0.7)
    pg.line(BMARGIN + 104, y_notes + 10, w - BMARGIN, y_notes + 10)
    pg.line(BMARGIN, y_notes + 28, w - BMARGIN, y_notes + 28)

    pg.text(w / 2, h - 16, f"DoDad Puzzles\u2122  \u2022  Puzzle #{num:03d} (Back)",
            7.5, False, "center", "#777777")


def booklet_answer_pages(pdf, puzzles, use_colors=False):
    """Compact Half-Letter answer key (6 answers per page = 40 pages for 240 puzzles)."""
    per_row, per_col = 2, 3
    per = per_row * per_col
    for start in range(0, len(puzzles), per):
        pg = pdf.new_page()
        pg.text(BMARGIN, BMARGIN + 12, "240 Multi-Technique Answer Key", 12.5, True, color=INK)
        pg.text(pg.w - BMARGIN, BMARGIN + 12,
                f"#{puzzles[start]['number']:03d} - #{puzzles[min(start + per, len(puzzles)) - 1]['number']:03d}",
                8.5, True, "right", "#555555")
        top = BMARGIN + 22
        cw = (pg.w - 2 * BMARGIN) / per_row
        ch = (pg.h - BMARGIN - 16 - top) / per_col
        size = min(cw - 24, ch - 26)
        for k, p in enumerate(puzzles[start:start + per]):
            col, row = k % per_row, k // per_row
            bx = BMARGIN + col * cw + (cw - size) / 2
            by = top + row * ch + 18
            pg.text(bx, by - 5, f"#{p['number']:03d}  {p['technique']}", 7.5, True, color=INK)
            draw_board(pg, bx, by, size, p, show="answer", holes=False, use_colors=use_colors)
        pg.text(pg.w / 2, pg.h - 14, "DoDad Puzzles\u2122  \u2022  240 Multi-Technique Answers",
                7.5, False, "center", "#777777")


def render_booklet_240(data, out_dir, use_colors=False):
    suffix = "_colors" if use_colors else ""
    title_base = "4x4 Color Sudoku - 240 Multi-Technique Booklet" if use_colors else "4x4 Sudoku - 240 Multi-Technique Booklet"
    book = PDF(size=HALF_LETTER, title=title_base)
    booklet_cover_page(book, data, use_colors=use_colors)
    booklet_guide_page(book, use_colors=use_colors)
    total = len(data["puzzles"])
    for p in data["puzzles"]:
        booklet_puzzle_front_page(book, p, total, use_colors=use_colors)
        booklet_timer_back_page(book, p, use_colors=use_colors)

    wb_path = os.path.join(out_dir, f"booklet_240{suffix}.pdf")
    book.save(wb_path)

    ans = PDF(size=HALF_LETTER, title=f"{title_base} - Answers")
    booklet_answer_pages(ans, data["puzzles"], use_colors=use_colors)
    ans_path = os.path.join(out_dir, f"answers_240{suffix}.pdf")
    ans.save(ans_path)
    print(f"Wrote {wb_path} ({len(book.pages)} pages) and {ans_path} ({len(ans.pages)} pages)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=2027)
    ap.add_argument("--json", default=os.path.join(ROOT, "puzzles", "multi_tech_240.json"))
    ap.add_argument("--main-puzzles", default=os.path.join(ROOT, "puzzles", "puzzles.json"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--regenerate", action="store_true")
    args = ap.parse_args()

    if args.regenerate or not os.path.exists(args.json):
        existing = load_existing_sigs(args.main_puzzles)
        data = generate_240(seed=args.seed, existing_sigs=existing)
        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(data, f, indent=1)
        print(f"Saved {args.json}")
    else:
        with open(args.json) as f:
            data = json.load(f)

    # Ensure corner_clues format
    for p in data["puzzles"]:
        p["corner_clues"] = [[d, list(c)] for d, c in p["corner_clues"]]

    os.makedirs(args.out_dir, exist_ok=True)
    render_booklet_240(data, args.out_dir, use_colors=True)
    render_booklet_240(data, args.out_dir, use_colors=False)


if __name__ == "__main__":
    main()
