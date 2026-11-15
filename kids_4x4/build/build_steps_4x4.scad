// ============================================================================
// 4x4 Kids Board — LEGO-style build-step renders (Flush Outer Perimeter Edition)
// Re-uses every part from ../../src/color_sudoku_board.scad
//
//   openscad -o step_03.png -D 'step=3' --camera=... build_steps_4x4.scad
//   (see ../Makefile target `instructions`)
//
// Coordinate convention (same as the main file): ix = column 0..3 (left->right),
// iy = row 0..3 (bottom->top), so the TOP-LEFT tile is (0, 3).
// ============================================================================

include <../../src/color_sudoku_board.scad>

// Silence the main file's own top-level dispatcher.
render_mode = "none";

/* [Build Step] */
// 0 = parts list, 1..10 = assembly steps, 99 = finished board
step = 1;

// Height new parts float above their final spot (LEGO "drop it in" look)
lift = 60;

NEW_COLOR  = "#FF9F1C";   // parts added in THIS step
DONE_COLOR = "#ECECE8";   // parts from earlier steps
BAR_COLOR  = "#26313A";
ARROW_COLOR = "#2A9D8F";

piece_colors = ["#E63946", "#3A86FF", "#2BA84A", "#F4A261"]; // digits 1..4

peg_floor_z_ = base_thickness - peg_socket_depth;

// Sample puzzle shown in steps 8-9 (puzzle 1.01 layout, row 0 = top)
sample = [
    [4, 1, 2, 0],
    [2, 0, 4, 0],
    [0, 4, 3, 0],
    [3, 0, 1, 0]
];

// ---------------------------------------------------------------------------
// Tile order: top-left corner, rest of top row, rest of left col, then rows 2..4
// ---------------------------------------------------------------------------
// step in which tile (ix, iy) is added
function tile_step(ix, iy) =
    (ix == 0 && iy == 3) ? 1 :
    (iy == 3)            ? 2 :
    (ix == 0)            ? 3 :
    (iy == 2)            ? 4 :
    (iy == 1)            ? 5 : 6;

module tile_at(ix, iy) {
    render(convexity = 4)
        board_grid_tile(ix, iy, 4, 4);
}

module down_arrow(h = 22) {
    color(ARROW_COLOR) {
        translate([0, 0, 6]) cylinder(d = 2.4, h = h - 6, $fn = 16);
        cylinder(d1 = 0.1, d2 = 7, h = 7, $fn = 24);
    }
}

// Draw a part either settled (done), or floating with an arrow (new).
// `at` = [x, y] where the arrow should point (the part's final centre).
module staged(s_added, z_final = 0, arrow = true, at = [0, 0]) {
    if (step >= 99 || s_added < step) {
        children();
    } else if (s_added == step) {
        translate([0, 0, lift]) color(NEW_COLOR) children();
        if (arrow) translate([at[0], at[1], z_final + 3]) down_arrow(lift - 14);
    }
}

// ---------------------------------------------------------------------------
// Interior region bars: 4 long bars (2x) through the middle (step 7)
// (No outer border bars needed — the outer edge tiles have solid raised walls!)
// ---------------------------------------------------------------------------
// [x, y, rotation, step]
inner_bars = [
    [1.0, 2, 0, 7], [3.0, 2, 0, 7], [2, 1.0, 90, 7], [2, 3.0, 90, 7]
];

module bar_set(list) {
    for (b = list) {
        tile_center_x = b[0] * cell_pitch;
        tile_center_y = b[1] * cell_pitch;
        staged(b[3], total_plate_h, at = [tile_center_x, tile_center_y])
            translate([tile_center_x, tile_center_y, slot_floor_z])
                rotate([0, 0, b[2]])
                    color(step == b[3] ? NEW_COLOR : BAR_COLOR) region_bar(2, BAR_COLOR);
    }
}

// ---------------------------------------------------------------------------
// Steps
// ---------------------------------------------------------------------------
module board_steps() {
    // tiles
    for (ix = [0 : 3], iy = [0 : 3]) {
        s = tile_step(ix, iy);
        if (s <= step || step >= 99)
            staged(s, total_plate_h, at = [(ix + 0.5) * cell_pitch, (iy + 0.5) * cell_pitch])
                color(s < step || step >= 99 ? DONE_COLOR : NEW_COLOR) tile_at(ix, iy);
    }
    if (step >= 7) bar_set(inner_bars);

    // step 8: clue pieces
    if (step >= 8) {
        for (r = [0 : 3], c = [0 : 3]) {
            v = sample[r][c];
            if (v > 0)
                staged(8, base_thickness, arrow = false)
                    translate([(c + 0.5) * cell_pitch, (3 - r + 0.5) * cell_pitch, base_thickness])
                        main_piece(piece_colors[v - 1], str(v));
        }
        if (step == 8) translate([0.5 * cell_pitch, 3.5 * cell_pitch, total_plate_h + 3]) down_arrow(lift - 14);
    }

    // step 9: pencil pegs for puzzle 1.01
    //   center marks 2 + 4 in row 4, column 4  (top-right & bottom-right holes)
    //   corner marks: the 3 in the top-right box is in row 1 or row 2 of column 4
    //   (bottom-left corner hole = digit 3)
    if (step >= 9) {
        c_pts = central_mark_coords();  // [BL, BR, TL, TR] in 2x2 mode
        for (d = [2, 4])
            staged(9, peg_floor_z_, arrow = false)
                translate([3.5 * cell_pitch + c_pts[d == 2 ? 3 : 1][0],
                           0.5 * cell_pitch + c_pts[d == 2 ? 3 : 1][1], peg_floor_z_])
                    pencil_peg(piece_colors[d - 1], str(d));
        for (iy = [3, 2])
            staged(9, peg_floor_z_, arrow = false)
                translate([3.5 * cell_pitch - corner_mark_offset,
                           (iy + 0.5) * cell_pitch - corner_mark_offset, peg_floor_z_])
                    pencil_peg(piece_colors[2], "3");
        if (step == 9) translate([3.5 * cell_pitch, 0.5 * cell_pitch, total_plate_h + 3]) down_arrow(lift - 14);
    }
}

// Jigsaw variant (step 10): swap the middle bars for 1x bars making wobbly shapes
jig_regions = [            // row 0 = top; same numbers = same wobbly room
    [0, 0, 0, 1],
    [2, 0, 1, 1],
    [2, 3, 3, 1],
    [2, 2, 3, 3]
];
// every inside edge between two different rooms gets a short (1x) bar: [x, y, rot]
jig_bars_1x = concat(
    [for (r = [0 : 3], c = [0 : 2]) if (jig_regions[r][c] != jig_regions[r][c + 1])
        [c + 1, 3 - r + 0.5, 90]],
    [for (r = [0 : 2], c = [0 : 3]) if (jig_regions[r][c] != jig_regions[r + 1][c])
        [c + 0.5, 3 - r, 0]]
);

module jigsaw_step() {
    color(DONE_COLOR) for (ix = [0 : 3], iy = [0 : 3]) tile_at(ix, iy);
    for (b = jig_bars_1x)
        translate([b[0] * cell_pitch, b[1] * cell_pitch, slot_floor_z + lift * 0.5])
            rotate([0, 0, b[2]]) color(NEW_COLOR) region_bar(1, NEW_COLOR);
}

// ---------------------------------------------------------------------------
// Parts list (step 0) — 9 tile types (3x3 layout) + bars + pieces + pegs
// ---------------------------------------------------------------------------
module label3d(t, s = 7) {
    color("#222222") linear_extrude(height = 0.6)
        text(t, size = s, font = "Liberation Sans:style=Bold", halign = "center", valign = "top");
}

module parts_list() {
    gap_x = 64;
    gap_y = 82;
    // 3x3 layout matching board positions: [col, row, qty, name, N, S, E, W]
    tile_items = [
        [0, 2, "1x", "NW corner", true,  false, false, true],
        [1, 2, "2x", "N edge",    true,  false, false, false],
        [2, 2, "1x", "NE corner", true,  false, true,  false],
        [0, 1, "2x", "W edge",    false, false, false, true],
        [1, 1, "4x", "center",    false, false, false, false],
        [2, 1, "2x", "E edge",    false, false, true,  false],
        [0, 0, "1x", "SW corner", false, true,  false, true],
        [1, 0, "2x", "S edge",    false, true,  false, false],
        [2, 0, "1x", "SE corner", false, true,  true,  false]
    ];
    for (it = tile_items) {
        translate([it[0] * gap_x, it[1] * gap_y, 0]) {
            color(DONE_COLOR) render(convexity = 4)
                board_tile(it[4], it[5], it[6], it[7]);
            translate([cell_pitch / 2, -13, 0]) label3d(it[2], 7.5);
            translate([cell_pitch / 2, -24, 0]) label3d(it[3], 4.5);
        }
    }
    translate([3.3 * gap_x, 1.75 * gap_y, 0]) {
        translate([cell_pitch, 18, 0]) color(BAR_COLOR) region_bar(2, BAR_COLOR);
        translate([cell_pitch, 0, 0]) label3d("4x long bar (2x)", 5);
        translate([cell_pitch, -30, 0]) color(BAR_COLOR) region_bar(1, BAR_COLOR);
        translate([cell_pitch, -48, 0]) label3d("12x short bar (1x)", 5);
    }
    translate([3.2 * gap_x, 0.1 * gap_y, 0]) {
        for (d = [1 : 4])
            translate([(d - 0.5) * 32, 22, 0]) main_piece(piece_colors[d - 1], str(d));
        translate([2 * 32, 0, 0]) label3d("16x main pieces (4 of each)", 4.8);
        for (d = [1 : 4])
            translate([(d - 0.5) * 16 + 32, -32, 0]) pencil_peg(piece_colors[d - 1], str(d));
        translate([2 * 32, -50, 0]) label3d("64x pencil pegs (16 of each)", 4.5);
    }
}

// ---------------------------------------------------------------------------
if (step == 0) {
    parts_list();
} else if (step == 10) {
    jigsaw_step();
} else {
    board_steps();
}
