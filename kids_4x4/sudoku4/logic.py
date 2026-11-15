"""Human-style logical solver used to grade puzzles by technique.

Each technique looks at the current candidate state and returns a single
*step* (a dict describing the deduction) or None.  The solver applies the
simplest available technique, over and over, until the grid is full or it
gets stuck.  Steps are recorded so the renderer can draw lesson diagrams.

Technique ids (in default "simplest first" order):

    hs_box     hidden single inside a box / region
    hs_line    hidden single inside a row or column
    ns         naked single (only one candidate left in a cell)
    color      colour-group logic (same colour = same digit)
    point      pointing pair (box candidates on one line clear that line)
    npair      naked pair
    xwing      X-Wing
"""

from __future__ import annotations

from . import grid as G

ALL_TECHS = ("hs_box", "hs_line", "ns", "color", "point", "npair", "xwing")
SINGLES = ("hs_box", "hs_line", "ns")


class State:
    def __init__(self, puzzle, variant, allowed=None):
        self.v = variant
        self.units = G.units_of(variant)
        self.peers = G.peers_of(variant)
        self.rows = [tuple(u) for u in G.rows()]
        self.cols = [tuple(u) for u in G.cols()]
        self.boxes = [tuple(u) for u in G.region_units(variant["regions"])]
        self.cell_box = {i: b_idx for b_idx, b in enumerate(self.boxes) for i in b}
        self.groups = G.color_groups(variant)
        self.values = [0] * 16
        if isinstance(allowed, dict):
            self.cands = [set(allowed["cands"][i]) for i in G.CELLS]
            self.box_spots = {k: set(v) for k, v in allowed["box_spots"].items()}
        else:
            self.cands = [set(allowed[i]) if allowed is not None else set(G.DIGITS)
                          for i in G.CELLS]
            self.box_spots = {(b_idx, d): set(b)
                              for b_idx, b in enumerate(self.boxes) for d in G.DIGITS}
        for i, d in enumerate(puzzle):
            if d:
                self.place(i, d)

    # -- mutation ----------------------------------------------------------
    def place(self, i, d):
        self.values[i] = d
        self.cands[i] = {d}
        b_i = self.cell_box[i]
        for dg in G.DIGITS:
            self.box_spots[(b_i, dg)].discard(i)
        self.box_spots[(b_i, d)] = {i}
        for p in self.peers[i]:
            self.cands[p].discard(d)
            self.box_spots[(self.cell_box[p], d)].discard(p)
        # a digit claimed by one colour can't belong to a different colour
        col = self.v["colors"].get(i)
        if col is not None:
            for g, cells in self.groups.items():
                if g != col:
                    for c in cells:
                        if not self.values[c]:
                            self.cands[c].discard(d)
                            self.box_spots[(self.cell_box[c], d)].discard(c)

    def eliminate(self, elims):
        for cell, d in elims:
            self.cands[cell].discard(d)
            self.box_spots[(self.cell_box[cell], d)].discard(cell)

    def apply(self, step):
        if step.get("place"):
            for cell, d in step["place"]:
                if not self.values[cell]:
                    self.place(cell, d)
        if step.get("elims"):
            self.eliminate(step["elims"])

    # -- queries -----------------------------------------------------------
    def solved(self):
        return all(self.values)

    def broken(self):
        return any(not self.values[i] and not self.cands[i] for i in G.CELLS)

    def snapshot(self):
        return {"values": list(self.values),
                "cands": [sorted(c) if not self.values[i] else [] for i, c in enumerate(self.cands)]}


# ---------------------------------------------------------------------------
# Techniques
# ---------------------------------------------------------------------------

def _hidden_single(st: State, units, kind):
    for u in units:
        placed = {st.values[i] for i in u if st.values[i]}
        for d in G.DIGITS:
            if d in placed:
                continue
            spots = [i for i in u if not st.values[i] and d in st.cands[i]]
            if len(spots) == 1:
                return {"tech": kind, "place": [(spots[0], d)], "cell": spots[0],
                        "digit": d, "unit": list(u)}
    return None


def t_hs_box(st):
    for b_idx, u in enumerate(st.boxes):
        placed = {st.values[i] for i in u if st.values[i]}
        for d in G.DIGITS:
            if d in placed:
                continue
            spots = [i for i in u if not st.values[i] and d in st.cands[i]
                     and i in st.box_spots[(b_idx, d)]]
            if len(spots) == 1:
                return {"tech": "hs_box", "place": [(spots[0], d)], "cell": spots[0],
                        "digit": d, "unit": list(u)}
    return None


def t_hs_line(st):
    return _hidden_single(st, st.rows + st.cols, "hs_line")


def t_ns(st):
    for i in G.CELLS:
        if not st.values[i] and len(st.cands[i]) == 1:
            d = next(iter(st.cands[i]))
            return {"tech": "ns", "place": [(i, d)], "cell": i, "digit": d}
    return None


def t_color(st):
    """Colour groups: (a) cells of one colour share candidates;
    (b) once a colour's digit is known, every cell of that colour gets it."""
    for g, cells in st.groups.items():
        known = {st.values[c] for c in cells if st.values[c]}
        if known:
            d = next(iter(known))
            todo = [c for c in cells if not st.values[c]]
            if todo:
                return {"tech": "color", "place": [(c, d) for c in todo], "group": cells,
                        "digit": d, "cell": todo[0]}
            continue
        common = set(G.DIGITS)
        for c in cells:
            common &= st.cands[c]
        elims = [(c, d) for c in cells for d in st.cands[c] if d not in common]
        if elims:
            return {"tech": "color", "elims": elims, "group": cells}
    return None


def t_point(st):
    lines = st.rows + st.cols
    for b_idx, b in enumerate(st.boxes):
        for d in G.DIGITS:
            if any(st.values[i] == d for i in b):
                continue
            spots = [i for i in b if not st.values[i] and d in st.cands[i]
                     and i in st.box_spots[(b_idx, d)]]
            if len(spots) < 2:
                continue
            for line in lines:
                if all(s in line for s in spots):
                    elims = [(i, d) for i in line
                             if i not in b and not st.values[i]
                             and d in st.cands[i] and i in st.box_spots[(st.cell_box[i], d)]]
                    if elims:
                        return {"tech": "point", "elims": elims, "digit": d,
                                "pattern": spots, "unit": list(b), "line": list(line)}
    return None


def t_npair(st):
    for u in st.units:
        open_cells = [i for i in u if not st.values[i] and len(st.cands[i]) == 2]
        for a in range(len(open_cells)):
            for b in range(a + 1, len(open_cells)):
                x, y = open_cells[a], open_cells[b]
                if st.cands[x] == st.cands[y]:
                    pair = st.cands[x]
                    elims = [(i, d) for i in u if i not in (x, y) and not st.values[i]
                             for d in pair if d in st.cands[i]]
                    if elims:
                        return {"tech": "npair", "elims": elims, "pattern": [x, y],
                                "digits": sorted(pair), "unit": list(u)}
    return None


def t_xwing(st):
    for d in G.DIGITS:
        for base, cover, axis in ((st.rows, st.cols, "row"), (st.cols, st.rows, "col")):
            spots = []
            for line in base:
                if any(st.values[i] == d for i in line):
                    spots.append(None)
                    continue
                s = [k for k, i in enumerate(line) if not st.values[i] and d in st.cands[i]]
                spots.append(s if len(s) == 2 else None)
            for a in range(4):
                for b in range(a + 1, 4):
                    if spots[a] and spots[a] == spots[b]:
                        k1, k2 = spots[a]
                        corners = [base[a][k1], base[a][k2], base[b][k1], base[b][k2]]
                        elims = []
                        for k in (k1, k2):
                            for i in cover[k]:
                                if i not in corners and not st.values[i] and d in st.cands[i]:
                                    elims.append((i, d))
                        if elims:
                            return {"tech": "xwing", "elims": elims, "digit": d,
                                    "pattern": corners, "axis": axis}
    return None


def single_placements(st):
    """Every (cell, digit) placement available right now via any single."""
    out = []
    for u in st.units:
        placed = {st.values[i] for i in u if st.values[i]}
        for d in G.DIGITS:
            if d in placed:
                continue
            spots = [i for i in u if not st.values[i] and d in st.cands[i]]
            if len(spots) == 1:
                out.append((spots[0], d))
    for i in G.CELLS:
        if not st.values[i] and len(st.cands[i]) == 1:
            out.append((i, next(iter(st.cands[i]))))
    return out


TECH_FUNCS = {
    "hs_box": t_hs_box,
    "hs_line": t_hs_line,
    "ns": t_ns,
    "color": t_color,
    "point": t_point,
    "npair": t_npair,
    "xwing": t_xwing,
}


def solve_logic(puzzle, variant, techs=ALL_TECHS, record=False, allowed=None):
    """Solve using only `techs` (tried in the given order).

    Returns (solved: bool, steps: list).  Each step carries a 'tech' key; when
    `record` is True each step also gets a 'before' snapshot for diagrams.
    """
    st = State(puzzle, variant, allowed)
    steps = []
    guard = 0
    while not st.solved():
        guard += 1
        if guard > 200 or st.broken():
            return False, steps
        step = None
        for t in techs:
            step = TECH_FUNCS[t](st)
            if step:
                break
        if not step:
            return False, steps
        if record:
            step["before"] = st.snapshot()
        steps.append(step)
        st.apply(step)
    return True, steps


def tech_counts(steps):
    out = {}
    for s in steps:
        out[s["tech"]] = out.get(s["tech"], 0) + 1
    return out
