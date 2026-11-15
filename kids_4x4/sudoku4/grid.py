"""4x4 Sudoku geometry, variant rules, and a brute-force uniqueness solver.

Cells are numbered 0..15 in reading order:  r = i // 4,  c = i % 4.
Digits are 1..4.  A puzzle is a 16-item list where 0 = empty.

A *variant* is a small dict describing the rules for one puzzle:

    {
      "regions":     [16 region ids]   # which "box" each cell belongs to
      "anti_king":   bool              # no repeat digit a king's step apart
      "anti_knight": bool              # no repeat digit a knight's jump apart
      "colors":      {cell: color_id}  # same colour = same digit,
                                       # different colour = different digit
    }
"""

from __future__ import annotations

from functools import lru_cache
import random

N = 4
CELLS = list(range(N * N))
DIGITS = (1, 2, 3, 4)

STANDARD_REGIONS = [0, 0, 1, 1,
                    0, 0, 1, 1,
                    2, 2, 3, 3,
                    2, 2, 3, 3]


def rc(i: int) -> tuple[int, int]:
    return divmod(i, N)


def idx(r: int, c: int) -> int:
    return r * N + c


def default_variant() -> dict:
    return {"regions": list(STANDARD_REGIONS), "anti_king": False,
            "anti_knight": False, "colors": {}}


def make_variant(regions=None, anti_king=False, anti_knight=False, colors=None) -> dict:
    v = default_variant()
    if regions is not None:
        v["regions"] = list(regions)
    v["anti_king"] = bool(anti_king)
    v["anti_knight"] = bool(anti_knight)
    v["colors"] = {int(k): int(c) for k, c in (colors or {}).items()}
    return v


# ---------------------------------------------------------------------------
# Units & peers
# ---------------------------------------------------------------------------

def rows() -> list[list[int]]:
    return [[idx(r, c) for c in range(N)] for r in range(N)]


def cols() -> list[list[int]]:
    return [[idx(r, c) for r in range(N)] for c in range(N)]


def region_units(regions) -> list[list[int]]:
    ids = sorted(set(regions))
    return [[i for i in CELLS if regions[i] == g] for g in ids]


def king_neighbors(i: int) -> list[int]:
    r, c = rc(i)
    out = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                out.append(idx(rr, cc))
    return out


def knight_neighbors(i: int) -> list[int]:
    r, c = rc(i)
    out = []
    for dr, dc in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            out.append(idx(rr, cc))
    return out


def orth_neighbors(i: int) -> list[int]:
    r, c = rc(i)
    out = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            out.append(idx(rr, cc))
    return out


def _variant_key(v: dict):
    return (tuple(v["regions"]), v["anti_king"], v["anti_knight"])


@lru_cache(maxsize=None)
def _geometry(key):
    regions, anti_king, anti_knight = key
    units = rows() + cols() + region_units(regions)
    peers = []
    for i in CELLS:
        p = set()
        for u in units:
            if i in u:
                p.update(u)
        if anti_king:
            p.update(king_neighbors(i))
        if anti_knight:
            p.update(knight_neighbors(i))
        p.discard(i)
        peers.append(frozenset(p))
    return [tuple(u) for u in units], tuple(peers)


def units_of(v: dict):
    return _geometry(_variant_key(v))[0]


def peers_of(v: dict):
    return _geometry(_variant_key(v))[1]


def color_groups(v: dict) -> dict[int, list[int]]:
    groups: dict[int, list[int]] = {}
    for cell, col in v.get("colors", {}).items():
        groups.setdefault(col, []).append(cell)
    return {k: sorted(g) for k, g in groups.items()}


# ---------------------------------------------------------------------------
# Brute force solver (used for uniqueness checks and full-grid enumeration)
# ---------------------------------------------------------------------------

def solve_all(puzzle, v: dict, limit: int = 2, allowed=None) -> list[list[int]]:
    """Return up to `limit` solutions of `puzzle` under variant `v`.

    `allowed` is an optional list of 16 sets restricting each cell (pencil-mark
    clues); None means every digit is allowed."""
    peers = peers_of(v)
    colors = v.get("colors", {})
    if isinstance(allowed, dict):
        boxes = region_units(v["regions"])
        cell_box = {i: b_idx for b_idx, b in enumerate(boxes) for i in b}
        allowed = [
            {d for d in allowed["cands"][i] if i in allowed["box_spots"][(cell_box[i], d)]}
            for i in CELLS
        ]
    grid = list(puzzle)
    sols: list[list[int]] = []

    def ok(i, d):
        if allowed is not None and d not in allowed[i]:
            return False
        for p in peers[i]:
            if grid[p] == d:
                return False
        ci = colors.get(i)
        if ci is not None:
            for cell, col in colors.items():
                if grid[cell] == 0 or cell == i:
                    continue
                if col == ci and grid[cell] != d:
                    return False
                if col != ci and grid[cell] == d:
                    return False
        return True

    # validate the givens first
    for i in CELLS:
        if grid[i]:
            d = grid[i]
            grid[i] = 0
            good = ok(i, d)
            grid[i] = d
            if not good:
                return []

    def rec():
        if len(sols) >= limit:
            return
        best, best_opts = -1, None
        for i in CELLS:
            if grid[i] == 0:
                opts = [d for d in DIGITS if ok(i, d)]
                if not opts:
                    return
                if best_opts is None or len(opts) < len(best_opts):
                    best, best_opts = i, opts
                    if len(opts) == 1:
                        break
        if best < 0:
            sols.append(list(grid))
            return
        for d in best_opts:
            grid[best] = d
            rec()
            grid[best] = 0
            if len(sols) >= limit:
                return

    rec()
    return sols


def count_solutions(puzzle, v: dict, limit: int = 2, allowed=None) -> int:
    return len(solve_all(puzzle, v, limit, allowed))


def is_unique(puzzle, v: dict, allowed=None) -> bool:
    return count_solutions(puzzle, v, 2, allowed) == 1


@lru_cache(maxsize=None)
def _all_grids(key):
    v = {"regions": list(key[0]), "anti_king": key[1], "anti_knight": key[2], "colors": {}}
    return tuple(tuple(g) for g in solve_all([0] * 16, v, limit=10_000))


def all_grids(v: dict) -> list[tuple[int, ...]]:
    """Every completed grid valid for the variant's geometry (ignores colours)."""
    return list(_all_grids(_variant_key(v)))


def random_grid(v: dict, rng: random.Random) -> list[int]:
    grids = all_grids(v)
    if not grids:
        raise ValueError("variant has no solutions")
    return list(rng.choice(grids))


# ---------------------------------------------------------------------------
# Jigsaw region layouts
# ---------------------------------------------------------------------------

def _connected(cells: list[int]) -> bool:
    s = set(cells)
    seen = {cells[0]}
    stack = [cells[0]]
    while stack:
        x = stack.pop()
        for y in orth_neighbors(x):
            if y in s and y not in seen:
                seen.add(y)
                stack.append(y)
    return len(seen) == len(s)


@lru_cache(maxsize=None)
def jigsaw_layouts() -> tuple[tuple[int, ...], ...]:
    """All partitions of the 4x4 grid into 4 connected 4-cell regions that
    (a) are not plain rows / columns / standard boxes and
    (b) admit at least one valid completed grid."""
    results = set()

    def rec(assign, region_id):
        if region_id == 4:
            results.add(tuple(assign))
            return
        start = assign.index(-1)
        # grow connected 4-cell shapes containing `start`
        shapes = set()

        def grow(shape):
            if len(shape) == 4:
                shapes.add(tuple(sorted(shape)))
                return
            for x in list(shape):
                for y in orth_neighbors(x):
                    if assign[y] == -1 and y not in shape:
                        grow(shape | {y})

        grow(frozenset([start]))
        for shp in shapes:
            for x in shp:
                assign[x] = region_id
            rec(assign, region_id + 1)
            for x in shp:
                assign[x] = -1

    rec([-1] * 16, 0)
    row_layout = tuple(r for r in range(4) for _ in range(4))
    col_layout = tuple(c for _ in range(4) for c in range(4))
    bad = {tuple(STANDARD_REGIONS), row_layout, col_layout}
    good = []
    for lay in sorted(results):
        if lay in bad:
            continue
        # regions equal to a row or column add nothing visually interesting but are legal;
        # we skip layouts where any region is a straight line (too easy / looks like a row)
        units = region_units(lay)
        if any(len({rc(i)[0] for i in u}) == 1 or len({rc(i)[1] for i in u}) == 1 for u in units):
            continue
        v = make_variant(regions=lay)
        if all_grids(v):
            good.append(lay)
    return tuple(good)
