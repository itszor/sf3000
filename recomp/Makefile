# Static recompilation of Star Fighter 3000 3.21: the translated program and
# modules (gen/<name>/, from SuperSpider's analyse and gen via
# ../tools/images.py) and game.c, linked with libroger (the RISC OS runtime,
# which also provides the Shared C Library).
ROGER   ?= $(HOME)/stuff/libroger
SS      ?= $(HOME)/stuff/superspider
CC      ?= gcc
CFLAGS  ?= -O2 -g -w -fno-strict-aliasing $(if $(TRACE),-DRECOMP_TRACE)
GEN     := $(wildcard gen/*/code*.c) $(wildcard gen/*/entries.c)
OBJ     := $(GEN:.c=.o) game.o
LIBS    := $(shell pkg-config --libs sdl3) -ljpeg -lm -lpthread
INC     := -I$(ROGER)/include

sf3000: $(OBJ) $(ROGER)/libroger.a
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(ROGER)/libroger.a $(LIBS)

$(ROGER)/libroger.a: FORCE
	$(MAKE) -C $(ROGER) libroger.a

gen/%.o: gen/%.c $(ROGER)/include/roger_cpu.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

game.o: game.c gen/modules.inc $(ROGER)/include/roger.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

# make regen: unsqueeze, analyse and translate every image
regen:
	rm -rf gen
	SUPERSPIDER=$(SS) python3 ../tools/images.py unpack analyse gen

# make roots: the gaps a --trace-gaps run logged (untranslated.log, or
# LOG=...) become roots for the next regen
LOG ?= untranslated.log
roots:
	SUPERSPIDER=$(SS) python3 ../tools/images.py roots $(LOG)

clean:
	rm -f gen/*/*.o game.o sf3000

.PHONY: FORCE regen roots clean
