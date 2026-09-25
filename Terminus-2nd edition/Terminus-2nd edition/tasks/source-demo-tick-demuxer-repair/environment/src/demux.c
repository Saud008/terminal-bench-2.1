/* Low-level SRCDEM packet reader — prints one JSON object per packet line. */
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define MAGIC "SRCDEM"
#define HDR_SIZE 36
#define PKT_USERCMD 0x01
#define PKT_SIGNON 0x02
#define PKT_STRING 0x03

static int read_full(int fd, void *buf, size_t n) {
    uint8_t *p = buf;
    size_t left = n;
    while (left > 0) {
        ssize_t r = read(fd, p, left);
        if (r == 0) return 0;
        if (r < 0) return -1;
        p += (size_t)r;
        left -= (size_t)r;
    }
    return 1;
}

static int parse_packet(const uint8_t *data, size_t avail, size_t *consumed) {
    if (avail < 1) return 2;
    uint8_t typ = data[0];
    if (typ == PKT_USERCMD) {
        if (avail < 8) return 2;
        uint8_t str_idx = data[1];
        uint16_t seq;
        uint32_t arg;
        memcpy(&seq, data + 2, 2);
        memcpy(&arg, data + 4, 4);
        printf("{\"type\":\"usercmd\",\"str_idx\":%u,\"seq\":%u,\"arg\":%u}\n",
               str_idx, seq, arg);
        *consumed = 8;
        return 0;
    }
    if (typ == PKT_SIGNON) {
        if (avail < 5) return 2;
        uint32_t base;
        memcpy(&base, data + 1, 4);
        printf("{\"type\":\"signon_reset\",\"new_base\":%u}\n", base);
        *consumed = 5;
        return 0;
    }
    if (typ == PKT_STRING) {
        if (avail < 2) return 2;
        printf("{\"type\":\"string_ref\",\"str_idx\":%u}\n", data[1]);
        *consumed = 2;
        return 0;
    }
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: demux-read <demo> <packet_off> <packet_len>\n");
        return 1;
    }
    const char *path = argv[1];
    long off = strtol(argv[2], NULL, 10);
    long len = strtol(argv[3], NULL, 10);
    if (off < 0 || len < 0) return 1;

    int fd = open(path, O_RDONLY);
    if (fd < 0) return 1;

    uint8_t *buf = malloc((size_t)len);
    if (!buf) return 1;
    if (lseek(fd, off, SEEK_SET) < 0) {
        free(buf);
        close(fd);
        return 1;
    }
    size_t got = 0;
    while (got < (size_t)len) {
        ssize_t r = read(fd, buf + got, (size_t)len - got);
        if (r == 0) {
            free(buf);
            close(fd);
            return 2;
        }
        if (r < 0) {
            free(buf);
            close(fd);
            return 1;
        }
        got += (size_t)r;
    }
    close(fd);

    size_t pos = 0;
    while (pos < (size_t)len) {
        size_t consumed = 0;
        int rc = parse_packet(buf + pos, (size_t)len - pos, &consumed);
        if (rc == 2) {
            free(buf);
            return 2;
        }
        if (rc != 0) {
            free(buf);
            return 1;
        }
        pos += consumed;
    }
    free(buf);
    return 0;
}
