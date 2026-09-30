#ifndef ZONEC_BUF_H
#define ZONEC_BUF_H

#include <stddef.h>
#include <stdint.h>

/* Growable byte buffer, used for both presentation text and wire data. */
typedef struct {
    unsigned char *data;
    size_t len;
    size_t cap;
} buf_t;

void buf_init(buf_t *b);
void buf_free(buf_t *b);
void buf_reset(buf_t *b);
void buf_put(buf_t *b, const void *p, size_t n);
void buf_put8(buf_t *b, unsigned v);
void buf_put16(buf_t *b, unsigned v);
void buf_put32(buf_t *b, uint32_t v);
void buf_puts(buf_t *b, const char *s);
void buf_printf(buf_t *b, const char *fmt, ...);
/* NUL-terminates the contents (not counted in len) and returns them. */
const char *buf_cstr(buf_t *b);

#endif
