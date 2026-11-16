// ============================================================================
// 4x4 Kids' Sudoku: Piece Holder with Upside-Down Board as the Lid (3 options)
// Holds 4 colors x (4 main pieces + 16 pencil-mark pegs) + region bars,
// with the monolithic 4x4 board (145.6 x 145.6 mm) flipped upside down as
// the flat-topped lid!
//
//   option A = "Standing Slots + Coved Peg Bins" (single-layer, 152.6 x 152.6 mm)
//   option B = "Two-Tier Stacker" (flat 4x4 mains + lift-out peg/bar tray)
//   option C = "Park & Count" (standing mains + 4x4 peg holes + region-bar caddy)
//
//   openscad -o out.png -D 'option="A"' -D 'part="open"' piece_holder.scad
//   openscad -o base.stl -D 'option="A"' -D 'part="base"' piece_holder.scad
// All parts fit the Bambu Lab A1 Mini 180 x 180 mm bed.
// ============================================================================

include <../../src/color_sudoku_board.scad>

// Silence the main file's own top-level dispatcher.
render_mode = "none";

/* [Selection] */
option = "A"; // ["A", "B", "C"]
part   = "open"; // ["open", "closed", "base", "tray", "lid"]

/* [Colors] */
// Blue, Red, Tan, Green (same Sharpie palette as the workbook)
COLORS = ["#0178d4", "#db2134", "#eab47f", "#22ab7e"];
HOLDER = "#F4F2EC";
TRAYC  = "#E6ECEF";
BOARDC = "#D9E3EC";

$fn = 48;

// ---------------------------------------------------------------------------
// Piece & Board envelope (derived from color_sudoku_board.scad)
// ---------------------------------------------------------------------------
main_w = tile_base_w;             // 28.4 mm square plinth
main_h = main_tile_height + 0.8;  // 16.8 mm incl. optional raised label
peg_d  = peg_circum_d;            // 6.28 mm across octagon corners
peg_f  = peg_eff_flat_d;          // 5.8 mm across flats
peg_l  = peg_height + 0.6;        // 16.6 mm incl. optional raised label
pad_h  = 0.6;                     // raised paint-marker color pads

board_span = 4 * cell_pitch;                    // 140.0 mm
board_w    = board_span + 2 * divider_hw;       // 145.6 mm
board_border_top_z = slot_floor_z + bar_tongue_h + bar_bevel_h + region_bar_crown_height; // 15.83 mm

// Common outer box dimensions (board_4x4 nests upside-down inside the top rim)
box_clr  = 0.3;                                 // per-side clearance around board
box_wall = 3.2;                                 // outer collar wall thickness
box_ix   = board_w + 2 * box_clr;               // 146.2 mm (collar opening)
box_ox   = box_ix + 2 * box_wall;               // 152.6 mm (fits 180x180 bed)
ledge_w  = 5.4;                                 // supports board's raised border
inner_w  = box_ix - 2 * ledge_w;                // 135.4 mm clear interior width

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
module rbox(x, y, h, r) { // corner-origin rounded box
    translate([x / 2, y / 2, 0]) linear_extrude(h) rounded_rect_2d(x, y, r);
}

module color_pad(w, l, c, r = 3) {
    color(c) linear_extrude(pad_h) rounded_rect_2d(w, l, r);
}

// Peg lying on its side along +X, centered at origin, resting on z = 0
module lying_peg(c) {
    translate([-peg_l / 2, 0, peg_f / 2]) rotate([0, 90, 0]) pencil_peg(c);
}

// Fill that turns the bottom edges of a box-shaped bin into smooth coves
module cove_fill(l, w, r) {
    difference() {
        cube([l, w, r]);
        hull() for (x = [r, l - r], y = [r, w - r]) {
            translate([x, y, r]) sphere(r, $fn = 32);
            translate([x, y, r]) cylinder(r = r, h = r + 1, $fn = 32);
        }
    }
}
function cove_lift(d, r) = d >= r ? 0 : r - sqrt(r * r - (r - d) * (r - d));

// Upside-down board_4x4 positioned to nest into a holder with ledge at z = ledge_z
module board_lid(ledge_z) {
    lid_top_z = ledge_z + board_border_top_z;
    color(BOARDC)
        translate([box_wall + box_clr + divider_hw,
                   box_wall + box_clr + board_w - divider_hw,
                   lid_top_z])
        rotate([180, 0, 0])
            monolithic_board(4);
}

// Outer shell with recessed top collar for the upside-down board_4x4 + finger-lift notches
module holder_shell(ledge_z) {
    total_h = ledge_z + board_border_top_z;
    color(HOLDER) difference() {
        rbox(box_ox, box_ox, total_h, 5);
        // Main interior cavity (clear of the board's raised border)
        translate([box_wall + ledge_w, box_wall + ledge_w, 2.0])
            rbox(inner_w, inner_w, total_h, 2.5);
        // Upper collar pocket for the 145.6 x 145.6 mm board
        translate([box_wall, box_wall, ledge_z])
            rbox(box_ix, box_ix, board_border_top_z + 1, 3.0);
        // Finger-lift thumb scoops on left and right edges of the collar
        for (x = [0, box_ox]) {
            translate([x, box_ox / 2, total_h])
                scale([0.45, 1, 0.55]) sphere(r = 16);
        }
    }
}

// ============================================================================
// OPTION A: "Standing Slots + Coved Peg Bins" (152.6 x 152.6 x 46.8 mm)
//   4 color rows: 4 main pieces stand on edge (easy pinch) + coved peg scoop bin
// ============================================================================
A_floor   = 2.0;
A_ledge_z = A_floor + main_w + 0.6;             // 31.0 mm (clears standing mains)
A_div     = 1.8;
A_row_w   = (inner_w - 3 * A_div) / 4;          // 32.5 mm per row
A_slot_w  = main_h + 0.8;                       // 17.6 mm (main on edge)
A_rib     = 1.4;
A_slot_l  = main_w + 1.0;                       // 29.4 mm
A_slot_h  = 21.0;                               // mains stick up 7.4 mm to pinch
A_bin_x0  = box_wall + ledge_w + 4 * A_slot_w + 3 * A_rib + A_div; // 74.6 + 1.8 = 76.4
A_bin_l   = inner_w - (4 * A_slot_w + 3 * A_rib + A_div);          // 59.0 mm
A_cove    = 6.0;
function A_row_y(i)  = box_wall + ledge_w + i * (A_row_w + A_div);
function A_slot_x(j) = box_wall + ledge_w + j * (A_slot_w + A_rib);

module A_base() {
    holder_shell(A_ledge_z);
    color(HOLDER) {
        // Row dividers
        for (i = [1:3])
            translate([box_wall + ledge_w, A_row_y(i) - A_div, A_floor - 0.01])
                cube([inner_w, A_div, A_slot_h]);
        // Divider between main slots and peg scoop bin
        translate([A_bin_x0 - A_div, box_wall + ledge_w, A_floor - 0.01])
            cube([A_div, inner_w, A_slot_h]);
        // Thin ribs between the 4 main slots
        for (i = [0:3], j = [1:3])
            translate([A_slot_x(j) - A_rib, A_row_y(i), A_floor - 0.01])
                cube([A_rib, A_row_w, A_slot_h]);
        // Coved floor in each peg bin
        for (i = [0:3])
            translate([A_bin_x0, A_row_y(i), A_floor - 0.01])
                cove_fill(A_bin_l, A_row_w, A_cove);
    }
    // Color pads in peg bins & along left inner wall
    for (i = [0:3]) {
        translate([A_bin_x0 + A_bin_l / 2, A_row_y(i) + A_row_w / 2, A_floor - 0.01])
            color_pad(36, 16, COLORS[i]);
        for (j = [0:3])
            translate([A_slot_x(j) + A_slot_w / 2, A_row_y(i) + A_row_w / 2, A_floor - 0.01])
                color_pad(10, 18, COLORS[i], 2);
    }
}

module A_pieces() {
    for (i = [0:3]) {
        for (j = [0:3])
            translate([A_slot_x(j) + A_slot_w / 2, A_row_y(i) + A_row_w / 2, A_floor + pad_h + main_w / 2])
                rotate([0, 90, 0]) translate([0, 0, -main_h / 2]) main_piece(COLORS[i]);
        // 16 loose pegs per bin, two layers
        for (k = [0:1], a = [0:1], b = [0:3]) {
            lx = 6.0 + a * (peg_l + 3.0) + peg_l / 2 + k * 1.5;
            ly = A_row_w / 2 + (b - 1.5) * 6.4 + k * 1.2;
            d  = min(ly - peg_d / 2, A_row_w - ly - peg_d / 2);
            translate([A_bin_x0 + lx, A_row_y(i) + ly,
                       A_floor + k * (peg_f + 0.2) + cove_lift(max(0, d), A_cove)])
                rotate([0, 0, (k == 0 ? 0 : 1) * (a == 0 ? 5 : -4) + (b - 1.5) * 1.5])
                    lying_peg(COLORS[i]);
        }
    }
}

// ============================================================================
// OPTION B: "Two-Tier Stacker" (152.6 x 152.6 x 45.6 mm)
//   Bottom tier: 4x4 flat main-piece pockets (16.8 mm tall)
//   Lift-out upper tray: 4 coved peg bins + dedicated region-bar slots
// ============================================================================
B_floor   = 2.0;
B_pocket  = main_w + 1.0;                       // 29.4 mm
B_pg      = (inner_w - 4 * B_pocket) / 3;       // 5.93 mm gap between pockets
B_main_h  = main_h + pad_h + 0.6;               // 18.0 mm tier height
B_tray_z  = B_floor + B_main_h;                 // 20.0 mm tray seat
B_tray_h  = 9.6;                                // tray height
B_ledge_z = B_tray_z + B_tray_h + 0.2;          // 29.8 mm
B_tray_clr = 0.4;
B_tray_w  = inner_w - 2 * B_tray_clr;           // 134.6 mm
B_bar_w   = 18.0;                               // right strip for region bars
B_peg_w   = B_tray_w - B_bar_w - 2.0;           // 114.6 mm for 4 peg bins
B_bin_w   = (B_peg_w - 3 * 2.0) / 4;            // 27.15 mm per color bin
B_bin_l   = B_tray_w - 4.0;                     // 130.6 mm long
function B_cell_xy(idx) = box_wall + ledge_w + idx * (B_pocket + B_pg);

module B_base() {
    holder_shell(B_ledge_z);
    color(HOLDER) {
        // 4x4 grid dividers for flat main pieces (only up to B_tray_z - 0.2)
        for (i = [1:3]) {
            translate([box_wall + ledge_w, B_cell_xy(i) - B_pg, B_floor - 0.01])
                cube([inner_w, B_pg, B_main_h]);
            translate([B_cell_xy(i) - B_pg, box_wall + ledge_w, B_floor - 0.01])
                cube([B_pg, inner_w, B_main_h]);
        }
    }
    for (i = [0:3], j = [0:3])
        translate([B_cell_xy(j) + B_pocket / 2, B_cell_xy(i) + B_pocket / 2, B_floor - 0.01])
            color_pad(18, 18, COLORS[i]);
}

module B_tray() {
    x0 = box_wall + ledge_w + B_tray_clr;
    y0 = box_wall + ledge_w + B_tray_clr;
    translate([x0, y0, B_tray_z]) {
        color(TRAYC) difference() {
            rbox(B_tray_w, B_tray_w, B_tray_h, 2.2);
            // 4 color peg bins
            for (i = [0:3])
                translate([2.0 + i * (B_bin_w + 2.0), 2.0, 1.4])
                    cube([B_bin_w, B_bin_l, B_tray_h]);
            // Region-bar storage trough on the right
            translate([2.0 + B_peg_w + 2.0, 2.0, 1.4])
                cube([B_bar_w - 4.0, B_bin_l, B_tray_h]);
            // Finger-lift notches on front & back of tray
            for (y = [0, B_tray_w])
                translate([B_tray_w / 2, y, B_tray_h])
                    scale([1, 0.45, 0.6]) sphere(r = 12);
        }
        // Color pads at bottom of each peg bin
        for (i = [0:3])
            translate([2.0 + i * (B_bin_w + 2.0) + B_bin_w / 2, B_tray_w / 2, 1.39])
                color_pad(14, 40, COLORS[i]);
    }
}

module B_pieces() {
    // 16 flat main pieces in bottom tier
    for (i = [0:3], j = [0:3])
        translate([B_cell_xy(j) + B_pocket / 2, B_cell_xy(i) + B_pocket / 2, B_floor + pad_h])
            main_piece(COLORS[i]);
    // 64 pegs in upper tray bins + 4 region bars in the right trough
    x0 = box_wall + ledge_w + B_tray_clr;
    y0 = box_wall + ledge_w + B_tray_clr;
    for (i = [0:3]) {
        bx = x0 + 2.0 + i * (B_bin_w + 2.0) + B_bin_w / 2;
        for (k = [0:1], a = [0:3], b = [0:1]) {
            translate([bx + (b - 0.5) * 7.5 + k * 1.2,
                       y0 + 18 + a * (peg_l + 6.0) + k * 2.0,
                       B_tray_z + 1.4 + pad_h + k * (peg_f + 0.2)])
                rotate([0, 0, 90 + (k == 0 ? 3 : -4)]) lying_peg(COLORS[i]);
        }
    }
    // Sample region bars in the right trough
    translate([x0 + 2.0 + B_peg_w + 2.0 + 4.5, y0 + 28, B_tray_z + 1.4])
        rotate([0, 0, 90]) region_bar(1, "#264653");
    translate([x0 + 2.0 + B_peg_w + 2.0 + 10.5, y0 + 55, B_tray_z + 1.4])
        rotate([0, 0, 90]) region_bar(2, "#264653");
}

// ============================================================================
// OPTION C: "Park & Count" (152.6 x 152.6 x 46.8 mm)
//   Single-layer: standing main slots + 4x4 upright peg holes + region-bar caddy
// ============================================================================
C_floor   = 2.0;
C_ledge_z = C_floor + main_w + 0.6;             // 31.0 mm
C_div     = 1.6;
C_row_w   = (inner_w - 3 * C_div) / 4;          // 32.65 mm per row
C_slot_w  = main_h + 0.6;                       // 17.4 mm
C_rib     = 1.3;
C_slot_h  = 21.0;
C_slots_w = 4 * C_slot_w + 3 * C_rib;           // 73.5 mm
C_pitch   = 8.4;                                // 4x4 peg hole pitch (1.52 mm walls)
C_hole    = peg_d + 0.6;                        // 6.88 mm
C_grid    = 3 * C_pitch + C_hole;               // 32.08 mm (fits 32.65 mm row!)
C_hdepth  = peg_socket_depth;                   // 6.2 mm
C_deck_h  = 11.0;                               // peg deck height (pegs stick up 10.4 mm)
C_grid_x0 = box_wall + ledge_w + C_slots_w + 2.2;
C_bar_x0  = C_grid_x0 + C_grid + 2.2;           // ~25.4 mm wide caddy on right
C_bar_w   = (box_wall + ledge_w + inner_w) - C_bar_x0;
function C_row_y(i)  = box_wall + ledge_w + i * (C_row_w + C_div);
function C_slot_x(j) = box_wall + ledge_w + j * (C_slot_w + C_rib);
function C_hole_xy(i, a, b) = [
    C_grid_x0 + (C_row_w - C_grid) / 2 + C_hole / 2 + a * C_pitch,
    C_row_y(i) + (C_row_w - C_grid) / 2 + C_hole / 2 + b * C_pitch
];

module C_base() {
    difference() {
        union() {
            holder_shell(C_ledge_z);
            color(HOLDER) {
                // Row dividers
                for (i = [1:3])
                    translate([box_wall + ledge_w, C_row_y(i) - C_div, C_floor - 0.01])
                        cube([C_slots_w + 2.2 + C_grid, C_div, C_slot_h]);
                // Divider between main slots and peg deck
                translate([C_grid_x0 - 2.2, box_wall + ledge_w, C_floor - 0.01])
                    cube([2.2, inner_w, C_slot_h]);
                // Divider between peg deck and region-bar caddy
                translate([C_bar_x0 - 2.2, box_wall + ledge_w, C_floor - 0.01])
                    cube([2.2, inner_w, C_slot_h]);
                // Thin ribs between the 4 main slots
                for (i = [0:3], j = [1:3])
                    translate([C_slot_x(j) - C_rib, C_row_y(i), C_floor - 0.01])
                        cube([C_rib, C_row_w, C_slot_h]);
                // Solid peg decks for each color row
                for (i = [0:3])
                    translate([C_grid_x0, C_row_y(i), C_floor - 0.01])
                        cube([C_grid + 0.6, C_row_w, C_deck_h - C_floor]);
                // Region-bar caddy divider ribs (3 lanes)
                for (k = [1:2])
                    translate([C_bar_x0 + k * (C_bar_w / 3) - 0.7, box_wall + ledge_w, C_floor - 0.01])
                        cube([1.4, inner_w, 12.0]);
            }
        }
        // Drill 4x4 peg holes in each color deck
        for (i = [0:3], a = [0:3], b = [0:3])
            translate(concat(C_hole_xy(i, a, b), [0])) {
                translate([0, 0, C_deck_h - C_hdepth])
                    cylinder(d = C_hole, h = C_hdepth + 1);
                translate([0, 0, C_deck_h - 0.8])
                    cylinder(d1 = C_hole, d2 = C_hole + 1.6, h = 0.81);
            }
    }
    // Color pads in main slots & colored rim around each peg deck
    for (i = [0:3]) {
        for (j = [0:3])
            translate([C_slot_x(j) + C_slot_w / 2, C_row_y(i) + C_row_w / 2, C_floor - 0.01])
                color_pad(10, 18, COLORS[i], 2);
        translate([C_grid_x0 + C_row_w / 2, C_row_y(i) + C_row_w / 2, C_deck_h - 0.01])
            color(COLORS[i]) linear_extrude(pad_h) difference() {
                rounded_rect_2d(C_grid + 0.2, C_grid + 0.2, 2);
                rounded_rect_2d(C_grid - 1.6, C_grid - 1.6, 1.5);
            }
    }
}

module C_pieces() {
    for (i = [0:3]) {
        for (j = [0:3])
            translate([C_slot_x(j) + C_slot_w / 2, C_row_y(i) + C_row_w / 2, C_floor + pad_h + main_w / 2])
                rotate([0, 90, 0]) translate([0, 0, -main_h / 2]) main_piece(COLORS[i]);
        for (a = [0:3], b = [0:3])
            translate(concat(C_hole_xy(i, a, b), [C_deck_h - C_hdepth]))
                pencil_peg(COLORS[i]);
    }
    // Sample region bars in the right caddy
    translate([C_bar_x0 + C_bar_w / 6, box_wall + ledge_w + 26, C_floor])
        rotate([0, 0, 90]) region_bar(1, "#264653");
    translate([C_bar_x0 + C_bar_w / 2, box_wall + ledge_w + 46, C_floor])
        rotate([0, 0, 90]) region_bar(2, "#264653");
    translate([C_bar_x0 + 5 * C_bar_w / 6, box_wall + ledge_w + 66, C_floor])
        rotate([0, 0, 90]) region_bar(3, "#264653");
}

// ============================================================================
// Dispatcher
// ============================================================================
module show(opt, prt) {
    if (opt == "A") {
        if (prt == "base") A_base();
        else if (prt == "lid") board_lid(A_ledge_z);
        else if (prt == "closed") { A_base(); board_lid(A_ledge_z); }
        else { A_base(); A_pieces(); }
    } else if (opt == "B") {
        if (prt == "base") B_base();
        else if (prt == "tray") translate([0, 0, -B_tray_z]) B_tray();
        else if (prt == "lid") board_lid(B_ledge_z);
        else if (prt == "closed") { B_base(); B_tray(); board_lid(B_ledge_z); }
        else { B_base(); B_tray(); B_pieces(); }
    } else if (opt == "C") {
        if (prt == "base") C_base();
        else if (prt == "lid") board_lid(C_ledge_z);
        else if (prt == "closed") { C_base(); board_lid(C_ledge_z); }
        else { C_base(); C_pieces(); }
    }
}

show(option, part);
