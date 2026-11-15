# Modular Color Sudoku System — Montessori Jigsaw 1×1 Edition

![Full 9×9 Finished Board](renders/finished_board_9x9.png)
![Close-Up Detail](renders/finished_board_closeup.png)

Parametric 3D-printable modular Color Sudoku board (~35 mm cell pitch, ~315 × 315 mm for a full 9×9) designed for **Bambu Studio / Bambu Lab A1 Mini** in White PLA / PLA Matte.

## Montessori Jigsaw Connection (Easy Kid Assembly + Holds Flat When Lifted)

- **Outward Male Nubbins on Bottom & Right, Inward Female Sockets on Top & Left:**
  - Each Male tab has a **1.5 mm center flex slot** + a **gentle mid-height Z-detent ridge** (`Z = 2.5 mm`) with generous `0.25 mm` XY clearance so kids can easily click tiles together and pull them apart without wedging.
  - Each Female socket has a **45° self-centering vaulted ceiling** and a **1.55 mm solid roof** underneath the cell floor (`Z = 6.45` to `8.0 mm`). When you pick the board up from the bottom, the vaulted roof + Z-detent + `8.0 mm` base hold the board flat without tiles dropping through.
- **Raised Flat Paint Surfaces:** `main_piece`, `pencil_peg`, and `region_bar_*` have raised flat top pads proud above the white body so you can paint the top surface cleanly with paint markers.

## STL Files (`stl/`)

- **One-Piece 4×4 Board (`stl/board_4x4.stl`)**:
  - Single-print monolithic 4×4 board (`145.6 × 145.6 × 12.5 mm` — prints in one piece on a Bambu Lab A1 Mini `180 × 180 mm` bed).
  - Features a solid raised perimeter barrier wall (`2.85 mm` solid outer wall behind each interior slot end) so interior `region_bar_2x` and `region_bar_1x` (Jigsaw) dividers drop right in and can never slide out, with all 4 outer sides completely smooth and flush for a tray.
- **Modular 1×1 Board Tiles — Flush Outer Perimeter & Captured Interior Slots** (for an $M \times N$ grid; 9×9 / 4×4 counts shown):
  - `tile_center.stl` — Interior tile with Bottom + Right region slots & tabs, Top + Left sockets (`(M-2)×(N-2)` = **49×** for 9×9, **4×** for 4×4)
  - `tile_edge_n.stl` — Top edge with flush solid North barrier wall (`M-2` = **7×** for 9×9, **2×** for 4×4)
  - `tile_edge_s.stl` — Bottom edge with flush solid South barrier wall (`M-2` = **7×** for 9×9, **2×** for 4×4)
  - `tile_edge_w.stl` — Left edge with flush solid West barrier wall (`N-2` = **7×** for 9×9, **2×** for 4×4)
  - `tile_edge_e.stl` — Right edge with flush solid East barrier wall (`N-2` = **7×** for 9×9, **2×** for 4×4)
  - `tile_corner_nw.stl` — Top-Left corner with flush solid North + West barrier walls (**1×**)
  - `tile_corner_ne.stl` — Top-Right corner with flush solid North + East barrier walls (**1×**)
  - `tile_corner_sw.stl` — Bottom-Left corner with flush solid South + West barrier walls (**1×**)
  - `tile_corner_se.stl` — Bottom-Right corner with flush solid South + East barrier walls (**1×**)
  - *Note:* All 4 outer board faces are completely flush (`M × 35 + 5.6 mm`, i.e., `145.6 × 145.6 mm` for 4×4 or `320.6 × 320.6 mm` for 9×9) with no protruding tabs or open sockets on the outside, and the solid outer barrier wall stops every interior region slot so interior divider bars cannot slide out.
- **Game Pieces & Dividers**:
  - `main_piece.stl` — Full-cell solved tile with raised flat paint pad
  - `pencil_peg.stl` — Non-rolling octagonal candidate peg with raised flat paint cap
  - `region_bar_1x.stl` — 1-cell mitered box divider with raised flat paint ridge
  - `region_bar_2x.stl` — 2-cell mitered box divider
  - `region_bar_3x.stl` — 3-cell mitered box divider

## Re-rendering STLs & Previews

```bash
make all
make renders
```
