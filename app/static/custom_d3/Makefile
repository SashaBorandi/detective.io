# Makefile -- Detective.io

D3 = ./d3.js

D3_FOLDER = ./node_modules/d3/

SMASH = ./node_modules/.bin/smash
RM = rm -rf

_LIBRARY_FILES = start.js        \
				 layout/force.js \
				 end.js
LIBRARY_FILES = $(addprefix $(D3_FOLDER)src/, $(_LIBRARY_FILES))

all: build clean

$(D3): install_deps
	$(SMASH) $(LIBRARY_FILES) > $@

build: $(D3)

install_deps:
	npm install

clean:
	$(RM) ./node_modules