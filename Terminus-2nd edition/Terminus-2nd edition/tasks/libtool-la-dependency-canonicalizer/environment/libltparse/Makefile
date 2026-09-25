CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra

all: ltparse

ltparse: parse_la.c
	$(CC) $(CFLAGS) -o $@ parse_la.c

clean:
	rm -f ltparse
