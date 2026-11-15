// ============================================================================
// 4x4 Kids' Sudoku: Piece Holder / Carry Case (3 design options)
// Holds 4 colors x (4 main pieces + 16 pencil-mark pegs), separated by color
// AND by piece type, with a lid so nothing falls out when carried.
//
// Re-uses the REAL piece geometry from ../../src/color_sudoku_board.scad, so
// every pocket is sized from the same parameters as the pieces themselves.
//
//   option A = "Tackle Box"   : 4 color rows, main pockets + coved peg scoop bin,
//                                sliding lid with click detent
//   option B = "Color Wheel"  : round; mains stand in rim slots, 4 dished peg
//                                wedges in the middle, quarter-turn twist lid
//   option C = "Park & Count" : every piece has its own home (4x4 peg holes like
//                                the board + main pockets), snap-on lid
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
part   = "open"; // ["open", "closed", "base", "lid"]

/* [Colors] */
// Blue, Red, Tan, Green (same Sharpie palette as the workbook)
COLORS = ["#0178d4", "#db2134", "#eab47f", "#22ab7e"];
HOLDER = "#F4F2EC";
LIDC   = "#D9E3EC";

$fn = 48;

// ---------------------------------------------------------------------------
// Piece envelope (derived from the board file)
// ---------------------------------------------------------------------------
main_w = tile_base_w;             // 28.4 mm square plinth
main_h = main_tile_height + 0.8;  // 16.8 mm incl. optional raised label
peg_d  = peg_circum_d;            // 6.28 mm across octagon corners
peg_f  = peg_eff_flat_d;          // 5.8 mm across flats
peg_l  = peg_height + 0.6;        // 16.6 mm incl. optional raised label
pad_h  = 0.6;                     // raised paint-marker color pads

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

// Fill that turns the bottom edges of a box-shaped bin into smooth coves,
// so fingers can sweep pegs up the curved wall instead of digging in corners.
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

// ============================================================================
// OPTION A: "Tackle Box" (172 x 133 x 25 mm) with sliding lid
// ============================================================================
A_wall  = 3.2;              // side walls carry the lid grooves
A_floor = 2.0;
A_div   = 2.0;              // full-height color divider
A_cell  = main_w + 1.8;     // main pocket (0.9 mm per side)
A_rib   = 1.6;              // low rib between main pockets (counting aid)
A_rib_h = 5.0;
A_bin   = 38.0;             // peg scoop bin length
A_cove  = 6.0;              // cove radius in peg bins
A_ix    = 4 * A_cell + 3 * A_rib + A_div + A_bin;
A_iy    = 4 * A_cell + 3 * A_div;
A_ih    = main_h + pad_h + 0.6;     // divider height above floor
A_lid_t = 2.2;
A_gap   = 0.4;              // lid underside to divider tops (pegs can't hop)
A_gd    = 1.6;              // lid groove depth into walls
A_lip   = 1.6;
A_gz    = A_floor + A_ih + A_gap;   // lid bottom face
A_oh    = A_gz + A_lid_t + 0.3 + A_lip;
A_ox    = A_ix + 2 * A_wall;
A_oy    = A_iy + 2 * A_wall;
A_bin_x = A_wall + 4 * A_cell + 3 * A_rib + A_div;
function A_row_y(i)  = A_wall + i * (A_cell + A_div);
function A_cell_x(j) = A_wall + j * (A_cell + A_rib);

module A_base() {
    color(HOLDER) difference() {
        rbox(A_ox, A_oy, A_oh, 4);
        translate([A_wall, A_wall, A_floor]) cube([A_ix, A_iy, A_oh]);
        // lid groove on 3 sides, open at +X end
        translate([A_wall - A_gd, A_wall - A_gd, A_gz])
            cube([A_ix + A_wall + A_gd + 1, A_iy + 2 * A_gd, A_lid_t + 0.3]);
        // +X end wall stops at the groove so the lid slides in over it
        translate([A_wall + A_ix - 1, A_wall, A_gz]) cube([A_wall + 2, A_iy, A_oh]);
        // click-detent dimple across the end wall top
        translate([A_ox - A_wall / 2, A_wall + 12, A_gz])
            rotate([-90, 0, 0]) cylinder(r = 0.7, h = A_iy - 24, $fn = 16);
    }
    color(HOLDER) {
        for (i = [1:3]) translate([A_wall, A_row_y(i) - A_div, 0]) cube([A_ix, A_div, A_floor + A_ih]);
        translate([A_bin_x - A_div, A_wall, 0]) cube([A_div, A_iy, A_floor + A_ih]);
        for (i = [0:3], j = [1:3])
            translate([A_cell_x(j) - A_rib, A_row_y(i), 0]) cube([A_rib, A_cell, A_floor + A_rib_h]);
        for (i = [0:3]) translate([A_bin_x, A_row_y(i), A_floor - 0.01]) cove_fill(A_bin, A_cell, A_cove);
    }
    // paint pads: "put the blue piece on the blue spot"
    for (i = [0:3], j = [0:3])
        translate([A_cell_x(j) + A_cell / 2, A_row_y(i) + A_cell / 2, A_floor - 0.01])
            color_pad(18, 18, COLORS[i]);
    // pad on the inside of the end wall of each peg bin
    for (i = [0:3])
        translate([A_wall + A_ix + 0.01, A_row_y(i) + A_cell / 2, A_floor + A_cove + (A_ih - A_cove) / 2])
            rotate([0, -90, 0]) color_pad(A_ih - A_cove - 3, A_cell - 8, COLORS[i], 2);
    // matching pads on the outside of the end wall (visible with lid on)
    for (i = [0:3])
        translate([A_ox - 0.01, A_row_y(i) + A_cell / 2, A_gz / 2])
            rotate([0, 90, 0]) color_pad(A_gz - 6, A_cell - 6, COLORS[i], 2);
}

module A_lid() {
    lx = A_ix + A_wall + A_gd - 0.3;
    ly = A_iy + 2 * A_gd - 0.6;
    t  = A_lid_t;
    translate([A_wall - A_gd + 0.3, A_wall - A_gd + 0.3, A_gz + 0.15]) {
        color(LIDC) {
            cube([lx, ly, t]);
            // thumb grip ridges at the pull end
            for (k = [0:4]) translate([lx - 6 - k * 3.2, ly / 2 - 30, t - 0.01]) cube([1.4, 60, 1.0]);
            // click detent bump (drops into the end-wall dimple)
            translate([lx - A_wall / 2 - 0.3 + 0.3, 12 + A_gd - 0.3, 0.01])
                rotate([-90, 0, 0]) difference() {
                    cylinder(r = 0.55, h = ly - 24 - 2 * A_gd, $fn = 16);
                    translate([-1, -2, -1]) cube([2, 2, ly]);
                }
        }
        // color dots on the lid, one over each row
        for (i = [0:3])
            translate([14, A_row_y(i) - (A_wall - A_gd + 0.3) + A_cell / 2, t - 0.01])
                color(COLORS[i]) cylinder(d = 14, h = pad_h);
    }
}

module A_pieces() {
    for (i = [0:3]) {
        for (j = [0:3])
            translate([A_cell_x(j) + A_cell / 2, A_row_y(i) + A_cell / 2, A_floor + pad_h])
                main_piece(COLORS[i]);
        // 16 loose pegs per bin, two layers
        for (k = [0:1], a = [0:1], b = [0:3]) {
            px = A_bin + 0; py = A_cell;
            lx = 1.6 + a * (peg_l + 1.2) + peg_l / 2 + k * 1.5;
            ly = py / 2 + (b - 1.5) * 6.4 + k * 1.6;
            d  = min(ly - peg_d / 2, py - ly - peg_d / 2);
            translate([A_bin_x + lx, A_row_y(i) + ly,
                       A_floor + k * (peg_f + 0.2) + cove_lift(max(0, d), A_cove)])
                rotate([0, 0, (k == 0 ? 0 : 1) * (a == 0 ? 6 : -5) + (b - 1.5) * 1.5])
                    lying_peg(COLORS[i]);
        }
    }
}

// ============================================================================
// OPTION B: "Color Wheel" (dia 169 x 34 mm) with quarter-turn twist lid
// ============================================================================
B_floor  = 2.0;
B_Rb     = 48.4;               // central peg bowl radius
B_R1     = 50.0;               // inner end of main-piece slots
B_slot_l = main_w + 1.0;       // radial
B_slot_w = main_h + 0.8;       // tangential (piece stands on edge)
B_R2     = B_R1 + B_slot_l;
B_Ro     = B_R2 + 2.6;         // outer wall
B_H      = B_floor + 22;       // wall top: mains stick up 6.4 mm to pinch
B_top    = B_floor + 0.4 + main_w + 0.8; // lid ceiling
B_dishR  = 45;
B_dishC  = 4 * B_Rb / (3 * PI) * sqrt(2); // wedge centroid distance
B_fill   = B_floor + 12;
B_lug_z0 = B_H - 8;
B_lug_h  = 3.0;
B_lug_w  = 10;
B_turn   = 24;                 // lock rotation (deg)
function B_ang(q, k) = 90 * q + 11.25 + 22.5 * k;
function B_dish_z(d) = B_floor + B_dishR - sqrt(B_dishR * B_dishR - d * d);

module B_base() {
    color(HOLDER) difference() {
        cylinder(r = B_Ro, h = B_H, $fn = 180);
        translate([0, 0, B_floor]) cylinder(r = B_Rb, h = B_H, $fn = 160);
        for (q = [0:3], k = [0:3])
            rotate(B_ang(q, k)) translate([B_R1, -B_slot_w / 2, B_floor]) cube([B_slot_l, B_slot_w, B_H]);
    }
    color(HOLDER) {
        // color dividers (cross)
        for (a = [0, 90]) rotate(a) translate([-B_Rb - 0.1, -1, 0]) cube([2 * B_Rb + 0.2, 2, B_H]);
        // dished floor in each peg wedge: pegs slide to the middle of the wedge
        difference() {
            cylinder(r = B_Rb + 0.05, h = B_fill, $fn = 160);
            for (q = [0:3]) rotate(90 * q + 45)
                translate([B_dishC, 0, B_floor + B_dishR]) sphere(B_dishR, $fn = 96);
        }
        // bayonet lugs
        for (a = [0, 120, 240]) rotate(a)
            translate([B_Ro - 0.5, -B_lug_w / 2, B_lug_z0]) cube([2.1, B_lug_w, B_lug_h]);
    }
    // color bands around the outside + spots at the bottom of each peg dish
    for (q = [0:3]) {
        rotate(90 * q + 2) color(COLORS[q])
            rotate_extrude(angle = 86, $fn = 180) translate([B_Ro - 0.01, 3]) square([pad_h, 8]);
        rotate(90 * q + 45) translate([B_dishC, 0, B_floor - 0.3]) color(COLORS[q]) cylinder(d = 14, h = 0.9);
    }
}

module B_lid(turned = 0) {
    ri = B_Ro + 0.35; ro = ri + 2.4; zb = B_H - 10; t = 2.4;
    rotate(turned) {
        color(LIDC) difference() {
            translate([0, 0, zb]) cylinder(r = ro, h = B_top + t - zb, $fn = 180);
            translate([0, 0, zb - 1]) cylinder(r = ri, h = B_top - zb + 1, $fn = 180);
            for (a = [0, 120, 240]) rotate(a) {
                // vertical entry
                translate([ri - 1, -(B_lug_w / 2 + 0.5), zb - 1])
                    cube([5, B_lug_w + 1, B_lug_z0 + B_lug_h + 0.4 - zb + 1]);
                // horizontal locking run
                rotate(-9) translate([0, 0, B_lug_z0 - 0.3])
                    rotate_extrude(angle = B_turn + 18, $fn = 180)
                        translate([ri - 1, 0]) square([5, B_lug_h + 0.7]);
            }
        }
        color(LIDC) {
            // underside ribs seal the peg bowl and the 4 wedges
            difference() {
                translate([0, 0, B_H + 0.4]) cylinder(r = 49.8, h = B_top - B_H, $fn = 160);
                translate([0, 0, B_H]) cylinder(r = 48.6, h = B_top, $fn = 160);
            }
            for (a = [0, 90]) rotate(a) translate([-48.6, -0.8, B_H + 0.4]) cube([97.2, 1.6, B_top - B_H]);
            // grip knurls on the skirt
            for (a = [0:10:359]) rotate(a + 5) translate([ro - 0.4, -0.8, zb + 1]) cube([1.2, 1.6, B_top + t - zb - 2]);
        }
        // quarter color pads on the top (match the wedges underneath)
        for (q = [0:3]) rotate(90 * q + 4) color(COLORS[q]) translate([0, 0, B_top + t - 0.01])
            rotate_extrude(angle = 82, $fn = 120) translate([20, 0]) square([50, pad_h]);
    }
}

module B_pieces() {
    for (q = [0:3]) {
        for (k = [0:3])
            rotate(B_ang(q, k)) translate([B_R1 + B_slot_l / 2, 0, B_floor + 0.4 + main_w / 2])
                rotate([90, 0, 0]) translate([0, 0, -main_h / 2]) main_piece(COLORS[q]);
        // 16 loose pegs in the dish
        rotate(90 * q + 45) translate([B_dishC, 0, 0])
            for (k = [0:1], a = [0:1], b = [0:3]) {
                x = (b - 1.5) * 6.5 + k * 2.0;
                y = (a - 0.5) * (peg_l + 1.0) + k * 2.5;
                translate([x, y, B_dish_z(sqrt(x * x + y * y)) + k * (peg_f + 0.2)])
                    rotate([0, 0, 90 + (k == 0 ? 0 : (a == 0 ? 10 : -8))]) lying_peg(COLORS[q]);
            }
    }
}

// ============================================================================
// OPTION C: "Park & Count" (174 x 165 x 23 mm) with snug friction-fit lid
// ============================================================================
C_deck    = 8.0;            // deck top
C_pocket  = main_w + 1.0;   // same 0.5 mm clearance as a board cell
C_pdepth  = 4.5 + pad_h;    // same wall engagement as the board (+ paint pad)
C_pg      = 2.0;            // gap between main pockets
C_pitch   = 9.5;            // peg hole pitch
C_hole    = peg_d + 0.6;
C_hdepth  = peg_socket_depth; // same 6.2 mm as the board
C_grid    = 3 * C_pitch + C_hole;
C_m       = 4.8;            // edge margin (leaves room for colored ring around mains)
C_gap     = 5.0;            // between pockets and peg grid
C_row     = 40.0;           // row pitch
C_main_w  = 4 * C_pocket + 3 * C_pg;
C_ox      = C_m + C_main_w + C_gap + C_grid + C_m;
C_oy      = C_m + 3 * C_row + C_grid + C_m;
C_neck_z  = 3.0;            // lid skirt comes down to here
C_inset   = 2.2;            // neck inset (lid skirt thickness + clearance)
C_lid_clr = 0.15;           // per-side friction-fit clearance (snug, no snap)
C_ceil    = C_deck + 13.0;  // lid ceiling
C_lid_t   = 2.2;
function C_row_y(i)    = C_m + (3 - i) * C_row + C_grid / 2; // row center, blue at the back
function C_pocket_x(j) = C_m + C_pocket / 2 + j * (C_pocket + C_pg);
C_grid_x0 = C_m + C_main_w + C_gap;
function C_hole_xy(i, a, b) = [C_grid_x0 + C_hole / 2 + a * C_pitch, C_row_y(i) - C_grid / 2 + C_hole / 2 + b * C_pitch];

module C_base() {
    color(HOLDER) difference() {
        union() {
            rbox(C_ox, C_oy, C_neck_z, 4);
            // Neck with slight top bevel for smooth lid seating
            translate([C_inset, C_inset, 0]) rbox(C_ox - 2 * C_inset, C_oy - 2 * C_inset, C_deck - 0.4, 2);
            hull() {
                translate([C_inset, C_inset, C_deck - 0.41])
                    rbox(C_ox - 2 * C_inset, C_oy - 2 * C_inset, 0.01, 2);
                translate([C_inset + 0.3, C_inset + 0.3, C_deck - 0.01])
                    rbox(C_ox - 2 * (C_inset + 0.3), C_oy - 2 * (C_inset + 0.3), 0.01, 1.8);
            }
        }
        // main pockets
        for (i = [0:3], j = [0:3])
            translate([C_pocket_x(j), C_row_y(i), C_deck - C_pdepth])
                linear_extrude(C_pdepth + 1) rounded_rect_2d(C_pocket, C_pocket, 2.6);
        // peg holes with lead-in chamfer
        for (i = [0:3], a = [0:3], b = [0:3]) translate(concat(C_hole_xy(i, a, b), [0])) {
            translate([0, 0, C_deck - C_hdepth]) cylinder(d = C_hole, h = C_hdepth + 1);
            translate([0, 0, C_deck - 0.8]) cylinder(d1 = C_hole, d2 = C_hole + 1.8, h = 0.81);
        }
        // thumb scoop under the lid edge (front)
        intersection() {
            translate([C_ox / 2, 0, C_neck_z]) scale([1, 0.45, 0.4]) sphere(14);
            translate([0, -1, -1]) cube([C_ox, C_oy, C_neck_z + 1]);
        }
    }
    for (i = [0:3]) {
        for (j = [0:3]) translate([C_pocket_x(j), C_row_y(i), C_deck - C_pdepth - 0.01])
            color_pad(18, 18, COLORS[i]);
        // colored "home" frame around each main-piece row
        translate([C_m + C_main_w / 2, C_row_y(i), C_deck - 0.01]) color(COLORS[i])
            linear_extrude(pad_h) difference() {
                rounded_rect_2d(C_main_w + 3.6, C_pocket + 3.6, 3);
                rounded_rect_2d(C_main_w + 1.2, C_pocket + 1.2, 2);
            }
        // colored "home" frame around each peg grid
        translate([C_grid_x0 + C_grid / 2, C_row_y(i), C_deck - 0.01]) color(COLORS[i])
            linear_extrude(pad_h) difference() {
                rounded_rect_2d(C_grid + 3.6, C_grid + 3.6, 3);
                rounded_rect_2d(C_grid + 1.2, C_grid + 1.2, 2);
            }
    }
}

module C_lid() {
    zb = C_neck_z + 0.2;
    color(LIDC) difference() {
        translate([0, 0, zb]) rbox(C_ox, C_oy, C_ceil + C_lid_t - zb, 4);
        translate([C_inset - C_lid_clr, C_inset - C_lid_clr, zb - 1])
            rbox(C_ox - 2 * (C_inset - C_lid_clr), C_oy - 2 * (C_inset - C_lid_clr), C_ceil - zb + 1, 2.2);
    }
    for (i = [0:3]) translate([C_ox / 2, C_row_y(i), C_ceil + C_lid_t - 0.01])
        color_pad(C_ox - 30, 10, COLORS[i], 5);
}

module C_pieces(missing = true) {
    for (i = [0:3]) {
        for (j = [0:3]) if (!(missing && i == 3 && j == 3))
            translate([C_pocket_x(j), C_row_y(i), C_deck - C_pdepth + pad_h]) main_piece(COLORS[i]);
        for (a = [0:3], b = [0:3]) if (!(missing && i == 3 && (a + b * 4) >= 11))
            translate(concat(C_hole_xy(i, a, b), [C_deck - C_hdepth])) pencil_peg(COLORS[i]);
    }
    // the "missing" green pieces waiting on the table in front of the case
    if (missing) {
        translate([C_ox - 30, -28, 0]) main_piece(COLORS[3]);
        for (k = [0:4]) translate([C_ox - 75 + k * 9, -22 - (k % 2) * 8, 0])
            rotate([0, 0, 20 * k]) lying_peg(COLORS[3]);
    }
}

// ============================================================================
// Dispatcher
// ============================================================================
module show(opt, prt) {
    if (opt == "A") {
        if (prt == "base") A_base();
        else if (prt == "lid") translate([0, 0, -(A_gz + 0.15)]) A_lid();
        else if (prt == "closed") { A_base(); A_lid(); }
        else { A_base(); A_pieces(); }
    } else if (opt == "B") {
        if (prt == "base") B_base();
        else if (prt == "lid") translate([0, 0, B_top + 2.4]) rotate([180, 0, 0]) B_lid();
        else if (prt == "closed") { B_base(); B_lid(-B_turn); }
        else { B_base(); B_pieces(); }
    } else if (opt == "C") {
        if (prt == "base") C_base();
        else if (prt == "lid") translate([0, 0, C_ceil + C_lid_t]) rotate([180, 0, 0]) C_lid();
        else if (prt == "closed") { C_base(); C_lid(); }
        else { C_base(); C_pieces(); }
    }
}

show(option, part);
