# A tiny project that exercises the common features. The "compiler" only
# echoes and touches files, so it runs anywhere:
#
#   cd examples/demo && ../../brickmake && ../../brickmake release

OUT  := build
SRCS := $(sort $(wildcard src/*.c))
OBJS := $(patsubst src/%.c,$(OUT)/%.o,$(SRCS))

CC      = echo cc
CFLAGS  = -O1 -Iinclude

.PHONY: all release clean
all: $(OUT)/demo

release: CFLAGS = -O3 -Iinclude -DNDEBUG
release: all

$(OUT)/demo: $(OBJS) | $(OUT)
	@echo "link $@ <- $^"
	@touch $@

$(OUT)/%.o: src/%.c include/demo.h | $(OUT)
	@$(CC) $(CFLAGS) -c $< -o $@
	@touch $@

$(OUT):
	mkdir -p $@

clean:
	rm -rf $(OUT)
