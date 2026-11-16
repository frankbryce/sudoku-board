// ============================================================================
// Modular Color Sudoku System — Montessori Jigsaw 1x1 Tile Edition
// Target Printer: Bambu Lab A1 Mini (180 x 180 x 180 mm build volume)
// Material: White PLA / PLA Matte (15% Gyroid infill recommended)
// ============================================================================
//
// PRINT MANIFEST (Modular 1x1 Jigsaw Tile System — Any Grid Size MxN, Flush Outer Perimeter):
//   - tile_center    ((M-2)x(N-2); 49x for 9x9, 4x for 4x4): Interior tile (S & E slots + tabs, N & W sockets).
//   - tile_edge_n    (M-2; 7x for 9x9, 2x for 4x4)         : Top edge (flush solid N wall, S slot + tab, E slot + tab, W socket).
//   - tile_edge_s    (M-2; 7x for 9x9, 2x for 4x4)         : Bottom edge (flush solid S wall, E slot + tab, N & W sockets).
//   - tile_edge_w    (N-2; 7x for 9x9, 2x for 4x4)         : Left edge (flush solid W wall, S & E slots + tabs, N socket).
//   - tile_edge_e    (N-2; 7x for 9x9, 2x for 4x4)         : Right edge (flush solid E wall, S slot + tab, N & W sockets).
//   - tile_corner_nw (1x)                                  : Top-Left corner (flush solid N & W walls, S & E slots + tabs).
//   - tile_corner_ne (1x)                                  : Top-Right corner (flush solid N & E walls, S slot + tab, W socket).
//   - tile_corner_sw (1x)                                  : Bottom-Left corner (flush solid S & W walls, E slot + tab, N socket).
//   - tile_corner_se (1x)                                  : Bottom-Right corner (flush solid S & E walls, N & W sockets).
//   - board_4x4      (1x monolithic 145.6x145.6 mm)        : Single-piece 4x4 board with flush solid outer walls & captured interior slots.
//   - main_piece     (x81 for 9x9, x16 for 4x4)            : Solved tile with raised flat paint pad.
//   - pencil_peg     (x144 for 9x9, x64 for 4x4)           : Octagonal candidate peg with raised flat paint cap.
//   - region_bar_1x / 2x / 3x                              : Mitered interior box dividers with raised flat paint ridge.
// ============================================================================

/* [Render Selection] */
// Select which part to preview / export:
render_mode = "assembly_preview"; // ["assembly_preview", "full_board_preview", "board_4x4", "tile_center", "tile_edge_n", "tile_edge_s", "tile_edge_w", "tile_edge_e", "tile_corner_nw", "tile_corner_ne", "tile_corner_sw", "tile_corner_se", "main_piece", "pencil_peg", "region_bar_1x", "region_bar_2x", "region_bar_3x"]

// Optional raised character on main_piece / pencil_peg ("" = blank, "1"-"9", "A"-"I")
piece_label = ""; // ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I"]

// Central pencil-mark layout ("2x2" = 4 wide-spaced holes for 6yo fingers; "3x2" = 6 holes for dense CTC puzzles)
center_mark_mode = "2x2"; // ["2x2", "3x2"]

/* [Board & Grid Dimensions — Compact 2/3 Scale (~35 mm Pitch)] */
// Center-to-center cell pitch (35 mm -> ~315 mm 9x9 board, ~2/3 of 50 mm original)
cell_pitch = 35.0;
// Base floor thickness (8.0 mm gives 8x bending stiffness & carries 6.2 mm deep anti-tip sockets!)
base_thickness = 8.0;
// Height of cell divider walls above the cell floor (holds 3.8 mm tile plinth securely)
wall_height = 4.5;

/* [Deep Anti-Tip Region Line Slot & Bar Dimensions (mm)] */
// Width of monolithic grid-line groove for changeable region bars
region_slot_width = 3.0;
// Depth of region-line groove (7.0 mm -> <3.1 deg wobble; geometrically impossible to tip sideways!)
region_slot_depth = 7.0;
// Thickness of solid wall flanking each side of a region-line groove
slot_wall_thickness = 1.3;
// Width of upper visible crown of region bar (sits proud above walls)
region_bar_crown_width = 4.0;
// Height of upper crown above the cell wall top
region_bar_crown_height = 2.4;

/* [Full-Cell Solved Piece & Deep Anti-Tip Peg Dimensions (mm)] */
// Visible top crown width of solved piece
main_tile_crown_width = 25.8;
// Total height of chunky solved tile (3.8 mm deep plinth + elevated finger scoop)
main_tile_height = 16.0;
// Depth of framed central candidate zone recess on cell floor
center_zone_recess_depth = 0.5;

// Across-flats width of non-rolling octagonal pencil-mark peg
peg_flat_diameter = 5.8;
// Total height of pencil-mark peg (6.2 mm buried in socket + 9.8 mm proud grip)
peg_height = 16.0;
// Depth of corner pencil-mark sockets into the 8.0 mm base (leaves 1.8 mm = 9 solid layers underneath)
peg_socket_depth = 6.2;

/* [FDM Clearances & Tolerances (mm)] */
// Per-side XY clearance on Montessori spring-slotted jigsaw tabs (easy kid pull-apart)
dovetail_clearance = 0.25;
// Per-side clearance on region-line bars inside deep slots (smooth zero-bind slip fit)
region_bar_clearance = 0.18;
// Per-side clearance of main tile's self-centering base plinth inside cell walls
tile_wall_clearance = 0.50;
// Radial clearance around octagonal peg corners inside round socket (loose gravity lift, <5.6 deg tilt)
peg_radial_clearance = 0.25;
// First-layer elephant-foot bevel inset on z=0 mating edges
elephant_foot_bevel = 0.40;

/* [Resolution] */
$fn = 48;

// ============================================================================
// Derived Geometric Constants (Do Not Edit Directly)
// ============================================================================
eps = 0.02;
total_plate_h = base_thickness + wall_height; // 12.5 mm (~0.5 inch rigid board)

// Half-width of a complete monolithic divider assembly (slot + 2 walls)
divider_hw = region_slot_width / 2 + slot_wall_thickness; // 3.2 mm default

// Open interior width of every cell
cell_open_w = cell_pitch - 2 * divider_hw; // 43.6 mm default

// Self-centering base plinth of main_piece (drops inside cell_open_w walls)
tile_base_w = cell_open_w - 2 * tile_wall_clearance; // 28.4 mm default
tile_crown_w = min(main_tile_crown_width, tile_base_w); // 25.8 mm default
tile_waist_w = tile_crown_w - 4.4; // 21.4 mm -> 2.2 mm 45-deg finger-hook lip per side

// Circumscribed diameter across corners of an octagon with given flat-to-flat width
peg_eff_flat_d = (center_mark_mode == "3x2") ? min(peg_flat_diameter, 5.4) : peg_flat_diameter;
peg_circum_d = peg_eff_flat_d / cos(22.5);
peg_socket_d = peg_circum_d + 2 * peg_radial_clearance;

// Framed central CTC candidate zone dimensions
center_zone_x = (center_mark_mode == "3x2") ? 21.6 : 16.8;
center_zone_y = (center_mark_mode == "3x2") ? 15.6 : 16.8;

// Corner pencil-mark offset from cell center
corner_mark_offset = cell_open_w / 2 - peg_socket_d / 2 - 1.15; // ~10.16 mm

// Montessori Vaulted Spring-Clip Jigsaw Dovetail parameters
dovetail_depth = 4.6;
dovetail_neck_w = 7.6;
dovetail_head_w = 10.2;
dovetail_h = 6.20;          // blind height inside 8.0 mm base (leaves solid roof above!)
dovetail_vault_h = 1.20;    // 45-deg self-centering top taper
dovetail_detent_z = 2.50;   // mid-height Z-retention click ridge
dovetail_detent_r = 0.26;   // gentle click protrusion (flexes into center slot)
dovetail_slot_w = 1.50;     // center flex slot in male tab for easy kid assembly

// Region bar derived dimensions
slot_floor_z = total_plate_h - region_slot_depth; // 5.5 mm solid floor underneath!
bar_tongue_w = region_slot_width - 2 * region_bar_clearance;
bar_tongue_h = region_slot_depth + 0.25; // keeps crown 0.25 mm clear above wall posts
bar_bevel_h = (region_bar_crown_width - bar_tongue_w) / 2; // 45-deg print-safe slope

// ============================================================================
// 2D / 3D Helper Primitives
// ============================================================================

module rounded_rect_2d(w, h, r) {
    cr = min(r, min(w, h) / 2 - 0.05);
    offset(r = cr)
        square([w - 2 * cr, h - 2 * cr], center = true);
}

// Regular octagon 2D with specified flat-to-flat width
module octagon_2d(flat_d) {
    circum_r = (flat_d / 2) / cos(22.5);
    rotate([0, 0, 22.5])
        circle(r = circum_r, $fn = 8);
}

// Trapezoidal dovetail 2D profile extending from y = -overlap to y = depth
module dovetail_2d(extra_offset = 0, overlap = 1.2) {
    pts = [
        [-dovetail_neck_w / 2 - extra_offset, -overlap],
        [ dovetail_neck_w / 2 + extra_offset, -overlap],
        [ dovetail_head_w / 2 + extra_offset,  dovetail_depth + extra_offset],
        [-dovetail_head_w / 2 - extra_offset,  dovetail_depth + extra_offset]
    ];
    offset(r = 0.6)
        offset(r = -0.6)
            polygon(pts);
}

// Montessori Slotted Spring-Clip Male Dovetail (extends in -Y from y = 0)
// - Blind 6.2 mm height with 45-deg self-centering top vault
// - 1.5 mm center flex slot + gentle Z=2.5 mm click ridge holds board flat when lifted
module male_dovetail_south() {
    z_straight = dovetail_h - dovetail_vault_h; // 5.0 mm
    det_half_h = 0.70;

    mirror([0, 1, 0]) {
        difference() {
            union() {
                // Main dovetail body with elephant-foot bevel
                hull() {
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = -elephant_foot_bevel, overlap = 1.4);
                    translate([0, 0, elephant_foot_bevel])
                        linear_extrude(height = z_straight - elephant_foot_bevel)
                            dovetail_2d(extra_offset = 0, overlap = 1.4);
                }
                // 45-deg self-centering top vault (z = 5.0 to 6.2 mm)
                hull() {
                    translate([0, 0, z_straight - eps])
                        linear_extrude(height = eps)
                            dovetail_2d(extra_offset = 0, overlap = 1.4);
                    translate([0, 0, dovetail_h - eps])
                        linear_extrude(height = eps)
                            dovetail_2d(extra_offset = -dovetail_vault_h, overlap = 1.4);
                }
                // Gentle mid-height Z-retention click ridge (z = 2.5 mm)
                hull() {
                    translate([0, 0, dovetail_detent_z - det_half_h])
                        linear_extrude(height = eps)
                            dovetail_2d(extra_offset = 0, overlap = 0.6);
                    translate([0, 0, dovetail_detent_z])
                        linear_extrude(height = eps)
                            dovetail_2d(extra_offset = dovetail_detent_r, overlap = 0.6);
                    translate([0, 0, dovetail_detent_z + det_half_h])
                        linear_extrude(height = eps)
                            dovetail_2d(extra_offset = 0, overlap = 0.6);
                }
            }

            // Center compliant flex slot so lobes flex inward easily for kids
            translate([-dovetail_slot_w / 2, 0.4, -eps])
                cube([dovetail_slot_w, dovetail_depth + 1.0, dovetail_h + 2 * eps]);
        }
    }
}

// Vaulted Blind-Roof Female Dovetail Socket (cuts in -Y from y = 0; leaves 1.55 mm solid roof!)
module female_dovetail_cut_from_north() {
    z_roof_start = dovetail_h - dovetail_vault_h + 0.25; // 5.25 mm
    z_roof_top   = dovetail_h + 0.25;                     // 6.45 mm (leaves 1.55 mm solid floor above!)
    det_half_h   = 0.75;

    mirror([0, 1, 0]) {
        union() {
            // Main vertical socket bore (z = 0 to 5.25 mm)
            translate([0, 0, -eps])
                linear_extrude(height = z_roof_start + 2 * eps)
                    dovetail_2d(extra_offset = dovetail_clearance, overlap = 1.2);
            // Bottom entry funnel bevel (z = 0)
            hull() {
                translate([0, 0, -eps])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance + 0.45, overlap = 1.2);
                translate([0, 0, 0.50])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance, overlap = 1.2);
            }
            // 45-deg vaulted ceiling (z = 5.25 to 6.45 mm; self-centers & prints support-free)
            hull() {
                translate([0, 0, z_roof_start - eps])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance, overlap = 1.2);
                translate([0, 0, z_roof_top])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance - dovetail_vault_h, overlap = 1.2);
            }
            // Matching mid-height Z-retention V-groove (z = 2.5 mm)
            hull() {
                translate([0, 0, dovetail_detent_z - det_half_h])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance, overlap = 0.6);
                translate([0, 0, dovetail_detent_z])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance + dovetail_detent_r + 0.04, overlap = 0.6);
                translate([0, 0, dovetail_detent_z + det_half_h])
                    linear_extrude(height = eps)
                        dovetail_2d(extra_offset = dovetail_clearance, overlap = 0.6);
            }
        }
    }
}

// Deep blind cylindrical peg socket with 0.60 mm 45-degree funnel entry chamfer
// Leaves >4.5 mm of straight vertical bore wall so sqrt(D^2 + L^2) > D_socket (non-tipping!)
module peg_socket_cut(z_top, floor_z) {
    funnel = 0.60;
    translate([0, 0, floor_z])
        cylinder(d = peg_socket_d, h = (z_top - floor_z) + eps);
    translate([0, 0, z_top - funnel])
        cylinder(d1 = peg_socket_d, d2 = peg_socket_d + 2 * funnel, h = funnel + eps);
}

// Subtle engraved L-chevron around each corner socket (CTC Snyder visual cue)
module corner_chevron_cut(sx, sy, z_top) {
    arm = 3.6;
    th = 0.9;
    depth = 0.35;
    r_out = peg_socket_d / 2 + 0.7;
    translate([sx * (corner_mark_offset + r_out), sy * (corner_mark_offset + r_out), z_top - depth]) {
        translate([sx > 0 ? -arm : 0, sy > 0 ? -th : 0, 0])
            cube([arm, th, depth + eps]);
        translate([sx > 0 ? -th : 0, sy > 0 ? -arm : 0, 0])
            cube([th, arm, depth + eps]);
    }
}

// ============================================================================
// Cell Interior Cutout (Open Floor + CTC Central Frame + Deep Anti-Tip Holes)
// ============================================================================

function central_mark_coords() =
    (center_mark_mode == "3x2")
    ? [
        [-6.8, -3.7], [0, -3.7], [6.8, -3.7],
        [-6.8,  3.7], [0,  3.7], [6.8,  3.7]
      ]
    : [
        [-4.4, -4.4], [ 4.4, -4.4],
        [-4.4,  4.4], [ 4.4,  4.4]
      ];

module cell_interior_cuts(cx, cy) {
    zone_floor_z = base_thickness - center_zone_recess_depth; // 7.5 mm
    peg_floor_z = base_thickness - peg_socket_depth;          // 1.8 mm solid bottom!

    translate([cx, cy, 0]) {
        // 1. Carve open cell interior down to base_thickness (with 0.5 mm wall top bevel)
        translate([0, 0, base_thickness])
            linear_extrude(height = wall_height + eps)
                rounded_rect_2d(cell_open_w, cell_open_w, 2.6);
        hull() {
            translate([0, 0, total_plate_h - 0.5])
                linear_extrude(height = eps)
                    rounded_rect_2d(cell_open_w, cell_open_w, 2.6);
            translate([0, 0, total_plate_h + eps])
                linear_extrude(height = eps)
                    rounded_rect_2d(cell_open_w + 1.0, cell_open_w + 1.0, 3.1);
        }

        // 2. Framed Central CTC Candidate Zone
        hull() {
            translate([0, 0, zone_floor_z])
                linear_extrude(height = center_zone_recess_depth - 0.25)
                    rounded_rect_2d(center_zone_x, center_zone_y, 3.5);
            translate([0, 0, base_thickness + eps])
                linear_extrude(height = eps)
                    rounded_rect_2d(center_zone_x + 0.5, center_zone_y + 0.5, 3.8);
        }

        // 3. Deep Central Pencil-Mark Sockets (5.7 mm deep below zone floor)
        for (pt = central_mark_coords()) {
            translate([pt[0], pt[1], 0])
                peg_socket_cut(z_top = zone_floor_z, floor_z = peg_floor_z);
        }

        // 4. Deep Corner Pencil-Mark Sockets (6.2 mm deep below cell floor) + Snyder Ticks
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([sx * corner_mark_offset, sy * corner_mark_offset, 0])
                peg_socket_cut(z_top = base_thickness, floor_z = peg_floor_z);
            corner_chevron_cut(sx, sy, base_thickness);
        }
    }
}

// Deep Monolithic Region-Line Groove along X or Y (7.0 mm deep)
module region_slot_x(y_pos, x_start, x_end) {
    len_x = x_end - x_start;
    chamf = 0.45;
    translate([x_start, y_pos - region_slot_width / 2, slot_floor_z])
        cube([len_x, region_slot_width, region_slot_depth + eps]);
    hull() {
        translate([x_start, y_pos - region_slot_width / 2, total_plate_h - chamf])
            cube([len_x, region_slot_width, eps]);
        translate([x_start, y_pos - region_slot_width / 2 - chamf, total_plate_h + eps])
            cube([len_x, region_slot_width + 2 * chamf, eps]);
    }
}

module region_slot_y(x_pos, y_start, y_end) {
    len_y = y_end - y_start;
    chamf = 0.45;
    translate([x_pos - region_slot_width / 2, y_start, slot_floor_z])
        cube([region_slot_width, len_y, region_slot_depth + eps]);
    hull() {
        translate([x_pos - region_slot_width / 2, y_start, total_plate_h - chamf])
            cube([region_slot_width, len_y, eps]);
        translate([x_pos - region_slot_width / 2 - chamf, y_start, total_plate_h + eps])
            cube([region_slot_width + 2 * chamf, len_y, eps]);
    }
}

// ============================================================================
// Board Plate Generator (Configurable NxN subgrid; 3x3 default, 1x1 test)
// ============================================================================

module board_subgrid(n_cells = 3, include_dovetails = true) {
    span = n_cells * cell_pitch;
    x0 = -divider_hw;
    y0 = -divider_hw;

    difference() {
        union() {
            hull() {
                translate([x0 + elephant_foot_bevel, y0 + elephant_foot_bevel, 0])
                    cube([span - 2 * elephant_foot_bevel, span - 2 * elephant_foot_bevel, eps]);
                translate([x0, y0, elephant_foot_bevel])
                    cube([span, span, total_plate_h - elephant_foot_bevel]);
            }

            if (include_dovetails) {
                for (i = [0 : n_cells - 1]) {
                    translate([(i + 0.5) * cell_pitch, y0, 0])
                        male_dovetail_south();
                    translate([x0, (i + 0.5) * cell_pitch, 0])
                        rotate([0, 0, -90])
                            male_dovetail_south();
                }
            }
        }

        for (ix = [0 : n_cells - 1], iy = [0 : n_cells - 1]) {
            cell_interior_cuts((ix + 0.5) * cell_pitch, (iy + 0.5) * cell_pitch);
        }

        for (k = [0 : n_cells - 1]) {
            region_slot_x(k * cell_pitch, x0 - eps, x0 + span + eps);
            region_slot_y(k * cell_pitch, y0 - eps, y0 + span + eps);
        }

        for (i = [0 : n_cells - 1]) {
            translate([(i + 0.5) * cell_pitch, divider_hw - 0.75, total_plate_h - 0.35])
                rotate([0, 0, 45]) cube([1.1, 1.1, 0.4], center = true);
            translate([divider_hw - 0.75, (i + 0.5) * cell_pitch, total_plate_h - 0.35])
                rotate([0, 0, 45]) cube([1.1, 1.1, 0.4], center = true);
        }

        if (include_dovetails) {
            for (i = [0 : n_cells - 1]) {
                translate([(i + 0.5) * cell_pitch, y0 + span, 0])
                    female_dovetail_cut_from_north();
                translate([x0 + span, (i + 0.5) * cell_pitch, 0])
                    rotate([0, 0, -90])
                        female_dovetail_cut_from_north();
            }
        }
    }
}

// ============================================================================
// Modular 1x1 Montessori Jigsaw Tile Generator (Flush Solid Outer Perimeter)
// ============================================================================
// - Outward Male spring-slotted nubbins on Bottom (South) and Right (East) when interior
// - Inward Female vaulted-roof sockets on Top (North) and Left (West) when interior
// - Outer perimeter edges (has_*_wall = true) have a solid raised barrier wall
//   (no perimeter region slots, no protruding tabs/sockets) that stops interior
//   region bars so they cannot slide out and keeps all 4 outer board faces flush!
//
// 9 Tile Variants for any M x N grid:
//   - tile_center    (N=false, S=false, E=false, W=false)
//   - tile_edge_n    (N=true,  S=false, E=false, W=false)
//   - tile_edge_s    (N=false, S=true,  E=false, W=false)
//   - tile_edge_w    (N=false, S=false, E=false, W=true)
//   - tile_edge_e    (N=false, S=false, E=true,  W=false)
//   - tile_corner_nw (N=true,  S=false, E=false, W=true)
//   - tile_corner_ne (N=true,  S=false, E=true,  W=false)
//   - tile_corner_sw (N=false, S=true,  E=false, W=true)
//   - tile_corner_se (N=false, S=true,  E=true,  W=false)

module board_tile(
    has_north_wall = false,
    has_south_wall = false,
    has_east_wall  = false,
    has_west_wall  = false
) {
    x0 = has_west_wall ? -divider_hw : divider_hw;
    x1 = cell_pitch + divider_hw;
    y0 = -divider_hw;
    y1 = cell_pitch + (has_north_wall ? divider_hw : -divider_hw);
    w_x = x1 - x0;
    w_y = y1 - y0;

    // Stop interior region slots inside the solid outer perimeter wall while leaving
    // full clearance for region_bar_1x / 2x / 3x tips (bar tip reaches 0.25 mm from
    // cell edge; stopping the slot at 0.55 mm inside the outer wall gives 0.30 mm end
    // clearance for jigsaw & box bars while keeping a solid 2.25 mm outer barrier wall).
    outer_slot_stop = region_slot_width / 2 + 0.55; // 2.05 mm inside the 2.80 mm divider_hw
    slot_x_min = has_west_wall  ? outer_slot_stop : (x0 - eps);
    slot_x_max = has_east_wall  ? (cell_pitch - outer_slot_stop) : (x1 + eps);
    slot_y_min = has_south_wall ? outer_slot_stop : (y0 - eps);
    slot_y_max = has_north_wall ? (cell_pitch - outer_slot_stop) : (y1 + eps);

    difference() {
        union() {
            // 1. Solid tile body with elephant-foot bevel
            hull() {
                translate([x0 + elephant_foot_bevel, y0 + elephant_foot_bevel, 0])
                    cube([w_x - 2 * elephant_foot_bevel, w_y - 2 * elephant_foot_bevel, eps]);
                translate([x0, y0, elephant_foot_bevel])
                    cube([w_x, w_y, total_plate_h - elephant_foot_bevel]);
            }

            // 2. Outward Male jigsaw nubbins on Bottom (South) and Right (East) only when interior
            if (!has_south_wall) {
                translate([0.5 * cell_pitch, y0, 0])
                    male_dovetail_south();
            }
            if (!has_east_wall) {
                translate([x0 + w_x, 0.5 * cell_pitch, 0])
                    rotate([0, 0, 90])
                        male_dovetail_south();
            }
        }

        // 3. Cell interior & peg sockets
        cell_interior_cuts(0.5 * cell_pitch, 0.5 * cell_pitch);

        // 4. Interior region slots on Bottom (South) and Right (East), stopped by any outer wall
        if (!has_south_wall) {
            region_slot_x(0, slot_x_min, slot_x_max);
        }
        if (!has_east_wall) {
            region_slot_y(cell_pitch, slot_y_min, slot_y_max);
        }

        // 4b. Remove isolated 1.3x1.3 mm corner nubbin at Bottom-Right only when both S & E slots exist
        if (!has_south_wall && !has_east_wall) {
            nub_w = slot_wall_thickness + 2 * eps;
            nub_h = region_slot_depth + 2 * eps;
            translate([cell_pitch + region_slot_width / 2 - eps, -divider_hw - eps, slot_floor_z])
                cube([nub_w, nub_w, nub_h]);
        }

        // 5. Inward Female vaulted-roof jigsaw sockets on Top (North) and Left (West) only when interior
        if (!has_north_wall) {
            translate([0.5 * cell_pitch, y0 + w_y, 0])
                female_dovetail_cut_from_north();
        }
        if (!has_west_wall) {
            translate([x0, 0.5 * cell_pitch, 0])
                rotate([0, 0, 90])
                    female_dovetail_cut_from_north();
        }
    }
}

// Helper: places the appropriate flush-perimeter tile at grid coordinate (ix, iy)
// within an ncols x nrows board (ix = 0..ncols-1 W->E, iy = 0..nrows-1 S->N).
module board_grid_tile(ix, iy, ncols, nrows) {
    translate([ix * cell_pitch, iy * cell_pitch, 0])
        board_tile(
            has_north_wall = (iy == nrows - 1),
            has_south_wall = (iy == 0),
            has_east_wall  = (ix == ncols - 1),
            has_west_wall  = (ix == 0)
        );
}

// Monolithic single-piece N x N board with flush solid outer walls and captured interior slots
// (For n_cells = 4: 145.6 x 145.6 x 12.5 mm — prints in one piece on a 180x180 mm A1 Mini bed)
module monolithic_board(n_cells = 4) {
    span = n_cells * cell_pitch;
    x0 = -divider_hw;
    y0 = -divider_hw;
    w = span + 2 * divider_hw;
    // Extend interior slots just past the perimeter grid line (0 / span) so
    // region_bar_1x / 2x / 3x tips (at 0.25 mm) seat cleanly against the outer wall
    // while keeping 2.7 mm of solid outer wall barrier.
    outer_slot_stop = -0.1;

    border_top_z = slot_floor_z + bar_tongue_h + bar_bevel_h + region_bar_crown_height;
    paint_ridge_h = 0.70;
    paint_ridge_w = region_bar_crown_width - 1.1;
    border_shoulder_z = border_top_z - paint_ridge_h;
    notch_w = region_bar_crown_width + 0.5;
    notch_in = 0.25; // notch reaches 0.25 mm past grid line (leaves 1.75 mm continuous outer border)

    union() {
        difference() {
            // 1. Solid one-piece board body with elephant-foot bevel on the outer perimeter
            hull() {
                translate([x0 + elephant_foot_bevel, y0 + elephant_foot_bevel, 0])
                    cube([w - 2 * elephant_foot_bevel, w - 2 * elephant_foot_bevel, eps]);
                translate([x0, y0, elephant_foot_bevel])
                    cube([w, w, total_plate_h - elephant_foot_bevel]);
            }

            // 2. Cell interiors & peg sockets for all n_cells x n_cells squares
            for (ix = [0 : n_cells - 1], iy = [0 : n_cells - 1]) {
                cell_interior_cuts((ix + 0.5) * cell_pitch, (iy + 0.5) * cell_pitch);
            }

            // 3. Full grid of interior region slots (k = 1..n_cells-1 in both X and Y) for
            //    both standard 2x2 box bars and 1x1 Jigsaw bars, stopped inside the outer wall.
            if (n_cells > 1) {
                for (k = [1 : n_cells - 1]) {
                    region_slot_x(k * cell_pitch, outer_slot_stop, span - outer_slot_stop);
                    region_slot_y(k * cell_pitch, outer_slot_stop, span - outer_slot_stop);
                }
                // Remove isolated 1.3x1.3 mm corner posts at interior slot intersections (kx, ky = 1..n_cells-1)
                // so adjacent perpendicular region bars (like Jigsaw turns) never collide with corner posts!
                nub_w = slot_wall_thickness + 2 * eps;
                nub_h = region_slot_depth + 2 * eps;
                for (kx = [1 : n_cells - 1], ky = [1 : n_cells - 1]) {
                    for (sx = [-1, 1], sy = [-1, 1]) {
                        cx_post = kx * cell_pitch + sx * (region_slot_width / 2 - eps);
                        cy_post = ky * cell_pitch + sy * (region_slot_width / 2 - eps);
                        translate([
                            sx > 0 ? cx_post : (cx_post - nub_w),
                            sy > 0 ? cy_post : (cy_post - nub_w),
                            slot_floor_z
                        ])
                            cube([nub_w, nub_w, nub_h]);
                    }
                }
            }
        }

        // 4. Raised permanent outer border (matches region_bar crown & paint ridge height)
        //    Centered on the perimeter grid lines (0 and span) so it aligns with the puzzle grid.
        difference() {
            for (edge = [0 : 3]) {
                translate([span / 2, span / 2, 0])
                rotate([0, 0, edge * 90])
                translate([-span / 2, -span / 2, 0]) {
                    // Lower crown shoulder
                    hull() {
                        translate([-bar_tongue_w / 2, -bar_tongue_w / 2, total_plate_h - eps])
                            cube([span + bar_tongue_w, bar_tongue_w, eps]);
                        translate([-region_bar_crown_width / 2, -region_bar_crown_width / 2, total_plate_h + 0.25 + bar_bevel_h])
                            cube([span + region_bar_crown_width, region_bar_crown_width, border_shoulder_z - (total_plate_h + 0.25 + bar_bevel_h)]);
                    }
                    // Raised flat paint ridge on top
                    translate([-paint_ridge_w / 2, -paint_ridge_w / 2, border_shoulder_z - eps])
                        cube([span + paint_ridge_w, paint_ridge_w, paint_ridge_h + eps]);
                }
            }
            if (n_cells > 1) {
                for (k = [1 : n_cells - 1]) {
                    // Notches in the raised permanent border so region_bars seat into the perimeter
                    translate([k * cell_pitch - notch_w / 2, -notch_in, total_plate_h - eps])
                        cube([notch_w, divider_hw + notch_in + eps, border_top_z - total_plate_h + 1]);
                    translate([k * cell_pitch - notch_w / 2, span - divider_hw - eps, total_plate_h - eps])
                        cube([notch_w, divider_hw + notch_in + eps, border_top_z - total_plate_h + 1]);
                    translate([-notch_in, k * cell_pitch - notch_w / 2, total_plate_h - eps])
                        cube([divider_hw + notch_in + eps, notch_w, border_top_z - total_plate_h + 1]);
                    translate([span - divider_hw - eps, k * cell_pitch - notch_w / 2, total_plate_h - eps])
                        cube([divider_hw + notch_in + eps, notch_w, border_top_z - total_plate_h + 1]);
                }
            }
        }
    }
}

// ============================================================================
// Snap-On Outer Border Rails (Completes East x=9P & North y=9P Perimeter Slots)
// ============================================================================

module east_border_rail(n_cells = 3, extend_ne_corner = false) {
    base_len = n_cells * cell_pitch;
    rail_len = extend_ne_corner ? (base_len + 2 * divider_hw) : base_len;
    y0 = -divider_hw;
    rail_w = 2 * divider_hw;

    difference() {
        union() {
            hull() {
                translate([-divider_hw + elephant_foot_bevel, y0 + elephant_foot_bevel, 0])
                    cube([rail_w - 2 * elephant_foot_bevel, rail_len - 2 * elephant_foot_bevel, eps]);
                translate([-divider_hw, y0, elephant_foot_bevel])
                    cube([rail_w, rail_len, total_plate_h - elephant_foot_bevel]);
            }
            for (i = [0 : n_cells - 1]) {
                translate([-divider_hw, (i + 0.5) * cell_pitch, 0])
                    rotate([0, 0, -90])
                        male_dovetail_south();
            }
        }

        slot_y_end = extend_ne_corner ? (base_len + region_slot_width / 2) : (y0 + rail_len + eps);
        region_slot_y(0, y0 - eps, slot_y_end);

        max_k = extend_ne_corner ? n_cells : (n_cells - 1);
        for (k = [0 : max_k]) {
            x_end_cut = (extend_ne_corner && k == n_cells) ? (region_slot_width / 2) : (divider_hw + eps);
            region_slot_x(k * cell_pitch, -divider_hw - eps, x_end_cut);
        }
    }
}

module north_border_rail(n_cells = 3) {
    translate([0, (n_cells * cell_pitch) - 2 * divider_hw, 0])
        mirror([0, 1, 0])
            east_border_rail(n_cells = n_cells, extend_ne_corner = false);
}

module outer_border_kit() {
    pitch_x = 2 * divider_hw + dovetail_depth + 4.5;
    translate([0 * pitch_x, 0, 0]) east_border_rail(3, false);
    translate([1 * pitch_x, 0, 0]) east_border_rail(3, false);
    translate([2 * pitch_x, 0, 0]) east_border_rail(3, true);
    translate([3 * pitch_x, 0, 0]) north_border_rail(3);
    translate([4 * pitch_x, 0, 0]) north_border_rail(3);
    translate([5 * pitch_x, 0, 0]) north_border_rail(3);
}

// ============================================================================
// Full-Cell Main Solved Piece (3.8 mm Deep Self-Centering Plinth + 38.8 mm Crown)
// ============================================================================

module raised_label(label, text_size, height, bold_offset = 0) {
    if (label != undef && label != "") {
        linear_extrude(height = height + eps)
            offset(delta = bold_offset)
                text(
                    label,
                    size = text_size,
                    font = "Liberation Sans:style=Bold",
                    halign = "center",
                    valign = "center"
                );
    }
}

module main_piece(paint_color = undef, label = "") {
    plinth_h = 3.8; // engages full vertical 4.5 mm cell wall so tiles never skate out when carried
    taper_dn = (tile_base_w - tile_waist_w) / 2;
    z_w2 = plinth_h + taper_dn;
    taper_up = (tile_crown_w - tile_waist_w) / 2;
    paint_pad_h = 0.90;
    crown_h = 3.2;
    z_w4 = (main_tile_height - paint_pad_h) - crown_h;
    z_w3 = z_w4 - taper_up;
    pad_w = tile_crown_w - 2.4;
    label_h = 0.80;

    difference() {
        union() {
            color(paint_color == undef ? undef : "#F5F5F2") {
                // 1. Deep 3.8 mm vertical-walled plinth (engages 4.5 mm cell walls squarely)
                hull() {
                    linear_extrude(height = eps)
                        rounded_rect_2d(tile_base_w - 2 * elephant_foot_bevel, tile_base_w - 2 * elephant_foot_bevel, 1.8);
                    translate([0, 0, elephant_foot_bevel + 0.1])
                        linear_extrude(height = plinth_h - elephant_foot_bevel - 0.1)
                            rounded_rect_2d(tile_base_w, tile_base_w, 2.2);
                }
                // 2. 45-degree inward bevel into finger-pinch waist (support-free)
                hull() {
                    translate([0, 0, plinth_h - eps])
                        linear_extrude(height = eps)
                            rounded_rect_2d(tile_base_w, tile_base_w, 2.2);
                    translate([0, 0, z_w2])
                        linear_extrude(height = max(0.8, z_w3 - z_w2))
                            rounded_rect_2d(tile_waist_w, tile_waist_w, 3.0);
                }
                // 3. 45-degree outward flare to white crown shoulder (support-free)
                hull() {
                    translate([0, 0, z_w3])
                        linear_extrude(height = eps)
                            rounded_rect_2d(tile_waist_w, tile_waist_w, 3.0);
                    translate([0, 0, z_w4])
                        linear_extrude(height = (main_tile_height - paint_pad_h) - z_w4 - 0.5)
                            rounded_rect_2d(tile_crown_w, tile_crown_w, 3.8);
                }
                // 4. White upper shoulder bevel (sits 0.9 mm BELOW the flat paint pad)
                hull() {
                    translate([0, 0, main_tile_height - paint_pad_h - 0.5 - eps])
                        linear_extrude(height = eps)
                            rounded_rect_2d(tile_crown_w, tile_crown_w, 3.8);
                    translate([0, 0, main_tile_height - paint_pad_h])
                        linear_extrude(height = eps)
                            rounded_rect_2d(pad_w + 0.6, pad_w + 0.6, 3.2);
                }
            }
            // 5. Raised flat paint pad on top (proud 0.9 mm above white shoulder for easy marker painting)
            color(paint_color)
                translate([0, 0, main_tile_height - paint_pad_h - eps])
                    linear_extrude(height = paint_pad_h + eps)
                        rounded_rect_2d(pad_w, pad_w, 3.0);
            // 6. Optional raised character on top of the paint pad
            color(paint_color)
                translate([0, 0, main_tile_height - eps])
                    raised_label(label, text_size = pad_w * 0.58, height = label_h);
        }

        // 4-Side Marker Color Groove near upper crown
        difference() {
            translate([0, 0, main_tile_height - paint_pad_h - 2.3])
                linear_extrude(height = 1.4)
                    rounded_rect_2d(tile_crown_w + 2, tile_crown_w + 2, 4.2);
            hull() {
                translate([0, 0, main_tile_height - paint_pad_h - 2.3 - eps])
                    linear_extrude(height = eps)
                        rounded_rect_2d(tile_crown_w, tile_crown_w, 3.8);
                translate([0, 0, main_tile_height - paint_pad_h - 1.6])
                    linear_extrude(height = eps)
                        rounded_rect_2d(tile_crown_w - 1.0, tile_crown_w - 1.0, 3.4);
            }
            hull() {
                translate([0, 0, main_tile_height - paint_pad_h - 1.6])
                    linear_extrude(height = eps)
                        rounded_rect_2d(tile_crown_w - 1.0, tile_crown_w - 1.0, 3.4);
                translate([0, 0, main_tile_height - paint_pad_h - 0.9 + eps])
                    linear_extrude(height = eps)
                        rounded_rect_2d(tile_crown_w, tile_crown_w, 3.8);
            }
        }
    }
}

// ============================================================================
// Universal Non-Rolling Anti-Tip Pencil-Mark Peg (17.5 mm tall; 5.7-6.2 mm seated)
// ============================================================================

module pencil_peg(paint_color = undef, label = "") {
    paint_cap_h = 0.80;
    cap_flat_d = peg_eff_flat_d - 0.9;
    label_h = 0.60;

    difference() {
        union() {
            // Lower white octagonal shaft up to (peg_height - paint_cap_h)
            color(paint_color == undef ? undef : "#F5F5F2")
                hull() {
                    linear_extrude(height = eps)
                        octagon_2d(peg_eff_flat_d - 0.9);
                    translate([0, 0, 0.55])
                        linear_extrude(height = peg_height - paint_cap_h - 0.55)
                            octagon_2d(peg_eff_flat_d);
                }
            // Raised flat octagonal paint cap on top (0.8 mm proud above white shaft)
            color(paint_color)
                translate([0, 0, peg_height - paint_cap_h - eps])
                    linear_extrude(height = paint_cap_h + eps)
                        octagon_2d(cap_flat_d);
            // Optional raised character on top of the paint cap
            color(paint_color)
                translate([0, 0, peg_height - eps])
                    raised_label(label, text_size = cap_flat_d * 0.62, height = label_h, bold_offset = 0.04);
        }

        // Grip groove below the raised paint cap
        difference() {
            translate([0, 0, peg_height - paint_cap_h - 2.2])
                cylinder(d = peg_circum_d + 2, h = 1.4);
            hull() {
                translate([0, 0, peg_height - paint_cap_h - 2.2 - eps])
                    linear_extrude(height = eps)
                        octagon_2d(peg_eff_flat_d);
                translate([0, 0, peg_height - paint_cap_h - 1.5])
                    linear_extrude(height = eps)
                        octagon_2d(peg_eff_flat_d - 0.9);
            }
            hull() {
                translate([0, 0, peg_height - paint_cap_h - 1.5])
                    linear_extrude(height = eps)
                        octagon_2d(peg_eff_flat_d - 0.9);
                translate([0, 0, peg_height - paint_cap_h - 0.8 + eps])
                    linear_extrude(height = eps)
                        octagon_2d(peg_eff_flat_d);
            }
        }
    }
}

// ============================================================================
// Deep-Tongue 45-Degree Mitered Region-Line Bar (7.25 mm Tongue -> Zero Side Tip!)
// ============================================================================

module miter_pointed_bar_2d(length, width) {
    half_l = length / 2;
    half_w = width / 2;
    shoulder_x = max(0.1, half_l - half_w);
    polygon([
        [-half_l,     0],
        [-shoulder_x, -half_w],
        [ shoulder_x, -half_w],
        [ half_l,     0],
        [ shoulder_x,  half_w],
        [-shoulder_x,  half_w]
    ]);
}

module region_bar(cells = 1, paint_color = undef) {
    vertex_tip_gap = 0.25;
    full_len = cells * cell_pitch - 2 * vertex_tip_gap;
    paint_ridge_h = 0.70;
    paint_ridge_w = region_bar_crown_width - 1.1;

    union() {
        color(paint_color == undef ? undef : "#F5F5F2") {
            // Deep anti-tip tongue
            hull() {
                linear_extrude(height = eps)
                    miter_pointed_bar_2d(full_len - 0.6, bar_tongue_w - 2 * elephant_foot_bevel);
                translate([0, 0, elephant_foot_bevel])
                    linear_extrude(height = bar_tongue_h - elephant_foot_bevel)
                        miter_pointed_bar_2d(full_len, bar_tongue_w);
            }
            // White flared crown shoulder (0.7 mm below the raised paint ridge)
            hull() {
                translate([0, 0, bar_tongue_h - eps])
                    linear_extrude(height = eps)
                        miter_pointed_bar_2d(full_len, bar_tongue_w);
                translate([0, 0, bar_tongue_h + bar_bevel_h])
                    linear_extrude(height = region_bar_crown_height - paint_ridge_h)
                        miter_pointed_bar_2d(full_len, region_bar_crown_width);
            }
        }
        // Raised flat paint ridge on top (proud 0.7 mm above white shoulder)
        color(paint_color)
            translate([0, 0, bar_tongue_h + bar_bevel_h + region_bar_crown_height - paint_ridge_h - eps])
                linear_extrude(height = paint_ridge_h + eps)
                    miter_pointed_bar_2d(full_len - 0.8, paint_ridge_w);
    }
}

// ============================================================================
// Interactive 3D Assembly Preview (Modular 1x1 Jigsaw Tiles Assembled as 3x3)
// ============================================================================

module assembly_preview() {
    sudoku_colors = [
        "#E63946", "#F4A261", "#E9C46A", "#2A9D8F", "#00B4D8",
        "#3A86FF", "#8338EC", "#FF006E", "#6D597A"
    ];

    peg_floor_z = base_thickness - peg_socket_depth;

    color("#F7F7F5") {
        for (ix = [0 : 2], iy = [0 : 2]) {
            board_grid_tile(ix, iy, 3, 3);
        }
    }

    translate([0.5 * cell_pitch, 2.5 * cell_pitch, base_thickness])
        main_piece(sudoku_colors[0]);
    translate([0.5 * cell_pitch, 1.5 * cell_pitch, base_thickness])
        main_piece(sudoku_colors[1]);
    translate([1.5 * cell_pitch, 1.5 * cell_pitch, base_thickness])
        main_piece(sudoku_colors[3]);
    translate([2.5 * cell_pitch, 0.5 * cell_pitch, base_thickness])
        main_piece(sudoku_colors[5]);

    translate([0.5 * cell_pitch - corner_mark_offset, 0.5 * cell_pitch + corner_mark_offset, peg_floor_z])
        pencil_peg(sudoku_colors[2]);
    translate([1.5 * cell_pitch - corner_mark_offset, 0.5 * cell_pitch + corner_mark_offset, peg_floor_z])
        pencil_peg(sudoku_colors[2]);

    c_pts = central_mark_coords();
    for (idx = [0 : 2]) {
        translate([2.5 * cell_pitch + c_pts[idx][0], 2.5 * cell_pitch + c_pts[idx][1], peg_floor_z])
            pencil_peg(sudoku_colors[idx + 4]);
    }

    translate([0.5 * cell_pitch, 2.0 * cell_pitch, slot_floor_z])
        region_bar(1, "#7209B7");
    translate([1.0 * cell_pitch, 1.5 * cell_pitch, slot_floor_z])
        rotate([0, 0, 90]) region_bar(1, "#7209B7");
    translate([1.5 * cell_pitch, 1.0 * cell_pitch, slot_floor_z])
        region_bar(1, "#7209B7");
    translate([2.0 * cell_pitch, 0.5 * cell_pitch, slot_floor_z])
        rotate([0, 0, 90]) region_bar(1, "#7209B7");
}

// Complete 9x9 Finished Board Preview (49x center + 28x edges + 4x corners, flush outer perimeter)
module full_board_preview() {
    sudoku_colors = [
        "#E63946", "#F4A261", "#E9C46A", "#2A9D8F", "#00B4D8",
        "#3A86FF", "#8338EC", "#FF006E", "#6D597A"
    ];
    peg_floor_z = base_thickness - peg_socket_depth;
    c_pts = central_mark_coords();

    // 1. White 9x9 modular jigsaw board (49 + 7*4 + 4 = 81 tiles) with flush outer perimeter
    color("#F5F5F2") {
        for (ix = [0 : 8], iy = [0 : 8]) {
            render(convexity = 4) board_grid_tile(ix, iy, 9, 9);
        }
    }

    // 2. Classic 3x3 interior box dividers (region_bar_3x; outer perimeter is a solid wall)
    for (bx = [0 : 2], gy = [3, 6]) {
        translate([(bx * 3 + 1.5) * cell_pitch, gy * cell_pitch, slot_floor_z])
            region_bar(3, "#264653");
    }
    for (by = [0 : 2], gx = [3, 6]) {
        translate([gx * cell_pitch, (by * 3 + 1.5) * cell_pitch, slot_floor_z])
            rotate([0, 0, 90])
                region_bar(3, "#264653");
    }

    // 3. Mid-game Sudoku puzzle (0 = empty/pencil marks, 1..9 = color index)
    puzzle = [
        [5, 3, 0,  0, 7, 0,  0, 0, 0],
        [6, 0, 0,  1, 9, 5,  0, 0, 0],
        [0, 9, 8,  0, 0, 0,  0, 6, 0],

        [8, 0, 0,  0, 6, 0,  0, 0, 3],
        [4, 0, 0,  8, 0, 3,  0, 0, 1],
        [7, 0, 0,  0, 2, 0,  0, 0, 6],

        [0, 6, 0,  0, 0, 0,  2, 8, 0],
        [0, 0, 0,  4, 1, 9,  0, 0, 5],
        [0, 0, 0,  0, 8, 0,  0, 7, 9]
    ];

    for (r = [0 : 8], c = [0 : 8]) {
        v = puzzle[8 - r][c];
        if (v > 0) {
            translate([(c + 0.5) * cell_pitch, (r + 0.5) * cell_pitch, base_thickness])
                main_piece(sudoku_colors[v - 1]);
        }
    }

    // 4. Sample corner & central pencil-mark pegs in a few empty cells
    translate([2.5 * cell_pitch - corner_mark_offset, 8.5 * cell_pitch + corner_mark_offset, peg_floor_z])
        pencil_peg(sudoku_colors[0]);
    translate([2.5 * cell_pitch + corner_mark_offset, 8.5 * cell_pitch + corner_mark_offset, peg_floor_z])
        pencil_peg(sudoku_colors[3]);

    translate([1.5 * cell_pitch + c_pts[0][0], 7.5 * cell_pitch + c_pts[0][1], peg_floor_z])
        pencil_peg(sudoku_colors[1]);
    translate([1.5 * cell_pitch + c_pts[3][0], 7.5 * cell_pitch + c_pts[3][1], peg_floor_z])
        pencil_peg(sudoku_colors[6]);

    translate([4.5 * cell_pitch + c_pts[1][0], 4.5 * cell_pitch + c_pts[1][1], peg_floor_z])
        pencil_peg(sudoku_colors[4]);
    translate([4.5 * cell_pitch + c_pts[2][0], 4.5 * cell_pitch + c_pts[2][1], peg_floor_z])
        pencil_peg(sudoku_colors[8]);
}

// ============================================================================
// Top-Level Dispatcher
// ============================================================================

if (render_mode == "assembly_preview") {
    assembly_preview();
} else if (render_mode == "full_board_preview") {
    full_board_preview();
} else if (render_mode == "board_4x4") {
    monolithic_board(4);
} else if (render_mode == "tile_center" || render_mode == "tile_2slot") {
    board_tile(false, false, false, false);
} else if (render_mode == "tile_edge_n" || render_mode == "tile_3slot_top") {
    board_tile(true,  false, false, false);
} else if (render_mode == "tile_edge_s") {
    board_tile(false, true,  false, false);
} else if (render_mode == "tile_edge_w" || render_mode == "tile_3slot_left") {
    board_tile(false, false, false, true);
} else if (render_mode == "tile_edge_e") {
    board_tile(false, false, true,  false);
} else if (render_mode == "tile_corner_nw" || render_mode == "tile_4slot") {
    board_tile(true,  false, false, true);
} else if (render_mode == "tile_corner_ne") {
    board_tile(true,  false, true,  false);
} else if (render_mode == "tile_corner_sw") {
    board_tile(false, true,  false, true);
} else if (render_mode == "tile_corner_se") {
    board_tile(false, true,  true,  false);
} else if (render_mode == "main_piece") {
    main_piece(label = piece_label);
} else if (render_mode == "pencil_peg") {
    pencil_peg(label = piece_label);
} else if (render_mode == "region_bar_1x") {
    region_bar(1);
} else if (render_mode == "region_bar_2x") {
    region_bar(2);
} else if (render_mode == "region_bar_3x") {
    region_bar(3);
}
