#!/usr/bin/env bash
# Render preview PNGs for all holder options (with upside-down board as lid) + board fix
set -e
cd "$(dirname "$0")"; mkdir -p images

r() {
    openscad -o "images/option_$1_$2.png" -D "option=\"$1\"" -D "part=\"$2\"" \
        --imgsize=1400,1050 --viewall --autocenter --camera=0,0,0,$3,0,$4,0 \
        --colorscheme=Tomorrow piece_holder.scad 2>/dev/null
}

for o in A B C; do
    r $o open 48 28 &
    r $o lid_lifting 58 28 &
    r $o closed 55 28 &
    openscad -o "images/option_${o}_top.png" -D "option=\"$o\"" -D "part=\"open\"" \
        --imgsize=1200,1200 --viewall --autocenter --camera=0,0,0,0,0,0,0 \
        --projection=o --colorscheme=Tomorrow piece_holder.scad 2>/dev/null &
done

openscad -o "images/board_border_and_notches.png" -D 'option="board_fix"' \
    --imgsize=1400,1050 --viewall --autocenter --camera=0,0,0,48,0,28,0 \
    --colorscheme=Tomorrow piece_holder.scad 2>/dev/null &

wait
