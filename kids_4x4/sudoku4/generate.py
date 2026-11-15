"""Level definitions + puzzle generators for the 4x4 kids' progression.

Run:   python3 -m sudoku4.generate  [--seed 2026] [--per-level 12]
Writes puzzles/puzzles.json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time

from . import grid as G
from . import logic as L

S = L.SINGLES  # ("hs_box", "hs_line", "ns")
LATIN_REGIONS = [r for r in range(4) for _ in range(4)]  # "no boxes" (rows duplicated)

# ---------------------------------------------------------------------------
# Level catalogue (kid-facing text lives here so the renderer can use it)
# ---------------------------------------------------------------------------

LEVELS = [
    {"level": 1, "key": "hidden_single", "name": "Hidden Single",
     "hint": "Look at one row, column or box. Is there only ONE cell left where a number can go?"},
    {"level": 2, "key": "naked_single", "name": "Naked Single",
     "hint": "Look at one empty cell. Its row, column and box already use 3 numbers - the 4th one goes here!"},
    {"level": 3, "key": "center_marks", "name": "Center Marks",
     "hint": "When a cell's row, column and box already use 2 numbers, mark the 2 numbers left in the center. Cross one out when it appears in that row, column or box!"},
    {"level": 4, "key": "snyder", "name": "Snyder Notation",
     "hint": "A small number in a corner means: inside this box, that number is in one of the corner-marked cells."},
    {"level": 5, "key": "pointing", "name": "Pointing Pairs",
     "hint": "If a box's corner marks for a number sit in one line, that number is zapped from the rest of that line."},
    {"level": 6, "key": "naked_pair", "name": "Naked Pair",
     "hint": "Two cells in a row, column or box with the SAME two center marks own those numbers. Nobody else there can use them."},
    {"level": 7, "key": "jigsaw", "name": "Jigsaw Sudoku",
     "hint": "The boxes are funny shapes! Each thick-outlined shape still needs 1, 2, 3 and 4."},
    {"level": 8, "key": "anti_knight", "name": "Anti-Knight Sudoku",
     "hint": "Normal rules, PLUS: the same number can never be a chess knight's jump apart (2 one way, 1 the other)."},
    {"level": 9, "key": "xwing", "name": "X-Wing (Optional)",
     "hint": "Optional boss move! Works in rows OR columns: if a number fits in only 2 cells across 2 rows (lined up in 2 columns), zap it from the rest of those columns - or 2 columns zapping 2 rows!"},
    {"level": 10, "key": "all_star", "name": "All-Star Challenge",
     "hint": "60 puzzles of increasing difficulty mixing every technique! The final 12 puzzles at the end require an X-Wing (marked with a warning symbol)."},
]
LEVEL_BY_NUM = {lv["level"]: lv for lv in LEVELS}

# ---------------------------------------------------------------------------
# Puzzle record helpers
# ---------------------------------------------------------------------------


def new_record(solution, regions=None):
    return {
        "givens": [0] * 16,
        "solution": list(solution),
        "regions": list(regions or G.STANDARD_REGIONS),
        "anti_knight": False,
        "colors": {},
        "center_clues": {},     # cell -> sorted digits
        "corner_clues": [],     # [digit, [cell, cell]]
        "fog_lit": None,        # list of initially clear cells (fog levels only)
    }


def variant_of(p):
    return G.make_variant(regions=p["regions"], anti_knight=p["anti_knight"], colors=p["colors"])


def allowed_of(p):
    if not p["center_clues"] and not p["corner_clues"]:
        return None
    al = [set(G.DIGITS) for _ in G.CELLS]
    for c, ds in p["center_clues"].items():
        al[int(c)] &= set(ds)
    boxes = G.region_units(p["regions"])
    box_spots = {(b_idx, d): set(b) for b_idx, b in enumerate(boxes) for d in G.DIGITS}
    for d, cells in p["corner_clues"]:
        b_idx = next(idx for idx, b in enumerate(boxes) if cells[0] in b)
        box_spots[(b_idx, d)] &= set(cells)
    return {"cands": al, "box_spots": box_spots}


def unique(p):
    return G.is_unique(p["givens"], variant_of(p), allowed_of(p))


def solves(p, techs):
    return L.solve_logic(p["givens"], variant_of(p), techs, allowed=allowed_of(p))[0]


def info_count(p):
    center_info = sum(4 - len(ds) for ds in p["center_clues"].values())
    return (3 * sum(1 for d in p["givens"] if d) + center_info + len(p["corner_clues"])
            + len(p["colors"]))


def signature(p):
    return json.dumps([p["givens"], p["regions"], sorted(p["center_clues"].items()),
                       sorted(map(lambda x: (x[0], tuple(x[1])), p["corner_clues"])),
                       sorted(p["colors"].items()), p["anti_knight"], p["fog_lit"]])


def minimize_givens(p, rng, keep):
    """Greedily blank givens (random order) while `keep(p)` stays true."""
    cells = [i for i in G.CELLS if p["givens"][i]]
    rng.shuffle(cells)
    for c in cells:
        old = p["givens"][c]
        p["givens"][c] = 0
        if not keep(p):
            p["givens"][c] = old
    return p


def add_back_givens(p, rng, target):
    empty = [i for i in G.CELLS if not p["givens"][i]]
    rng.shuffle(empty)
    while sum(1 for d in p["givens"] if d) < target and empty:
        c = empty.pop()
        p["givens"][c] = p["solution"][c]
    return p


# ---------------------------------------------------------------------------
# Generators — each returns a candidate record or None
# ---------------------------------------------------------------------------

def gen_plain(rng, level):
    v = G.default_variant()
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    p["givens"] = list(sol)
    if level == 1:
        keep = lambda q: unique(q) and solves(q, ("hs_box", "hs_line"))
    else:
        keep = lambda q: unique(q) and solves(q, ("ns",))
    minimize_givens(p, rng, keep)
    # nicer progression: early puzzles get extra givens (added later by schedule)
    return p


def starting_pure_naked_single(p):
    """True if the opening position has a naked single that is NOT also a hidden single."""
    st = L.State(p["givens"], variant_of(p), allowed_of(p))
    hs = set()
    for u in st.units:
        for d in G.DIGITS:
            spots = [i for i in u if not st.values[i] and d in st.cands[i]]
            if len(spots) == 1 and not any(st.values[i] == d for i in u):
                hs.add((spots[0], d))
    for i in G.CELLS:
        if not st.values[i] and len(st.cands[i]) == 1:
            if (i, next(iter(st.cands[i]))) not in hs:
                return True
    return False


def _cand_state_to_record(sol, al, regions=None, anti_knight=False):
    p = new_record(sol, regions=regions)
    p["anti_knight"] = anti_knight
    for i in G.CELLS:
        if len(al[i]) == 1:
            p["givens"][i] = sol[i]
        else:
            p["center_clues"][i] = sorted(al[i])
    return p


def _has_other_pair(al, units, target_pair_cells):
    tset = set(target_pair_cells)
    for u in units:
        open2 = [i for i in u if len(al[i]) == 2]
        for a in range(len(open2)):
            for b in range(a + 1, len(open2)):
                x, y = open2[a], open2[b]
                if al[x] == al[y] and {x, y} != tset:
                    return True
    return False


def _gen_clean_npair(rng, v):
    grids = G.all_grids(v)
    if not grids:
        return None
    sol = list(rng.choice(grids))
    units = G.units_of(v)
    u = rng.choice(units)
    x, y = rng.sample(list(u), 2)
    pair = {sol[x], sol[y]}
    z, w = [c for c in u if c not in (x, y)]
    other_pair = {sol[z], sol[w]}
    al = [set(G.DIGITS) for _ in G.CELLS]
    al[x] = set(pair)
    al[y] = set(pair)
    d1, d2 = sorted(pair)
    al[z] = other_pair | {d1}
    al[w] = other_pair | {d2}

    must_keep = {(x, d1), (x, d2), (y, d1), (y, d2), (z, d1), (w, d2)}
    cand_drops = [(i, d) for i in G.CELLS if i not in (x, y)
                  for d in G.DIGITS if d != sol[i] and d in al[i] and (i, d) not in must_keep]
    rng.shuffle(cand_drops)
    for i, d in cand_drops:
        if len(al[i]) <= 2:
            continue
        al[i].discard(d)
        st = L.State([0] * 16, v, al)
        if any(L.TECH_FUNCS[t](st) is not None for t in S + ("point",)) or _has_other_pair(al, units, (x, y)):
            al[i].add(d)
    if any(len(s) not in (2, 3) for s in al) or _has_other_pair(al, units, (x, y)):
        return None
    p = _cand_state_to_record(sol, al, regions=v["regions"], anti_knight=v["anti_knight"])
    if not unique(p) or solves(p, S + ("point",)):
        return None
    ok, steps = L.solve_logic(p["givens"], v, S + ("point", "npair"), allowed=allowed_of(p))
    if not ok or not steps or steps[0]["tech"] != "npair":
        return None
    if len({c for c, _ in steps[0]["elims"]}) < 2 or len(set(steps[0]["digits"]) & {d for _, d in steps[0]["elims"]}) < 2:
        return None
    return p


def _gen_clean_xwing(rng, v):
    sol = G.random_grid(v, rng)
    d = rng.choice(G.DIGITS)
    axis = rng.choice(["row", "col"])
    base_lines = G.rows() if axis == "row" else G.cols()
    cover_lines = G.cols() if axis == "row" else G.rows()
    pairs = []
    for a in range(4):
        for b in range(a + 1, 4):
            k1 = next(k for k in range(4) if sol[base_lines[a][k]] == d)
            k2 = next(k for k in range(4) if sol[base_lines[b][k]] == d)
            if k1 != k2:
                corners = [base_lines[a][k1], base_lines[a][k2], base_lines[b][k1], base_lines[b][k2]]
                if len({v["regions"][c] for c in corners}) == 4:
                    pairs.append((a, b, min(k1, k2), max(k1, k2), corners))
    if not pairs:
        return None
    a, b, k1, k2, corners = rng.choice(pairs)
    al = [set(G.DIGITS) for _ in G.CELLS]
    for line_idx in (a, b):
        for c in base_lines[line_idx]:
            if c not in corners:
                al[c].discard(d)
    elim_targets = [c for k in (k1, k2) for c in cover_lines[k] if c not in corners]
    rng.shuffle(elim_targets)
    n_t = 2
    for t in elim_targets[:n_t]:
        al[t] = {sol[t], d}

    must_keep_d = set(corners) | set(elim_targets[:n_t])
    cand_drops = [(i, x) for i in G.CELLS for x in G.DIGITS
                  if x != sol[i] and x in al[i] and not (i in must_keep_d and x == d)]
    rng.shuffle(cand_drops)
    for i, x in cand_drops:
        if len(al[i]) <= 2:
            continue
        al[i].discard(x)
        st = L.State([0] * 16, v, al)
        if any(L.TECH_FUNCS[t](st) is not None for t in S + ("point", "npair")):
            al[i].add(x)
    if any(len(s) not in (2, 3) for s in al):
        return None
    p = _cand_state_to_record(sol, al, regions=v["regions"], anti_knight=v["anti_knight"])
    if not unique(p) or solves(p, S + ("point", "npair")):
        return None
    ok, steps = L.solve_logic(p["givens"], v, S + ("point", "npair", "xwing"), allowed=allowed_of(p))
    if not ok or not steps or steps[0]["tech"] != "xwing":
        return None
    if len({c for c, _ in steps[0]["elims"]}) < 2:
        return None
    return p


def gen_center(rng, level):
    """Center-mark puzzles:
    - Level 3: minimal 4-given puzzles with 3-4 true 2-candidate center marks pre-printed
      (each printed center mark is the exact pair of digits not yet in that cell's row/col/box).
    - Level 6 (Naked Pair) & Level 7 (X-Wing): every empty cell has 2 or 3 center marks
      printed covering 100% of its possible values (no blank cells, no 4-candidate cells).
    """
    v = G.default_variant()
    if level == 3:
        peers = G.peers_of(v)
        sol = G.random_grid(v, rng)
        p = new_record(sol)
        p["givens"] = list(sol)
        minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
        giv = p["givens"]
        two_cands = {}
        for i in G.CELLS:
            if not giv[i]:
                seen = {giv[q] for q in peers[i] if giv[q]}
                rem = sorted(set(G.DIGITS) - seen)
                if len(rem) == 2:
                    two_cands[i] = rem
        if len(two_cands) < 3:
            return None
        k = min(len(two_cands), rng.randint(3, 4))
        chosen = sorted(rng.sample(list(two_cands.keys()), k))
        p["center_clues"] = {i: two_cands[i] for i in chosen}
        return p
    if level == 6:
        return _gen_clean_npair(rng, v)
    if level == 9:
        return _gen_clean_xwing(rng, v)
    return None


def _gen_clean_pointing(rng, v):
    grids = G.all_grids(v)
    if not grids:
        return None
    sol = list(rng.choice(grids))
    boxes = G.region_units(v["regions"])
    peers = G.peers_of(v)
    if v["anti_knight"]:
        q = new_record(sol, regions=v["regions"])
        q["anti_knight"] = True
        c_giv = rng.choice(G.CELLS)
        d_giv = sol[c_giv]
        q["givens"][c_giv] = d_giv
        b1, b2 = rng.sample(boxes, 2)
        is_row = rng.choice([True, False])
        shared_lines = ([r for r in range(4) if any(G.rc(x)[0] == r for x in b1) and any(G.rc(x)[0] == r for x in b2)]
                        if is_row else
                        [col for col in range(4) if any(G.rc(x)[1] == col for x in b1) and any(G.rc(x)[1] == col for x in b2)])
        if not shared_lines:
            return None
        line_idx = rng.choice(shared_lines)
        line_cells = G.rows()[line_idx] if is_row else G.cols()[line_idx]
        d_cands = [sol[x] for x in b1 if x in line_cells and sol[x] != d_giv]
        if not d_cands:
            return None
        d = rng.choice(d_cands)
        t1 = next(x for x in b1 if sol[x] == d)
        t2 = next(x for x in b2 if sol[x] == d)
        if t2 in line_cells:
            return None
        o1_cands = [x for x in b1 if x in line_cells and x != t1 and sol[x] != d_giv]
        o2_cands = [x for x in b2 if x in line_cells and sol[x] != d_giv]
        if not o1_cands or not o2_cands:
            return None
        o1, o2 = rng.choice(o1_cands), rng.choice(o2_cands)
        q["corner_clues"] = [[d, sorted([t1, o1])], [d, sorted([t2, o2])]]
        for bx in boxes:
            if bx in (b1, b2):
                continue
            for dg in rng.sample([x for x in G.DIGITS if x not in (d, d_giv)], 2):
                tx = next(x for x in bx if sol[x] == dg)
                ox_cands = [x for x in bx if x != tx and sol[x] != d_giv
                            and G.rc(x)[0] != G.rc(tx)[0] and G.rc(x)[1] != G.rc(tx)[1]]
                if ox_cands and rng.random() < 0.8:
                    q["corner_clues"].append([dg, sorted([tx, rng.choice(ox_cands)])])
                    break
        for dg, cells in q["corner_clues"]:
            if any(q["givens"][p] == dg for c in cells for p in peers[c]):
                return None
        if not unique(q) or solves(q, S):
            return None
        ok, steps = L.solve_logic(q["givens"], v, ("hs_box", "hs_line", "point"), allowed=allowed_of(q))
        if ok and any(s["tech"] == "point" and s["elims"] == [(o2, d)] for s in steps):
            return q
        return None

    p = new_record(sol, regions=v["regions"])
    p["anti_knight"] = v["anti_knight"]
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, ("hs_box", "hs_line")))
    given_cells = [i for i in G.CELLS if p["givens"][i]]
    rng.shuffle(given_cells)
    for t2 in given_cells:
        d = sol[t2]
        b2 = next(b for b in boxes if t2 in b)
        for is_row in rng.sample([True, False], 2):
            r_t2, c_t2 = G.rc(t2)
            other_lines = ([r for r in {G.rc(x)[0] for x in b2} if r != r_t2]
                           if is_row else
                           [c for c in {G.rc(x)[1] for x in b2} if c != c_t2])
            for line_idx in other_lines:
                line_cells = G.rows()[line_idx] if is_row else G.cols()[line_idx]
                b1_list = [b for b in boxes if b != b2 and any(x in line_cells for x in b)]
                for b1 in b1_list:
                    t1 = next(x for x in b1 if sol[x] == d)
                    if t1 not in line_cells or p["givens"][t1]:
                        continue
                    o1_cands = [x for x in b1 if x in line_cells and x != t1 and not p["givens"][x]
                                and not any(p["givens"][q] == d for q in peers[x] if q != t2)]
                    o2_cands = [x for x in b2 if x in line_cells and not p["givens"][x]
                                and not any(p["givens"][q] == d for q in peers[x] if q != t2)]
                    if not o1_cands or not o2_cands:
                        continue
                    o1 = rng.choice(o1_cands)
                    o2 = rng.choice(o2_cands)
                    q = new_record(sol, regions=v["regions"])
                    q["anti_knight"] = v["anti_knight"]
                    q["givens"] = list(p["givens"])
                    q["givens"][t2] = 0
                    q["corner_clues"] = [[d, sorted([t1, o1])], [d, sorted([t2, o2])]]
                    # Optionally convert 1 more given of a DIFFERENT digit in another box into a diagonal corner pair
                    other_givs = [g for g in G.CELLS if q["givens"][g] and g not in b1 and g not in b2
                                  and sol[g] != d]
                    if other_givs and rng.random() < 0.65:
                        g_drop = rng.choice(other_givs)
                        dg = sol[g_drop]
                        bg = next(b for b in boxes if g_drop in b)
                        og_cands = [x for x in bg if x != g_drop and not q["givens"][x]
                                    and G.rc(x)[0] != G.rc(g_drop)[0] and G.rc(x)[1] != G.rc(g_drop)[1]
                                    and not any(q["givens"][pr] == dg for pr in peers[x] if pr != g_drop)]
                        if og_cands:
                            q["givens"][g_drop] = 0
                            q["corner_clues"].append([dg, sorted([g_drop, rng.choice(og_cands)])])
                    if any(q["givens"][pr] == dg for dg, cs in q["corner_clues"] for c in cs for pr in peers[c]):
                        continue
                    if not unique(q) or solves(q, S):
                        continue
                    ok, steps = L.solve_logic(q["givens"], v, ("hs_box", "hs_line", "point"),
                                              allowed=allowed_of(q))
                    if not ok or len(steps) < 2:
                        continue
                    pt_steps = [s for s in steps if s["tech"] == "point"]
                    if len(pt_steps) != 1:
                        continue
                    # Ensure Step 0 is the Pointing Pair hitting our printed corner mark (o2, d),
                    # and Step 1 immediately places d in t2 via hs_box!
                    if (steps[0]["tech"] == "point" and steps[0]["elims"] == [(o2, d)]
                            and steps[1]["tech"] == "hs_box" and steps[1]["cell"] == t2 and steps[1]["digit"] == d):
                        return q
    return None


def gen_corner(rng, level):
    """Snyder corner-mark clue puzzles (levels 4, 5)."""
    v = G.default_variant()
    if level == 5:
        return _gen_clean_pointing(rng, v)
    sol = G.random_grid(v, rng)
    boxes = G.region_units(v["regions"])
    peers = G.peers_of(v)
    p = new_record(sol)
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, ("hs_box", "hs_line")))
    # Replace 1-2 givens with diagonal Snyder corner pairs so they are never pointing pairs
    given_cells = [i for i in G.CELLS if p["givens"][i]]
    rng.shuffle(given_cells)
    n_replace = rng.choice([1, 2, 2])
    replaced = 0
    for t in given_cells:
        if replaced >= n_replace:
            break
        d = sol[t]
        b = next(bx for bx in boxes if t in bx)
        diag = [o for o in b if o != t and not p["givens"][o]
                and G.rc(o)[0] != G.rc(t)[0] and G.rc(o)[1] != G.rc(t)[1]
                and not any(p["givens"][q] == d for q in peers[o] if q != t)]
        if not diag:
            continue
        o = rng.choice(diag)
        p["givens"][t] = 0
        p["corner_clues"].append([d, sorted([t, o])])
        replaced += 1

    def grade(q):
        if not q["corner_clues"] or not unique(q):
            return False
        if any(q["givens"][pr] == dg for dg, cs in q["corner_clues"] for c in cs for pr in peers[c]):
            return False
        if unique(dict(q, corner_clues=[])):
            return False
        ok, steps = L.solve_logic(q["givens"], v, ("hs_box", "hs_line"), record=True, allowed=allowed_of(q))
        if not ok:
            return False
        # Every corner clue must resolve because its partner cell got filled
        for dg, cells in q["corner_clues"]:
            resolved_by_fill = False
            for s in steps:
                if s["cell"] in cells and s["digit"] == dg:
                    other = [c for c in cells if c != s["cell"]][0]
                    if s["before"]["values"][other] != 0:
                        resolved_by_fill = True
            if not resolved_by_fill:
                return False
        return True

    if not grade(p):
        return None
    for k in rng.sample(range(len(p["corner_clues"])), len(p["corner_clues"])):
        if k < len(p["corner_clues"]):
            q = dict(p, corner_clues=[c for j, c in enumerate(p["corner_clues"]) if j != k])
            if grade(q):
                p = q
    return p


COLOR_IDS = [0, 1, 2, 3]


def gen_coloring(rng, level):
    v = G.default_variant()
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    digits = rng.sample(G.DIGITS, rng.choice([2, 3, 3]))
    colors = {}
    for k, d in enumerate(digits):
        cells = [i for i in G.CELLS if sol[i] == d]
        for c in rng.sample(cells, rng.choice([2, 3, 3, 4])):
            colors[c] = COLOR_IDS[k]
    p["colors"] = colors
    p["givens"] = [sol[i] if i not in colors else 0 for i in G.CELLS]

    def grade(q):
        if not unique(q) or not solves(q, S + ("color",)):
            return False
        bare = dict(q, colors={})
        return not unique(bare)

    if not grade(p):
        return None
    minimize_givens(p, rng, grade)
    # trim colour groups (keep >= 2 cells each)
    for c in rng.sample(list(p["colors"]), len(p["colors"])):
        col = p["colors"][c]
        if sum(1 for x in p["colors"].values() if x == col) <= 2:
            continue
        q = dict(p, colors={k: x for k, x in p["colors"].items() if k != c})
        if grade(q):
            p = q
    if not any(p["givens"]):
        return None
    # renumber colours 0.. in order of first appearance for consistent palettes
    order = []
    for c in sorted(p["colors"]):
        if p["colors"][c] not in order:
            order.append(p["colors"][c])
    p["colors"] = {c: order.index(x) for c, x in p["colors"].items()}
    return p


def gen_jigsaw(rng, level):
    layout = list(rng.choice(G.jigsaw_layouts()))
    v = G.make_variant(regions=layout)
    sol = G.random_grid(v, rng)
    p = new_record(sol, regions=layout)
    p["givens"] = list(sol)

    def grade(q):
        return unique(q) and solves(q, S)

    minimize_givens(p, rng, grade)
    if unique(dict(p, regions=LATIN_REGIONS)):
        return None  # jigsaw shapes must matter
    return p


def gen_anti_knight(rng, level):
    v = G.make_variant(anti_knight=True)
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    p["anti_knight"] = True
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if unique(dict(p, anti_knight=False)):
        return None  # the knight rule must matter
    return p


def fog_playthrough(p):
    """Simulate a kid solving with singles while the fog lifts.

    The kid only knows givens in clear cells (plus digits already written)
    and may only write into clear cells.  Returns (completed, reveals) where
    `reveals` counts placements that lifted fog off new cells."""
    v = variant_of(p)
    sol, giv = p["solution"], p["givens"]
    lit = set(p["fog_lit"])
    placed = {}
    reveals = 0
    todo = {i for i in G.CELLS if not giv[i]}
    while todo - set(placed):
        known = [giv[i] if (i in lit and giv[i]) else placed.get(i, 0) for i in G.CELLS]
        st = L.State(known, v)
        move = next(((c, d) for c, d in L.single_placements(st)
                     if c in lit and not giv[c] and c not in placed), None)
        if move is None:
            return False, reveals
        cell, d = move
        if sol[cell] != d:
            return False, reveals
        placed[cell] = d
        new = set(G.orth_neighbors(cell)) - lit
        if new:
            reveals += 1
        lit |= new
    return True, reveals


def gen_fog(rng, level):
    v = G.default_variant()
    sol = G.random_grid(v, rng)
    p = new_record(sol)
    p["givens"] = list(sol)
    minimize_givens(p, rng, lambda q: unique(q) and solves(q, S))
    if sum(1 for d in p["givens"] if d) < 5:
        add_back_givens(p, rng, 5)
    # initial light: a random connected blob of 4-6 cells containing >= 2 givens
    for _ in range(40):
        start = rng.choice(G.CELLS)
        blob = {start}
        size = rng.randint(4, 6)
        while len(blob) < size:
            x = rng.choice(sorted(blob))
            blob.add(rng.choice(G.orth_neighbors(x)))
        if sum(1 for c in blob if p["givens"][c]) < 2:
            continue
        p["fog_lit"] = sorted(blob)
        visible = [p["givens"][i] if i in blob else 0 for i in G.CELLS]
        if G.is_unique(visible, v):
            continue  # fog has to matter
        ok, reveals = fog_playthrough(p)
        if ok and reveals >= 2:
            return p
    return None


def gen_center_corner_combo(rng):
    """Puzzle combining BOTH center-mark clues and Snyder corner-mark clues."""
    v = G.default_variant()
    sol = G.random_grid(v, rng)
    boxes = G.region_units(v["regions"])
    peers = G.peers_of(v)
    p = new_record(sol)
    for c in rng.sample(G.CELLS, rng.choice([2, 3])):
        p["givens"][c] = sol[c]
    # Add 1-2 diagonal corner clues in boxes without that digit given
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
        if not q["center_clues"] or not q["corner_clues"]:
            return False
        if not unique(q):
            return False
        if unique(dict(q, center_clues={})) or unique(dict(q, corner_clues=[])):
            return False
        ok, steps = L.solve_logic(q["givens"], v, ("hs_box", "hs_line", "ns"), record=True, allowed=allowed_of(q))
        if not ok:
            return False
        if any(s["tech"] == "ns" and s["cell"] not in q["center_clues"] for s in steps):
            return False
        for d, cells in q["corner_clues"]:
            if not any(s["cell"] in cells and s["digit"] == d
                       and s["before"]["values"][[c for c in cells if c != s["cell"]][0]] != 0
                       for s in steps):
                return False
        return True

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


def gen_variant_with_marks(rng, use_jigsaw=False, use_knight=False, need_tech="point"):
    """Jigsaw or Anti-Knight combined with Pointing Pairs, Naked Pairs, or X-Wing."""
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
    """Grandmaster mashup: Jigsaw shapes AND Anti-Knight rule together."""
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


GENERATORS = {
    1: gen_plain, 2: gen_plain, 3: gen_center, 4: gen_corner, 5: gen_corner,
    6: gen_center, 7: gen_jigsaw, 8: gen_anti_knight, 9: gen_center,
}

# extra givens for the first puzzles of the easy levels (gentle ramp)
GIVEN_RAMP = {1: [9, 8, 8, 7, 7, 7, 6, 6, 6, 0, 0, 0],
              2: [8, 7, 7, 6, 6, 6, 5, 5, 0, 0, 0, 0]}


def difficulty(p):
    """Rough score: less information + more steps of the newest technique = harder."""
    return -info_count(p)


def build_level_10(per_level, seed, existing_sigs=None):
    """Build 60 puzzles of increasing difficulty using all techniques in different ways."""
    rng = random.Random(seed * 1000 + 10)
    seen = set(existing_sigs or ())
    buckets = []

    def collect(fn, count, tier_score, label):
        got = []
        attempts = 0
        while len(got) < count and attempts < count * 3000:
            attempts += 1
            p = fn(rng)
            if p is None:
                continue
            sig = signature(p)
            if sig in seen:
                continue
            seen.add(sig)
            p["_tier"] = tier_score
            p["_label"] = label
            got.append(p)
        return got

    # 1. Warm-up Singles (self-pegging with 6 -> 5 -> 4 givens): 8 puzzles
    def gen_warmup(target_givens):
        def _fn(r):
            p = gen_plain(r, 2)
            if p and target_givens > sum(1 for d in p["givens"] if d):
                add_back_givens(p, r, target_givens)
            return p
        return _fn

    buckets += collect(gen_warmup(6), 2, 10, "Singles Warm-Up")
    buckets += collect(gen_warmup(5), 3, 15, "Singles + Self-Pegging")
    buckets += collect(lambda r: gen_plain(r, 2), 3, 20, "Minimal Singles")

    # 2. Center Marks, Snyder Corner Marks, and Center+Corner Combos: 12 puzzles
    buckets += collect(lambda r: gen_center(r, 3), 4, 25, "Center Marks")
    buckets += collect(lambda r: gen_corner(r, 4), 4, 30, "Snyder Corner Marks")
    buckets += collect(gen_center_corner_combo, 4, 35, "Center + Corner Combo")

    # 3. Jigsaw & Anti-Knight (pure self-pegging): 10 puzzles
    buckets += collect(lambda r: gen_jigsaw(r, 7), 5, 42, "Jigsaw Sudoku")
    buckets += collect(lambda r: gen_anti_knight(r, 8), 5, 48, "Anti-Knight")

    # 4. Pointing Pairs & Naked Pairs (standard + Jigsaw/Knight remixes): 12 puzzles
    buckets += collect(lambda r: gen_corner(r, 5), 4, 55, "Pointing Pairs")
    buckets += collect(lambda r: gen_center(r, 6), 4, 62, "Naked Pair")
    buckets += collect(lambda r: gen_variant_with_marks(r, use_jigsaw=True, need_tech="point"),
                       2, 68, "Jigsaw + Pointing")
    buckets += collect(lambda r: gen_variant_with_marks(r, use_knight=True, need_tech="point"),
                       2, 72, "Anti-Knight + Pointing")

    # 5. Advanced Non-X-Wing Variant Combos & Grandmaster Jigsaw+Knight: 6 puzzles (brings non-X-Wing total to 48)
    buckets += collect(lambda r: gen_variant_with_marks(r, use_jigsaw=True, need_tech="npair"),
                       1, 80, "Jigsaw + Naked Pair")
    buckets += collect(lambda r: gen_variant_with_marks(r, use_knight=True, need_tech="npair"),
                       1, 84, "Anti-Knight + Naked Pair")
    buckets += collect(gen_jigsaw_knight, 4, 88, "Jigsaw + Anti-Knight")

    # 6. Final 12 Optional Boss Puzzles (49..60): ALL require X-Wing!
    buckets += collect(lambda r: gen_center(r, 9), 6, 92, "X-Wing")
    buckets += collect(lambda r: gen_variant_with_marks(r, use_jigsaw=True, need_tech="xwing"),
                       3, 95, "Jigsaw + X-Wing")
    buckets += collect(lambda r: gen_variant_with_marks(r, use_knight=True, need_tech="xwing"),
                       3, 98, "Anti-Knight + X-Wing")

    # Sort strictly by (tier, fewer givens/clues)
    buckets.sort(key=lambda p: (p["_tier"], -sum(1 for d in p["givens"] if d), difficulty(p)))
    picks = buckets[:per_level]
    print(f"  level 10 {LEVEL_BY_NUM[10]['name']:<20} {len(picks):3d} mixed puzzles assembled")
    return picks


def build_level(level, per_level, seed, time_budget=60.0):
    rng = random.Random(seed * 1000 + level)
    gen = GENERATORS[level]
    found = {}
    target = per_level * 4  # oversample, then pick a spread
    t0 = time.time()
    attempts = 0
    while len(found) < target and time.time() - t0 < time_budget:
        attempts += 1
        p = gen(rng, level)
        if p is None:
            continue
        if level == 2 and not starting_pure_naked_single(p):
            continue
        found.setdefault(signature(p), p)
    pool = sorted(found.values(), key=difficulty)
    if len(pool) < per_level:
        raise RuntimeError(f"level {level}: only found {len(pool)} puzzles in {attempts} attempts")
    # even spread from easiest to hardest
    picks = [pool[round(k * (len(pool) - 1) / (per_level - 1))] for k in range(per_level)]
    if level == 4:
        for idx, p in enumerate(picks):
            ok, steps = L.solve_logic(p["givens"], variant_of(p), ("hs_box", "hs_line"),
                                      allowed=allowed_of(p))
            corner_marks = {(c, d) for d, cells in p["corner_clues"] for c in cells}
            if ok and len(steps) >= 2 and (steps[1]["cell"], steps[1]["digit"]) in corner_marks:
                if idx != 0:
                    picks[0], picks[idx] = picks[idx], picks[0]
                break
    if level == 9:
        def _xw_axis(p_rec):
            _, sts = L.solve_logic(p_rec["givens"], variant_of(p_rec), S + ("point", "npair", "xwing"),
                                   allowed=allowed_of(p_rec))
            return next((s["axis"] for s in sts if s["tech"] == "xwing"), None)
        for idx, p in enumerate(picks):
            if _xw_axis(p) == "row":
                if idx != 0:
                    picks[0], picks[idx] = picks[idx], picks[0]
                break
        for idx in range(1, len(picks)):
            if _xw_axis(picks[idx]) == "col":
                if idx != 1:
                    picks[1], picks[idx] = picks[idx], picks[1]
                break
    ramp = GIVEN_RAMP.get(level)
    if ramp:
        for p, tgt in zip(picks, ramp):
            if tgt:
                for _ in range(20):
                    q = json.loads(json.dumps(p))
                    q["colors"] = {}
                    add_back_givens(q, rng, tgt)
                    if level == 1 or starting_pure_naked_single(q):
                        p["givens"] = q["givens"]
                        break
    print(f"  level {level:2d} {LEVEL_BY_NUM[level]['name']:<20} "
          f"{len(found):3d} candidates / {attempts} attempts")
    return picks


def finalize(p, level, number):
    lv = LEVEL_BY_NUM[level]
    v = variant_of(p)
    techs = S + ("color", "point", "npair", "xwing")
    ok, steps = L.solve_logic(p["givens"], v, techs, allowed=allowed_of(p))
    assert ok and unique(p), (level, number)
    p.pop("_tier", None)
    tech_name = p.pop("_label", lv["name"])
    p.update({
        "id": f"{level:02d}-{number:02d}",
        "level": level,
        "number": number,
        "technique": tech_name,
        "tech_counts": L.tech_counts(steps),
    })
    # JSON keys must be strings
    p["center_clues"] = {str(k): v for k, v in sorted(p["center_clues"].items())}
    p["colors"] = {str(k): v for k, v in sorted(p["colors"].items())}
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--per-level", type=int, default=12)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "puzzles", "puzzles.json"))
    args = ap.parse_args()

    print(f"Generating puzzles (seed {args.seed})...")
    puzzles = []
    existing_sigs = set()
    for lv in LEVELS:
        if lv["level"] == 10:
            picks = build_level_10(60, args.seed, existing_sigs=existing_sigs)
        else:
            picks = build_level(lv["level"], args.per_level, args.seed)
            for p in picks:
                existing_sigs.add(signature(p))
        for n, p in enumerate(picks, 1):
            puzzles.append(finalize(p, lv["level"], n))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"seed": args.seed, "levels": LEVELS, "puzzles": puzzles}, f, indent=1)
    print(f"Wrote {len(puzzles)} puzzles -> {os.path.normpath(args.out)}")


if __name__ == "__main__":
    main()
