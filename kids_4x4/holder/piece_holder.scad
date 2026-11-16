// ============================================================================
// 4x4 Kids' Sudoku: Piece Holder / Carry Case — "Flush Board-as-Lid" Edition
// The 4x4 Sudoku board (145.6 x 145.6 mm) flips UPSIDE DOWN to serve as a
// flush, flat-topped lid! Its 4.8 mm wide outer border ridge sits directly on
// the holder's outer wall so the board and holder are 100% flush (145.6 x 145.6 mm).
//
// Holds all 4 colors x (4 main pieces + 16 pencil-mark pegs) PLUS 1x, 2x, and 3x
// changeable region border bars.
//
//   option A = "Row Tackle Box"     : 4 horizontal color rows (4 upright main
//                                     slots + wide coved peg scoop bin per row)
//                                     + full-length side Region Bar Vault
//   option B = "Four-Quadrant Tray" : 4 corner color quadrants matching the
//                                     board's 2x2 boxes; main pieces lie FLAT
//                                     face-up in 2x2-stack wells with wide 22 mm
//                                     finger slots + coved peg dish + central
//                                     cross vault for 1x, 2x, and 3x region bars
//   option C = "Park & Count"       : Every single piece has its own home
//                                     (4 individual main pockets + 4x4 peg-hole
//                                     grid per color row + region bar rack)
// ============================================================================

include <../../src/color_sudoku_board.scad>

// Silence the main file's own top-level dispatcher.
render_mode = "none";

/* [Selection] */
option = "B";    // ["A", "B", "C", "board_fix", "rubber_band"]
part   = "open"; // ["open", "closed", "lid_lifting", "base"]

/* [Colors] */
// Blue, Red, Tan, Green (same Sharpie palette as the workbook)
COLORS = ["#0178d4", "#db2134", "#eab47f", "#22ab7e"];
HOLDER = "#F4F2EC";
BAR_C  = "#22272E";
BAR_2C = "#384152";
BAR_3C = "#1D3557";

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

// Flush Holder Outer Shell & Inner Locating Lip:
// - Board outer wall is [-72.8, +72.8] (145.6 x 145.6 mm).
// - Board's permanent raised outer border ridge is 4.8 mm wide: from ±68.0 mm out to ±72.8 mm!
// - Holder outer wall is ALSO [-72.8, +72.8] (145.6 x 145.6 mm) — 100% FLUSH with the board!
// - At z = z_seat, the holder's 4.8 mm perimeter rim ([-72.8, +72.8] to [-68.0, +68.0]) supports
//   the board's 4.8 mm permanent border ridge directly.
// - Inside ±68.0 mm, a 1.75 mm thick inner locating lip at ±67.65 mm (0.35 mm clearance per side)
//   rises 2.80 mm into the board's recessed cell area to lock the lid in X & Y!
H_out_hw  = B_width / 2;                              // 72.80 mm (145.6 x 145.6 mm FLUSH!)
H_bord_in = B_span / 2 - region_bar_crown_width / 2;  // 68.00 mm (inner edge of 4.8 mm board ridge)
H_lip_clr = 0.35;                                     // per-side XY clearance inside board ridge
H_lip_hw  = H_bord_in - H_lip_clr;                    // 67.65 mm (outer face of locating lip)
H_lip_t   = 1.75;                                     // thickness of inner locating lip
H_in_hw   = H_lip_hw - H_lip_t;                       // 65.90 mm (131.8 x 131.8 mm clear interior)
H_floor   = 2.0;                                      // flat solid bottom on build plate (z = 0)
H_seal_up = B_bord_h - 0.53;                          // 2.80 mm inner lip height inside board border

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
module cbox(x0, y0, z0, dx, dy, dz) {
    translate([x0, y0, z0]) cube([dx, dy, dz]);
}

module rbox_center(w, l, h, r = 0.4) {
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
module standing_main_piece(c) {
    translate([main_tile_height / 2, 0, main_w / 2])
        rotate([0, -90, 0])
            main_piece(c);
}

// Fill that turns the bottom edges of a rectangular bin [dx, dy] into smooth coves
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
        translate([g - nw / 2, -H_lip_hw - 1, z_seat - 0.1])
            cube([nw, 2 * H_lip_hw + 2, H_seal_up + 1.0]);
        translate([-H_lip_hw - 1, g - nw / 2, z_seat - 0.1])
            cube([2 * H_lip_hw + 2, nw, H_seal_up + 1.0]);
    }
}

// Flush Outer Shell shared by all 3 options:
// - Outer wall is 145.6 x 145.6 mm (100% flush with the upside-down 4x4 board!)
// - Top perimeter ledge (4.8 mm wide at z = z_seat) supports the board's 4.8 mm outer ridge
// - Inner locating lip rises 2.8 mm inside the board's ridge (with 0.35 mm clearance + top bevel)
// - Finger-lift scoops on Left (-X) and Right (+X) edges at z = z_seat to lift the board off
module holder_outer_shell(z_seat) {
    difference() {
        union() {
            // 1. Flush 145.6 x 145.6 mm outer body up to z = z_seat (with elephant-foot bevel)
            hull() {
                rbox_center(2 * (H_out_hw - elephant_foot_bevel), 2 * (H_out_hw - elephant_foot_bevel), eps, 0.2);
                translate([0, 0, elephant_foot_bevel])
                    rbox_center(2 * H_out_hw, 2 * H_out_hw, z_seat - elephant_foot_bevel, 0.2);
            }
            // 2. Inner locating lip rising 2.8 mm above z_seat (locks inside the board's 4.8 mm ridge)
            hull() {
                translate([0, 0, z_seat - eps])
                    rbox_center(2 * H_lip_hw, 2 * H_lip_hw, H_seal_up - 0.5 + eps, 1.6);
                translate([0, 0, z_seat + H_seal_up - 0.5])
                    rbox_center(2 * (H_lip_hw - 0.4), 2 * (H_lip_hw - 0.4), 0.5, 1.4);
            }
        }

        // Inner main compartment cavity [-H_in_hw, +H_in_hw] from H_floor to top
        translate([0, 0, H_floor])
            rbox_center(2 * H_in_hw, 2 * H_in_hw, z_seat + H_seal_up + 2, 1.2);

        // Finger-lift scoops on Left (-X) and Right (+X) outer ledges at z = z_seat
        for (sx = [-1, 1]) {
            translate([sx * (H_out_hw + 1), 0, z_seat + 3.5])
                rotate([0, 90, 0])
                    cylinder(d = 34, h = 10.2, center = true, $fn = 48);
        }

        // Cross-notches in the inner locating lip for installed board region bars
        board_grid_bar_clearance_cuts(z_seat);
    }
}

// Upside-down 4x4 board positioned as the flush lid
// When open_angle > 0, hinges the upside-down board open at the back edge so the viewer
// can see the 4x4 Sudoku cells & 4.8 mm black border ridge on the underside of the lid!
module upside_down_board_lid(z_seat, open_angle = 0, show_bars_in_board = true) {
    translate([0, B_width / 2, z_seat + (open_angle > 0 ? 4 : 0)])
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
// OPTION A: "Row Tackle Box" (145.6 x 145.6 x 29 mm base; Flush Board = Lid)
// ============================================================================
A_seat     = 29.0;
A_div_h    = A_seat + H_seal_up;
A_div_t    = 2.0;
A_row_w    = (2 * H_in_hw - 3 * A_div_t) / 4; // 31.45 mm row width in Y
A_slot_dx  = 17.4;
A_rib_t    = 1.6;
A_rib_h    = 11.0;
A_mains_dx = 4 * A_slot_dx + 3 * A_rib_t;     // 74.4 mm
A_bar_dx   = 11.4;                            // right-side Region Bar Vault (131.8 mm long -> fits 1x, 2x, 3x!)
A_bin_dx   = 2 * H_in_hw - A_mains_dx - A_bar_dx - 2 * A_div_t; // 42.0 mm peg bin length
A_x_mains  = -H_in_hw;
A_x_bin    = A_x_mains + A_mains_dx + A_div_t;
A_x_bar    = A_x_bin + A_bin_dx + A_div_t;
A_cove_r   = 6.0;

function A_row_y0(i)  = -H_in_hw + (3 - i) * (A_row_w + A_div_t);
function A_slot_x0(j) = A_x_mains + j * (A_slot_dx + A_rib_t);

module A_base() {
    color(HOLDER) {
        holder_outer_shell(A_seat);

        difference() {
            union() {
                for (i = [1 : 3]) {
                    y_div = -H_in_hw + i * A_row_w + (i - 1) * A_div_t;
                    cbox(-H_in_hw, y_div, H_floor - eps, A_mains_dx + A_div_t + A_bin_dx, A_div_t, A_div_h - H_floor);
                }
                cbox(A_x_bin - A_div_t, -H_in_hw, H_floor - eps, A_div_t, 2 * H_in_hw, A_div_h - H_floor);
                cbox(A_x_bar - A_div_t, -H_in_hw, H_floor - eps, A_div_t, 2 * H_in_hw, A_div_h - H_floor);

                for (i = [0 : 3], j = [1 : 3]) {
                    cbox(A_slot_x0(j) - A_rib_t, A_row_y0(i), H_floor - eps, A_rib_t, A_row_w, A_rib_h);
                }
                for (i = [0 : 3]) {
                    cbox(A_x_bin, A_row_y0(i), H_floor - eps, A_bin_dx, A_row_w, 12.1);
                    translate([A_x_bin, A_row_y0(i), H_floor + 12.0])
                        cove_fill(A_bin_dx, A_row_w, A_cove_r);
                }
            }
            for (i = [1 : 3], j = [0 : 3]) {
                y_div = -H_in_hw + i * A_row_w + (i - 1) * A_div_t + A_div_t / 2;
                xc = A_slot_x0(j) + A_slot_dx / 2;
                translate([xc, y_div, A_div_h - 4])
                    rotate([90, 0, 0])
                        cylinder(d = 12, h = A_div_t + 2, center = true, $fn = 32);
            }
            board_grid_bar_clearance_cuts(A_seat);
        }
    }

    for (i = [0 : 3]) {
        yc = A_row_y0(i) + A_row_w / 2;
        for (j = [0 : 3]) {
            xc = A_slot_x0(j) + A_slot_dx / 2;
            translate([xc, yc, H_floor - eps])
                color_pad(12, 22, COLORS[i], 2);
        }
        translate([A_x_bin + A_bin_dx / 2, yc, H_floor + 12.0 - eps])
            color_pad(A_bin_dx - 15, A_row_w - 15, COLORS[i], 3);
    }
}

module A_pieces() {
    for (i = [0 : 3]) {
        yc = A_row_y0(i) + A_row_w / 2;
        for (j = [0 : 3]) {
            xc = A_slot_x0(j) + A_slot_dx / 2;
            translate([xc, yc, H_floor + pad_h])
                standing_main_piece(COLORS[i]);
        }
        for (k = [0 : 1], a = [0 : 1], b = [0 : 3]) {
            lx = 3.2 + a * (peg_l + 1.6) + peg_l / 2 + k * 1.0;
            ly = A_row_w / 2 + (b - 1.5) * 6.3;
            d  = min(ly - peg_d / 2, A_row_w - ly - peg_d / 2);
            translate([A_x_bin + lx, A_row_y0(i) + ly,
                       H_floor + 12.0 + k * (peg_f + 0.2) + cove_lift(max(0, d), A_cove_r)])
                rotate([0, 0, (k == 0 ? 1 : -1) * 4])
                    lying_peg(COLORS[i]);
        }
    }
    // Show 3x, 2x, and 1x bars in the 131.8 mm long Region Bar Vault
    translate([A_x_bar + 2.5, 0, H_floor]) rotate([0, 0, 90]) region_bar(3, BAR_3C);
    translate([A_x_bar + 6.0, -25, H_floor]) rotate([0, 0, 90]) region_bar(2, BAR_2C);
    for (m = [0 : 2])
        translate([A_x_bar + 9.2, -42 + m * 42, H_floor]) rotate([0, 0, 90]) region_bar(1, BAR_C);
}

// ============================================================================
// OPTION B: "Four-Quadrant Flat Tray" (145.6 x 145.6 x 33.5 mm base; Flush Board = Lid)
// - 100% Flush with the 145.6 x 145.6 mm upside-down 4x4 board!
// - 4 Corner Color Quadrants matching the 4 boxes of the 4x4 board
// - Main pieces lie FLAT (face-up!) in 2 side-by-side 2-deep square wells per quadrant
// - Wide 22 mm Finger-Pinch Slots on BOTH sides of every main-piece stack (down to
//   the bottom piece!) so adult or kid fingers pull out both tiles effortlessly!
// - Full-length 131.8 mm Central Cross Vault holds:
//     * 3x Region Bars (104.5 mm) & 2x Region Bars (69.5 mm) along the X-corridor
//     * 12x 1x Jigsaw Bars (34.5 mm) in the North & South Y-arms!
// ============================================================================
B_seat       = 33.0;                   // board border seat Z (fits 2-stacked flat main pieces: 32.0 mm)
B_div_h      = B_seat + H_seal_up;     // 35.8 mm divider top
B_cross_w    = 9.8;                    // central cross channel width (holds 2 parallel rows of bars, 3 layers deep)
B_div_t      = 1.6;
B_q_min      = B_cross_w / 2 + B_div_t;// 6.50 mm from center axes
B_q_span     = H_in_hw - B_q_min;      // 59.40 x 59.40 mm clear inside each quadrant
B_well_rib   = 1.4;                    // divider rib between the 2 flat main-piece stacks
B_well_w     = (B_q_span - B_well_rib) / 2; // 29.00 x 29.00 mm flat main-piece well (28.4 mm tile + 0.6 mm clr)
B_bin_dy     = B_q_span - B_well_w - B_div_t; // 28.80 mm wide peg bin along Y
B_peg_floor  = 8.0;                    // peg floor at z = H_floor + 8.0 = 10.0 mm (exposes bottom tile's crown!)
B_cove_r     = 5.0;
B_finger_w   = 21.0;                   // 21.0 mm wide through-wall thumb & index-finger pinch windows!

// Quadrant signs: 0=TL (Blue), 1=TR (Red), 2=BL (Tan), 3=BR (Green)
B_qx = [-1,  1, -1,  1];
B_qy = [ 1,  1, -1, -1];

module B_base() {
    color(HOLDER) {
        difference() {
            union() {
                holder_outer_shell(B_seat);

                // Central cross walls forming the 4 quadrants + central bar vault
                for (s = [-1, 1]) {
                    cbox(s * (B_cross_w / 2 + B_div_t / 2) - B_div_t / 2, -H_in_hw, H_floor - eps,
                         B_div_t, 2 * H_in_hw, B_div_h - H_floor);
                    cbox(-H_in_hw, s * (B_cross_w / 2 + B_div_t / 2) - B_div_t / 2, H_floor - eps,
                         2 * H_in_hw, B_div_t, B_div_h - H_floor);
                    // Low stop-tabs at y = ±(B_cross_w/2 + B_div_t) in the Y-arms so 1x bars in the
                    // North & South arms never slide into the full-length X-corridor (where 2x & 3x bars sit)
                    cbox(-B_cross_w / 2, s * (B_cross_w / 2 + 0.4) - 0.6, H_floor - eps,
                         B_cross_w, 1.2, 22.0);
                }

                // Inside each of the 4 quadrants:
                for (q = [0 : 3]) {
                    sx = B_qx[q];
                    sy = B_qy[q];
                    x0 = sx > 0 ? B_q_min : -H_in_hw;
                    y_well0 = sy > 0 ? (H_in_hw - B_well_w) : -H_in_hw;
                    y_div0  = sy > 0 ? (y_well0 - B_div_t)  : (y_well0 + B_well_w);
                    y_bin0  = sy > 0 ? B_q_min              : (y_div0 + B_div_t);

                    // Divider between the 2 flat main wells and the peg scoop dish (stops at B_seat)
                    cbox(x0, y_div0, H_floor - eps, B_q_span, B_div_t, B_seat - H_floor);
                    // Rib between the 2 side-by-side flat main wells (stops below B_seat)
                    cbox(x0 + B_well_w, y_well0, H_floor - eps, B_well_rib, B_well_w, B_seat - H_floor - 1.0);

                    // Elevated coved floor in the peg scoop dish (at z = H_floor + 8.0 mm)
                    cbox(x0, y_bin0, H_floor - eps, B_q_span, B_bin_dy, B_peg_floor + 0.1);
                    translate([x0, y_bin0, H_floor + B_peg_floor])
                        cove_fill(B_q_span, B_bin_dy, B_cove_r);
                }
            }

            // Central X-corridor clear-through cut (keeps the full 131.8 mm X-corridor open
            // for 3x [104.5 mm] and 2x [69.5 mm] region bars!)
            cbox(-H_in_hw - 1, -B_cross_w / 2, H_floor, 2 * H_in_hw + 2, B_cross_w, B_div_h);

            // Y-arm clear-through cuts in North & South arms (each 59.4 mm long -> fits 1x [34.5 mm] bars!)
            for (sy = [-1, 1]) {
                y_arm0 = sy > 0 ? (B_cross_w / 2 + 1.2) : -H_in_hw;
                cbox(-B_cross_w / 2, y_arm0, H_floor, B_cross_w, H_in_hw - B_cross_w / 2 - 1.2, B_div_h);
            }

            // Wide 21 mm Through-Wall Thumb & Index-Finger Pinch Windows on every main-piece stack:
            // - Outer North/South wall has a 21 mm wide U-window down to z = H_floor + 7.5 mm (exposing
            //   both the top and bottom main pieces from the outside of the box for your thumb!)
            // - Inner peg-bin divider wall has a matching 21 mm wide U-window down to the peg-dish floor
            //   (z = H_floor + B_peg_floor = 10.0 mm) so your index finger reaches in from the wide peg
            //   dish to pinch either tile directly!
            for (q = [0 : 3]) {
                sx = B_qx[q];
                sy = B_qy[q];
                x0 = sx > 0 ? B_q_min : -H_in_hw;
                x_rib = x0 + B_well_w + B_well_rib / 2;
                y_well_c = sy > 0 ? (H_in_hw - B_well_w / 2) : (-H_in_hw + B_well_w / 2);
                y_div_c  = sy > 0 ? (H_in_hw - B_well_w - B_div_t / 2) : (-H_in_hw + B_well_w + B_div_t / 2);
                y_out_c  = sy > 0 ? ((H_in_hw + H_out_hw) / 2) : (-(H_in_hw + H_out_hw) / 2);

                // Low U-window between the two side-by-side wells
                hull() {
                    translate([x_rib, y_well_c, H_floor + 8.0 + B_finger_w / 2])
                        rotate([0, 90, 0]) cylinder(d = B_finger_w, h = B_well_rib + 4, center = true, $fn = 32);
                    translate([x_rib, y_well_c, B_div_h + 10])
                        rotate([0, 90, 0]) cylinder(d = B_finger_w, h = B_well_rib + 4, center = true, $fn = 32);
                }

                for (w = [0, 1]) {
                    xw = x0 + B_well_w / 2 + w * (B_well_w + B_well_rib);

                    // 1) Through-wall THUMB WINDOW in the outer North/South wall (down to z = H_floor + 7.5 mm)
                    hull() {
                        translate([xw, y_out_c, H_floor + 7.5 + B_finger_w / 2])
                            rotate([90, 0, 0]) cylinder(d = B_finger_w, h = (H_out_hw - H_in_hw) + 6, center = true, $fn = 36);
                        translate([xw, y_out_c, B_div_h + 12])
                            rotate([90, 0, 0]) cylinder(d = B_finger_w, h = (H_out_hw - H_in_hw) + 6, center = true, $fn = 36);
                    }

                    // 2) Matching INDEX-FINGER WINDOW through the peg-bin divider wall & cove
                    //    (flat bottom at z = H_floor + B_peg_floor = 10.0 mm, flush with the peg-dish floor!)
                    z_cut0 = H_floor + B_peg_floor;
                    translate([xw, y_div_c - sy * 2.5, z_cut0])
                        linear_extrude(height = B_div_h - z_cut0 + 2)
                            rounded_rect_2d(B_finger_w, B_div_t + 8.0, 2.5);
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
            xw = x0 + B_well_w / 2 + w * (B_well_w + B_well_rib);
            translate([xw, y_well_c, H_floor - eps])
                color_pad(18, 18, COLORS[q], 3);
        }
        translate([x0 + B_q_span / 2, y_bin0 + B_bin_dy / 2, H_floor + B_peg_floor - eps])
            color_pad(B_q_span - 18, B_bin_dy - 14, COLORS[q], 3);
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
            xw = x0 + B_well_w / 2 + w * (B_well_w + B_well_rib);
            translate([xw, y_well_c, H_floor + pad_h + layer * main_tile_height])
                main_piece(COLORS[q]);
        }

        // 16 loose pegs in each quadrant's coved scoop dish
        for (k = [0 : 1], a = [0 : 1], b = [0 : 3]) {
            lx = 10.5 + a * (peg_l + 4.5) + peg_l / 2 + k * 1.5;
            ly = B_bin_dy / 2 + (b - 1.5) * 6.0;
            d  = min(ly - peg_d / 2, B_bin_dy - ly - peg_d / 2);
            translate([x0 + lx, y_bin0 + ly,
                       H_floor + B_peg_floor + k * (peg_f + 0.2) + cove_lift(max(0, d), B_cove_r)])
                rotate([0, 0, (k == 0 ? 1 : -1) * 5])
                    lying_peg(COLORS[q]);
        }
    }

    // Central Cross Vault loaded with ALL 3 Region Border Lengths side-by-side:
    // 1) Long 3x region bars (104.5 mm, navy-slate) in the South lane of the full-length X-corridor
    for (layer = [0 : 2]) {
        translate([0, -2.3, H_floor + layer * 10.5])
            region_bar(3, BAR_3C);
    }
    // 2) Medium 2x region bars (69.5 mm, steel-grey) in the North lane of the full-length X-corridor
    for (layer = [0 : 2]) {
        translate([0, +2.3, H_floor + layer * 10.5])
            region_bar(2, BAR_2C);
    }
    // 3) Short 1x jigsaw bars (34.5 mm, charcoal) in the North and South Y-arms (6 per arm = 12 total)
    for (sy = [-1, 1], col = [-1, 1], layer = [0 : 2]) {
        translate([col * 2.3, sy * 36.0, H_floor + layer * 10.5])
            rotate([0, 0, 90])
                region_bar(1, BAR_C);
    }
}

// ============================================================================
// OPTION C: "Park & Count" (145.6 x 145.6 x 29 mm base; Flush Board = Lid)
// ============================================================================
C_seat      = 29.0;
C_div_h     = C_seat + H_seal_up;
C_div_t     = 2.0;
C_row_w     = (2 * H_in_hw - 3 * C_div_t) / 4; // 31.45 mm per color row
C_pock_dx   = 17.4;
C_pock_rib  = 2.2;
C_mains_dx  = 4 * C_pock_dx + 3 * C_pock_rib;  // 76.2 mm
C_peg_pitch = 7.5;
C_peg_hole  = peg_d + 0.55;
C_grid_dx   = 33.4;
C_bar_dx    = 2 * H_in_hw - C_mains_dx - C_grid_dx - 2 * C_div_t; // 18.2 mm center bar bay
C_x_mains   = -H_in_hw;
C_x_bar     = C_x_mains + C_mains_dx + C_div_t;
C_x_grid    = C_x_bar + C_bar_dx + C_div_t;
C_deck_z    = H_floor + 19.5;

function C_row_y0(i)  = -H_in_hw + (3 - i) * (C_row_w + C_div_t);
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
                for (i = [1 : 3]) {
                    y_div = -H_in_hw + i * C_row_w + (i - 1) * C_div_t;
                    cbox(-H_in_hw, y_div, H_floor - eps, C_mains_dx, C_div_t, C_div_h - H_floor);
                    cbox(C_x_grid, y_div, H_floor - eps, C_grid_dx,  C_div_t, C_div_h - H_floor);
                }
                cbox(C_x_bar - C_div_t,  -H_in_hw, H_floor - eps, C_div_t, 2 * H_in_hw, C_div_h - H_floor);
                cbox(C_x_grid - C_div_t, -H_in_hw, H_floor - eps, C_div_t, 2 * H_in_hw, C_div_h - H_floor);

                for (i = [0 : 3], j = [1 : 3]) {
                    cbox(C_pock_x0(j) - C_pock_rib, C_row_y0(i), H_floor - eps,
                         C_pock_rib, C_row_w, C_div_h - H_floor - 4);
                }
                cbox(C_x_grid, -H_in_hw, H_floor - eps, C_grid_dx, 2 * H_in_hw, C_deck_z - H_floor);
            }

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

    for (i = [0 : 3]) {
        yc = C_row_y0(i) + C_row_w / 2;
        for (j = [0 : 3]) {
            xc = C_pock_x0(j) + C_pock_dx / 2;
            translate([xc, yc, H_floor - eps])
                color_pad(12, 22, COLORS[i], 2);
        }
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
    translate([C_x_bar + 4.0, 0, H_floor]) rotate([0, 0, 90]) region_bar(3, BAR_3C);
    translate([C_x_bar + 9.0, -25, H_floor]) rotate([0, 0, 90]) region_bar(2, BAR_2C);
    for (m = [0 : 2]) {
        translate([C_x_bar + 14.0, -42 + m * 42, H_floor])
            rotate([0, 0, 90])
                region_bar(1, BAR_C);
    }
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
// Board Fix & Rubber-Band Notch Showcase Scenes
// ============================================================================
module board_fix_showcase() {
    monolithic_board(4, border_color = BAR_C);
    translate([1.0 * cell_pitch, 2.0 * cell_pitch, slot_floor_z])
        region_bar(2, BAR_C);
    translate([3.0 * cell_pitch, 2.0 * cell_pitch, slot_floor_z])
        region_bar(2, BAR_C);
    translate([2.0 * cell_pitch, 3.0 * cell_pitch, slot_floor_z])
        rotate([0, 0, 90]) region_bar(2, BAR_C);
    translate([2.0 * cell_pitch, 1.0 * cell_pitch, slot_floor_z + 18])
        rotate([0, 0, 90]) color("#FF9F1C") region_bar(2, "#FF9F1C");
    translate([0.5 * cell_pitch, 3.0 * cell_pitch, slot_floor_z])
        region_bar(1, BAR_C);
}

// Close-up of main_piece and pencil_peg showing the deep rubber-band notches
// (left pair: bare notch profile; right pair: with rubber band seated in the notch!)
module rubber_band_showcase() {
    // 1. Bare main_piece showing the deep 1.25 mm x 2.6 mm rubber-band channel
    translate([-22, 0, 0]) main_piece(COLORS[0], "1");

    // 2. Main_piece with a tactile rubber band seated in the channel
    translate([22, 0, 0]) {
        main_piece(COLORS[1], "2");
        color("#E07A5F")
            translate([0, 0, 11.75])
                linear_extrude(height = 1.5)
                    difference() {
                        rounded_rect_2d(tile_crown_w + 0.7, tile_crown_w + 0.7, 4.0);
                        rounded_rect_2d(tile_crown_w - 2.4, tile_crown_w - 2.4, 2.8);
                    }
    }

    // 3. Bare pencil_peg showing the deep 0.95 mm x 2.6 mm rubber-band notch
    translate([-12, -26, 0]) pencil_peg(COLORS[0], "1");

    // 4. Pencil_peg with a tactile rubber band seated in the notch
    translate([12, -26, 0]) {
        pencil_peg(COLORS[1], "2");
        color("#E07A5F")
            translate([0, 0, 12.15])
                linear_extrude(height = 1.3)
                    difference() {
                        octagon_2d(peg_eff_flat_d + 0.5);
                        octagon_2d(peg_eff_flat_d - 1.8);
                    }
    }
}

// ============================================================================
// Dispatcher
// ============================================================================
module show(opt, prt) {
    if (opt == "board_fix") {
        board_fix_showcase();
    } else if (opt == "rubber_band") {
        rubber_band_showcase();
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
