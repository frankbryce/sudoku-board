SCAD := src/color_sudoku_board.scad
OPENSCAD := openscad
CENTER_MARK_MODE ?= 2x2

LABELS := 1 2 3 4 5 6 7 8 9 A B C D E F G H I
MAIN_LABELED_STLS := $(addprefix stl/main_piece_,$(addsuffix .stl,$(LABELS)))
PEG_LABELED_STLS := $(addprefix stl/pencil_peg_,$(addsuffix .stl,$(LABELS)))

STLS := \
	stl/board_4x4.stl \
	stl/tile_center.stl \
	stl/tile_edge_n.stl \
	stl/tile_edge_s.stl \
	stl/tile_edge_w.stl \
	stl/tile_edge_e.stl \
	stl/tile_corner_nw.stl \
	stl/tile_corner_ne.stl \
	stl/tile_corner_sw.stl \
	stl/tile_corner_se.stl \
	stl/main_piece.stl \
	stl/pencil_peg.stl \
	stl/region_bar_1x.stl \
	stl/region_bar_2x.stl \
	stl/region_bar_3x.stl \
	$(MAIN_LABELED_STLS) \
	$(PEG_LABELED_STLS)

.PHONY: all renders clean

all: $(STLS)

renders: renders/finished_board_9x9.png renders/finished_board_closeup.png

renders/finished_board_9x9.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --projection=p -D 'render_mode="full_board_preview"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

renders/finished_board_closeup.png: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ --imgsize=1600,1200 --autocenter --viewall --projection=p -D 'render_mode="assembly_preview"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/main_piece_%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="main_piece"' -D 'piece_label="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/pencil_peg_%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="pencil_peg"' -D 'piece_label="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

stl/%.stl: $(SCAD)
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'render_mode="$*"' -D 'center_mark_mode="$(CENTER_MARK_MODE)"' $<

clean:
	rm -f $(STLS)
