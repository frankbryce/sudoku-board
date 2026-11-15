"""Kid-facing lesson text for each level (plain ASCII so the built-in PDF fonts work)."""

LESSONS = {
    1: {
        "what": "Pick one row, column or box. Find a number it still needs. Check every empty "
                "cell in that row, column or box: if that number is blocked everywhere except "
                "ONE cell, it has to go there.",
        "board": "Slide a finger along the row (or around the box). Put a main piece in the only "
                 "open spot. Tip: hunt one number at a time - all the 1s, then all the 2s...",
        "dad": "Ask \"Where can the 3 go in this box?\" instead of \"What goes here?\". That is "
               "the whole trick of a hidden single.",
    },
    2: {
        "what": "Pick one empty cell. Look at its row, its column AND its box. If those already "
                "use three different numbers, the cell gets the last one.",
        "board": "Point at the cell, then count the numbers you can see in its row, column and "
                 "box. Missing just one? Place that main piece!",
        "dad": "Hidden single = 'where does this NUMBER go?'. Naked single = 'what goes in this "
               "CELL?'. Take turns asking each question.",
    },
    3: {
        "what": "What if a cell's row, column and box only use 2 different numbers so far (say "
                "2 and 4)? You can't place a big main piece yet, because 2 numbers are still "
                "possible (1 and 3). Instead, put small CENTER MARKS in the middle of that cell "
                "to remember 'this cell can only be 1 or 3'. (To get you started, some cells "
                "on these pages already have their 2 center marks printed for you!)",
        "board": "Put center pegs into a cell for the numbers not yet in its "
                 "row, column and box. Later, when you place a main piece in the same row, column "
                 "or box that matches one of those center pegs, pull that peg out! Only ONE center "
                 "peg left? Swap it for that main piece!",
        "dad": "Point at a cell with two center marks and ask: \"First, why can this cell "
               "only be 1 or 3? Because 2 and 4 are already in its row, column or box! Now, once "
               "we place a 3 in its column, which center peg is left?\"",
    },
    4: {
        "what": "Snyder notation uses CORNER marks, and only inside one box. A corner mark says: "
                "\"in THIS box, this number must be in one of these marked cells.\" Usually there "
                "are just two.",
        "board": "Corner pegs go in the corner holes of a cell. When one of the two cells fills up, the "
                 "number goes in the other one.",
        "dad": "Corner marks belong to a BOX. Center marks belong to a CELL. Kid can run "
               "the corner pegs while Dad runs the center pegs!",
    },
    5: {
        "what": "If the corner marks for a number in a box all sit in ONE row (or column), "
                "that number has to land on that line inside this box. So it can't be anywhere "
                "else on that line, even in the next box over.",
        "board": "Lay a region bar or pencil along the line of corner pegs, like a laser beam. "
                 "Pull out any matching pegs it hits outside the box, and cross off that number.",
        "dad": "Name it out loud: \"The 2s in this box point down column 4, so column 4 has no other 2.\"",
    },
    6: {
        "what": "Two cells in the same row, column or box with the SAME two center marks "
                "(like 1-3 and 1-3) share those two numbers between them. We don't know which "
                "cell gets which, but nobody else in that row, column or box can use them.",
        "board": "On these pages, every cell shows all of its possible numbers as center marks. "
                 "Find two cells in a row, column or box with the exact same two center pegs, "
                 "then pull those numbers' pegs out of every other cell in that shared row, column or box.",
        "dad": "It's a buddy system: two friends sitting in two seats. Anyone else asking for "
               "those seats gets turned away.",
    },
    7: {
        "what": "Jigsaw sudoku swaps the square boxes for wobbly shapes. Every row, every column "
                "and every thick-outlined shape still needs 1, 2, 3 and 4 exactly once.",
        "board": "Pull out the box bars and rebuild the shapes with short (1x) region bars before "
                 "you start. Hidden singles inside the funny shapes are the key.",
        "dad": "Before solving, have Kid trace each shape with a finger and count its 4 cells.",
    },
    8: {
        "what": "Normal sudoku rules, plus: the same number can never be a chess knight's jump "
                "apart. A knight jumps 2 cells one way and 1 cell sideways, like an L.",
        "board": "Put a peg on a placed number, then tap every L-jump away from it. None of those "
                 "cells can be that number.",
        "dad": "Fun fact: Anti-KING (no matching numbers touching, even on a corner) is "
               "IMPOSSIBLE on a 4x4! Try making one together and see why. (Each box already "
               "fills all its touching spots...)",
    },
    9: {
        "what": "Optional boss move! Pick one number. It works two ways - by ROWS or by COLUMNS: "
                "(1) If in TWO ROWS that number fits in only two cells each, and they line up in the "
                "SAME TWO COLUMNS, cross that number off the rest of both columns! "
                "(2) Or flip it: if in TWO COLUMNS that number fits in only two cells each, and they "
                "line up in the SAME TWO ROWS, cross that number off the rest of both rows!",
        "board": "On these pages, every cell shows all of its possible numbers as center marks. "
                 "Look for four matching center marks forming the corners of a rectangle (an X). "
                 "If the two rows only have that number on the X corners, zap the columns; if the "
                 "two columns only have that number on the X corners, zap the rows!",
        "dad": "Trace the X with two fingers. One answer sits on each diagonal of the X, which "
               "locks both lines at once!",
    },
    10: {
        "what": "You've learned every technique in the book! This final challenge has 60 puzzles "
                "that get trickier as you go, mixing Hidden Singles, Naked Singles, Center Marks, "
                "Snyder Corner Marks, Pointing Pairs, Naked Pairs, Jigsaw shapes and Anti-Knight. "
                "The final 12 puzzles at the very end require an X-Wing and are marked with a "
                "special warning symbol!",
        "board": "Use your own pencil-mark pegs to help! Even when a puzzle has no small marks "
                 "printed on the page, you can put in your OWN corner pegs (when a number fits in "
                 "only 2 spots of a box) and your OWN center pegs (when a cell is down to 2 or 3 "
                 "numbers). Your pegs make pairs, pointing lines and singles jump right out!",
        "dad": "Let Kid decide when to reach for the peg tray! Puzzles 1-48 never need an X-Wing, "
               "and the last 12 puzzles (49-60) are clearly badged if you want to tackle the optional "
               "X-Wing boss round together.",
    },
}

LESSONS_COLORS = {
    1: {
        "what": "Pick one row, column or box. Find a color it still needs. Check every empty "
                "cell in that row, column or box: if that color is blocked everywhere except "
                "ONE cell, it has to go there.",
        "board": "Slide a finger along the row (or around the box). Put a main piece in the only "
                 "open spot. Tip: hunt one color at a time - all the Blues, then all the Reds...",
        "dad": "Ask \"Where can the Green piece go in this box?\" instead of \"What goes here?\". "
               "That is the whole trick of a hidden single.",
    },
    2: {
        "what": "Pick one empty cell. Look at its row, its column AND its box. If those already "
                "use three different colors, the cell gets the last one.",
        "board": "Point at the cell, then check the colors you can see in its row, column and "
                 "box. Missing just one? Place that main piece!",
        "dad": "Hidden single = 'where does this COLOR go?'. Naked single = 'what goes in this "
               "CELL?'. Take turns asking each question.",
    },
    3: {
        "what": "What if a cell's row, column and box only use 2 different colors so far (say "
                "Red and Green)? You can't place a big main piece yet, because 2 colors are still "
                "possible (Blue and Tan). Instead, put small CENTER MARKS in the middle of that "
                "cell to remember 'this cell can only be Blue or Tan'. (To get you started, "
                "some cells on these pages already have their 2 center dots printed for you!)",
        "board": "Put center pegs into a cell for the colors not yet in its "
                 "row, column and box. Later, when you place a main piece in the same row, column "
                 "or box that matches one of those center pegs, pull that peg out! Only ONE center "
                 "peg left? Swap it for that main piece!",
        "dad": "Point at a cell with two center pegs and ask: \"First, why can this cell "
               "only be Blue or Tan? Because Red and Green are already in its row, column or box! "
               "Now, once we place Tan in its column, which center peg is left?\"",
    },
    4: {
        "what": "Snyder notation uses CORNER marks, and only inside one box. A corner mark says: "
                "\"in THIS box, this color must be in one of these marked cells.\" Usually there "
                "are just two.",
        "board": "Corner pegs go in the corner holes of a cell. When one of the two cells fills up, that "
                 "color goes in the other one.",
        "dad": "Corner marks belong to a BOX. Center marks belong to a CELL. Kid can run "
               "the corner pegs while Dad runs the center pegs!",
    },
    5: {
        "what": "If the corner marks for a color in a box all sit in ONE row (or column), "
                "that color has to land on that line inside this box. So it can't be anywhere "
                "else on that line, even in the next box over.",
        "board": "Lay a region bar or pencil along the line of corner pegs, like a laser beam. "
                 "Pull out any matching pegs it hits outside the box, and cross off that color.",
        "dad": "Name it out loud: \"The Reds in this box point down column 4, so column 4 has no other Red.\"",
    },
    6: {
        "what": "Two cells in the same row, column or box with the SAME two center marks "
                "(like Blue + Tan and Blue + Tan) share those two colors between them. We don't know "
                "which cell gets which, but nobody else in that row, column or box can use them.",
        "board": "On these pages, every cell shows all of its possible colors as center dots. "
                 "Find two cells in a row, column or box with the exact same two center pegs, "
                 "then pull those colors' pegs out of every other cell in that shared row, column or box.",
        "dad": "It's a buddy system: two friends sitting in two seats. Anyone else asking for "
               "those seats gets turned away.",
    },
    7: {
        "what": "Jigsaw sudoku swaps the square boxes for wobbly shapes. Every row, every column "
                "and every thick-outlined shape still needs all 4 colors (Blue, Red, Tan and Green) "
                "exactly once.",
        "board": "Pull out the box bars and rebuild the shapes with short (1x) region bars before "
                 "you start. Hidden singles inside the funny shapes are the key.",
        "dad": "Before solving, have Kid trace each shape with a finger and count its 4 cells.",
    },
    8: {
        "what": "Normal sudoku rules, plus: the same color can never be a chess knight's jump "
                "apart. A knight jumps 2 cells one way and 1 cell sideways, like an L.",
        "board": "Put a finger on a placed piece, then tap every L-jump away from it. None of those "
                 "cells can be that color.",
        "dad": "Fun fact: Anti-KING (no matching colors touching, even on a corner) is "
               "IMPOSSIBLE on a 4x4! Try making one together and see why. (Each box already "
               "fills all its touching spots...)",
    },
    9: {
        "what": "Optional boss move! Pick one color. It works two ways - by ROWS or by COLUMNS: "
                "(1) If in TWO ROWS that color fits in only two cells each, and they line up in the "
                "SAME TWO COLUMNS, cross that color off the rest of both columns! "
                "(2) Or flip it: if in TWO COLUMNS that color fits in only two cells each, and they "
                "line up in the SAME TWO ROWS, cross that color off the rest of both rows!",
        "board": "On these pages, every cell shows all of its possible colors as center dots. "
                 "Look for four matching center pegs forming the corners of a rectangle (an X). "
                 "If the two rows only have that color on the X corners, zap the columns; if the "
                 "two columns only have that color on the X corners, zap the rows!",
        "dad": "Trace the X with two fingers. One answer sits on each diagonal of the X, which "
               "locks both lines at once!",
    },
    10: {
        "what": "You've learned every technique in the book! This final challenge has 60 puzzles "
                "that get trickier as you go, mixing Hidden Singles, Naked Singles, Center Marks, "
                "Snyder Corner Marks, Pointing Pairs, Naked Pairs, Jigsaw shapes and Anti-Knight. "
                "The final 12 puzzles at the very end require an X-Wing and are marked with a "
                "special warning symbol!",
        "board": "Use your own pencil-mark pegs to help! Even when a puzzle has no small dots "
                 "printed on the page, you can put in your OWN corner pegs (when a color fits in "
                 "only 2 spots of a box) and your OWN center pegs (when a cell is down to 2 or 3 "
                 "colors). Your pegs make pairs, pointing lines and singles jump right out!",
        "dad": "Let Kid decide when to reach for the peg tray! Puzzles 1-48 never need an X-Wing, "
               "and the last 12 puzzles (49-60) are clearly badged if you want to tackle the optional "
               "X-Wing boss round together.",
    },
}


