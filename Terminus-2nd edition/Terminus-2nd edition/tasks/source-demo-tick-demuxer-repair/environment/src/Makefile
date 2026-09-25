CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra -std=c11

demux-read: demux.c
	$(CC) $(CFLAGS) -o demux-read demux.c

.PHONY: clean
clean:
	rm -f demux-read
