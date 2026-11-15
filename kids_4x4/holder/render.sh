#!/usr/bin/env bash
# Render preview PNGs for all holder options (needs openscad)
cd "$(dirname "$0")"; mkdir -p images
r() { openscad -o "images/option_$1_$2.png" -D "option=\"$1\"" -D "part=\"$2\"" --imgsize=1400,1000 --viewall --autocenter --camera=0,0,0,$3,0,$4,0 --colorscheme=Tomorrow piece_holder.scad 2>/dev/null; }
for o in A B C; do r $o open 50 25 & r $o closed 60 25 & done; wait
for o in A B C; do openscad -o "images/option_${o}_top.png" -D "option=\"$o\"" -D "part=\"open\"" --imgsize=1200,1000 --viewall --autocenter --camera=0,0,0,0,0,0,0 --projection=o --colorscheme=Tomorrow piece_holder.scad 2>/dev/null & done; wait
