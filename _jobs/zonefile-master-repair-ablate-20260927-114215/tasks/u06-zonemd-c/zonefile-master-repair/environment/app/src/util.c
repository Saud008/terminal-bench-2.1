#include "util.h"

#include <stdio.h>
#include <string.h>

void *xmalloc(size_t n)
{
    void *p = malloc(n ? n : 1);
    if (!p) {
        fputs("zonec: out of memory\n", stderr);
        exit(3);
    }
    return p;
}

void *xrealloc(void *p, size_t n)
{
    void *q = realloc(p, n ? n : 1);
    if (!q) {
        fputs("zonec: out of memory\n", stderr);
        exit(3);
    }
    return q;
}

char *xstrdup(const char *s)
{
    size_t n = strlen(s) + 1;
    char *d = xmalloc(n);
    memcpy(d, s, n);
    return d;
}

int parse_u32(const char *s, uint32_t max, uint32_t *out)
{
    uint64_t v = 0;
    if (!*s)
        return -1;
    for (; *s; s++) {
        if (*s < '0' || *s > '9')
            return -1;
        v = v * 10 + (uint64_t)(*s - '0');
        if (v > max)
            return -1;
    }
    *out = (uint32_t)v;
    return 0;
}

static int is_digit(char c)
{
    return c >= '0' && c <= '9';
}

int decode_string(const char *raw, unsigned char *out, size_t cap, size_t *len)
{
    size_t n = 0;
    const char *p = raw;
    while (*p) {
        unsigned c;
        if (*p == '\\') {
            if (is_digit(p[1])) {
                if (!is_digit(p[2]) || !is_digit(p[3]))
                    return DECODE_BAD_ESCAPE;
                c = (unsigned)(p[1] - '0') * 100 + (unsigned)(p[2] - '0') * 10 + (unsigned)(p[3] - '0');
                if (c > 255)
                    return DECODE_BAD_ESCAPE;
                p += 4;
            } else if (p[1]) {
                c = (unsigned char)p[1];
                p += 2;
            } else {
                return DECODE_BAD_ESCAPE;
            }
        } else {
            c = (unsigned char)*p++;
        }
        if (n >= cap)
            return DECODE_TOO_LONG;
        out[n++] = (unsigned char)c;
    }
    *len = n;
    return DECODE_OK;
}

void emit_string(buf_t *b, const unsigned char *s, size_t n)
{
    buf_put8(b, '"');
    for (size_t i = 0; i < n; i++) {
        unsigned char c = s[i];
        if (c == '"' || c == '\\') {
            buf_put8(b, '\\');
            buf_put8(b, c);
        } else if (c < 0x20 || c >= 0x7f) {
            buf_printf(b, "\\%03u", c);
        } else {
            buf_put8(b, c);
        }
    }
    buf_put8(b, '"');
}
