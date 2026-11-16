// ============================================================================
// 4x4 Kids' Sudoku: Piece Holder / Carry Case — "Board-as-Lid" Edition
// The 4x4 Sudoku board (145.6 x 145.6 mm) flips UPSIDE DOWN to serve as a
// flush, flat-topped lid! Zero separate lid to print.
//
// Holds all 4 colors x (4 main pieces + 16 pencil-mark pegs) PLUS the
// changeable region border bars (4x long 2x bars + 12x short 1x jigsaw bars),
// separated by color and piece type.
//
//   option A = "Row Tackle Box"     : 4 horizontal color rows (4 upright main
//                                     slots + wide coved peg scoop bin per row)
//                                     + full-length side Region Bar Vault
//   option B = "Four-Quadrant Tray" : 4 corner color quadrants matching the
//                                     board's 2x2 boxes; main pieces lie FLAT
//                                     face-up in 2x2-stack wells with finger
//                                     slots + wide coved peg dish + central
//                                     cross slot for region bars
//   option C = "Park & Count"       : Every single piece has its own home
//                                     (4 individual main pockets + 4x4 peg-hole
//                                     grid per color row + region bar rack) so
//                                     a missing piece is obvious at a glance
//
//   openscad -o out.png -D 'option="A"' -D 'part="open"' piece_holder.scad
//   openscad -o base.stl -D 'option="A"' -D 'part="base"' piece_holder.scad
// ============================================================================

include <../../src/color_sudoku_board.scad>

// Silence the main file's own top-level dispatcher.
render_mode = "none";

/* [Selection] */
option = "A";    // ["A", "B", "C", "board_fix"]
part   = "open"; // ["open", "closed", "lid_lifting", "base"]

/* [Colors] */
// Blue, Red, Tan, Green (same Sharpie palette as the workbook)
COLORS = ["#0178d4", "#db2134", "#eab47f", "#22ab7e"];
HOLDER = "#F4F2EC";
BAR_C  = "#22272E";

$fn = 48;

// ---------------------------------------------------------------------------
// Piece & Board Envelope (derived directly from ../../src/color_sudoku_board.scad)
// ---------------------------------------------------------------------------
main_w = tile_base_w;             // 28.4 mm square plinth
main_h = main_tile_height + 0.8;  // 16.8 mm incl. optional raised label
peg_d  = peg_circum_d;            // 6.28 mm across octagon corners
peg_f  = peg_eff_flat_d;          // 5.8 mm across flats
peg_l  = peg_height + 0.6;        // 16.6 mm incl. optional raised label
pad_h  = 0.6;                     // raised paint-marker color pads

// 4x4 Monolithic Board envelope (upside-down lid)
B_span   = 4 * cell_pitch;                // 140.0 mm grid span
B_width  = B_span + 2 * divider_hw;       // 145.6 mm outer board width
B_deck_h = total_plate_h;                 // 12.50 mm cell wall height
B_bord_h = border_total_h;                // 3.33 mm raised permanent black border
B_tot_h  = board_total_h;                 // 15.83 mm total board thickness

// Shared Holder Outer Shell & Board-Lid Capture Rim
// - Outer pocket (146.3 x 146.3 mm) cradles the 145.6 x 145.6 mm upside-down board
// - Inner compartment box (134.4 x 134.4 mm, [-67.2, +67.2]) sits inside the board's
//   recessed cell area so internal walls seal within 0.5 mm of the board's cell walls!
H_in_hw   = 67.2;                         // 134.4 x 134.4 mm clear interior
H_wall    = 2.6;                          // inner wall under board border ledge
H_rim_clr = 0.35;                         // per-side clearance around 145.6 mm board
H_rim_hw  = B_width / 2 + H_rim_clr;      // 73.15 mm (146.3 mm pocket)
H_rim_w   = 2.6;                          // outer capture rim thickness
H_out_hw  = H_rim_hw + H_rim_w;           // 75.75 mm -> 151.5 x 151.5 mm outer footprint
H_floor   = 2.0;                          // flat solid bottom on build plate (z = 0)
H_seal_up = B_bord_h - 0.53;              // 2.80 mm inner lip rising inside board border
H_rim_h   = 8.5;                          // outer capture rim height above board seat

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
module cbox(x0, y0, z0, dx, dy, dz) {
    translate([x0, y0, z0]) cube([dx, dy, dz]);
}

module rbox_center(w, l, h, r = 4) {
    linear_extrude(height = h) rounded_rect_2d(w, l, r);
}

module color_pad(w, l, c, r = 2.5) {
    color(c) linear_extrude(height = pad_h) rounded_rect_2d(w, l, r);
}

// Peg lying on its side along +X, centered at origin, resting on z = 0
module lying_peg(c) {
    translate([-peg_l / 2, 0, peg_f / 2]) rotate([0, 90, 0]) pencil_peg(c);
}

// Main piece standing on its side edge:
// - width (28.4 mm) along Y, thickness (16.0 mm) along X, height (28.4 mm) along Z
// - colored paint pad faces -X
module standing_main_piece(c) {
    translate([main_tile_height / 2, 0, main_w / 2])
        rotate([0, -90, 0])
            main_piece(c);
}

// Fill that turns the bottom edges of a rectangular bin [dx, dy] into smooth coves
// of radius r, so fingers sweep pegs smoothly up the curved walls.
module cove_fill(dx, dy, r) {
    difference() {
        cube([dx, dy, r]);
        hull() for (x = [r, dx - r], y = [r, dy - r]) {
            translate([x, y, r]) sphere(r = r, $fn = 32);
            translate([x, y, r]) cylinder(r = r, h = r + 1, $fn = 32);
        }
    }
}
function cove_lift(d, r) = d >= r ? 0 : r - sqrt(r * r - (r - d) * (r - d));

// Cross-notches at the 3 interior board grid lines (-35, 0, +35 mm) in the top
// H_seal_up of holder dividers, so the board closes flush even if region bars
// remain installed in the board when it is flipped over as the lid!
module board_grid_bar_clearance_cuts(z_seat) {
    nw = region_bar_crown_width + 0.8; // 4.8 mm clearance channel
    for (g = [-cell_pitch, 0, cell_pitch]) {
        translate([g - nw / 2, -H_in_hw - 1, z_seat - 0.1])
            cube([nw, 2 * H_in_hw + 2, H_seal_up + 1.0]);
        translate([-H_in_hw - 1, g - nw / 2, z_seat - 0.1])
            cube([2 * H_in_hw + 2, nw, H_seal_up + 1.0]);
    }
}

// Outer shell shared by all 3 options:
// - Flat z = 0 bottom
// - Stepped upper rim at z = z_seat that cradles the 145.6 x 145.6 mm upside-down board
// - Inner labyrinth lip rising to z = z_seat + H_seal_up inside the board's border
// - Wide ergonomic thumb scoops on Left (-X) and Right (+X) rims to lift the board out
module holder_outer_shell(z_seat) {
    z_top = z_seat + H_rim_h;
    z_lip = z_seat + H_seal_up;
    difference() {
        // Outer body from z = 0 to z_top
        rbox_center(2 * H_out_hw, 2 * H_out_hw, z_top, 5);

        // Upper board-lid pocket above z_seat (146.3 x 146.3 mm with lead-in chamfer)
        translate([0, 0, z_seat])
            rbox_center(2 * H_rim_hw, 2 * H_rim_hw, H_rim_h + 1, 2.0);
        hull() {
            translate([0, 0, z_top - 1.0])
                rbox_center(2 * H_rim_hw, 2 * H_rim_hw, eps, 2.0);
            translate([0, 0, z_top + eps])
                rbox_center(2 * H_rim_hw + 1.6, 2 * H_rim_hw + 1.6, eps, 2.6);
        }

        // Inner main compartment cavity [-H_in_hw, +H_in_hw] from H_floor to z_top
        translate([0, 0, H_floor])
            rbox_center(2 * H_in_hw, 2 * H_in_hw, z_top, 2.0);

        // Thumb scoops on Left (-X) and Right (+X) rims for lifting the board lid
        for (sx = [-1, 1]) {
            translate([sx * H_out_hw, 0, z_top + 2])
                rotate([0, 90, 0])
                    cylinder(d = 38, h = 16, center = true, $fn = 64);
        }
    }
    // Inner labyrinth lip around [-H_in_hw, +H_in_hw] rising to z_lip (inside board border)
    difference() {
        translate([0, 0, z_seat - eps])
            rbox_center(2 * (H_in_hw + 1.8), 2 * (H_in_hw + 1.8), H_seal_up + eps, 2.8);
        translate([0, 0, z_seat - 1])
            rbox_center(2 * H_in_hw, 2 * H_in_hw, H_seal_up + 2, 2.0);
        board_grid_bar_clearance_cuts(z_seat);
    }
}

// Upside-down 4x4 board positioned as the lid (with the 4 standard 2x region bars seated)
// When open_angle > 0, hinges the upside-down board open at the back edge so the viewer
// can see the 4x4 Sudoku cells & black border on the underside of the lid!
module upside_down_board_lid(z_seat, open_angle = 0, show_bars_in_board = true) {
    translate([0, B_width / 2, z_seat + (open_angle > 0 ? H_rim_h + 4 : 0)])
        rotate([-open_angle, 0, 0])
            translate([0, -B_width / 2, B_tot_h])
                rotate([180, 0, 0])
                    translate([-2 * cell_pitch, -2 * cell_pitch, 0]) {
                        monolithic_board(4, border_color = BAR_C);
                        if (show_bars_in_board) {
                            for (b = [[1, 2, 0], [3, 2, 0], [2, 1, 90], [2, 3, 90]])
                                translate([b[0] * cell_pitch, b[1] * cell_pitch, slot_floor_z])
                                    rotate([0, 0, b[2]])
                                        region_bar(2, BAR_C);
                        }
                    }
}

// ============================================================================
// OPTION A: "Row Tackle Box" (151.5 x 151.5 x 38 mm base; Board = Lid)
// - 4 Horizontal Color Rows (Blue, Red, Tan, Green)
// - Left of each row: 4 upright main-piece slots with pinch cutouts
// - Middle of each row: Wide coved finger-scoop peg bin (45 x 32 mm)
// - Right column: Full-length Region Bar Vault for 2x and 1x region bars
// ============================================================================
A_seat     = 29.0;                    // board border seat Z (leaves 31.8 mm interior height)
A_div_h    = A_seat + H_seal_up;      // 31.8 mm divider top (0.5 mm below upside-down board)
A_div_t    = 2.0;
A_row_w    = (2 * H_in_hw - 3 * A_div_t) / 4; // 32.1 mm row width in Y
A_slot_dx  = 17.4;                    // upright main-piece slot width along X
A_rib_t    = 1.6;                     // low counting rib between upright main slots
A_rib_h    = 11.0;
A_mains_dx = 4 * A_slot_dx + 3 * A_rib_t; // 74.4 mm total for 4 upright mains
A_bar_dx   = 12.0;                    // right-side Region Bar Vault width
A_bin_dx   = 2 * H_in_hw - A_mains_dx - A_bar_dx - 2 * A_div_t; // 44.0 mm peg bin length
A_x_mains  = -H_in_hw;                // -67.2 mm
A_x_bin    = A_x_mains + A_mains_dx + A_div_t; // +9.2 mm
A_x_bar    = A_x_bin + A_bin_dx + A_div_t;     // +55.2 mm
A_cove_r   = 6.0;

function A_row_y0(i) = -H_in_hw + (3 - i) * (A_row_w + A_div_t);
function A_slot_x0(j) = A_x_mains + j * (A_slot_dx + A_rib_t);

module A_base() {
    color(HOLDER) {
        holder_outer_shell(A_seat);

        difference() {
            union() {
                // 3 full-height horizontal row dividers (separating the 4 colors across mains + peg bins)
                for (i = [1 : 3]) {
                    y_div = -H_in_hw + i * A_row_w + (i - 1) * A_div_t;
                    cbox(-H_in_hw, y_div, H_floor - eps, A_mains_dx + A_div_t + A_bin_dx, A_div_t, A_div_h - H_floor);
                }
                // Full-height divider between upright main slots and peg scoop bins
                cbox(A_x_bin - A_div_t, -H_in_hw, H_floor - eps, A_div_t, 2 * H_in_hw, A_div_h - H_floor);
                // Full-height divider for the right-side Region Bar Vault
                cbox(A_x_bar - A_div_t, -H_in_hw, H_floor - eps, A_div_t, 2 * H_in_hw, A_div_h - H_floor);

                // Low counting ribs between the 4 upright main-piece slots in each row
                for (i = [0 : 3], j = [1 : 3]) {
                    cbox(A_slot_x0(j) - A_rib_t, A_row_y0(i), H_floor - eps, A_rib_t, A_row_w, A_rib_h);
                }
                // Raised coved floor in the 4 peg scoop bins (brings pegs closer to top for easy scooping)
                for (i = [0 : 3]) {
                    cbox(A_x_bin, A_row_y0(i), H_floor - eps, A_bin_dx, A_row_w, 12.0);
                    translate([A_x_bin, A_row_y0(i), H_floor + 12.0 - eps])
                        cove_fill(A_bin_dx, A_row_w, A_cove_r);
                }
            }
            // Finger-pinch U-cutouts in the row dividers between upright main slots
            for (i = [1 : 3], j = [0 : 3]) {
                y_div = -H_in_hw + i * A_row_w + (i - 1) * A_div_t + A_div_t / 2;
                xc = A_slot_x0(j) + A_slot_dx / 2;
                translate([xc, y_div, A_div_h - 4])
                    rotate([90, 0, 0])
                        cylinder(d = 11, h = A_div_t + 2, center = true, $fn = 32);
            }
            board_grid_bar_clearance_cuts(A_seat);
        }
    }

    // Color marker pads in every main-piece slot and at the bottom of every peg scoop bin
    for (i = [0 : 3]) {
        yc = A_row_y0(i) + A_row_w / 2;
        for (j = [0 : 3]) {
            xc = A_slot_x0(j) + A_slot_dx / 2;
            translate([xc, yc, H_floor - eps])
                color_pad(12, 22, COLORS[i], 2);
        }
        translate([A_x_bin + A_bin_dx / 2, yc, H_floor + 12.0 - eps])
            color_pad(A_bin_dx - 16, A_row_w - 16, COLORS[i], 3);
    }
}

module A_pieces() {
    for (i = [0 : 3]) {
        yc = A_row_y0(i) + A_row_w / 2;
        // 4 upright main pieces per color row
        for (j = [0 : 3]) {
            xc = A_slot_x0(j) + A_slot_dx / 2;
            translate([xc, yc, H_floor + pad_h])
                standing_main_piece(COLORS[i]);
        }
        // 16 pegs per color in the coved scoop bin (2 layers of 2x4)
        for (k = [0 : 1], a = [0 : 1], b = [0 : 3]) {
            lx = 4.0 + a * (peg_l + 2.0) + peg_l / 2 + k * 1.2;
            ly = A_row_w / 2 + (b - 1.5) * 6.4;
            d  = min(ly - peg_d / 2, A_row_w - ly - peg_d / 2);
            translate([A_x_bin + lx, A_row_y0(i) + ly,
                       H_floor + 12.0 + k * (peg_f + 0.2) + cove_lift(max(0, d), A_cove_r)])
                rotate([0, 0, (k == 0 ? 1 : -1) * 4])
                    lying_peg(COLORS[i]);
        }
    }
    // Spare 1x jigsaw bars stored in the right-side Region Bar Vault
    for (m = [0 : 3], n = [0 : 2]) {
        translate([A_x_bar + 3.0 + n * 3.2, -H_in_hw + 20 + m * 31, H_floor])
            rotate([0, 0, 90])
                region_bar(1, BAR_C);
    }
}

// ============================================================================
// OPTION B: "Four-Quadrant Flat Tray" (151.5 x 151.5 x 41 mm base; Board = Lid)
// - 4 Corner Color Quadrants matching the 4 boxes of the 4x4 board
// - Main pieces lie FLAT (face-up!) in 2 side-by-side 2-deep square wells per quadrant
// - Wide coved peg scoop dish right next to each color's flat main pieces
// - Central Cross Vault through X=0 and Y=0 holds the 2x and 1x region bars
// ============================================================================
B_seat     = 32.5;                    // board border seat Z (fits 2-stacked flat main pieces: 32.0 mm)
B_div_h    = B_seat + H_seal_up;      // 35.3 mm divider top
B_cross_w  = 9.6;                     // central cross channel for region bars
B_div_t    = 2.0;
B_q_min    = B_cross_w / 2 + B_div_t; // 6.8 mm from center axes
B_q_span   = H_in_hw - B_q_min;       // 60.4 x 60.4 mm clear inside each quadrant
B_well_w   = (B_q_span - B_div_t) / 2;// 29.2 x 29.2 mm flat main-piece well
B_bin_dy   = B_q_span - B_well_w - B_div_t; // 29.2 mm wide peg bin along Y
B_cove_r   = 6.0;

// Quadrant signs: 0=TL (Blue), 1=TR (Red), 2=BL (Tan), 3=BR (Green)
B_qx = [-1,  1, -1,  1];
B_qy = [ 1,  1, -1, -1];

module B_base() {
    color(HOLDER) {
        holder_outer_shell(B_seat);

        difference() {
            union() {
                // Central cross walls forming the 4 quadrants + central bar vault
                for (s = [-1, 1]) {
                    cbox(s * (B_cross_w / 2 + B_div_t / 2) - B_div_t / 2, -H_in_hw, H_floor - eps,
                         B_div_t, 2 * H_in_hw, B_div_h - H_floor);
                    cbox(-H_in_hw, s * (B_cross_w / 2 + B_div_t / 2) - B_div_t / 2, H_floor - eps,
                         2 * H_in_hw, B_div_t, B_div_h - H_floor);
                }

                // Inside each of the 4 quadrants:
                // - Outer half (away from Y=0): 2 side-by-side flat square wells (29.2 x 29.2 mm)
                // - Inner half (next to Y=0): elevated coved peg scoop dish (60.4 x 29.2 mm)
                for (q = [0 : 3]) {
                    sx = B_qx[q];
                    sy = B_qy[q];
                    x0 = sx > 0 ? B_q_min : -H_in_hw;
                    y_well0 = sy > 0 ? (H_in_hw - B_well_w) : -H_in_hw;
                    y_div0  = sy > 0 ? (y_well0 - B_div_t)  : (y_well0 + B_well_w);
                    y_bin0  = sy > 0 ? B_q_min              : (y_div0 + B_div_t);

                    // Divider between the 2 flat main wells and the peg scoop dish
                    cbox(x0, y_div0, H_floor - eps, B_q_span, B_div_t, B_div_h - H_floor);
                    // Rib between the 2 side-by-side flat main wells
                    cbox(x0 + B_well_w, y_well0, H_floor - eps, B_div_t, B_well_w, B_div_h - H_floor - 3);

                    // Elevated coved floor in the peg scoop dish (so pegs sit in a shallow top dish)
                    cbox(x0, y_bin0, H_floor - eps, B_q_span, B_bin_dy, 16.0);
                    translate([x0, y_bin0, H_floor + 16.0 - eps])
                        cove_fill(B_q_span, B_bin_dy, B_cove_r);
                }
            }

            // Deep U-shaped finger-pinch slots in the rib & wall between the 2 flat main wells
            // so both the top and bottom stacked main pieces can be pinched by their waists!
            for (q = [0 : 3]) {
                sx = B_qx[q];
                sy = B_qy[q];
                x_rib = (sx > 0 ? B_q_min : -H_in_hw) + B_well_w + B_div_t / 2;
                y_well_c = sy > 0 ? (H_in_hw - B_well_w / 2) : (-H_in_hw + B_well_w / 2);
                y_div_c  = sy > 0 ? (H_in_hw - B_well_w - B_div_t / 2) : (-H_in_hw + B_well_w + B_div_t / 2);

                // Finger slot between the two wells (down to z = H_floor + 5)
                hull() {
                    translate([x_rib, y_well_c, H_floor + 11])
                        rotate([0, 90, 0]) cylinder(d = 14, h = B_div_t + 2, center = true, $fn = 32);
                    translate([x_rib, y_well_c, B_div_h + 2])
                        rotate([0, 90, 0]) cylinder(d = 16, h = B_div_t + 2, center = true, $fn = 32);
                }
                // Finger scoop from the peg-bin divider into each well
                for (w = [0, 1]) {
                    xw = (sx > 0 ? B_q_min : -H_in_hw) + B_well_w / 2 + w * (B_well_w + B_div_t);
                    hull() {
                        translate([xw, y_div_c, H_floor + 20])
                            rotate([90, 0, 0]) cylinder(d = 14, h = B_div_t + 2, center = true, $fn = 32);
                        translate([xw, y_div_c, B_div_h + 2])
                            rotate([90, 0, 0]) cylinder(d = 16, h = B_div_t + 2, center = true, $fn = 32);
                    }
                }
            }
            board_grid_bar_clearance_cuts(B_seat);
        }
    }

    // Color pads in the 2 flat wells + peg dish of each quadrant
    for (q = [0 : 3]) {
        sx = B_qx[q];
        sy = B_qy[q];
        x0 = sx > 0 ? B_q_min : -H_in_hw;
        y_well_c = sy > 0 ? (H_in_hw - B_well_w / 2) : (-H_in_hw + B_well_w / 2);
        y_bin0   = sy > 0 ? B_q_min : (-H_in_hw + B_well_w + B_div_t);

        for (w = [0, 1]) {
            xw = x0 + B_well_w / 2 + w * (B_well_w + B_div_t);
            translate([xw, y_well_c, H_floor - eps])
                color_pad(18, 18, COLORS[q], 3);
        }
        translate([x0 + B_q_span / 2, y_bin0 + B_bin_dy / 2, H_floor + 16.0 - eps])
            color_pad(B_q_span - 18, B_bin_dy - 15, COLORS[q], 3);
    }
}

module B_pieces() {
    for (q = [0 : 3]) {
        sx = B_qx[q];
        sy = B_qy[q];
        x0 = sx > 0 ? B_q_min : -H_in_hw;
        y_well_c = sy > 0 ? (H_in_hw - B_well_w / 2) : (-H_in_hw + B_well_w / 2);
        y_bin0   = sy > 0 ? B_q_min : (-H_in_hw + B_well_w + B_div_t);

        // 4 flat main pieces per quadrant (2 side-by-side stacks of 2)
        for (w = [0, 1], layer = [0, 1]) {
            xw = x0 + B_well_w / 2 + w * (B_well_w + B_div_t);
            translate([xw, y_well_c, H_floor + pad_h + layer * main_tile_height])
                main_piece(COLORS[q]);
        }

        // 16 loose pegs in each quadrant's coved scoop dish
        for (k = [0 : 1], a = [0 : 1], b = [0 : 3]) {
            lx = 11.0 + a * (peg_l + 5.0) + peg_l / 2 + k * 1.5;
            ly = B_bin_dy / 2 + (b - 1.5) * 6.0;
            d  = min(ly - peg_d / 2, B_bin_dy - ly - peg_d / 2);
            translate([x0 + lx, y_bin0 + ly,
                       H_floor + 16.0 + k * (peg_f + 0.2) + cove_lift(max(0, d), B_cove_r)])
                rotate([0, 0, (k == 0 ? 1 : -1) * 5])
                    lying_peg(COLORS[q]);
        }
    }
    // Short 1x jigsaw bars stored in the central cross channel
    for (s = [-1, 1], idx = [0 : 1]) {
        translate([s * 34, (idx - 0.5) * 4.2, H_floor])
            region_bar(1, BAR_C);
        translate([(idx - 0.5) * 4.2, s * 34, H_floor])
            rotate([0, 0, 90])
                region_bar(1, BAR_C);
    }
}

// ============================================================================
// OPTION C: "Park & Count" (151.5 x 151.5 x 38 mm base; Board = Lid)
// - Every single piece has its own individual home so missing pieces jump out!
// - 4 Color Rows:
//   * Left (4 individual upright main-piece pockets with colored floor pads)
//   * Center (dedicated Region Bar Rack for 1x and 2x bars)
//   * Right (4x4 peg-hole deck = 16 individual anti-tip peg sockets per color)
// ============================================================================
C_seat      = 29.0;                   // board border seat Z
C_div_h     = C_seat + H_seal_up;     // 31.8 mm divider top
C_div_t     = 2.0;
C_row_w     = (2 * H_in_hw - 3 * C_div_t) / 4; // 32.1 mm per color row
C_pock_dx   = 17.6;                   // upright main-piece pocket width
C_pock_rib  = 2.4;
C_mains_dx  = 4 * C_pock_dx + 3 * C_pock_rib;  // 77.6 mm
C_peg_pitch = 7.6;                    // 4x4 peg hole pitch
C_peg_hole  = peg_d + 0.55;           // 6.83 mm hole diameter
C_grid_dx   = 34.0;                   // width of 4x4 peg-grid deck
C_bar_dx    = 2 * H_in_hw - C_mains_dx - C_grid_dx - 2 * C_div_t; // 18.8 mm center bar bay
C_x_mains   = -H_in_hw;               // -67.2 mm
C_x_bar     = C_x_mains + C_mains_dx + C_div_t; // +12.4 mm
C_x_grid    = C_x_bar + C_bar_dx + C_div_t;     // +33.2 mm
C_deck_z    = H_floor + 19.5;         // elevated deck for the 4x4 peg holes

function C_row_y0(i) = -H_in_hw + (3 - i) * (C_row_w + C_div_t);
function C_pock_x0(j) = C_x_mains + j * (C_pock_dx + C_pock_rib);
function C_peg_xy(i, a, b) = [
    C_x_grid + C_grid_dx / 2 + (a - 1.5) * C_peg_pitch,
    C_row_y0(i) + C_row_w / 2 + (b - 1.5) * C_peg_pitch
];

module C_base() {
    color(HOLDER) {
        holder_outer_shell(C_seat);

        difference() {
            union() {
                // 3 horizontal color-row dividers
                for (i = [1 : 3]) {
                    y_div = -H_in_hw + i * C_row_w + (i - 1) * C_div_t;
                    cbox(-H_in_hw, y_div, H_floor - eps, C_mains_dx, C_div_t, C_div_h - H_floor);
                    cbox(C_x_grid, y_div, H_floor - eps, C_grid_dx,  C_div_t, C_div_h - H_floor);
                }
                // Divider walls flanking the central Region Bar Bay
                cbox(C_x_bar - C_div_t,  -H_in_hw, H_floor - eps, C_div_t, 2 * H_in_hw, C_div_h - H_floor);
                cbox(C_x_grid - C_div_t, -H_in_hw, H_floor - eps, C_div_t, 2 * H_in_hw, C_div_h - H_floor);

                // Individual pocket ribs between the 4 upright main pieces in each row
                for (i = [0 : 3], j = [1 : 3]) {
                    cbox(C_pock_x0(j) - C_pock_rib, C_row_y0(i), H_floor - eps,
                         C_pock_rib, C_row_w, C_div_h - H_floor - 4);
                }

                // Elevated 4x4 peg-hole deck on the right side
                cbox(C_x_grid, -H_in_hw, H_floor - eps, C_grid_dx, 2 * H_in_hw, C_deck_z - H_floor);
            }

            // Deep U-shaped finger pinch cutouts in the main-piece pocket ribs & row dividers
            for (i = [0 : 3], j = [1 : 3]) {
                xr = C_pock_x0(j) - C_pock_rib / 2;
                yc = C_row_y0(i) + C_row_w / 2;
                hull() {
                    translate([xr, yc, H_floor + 12])
                        rotate([0, 90, 0]) cylinder(d = 14, h = C_pock_rib + 2, center = true, $fn = 32);
                    translate([xr, yc, C_div_h + 2])
                        rotate([0, 90, 0]) cylinder(d = 16, h = C_pock_rib + 2, center = true, $fn = 32);
                }
            }

            // 64 individual peg sockets (4x4 per color row) with 45-deg entry chamfers
            for (i = [0 : 3], a = [0 : 3], b = [0 : 3]) {
                pt = C_peg_xy(i, a, b);
                translate([pt[0], pt[1], C_deck_z - peg_socket_depth])
                    cylinder(d = C_peg_hole, h = peg_socket_depth + 1);
                translate([pt[0], pt[1], C_deck_z - 0.7])
                    cylinder(d1 = C_peg_hole, d2 = C_peg_hole + 1.4, h = 0.75);
            }

            board_grid_bar_clearance_cuts(C_seat);
        }
    }

    // Color pads in each main-piece pocket + colored frame around each 4x4 peg grid
    for (i = [0 : 3]) {
        yc = C_row_y0(i) + C_row_w / 2;
        for (j = [0 : 3]) {
            xc = C_pock_x0(j) + C_pock_dx / 2;
            translate([xc, yc, H_floor - eps])
                color_pad(12, 22, COLORS[i], 2);
        }
        // Colored ring around each 4x4 peg grid on the deck
        translate([C_x_grid + C_grid_dx / 2, yc, C_deck_z - eps])
            color(COLORS[i])
                linear_extrude(height = pad_h)
                    difference() {
                        rounded_rect_2d(C_grid_dx - 1.6, C_row_w - 1.6, 2.5);
                        rounded_rect_2d(C_grid_dx - 4.0, C_row_w - 4.0, 1.5);
                    }
    }
}

module C_pieces(missing = true) {
    for (i = [0 : 3]) {
        yc = C_row_y0(i) + C_row_w / 2;
        for (j = [0 : 3]) if (!(missing && i == 3 && j == 3)) {
            xc = C_pock_x0(j) + C_pock_dx / 2;
            translate([xc, yc, H_floor + pad_h])
                standing_main_piece(COLORS[i]);
        }
        for (a = [0 : 3], b = [0 : 3]) if (!(missing && i == 3 && (a + b * 4) >= 13)) {
            pt = C_peg_xy(i, a, b);
            translate([pt[0], pt[1], C_deck_z - peg_socket_depth])
                pencil_peg(COLORS[i]);
        }
    }
    // Spare 1x jigsaw bars in the central Region Bar Bay
    for (m = [0 : 3], n = [0 : 2]) {
        translate([C_x_bar + 4.2 + n * 5.0, -H_in_hw + 20 + m * 31, H_floor])
            rotate([0, 0, 90])
                region_bar(1, BAR_C);
    }
    // Show the "missing" green pieces out in front of the holder so the empty holes are obvious
    if (missing) {
        translate([48, -H_out_hw - 22, 0])
            main_piece(COLORS[3]);
        for (k = [0 : 2])
            translate([12 - k * 14, -H_out_hw - 20, 0])
                rotate([0, 0, 18 * k])
                    lying_peg(COLORS[3]);
    }
}

// ============================================================================
// Board Fix Showcase Scene (Permanent Black Outer Border + Edge Notches)
// ============================================================================
module board_fix_showcase() {
    monolithic_board(4, border_color = BAR_C);
    // 2 seated 2x bars + 1 seated 1x bar + 1 lifted 2x bar showing the edge notch fit
    translate([1.0 * cell_pitch, 2.0 * cell_pitch, slot_floor_z])
        region_bar(2, BAR_C);
    translate([3.0 * cell_pitch, 2.0 * cell_pitch, slot_floor_z])
        region_bar(2, BAR_C);
    translate([2.0 * cell_pitch, 3.0 * cell_pitch, slot_floor_z])
        rotate([0, 0, 90]) region_bar(2, BAR_C);
    // Lifted bar hovering right over the South border notch at x = 2 * cell_pitch
    translate([2.0 * cell_pitch, 1.0 * cell_pitch, slot_floor_z + 18])
        rotate([0, 0, 90]) color("#FF9F1C") region_bar(2, "#FF9F1C");
    // Sample jigsaw bar seated into the West border notch at y = 3 * cell_pitch
    translate([0.5 * cell_pitch, 3.0 * cell_pitch, slot_floor_z])
        region_bar(1, BAR_C);
}

// ============================================================================
// Dispatcher
// ============================================================================
module show(opt, prt) {
    if (opt == "board_fix") {
        board_fix_showcase();
    } else if (opt == "A") {
        if (prt == "base") A_base();
        else if (prt == "closed") { A_base(); upside_down_board_lid(A_seat, 0); }
        else if (prt == "lid_lifting") { A_base(); A_pieces(); upside_down_board_lid(A_seat, 62); }
        else { A_base(); A_pieces(); }
    } else if (opt == "B") {
        if (prt == "base") B_base();
        else if (prt == "closed") { B_base(); upside_down_board_lid(B_seat, 0); }
        else if (prt == "lid_lifting") { B_base(); B_pieces(); upside_down_board_lid(B_seat, 62); }
        else { B_base(); B_pieces(); }
    } else if (opt == "C") {
        if (prt == "base") C_base();
        else if (prt == "closed") { C_base(); upside_down_board_lid(C_seat, 0); }
        else if (prt == "lid_lifting") { C_base(); C_pieces(false); upside_down_board_lid(C_seat, 62); }
        else { C_base(); C_pieces(true); }
    }
}

show(option, part);
