SCAD := src/color_sudoku_board.scad
HOLDER_SCAD := kids_4x4/holder/piece_holder.scad
OPENSCAD := openscad
CENTER_MARK_MODE ?= 2x2
HOLDER_OPTION ?= B

LABELS := 1 2 3 4 5 6 7 8 9 A B C D E F G H I
SHAPES := circle square triangle star asterisk heart crescent clover hexagon
MAIN_LABELED_STLS := $(addprefix stl/pieces/main_piece_,$(addsuffix .stl,$(LABELS)))
MAIN_SHAPED_STLS := $(addprefix stl/pieces/main_piece_shape_,$(addsuffix .stl,$(SHAPES)))
PEG_LABELED_STLS := $(addprefix stl/pegs/pencil_peg_,$(addsuffix .stl,$(LABELS)))

STLS := \
	stl/boards/board_4x4.stl \
	stl/holders/piece_holder.stl \
	stl/boards/tile_center.stl \
	stl/boards/tile_edge_n.stl \
	stl/boards/tile_edge_s.stl \
	stl/boards/tile_edge_w.stl \
	stl/boards/tile_edge_e.stl \
	stl/boards/tile_corner_nw.stl \
	stl/boards/tile_corner_ne.stl \
	stl/boards/tile_corner_sw.stl \
	stl/boards/tile_corner_se.stl \
	stl/pieces/main_piece.stl \
	stl/pegs/pencil_peg.stl \
	stl/borders/region_bar_1x.stl \
	stl/borders/region_bar_2x.stl \
	stl/borders/region_bar_3x.stl \
	$(MAIN_LABELED_STLS) \
	$(MAIN_SHAPED_STLS) \
	$(PEG_LABELED_STLS)

.PHONY: all renders clean

all: $(STLS)

renders: renders/finished_board_9x9.png renders/finished_board_closeup.png renders/finished_board_4x4.png renders/holder_option_b_lid_lifting.png renders/main_piece_shapes.png

renders/finished_board_9x9.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --projection=p -D 'render_mode="full_board_preview"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

renders/finished_board_closeup.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --projection=p -D 'render_mode="assembly_preview"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

renders/finished_board_4x4.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --camera=0,0,0,46,0,22,0 --projection=p --colorscheme=Tomorrow -D 'render_mode="board_4x4_preview"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

renders/holder_option_b_lid_lifting.png: $(HOLDER_SCAD) $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --camera=0,0,0,58,0,28,0 --projection=p --colorscheme=Tomorrow -D 'option="B"' -D 'part="lid_lifting"' $<

renders/main_piece_shapes.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --camera=0,0,10,25,0,0,0 --projection=p --colorscheme=Tomorrow -D 'render_mode="shapes_preview"' $<

stl/holders/piece_holder.stl: $(HOLDER_SCAD) $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'option="$(HOLDER_OPTION)"' -D 'part="base"' $<

stl/pieces/main_piece_shape_%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="main_piece"' -D 'piece_shape="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/pieces/main_piece_%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="main_piece"' -D 'piece_label="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/pieces/main_piece.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="main_piece"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/pegs/pencil_peg_%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="pencil_peg"' -D 'piece_label="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/pegs/pencil_peg.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="pencil_peg"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/boards/%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/borders/%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

clean:
	rm -f $(STLS)
