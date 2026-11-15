PYTHON   ?= python3
OPENSCAD ?= openscad
SEED     ?= 2026
PER      ?= 12

SCAD     := build/build_steps_4x4.scad
STEPS    := 0 1 2 3 4 5 6 7 8 9 10
STEP_PNGS := $(foreach s,$(STEPS),build/images/step_$(shell printf %02d $(s)).png)
CAMERA   := -110,-270,380,70,75,20

export PYTHONPATH := $(CURDIR)

.PHONY: all puzzles pdf instructions clean

all: pdf

## Regenerate puzzles/puzzles.json  (make puzzles SEED=7 PER=16)
puzzles:
	$(PYTHON) -m sudoku4.generate --seed $(SEED) --per-level $(PER)

puzzles/puzzles.json:
	$(PYTHON) -m sudoku4.generate --seed $(SEED) --per-level $(PER)

## Render output/workbook.pdf + output/answers.pdf AND output/workbook_colors.pdf + output/answers_colors.pdf
pdf: puzzles/puzzles.json
	$(PYTHON) -m sudoku4.render

## Render the LEGO-style build-step pictures with OpenSCAD
instructions: $(STEP_PNGS)

build/images/step_00.png: $(SCAD) ../src/color_sudoku_board.scad
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'step=0' --imgsize=1400,1000 --camera=0,0,0,55,0,25,0 --viewall --autocenter --projection=o --colorscheme=Tomorrow $<

build/images/step_%.png: $(SCAD) ../src/color_sudoku_board.scad
	@mkdir -p $(dir $@)
	$(OPENSCAD) -o $@ -D 'step=$(shell echo $* | sed 's/^0//')' --imgsize=1200,900 --camera=$(CAMERA) --projection=p --colorscheme=Tomorrow $<

clean:
	rm -f output/*.pdf output/*.png build/images/*.png
