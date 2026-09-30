#include "buf.h"
#include "util.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>

void buf_init(buf_t *b)
{
    b->data = NULL;
    b->len = 0;
    b->cap = 0;
}

void buf_free(buf_t *b)
{
    free(b->data);
    buf_init(b);
}

void buf_reset(buf_t *b)
{
    b->len = 0;
}

static void reserve(buf_t *b, size_t extra)
{
    size_t need = b->len + extra + 1;
    if (need <= b->cap)
        return;
    size_t cap = b->cap ? b->cap : 64;
    while (cap < need)
        cap *= 2;
    b->data = xrealloc(b->data, cap);
    b->cap = cap;
}

void buf_put(buf_t *b, const void *p, size_t n)
{
    reserve(b, n);
    if (n)
        memcpy(b->data + b->len, p, n);
    b->len += n;
}

void buf_put8(buf_t *b, unsigned v)
{
    unsigned char c = (unsigned char)v;
    buf_put(b, &c, 1);
}

void buf_put16(buf_t *b, unsigned v)
{
    unsigned char c[2] = { (unsigned char)(v >> 8), (unsigned char)v };
    buf_put(b, c, 2);
}

void buf_put32(buf_t *b, uint32_t v)
{
    unsigned char c[4] = {
        (unsigned char)(v >> 24), (unsigned char)(v >> 16),
        (unsigned char)(v >> 8), (unsigned char)v,
    };
    buf_put(b, c, 4);
}

void buf_puts(buf_t *b, const char *s)
{
    buf_put(b, s, strlen(s));
}

void buf_printf(buf_t *b, const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(NULL, 0, fmt, ap);
    va_end(ap);
    if (n <= 0)
        return;
    reserve(b, (size_t)n);
    va_start(ap, fmt);
    vsnprintf((char *)b->data + b->len, (size_t)n + 1, fmt, ap);
    va_end(ap);
    b->len += (size_t)n;
}

const char *buf_cstr(buf_t *b)
{
    reserve(b, 0);
    b->data[b->len] = '\0';
    return (const char *)b->data;
}
