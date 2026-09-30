CC      ?= cc
CFLAGS  ?= -O2 -g -Wall -Wextra -std=c11
CPPFLAGS += -D_POSIX_C_SOURCE=200809L
BUILD   ?= build

SRCS := $(wildcard src/*.c)
HDRS := $(wildcard src/*.h)
OBJS := $(patsubst src/%.c,$(BUILD)/%.o,$(SRCS))

all: $(BUILD)/zonec

$(BUILD)/zonec: $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

$(BUILD)/%.o: src/%.c $(HDRS) | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

$(BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)

.PHONY: all clean
