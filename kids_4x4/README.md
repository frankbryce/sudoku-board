# 4x4 Kids' Sudoku: Puzzles, Printable Workbook & Board Build Guide

A self-contained add-on for the modular sudoku board in this repo, set up as a **4x4** board for kids.

* **`sudoku4/`**: pure-Python (stdlib only) puzzle generator, technique grader and PDF renderer
* **`puzzles/puzzles.json`**: the generated set: **10 levels (9 × 12 + 60 = 168 puzzles)**
* **`output/workbook.pdf`** & **`output/answers.pdf`**: standard numbered workbook (`1–4`) + answer key
* **`output/workbook_colors.pdf`** & **`output/answers_colors.pdf`**: standard color-piece workbook using the 4 marker colors (**Blue**, **Red**, **Tan**, **Green**) + answer key
* **`output/workbook_visual.pdf`** & **`output/answers_visual.pdf`**: **Visual Edition** (3-panel visual storyboards, close-up action diagrams, visual peg-hole map, and symbol-only puzzles with zero puzzle numbers) in numbered mode
* **`output/workbook_visual_colors.pdf`** & **`output/answers_visual_colors.pdf`**: **Visual Edition** using the 4 marker colors
* **`output/workbook_toddler.pdf`** & **`output/answers_toddler.pdf`**: **Dad & Me Edition** (wordless 3-step picture sequence + "Touch all 4" finger bar for kids, plus a "FOR DAD" 3-step pointing & play script, and symbol-only puzzles) in numbered mode
* **`output/workbook_toddler_colors.pdf`** & **`output/answers_toddler_colors.pdf`**: **Dad & Me Edition** using the 4 marker colors
* **`build/BUILD_INSTRUCTIONS.md`**: LEGO-style step-by-step assembly with OpenSCAD renders

```bash
make pdf             # render workbook.pdf + answers.pdf (+ color editions) from puzzles.json
make puzzles         # regenerate puzzles (make puzzles SEED=7 PER=12)
make instructions    # re-render build-step pictures (needs openscad)
```

No `pip install` needed: Python 3.9+ and (optional) OpenSCAD only.

## The progression

Levels 1–9 each add **one** new technique, and **Level 10 (All-Star Challenge)** mixes all of them across 60 puzzles of increasing difficulty while encouraging kids to place their own center and corner pegs in empty cells to help solve.

| Level | Technique | Puzzles | How the puzzles are graded |
|---:|---|---:|---|
| 1 | Hidden Single | 12 | Solvable with hidden singles only. Clues ramp from 9 down to minimal. |
| 2 | Naked Single | 12 | Solvable with naked singles only. Every opening position has a naked single that is *not* also a hidden single. |
| 3 | Center Marks | 12 | Minimal 4-given puzzles with 3–4 true 2-candidate center marks pre-printed (matching the two digits/colors not yet in that cell's row, column and box). |
| 4 | Snyder Notation | 12 | Corner-mark clues ("in this box, N is in one of these cells") are needed for a unique answer. Solvable with hidden singles. |
| 5 | Pointing Pairs | 12 | Corner-mark clues. Hidden singles get **stuck**; one pointing pair zaps a corner mark in the neighboring box and un-sticks them. |
| 6 | Naked Pair | 12 | Complete 2–3 candidate center-mark clues in every cell. Singles + pointing get stuck; a naked pair is **required** at Step 1. |
| 7 | Jigsaw Sudoku | 12 | Irregular regions (one of 24 valid 4x4 layouts). The shapes are needed for a unique answer. |
| 8 | Anti-Knight Sudoku | 12 | No repeat a knight's move apart. The knight rule is needed for a unique answer. |
| 9 | X-Wing (Optional) | 12 | Complete 2–3 candidate center-mark clues in every cell. Singles + pointing + naked pairs get stuck; an X-Wing (in rows or columns) is **required** at Step 1. |
| 10 | All-Star Challenge | 60 | 60 puzzles of increasing difficulty mixing all techniques. Puzzles 1–48 use Techniques 1–8; the final 12 puzzles (49–60) require an **X-Wing** and are clearly marked with an extra warning symbol. |

### Why levels 3–7 use pencil-mark clues

I sampled 20,000+ plain 4x4 puzzles. **Every** one can be solved with hidden singles alone, and
also with naked singles alone. So in plain 4x4, pointing pairs, naked pairs and X-Wings are never
needed. To make each technique matter, levels 3–7 print **pencil marks as clues**. Each
clue is a physical peg on the board:

* small number in a **circle** near the middle = **center mark** ("this cell is one of these")
* small number in a **square** out in a corner = **corner mark / Snyder** ("in this box, this
  number is in one of the marked cells")

The grader proves the target technique is needed: the puzzle can't be finished without it, and
can be finished with it.

**Peg positions are fixed per digit** on both the board and the printout:
1 = top-left, 2 = top-right, 3 = bottom-left, 4 = bottom-right.

### Why there's no Anti-King level

Anti-King can't be done on 4x4. Every 2x2 box already uses all four digits, and with no
repeats touching diagonally, row 3 runs out of options. The Anti-Knight lesson page turns this
into a "try it and see why" challenge.

## Printing

Print `output/workbook.pdf` at **100% / Actual size** on US Letter. Color is best (Coloring
level, lesson highlights). Each colored square also has a shape symbol (circle, square,
triangle, diamond), so it still works in black and white. The answer key also shows Dad which
clues sit under the fog in Level 11.

Render a subset: `PYTHONPATH=. python3 -m sudoku4.render --levels 5 6 7 --no-lessons --no-cover`

## Code map

| File | Purpose |
|---|---|
| `sudoku4/grid.py` | Geometry, variant rules (regions / anti-knight / colors), brute-force uniqueness solver, jigsaw layout enumeration |
| `sudoku4/logic.py` | Human-style solver: `hs_box`, `hs_line`, `ns`, `color`, `point`, `npair`, `xwing`, with step logs |
| `sudoku4/generate.py` | Level catalogue + per-level generators and grading rules |
| `sudoku4/lessons.py` | Kid-facing lesson text |
| `sudoku4/render.py` | Workbook / answer-key layout, top-down board drawing |
| `sudoku4/pdf.py` | Tiny dependency-free PDF writer |
| `build/build_steps_4x4.scad` | Build-step scenes (includes `../src/color_sudoku_board.scad`) |

