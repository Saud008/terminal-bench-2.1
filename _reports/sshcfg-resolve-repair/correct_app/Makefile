CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter
PREFIX ?= /usr/local

SRCS = $(wildcard src/*.c)
HDRS = $(wildcard src/*.h)

hopcfg: $(SRCS) $(HDRS)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

check: hopcfg
	sh t/run.sh ./hopcfg

install: hopcfg
	install -m 0755 hopcfg $(PREFIX)/bin/hopcfg

clean:
	rm -f hopcfg

.PHONY: check install clean
