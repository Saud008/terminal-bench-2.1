#ifndef ZONEC_UTIL_H
#define ZONEC_UTIL_H

#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

#include "buf.h"

void *xmalloc(size_t n);
void *xrealloc(void *p, size_t n);
char *xstrdup(const char *s);

/* Strict unsigned decimal: digits only, no sign, value <= max. 0 on success. */
int parse_u32(const char *s, uint32_t max, uint32_t *out);

enum {
    DECODE_OK = 0,
    DECODE_BAD_ESCAPE = -1,
    DECODE_TOO_LONG = -2,
};

/* Decodes \X and \DDD escapes of a character-string token into at most
 * cap octets. */
int decode_string(const char *raw, unsigned char *out, size_t cap, size_t *len);

/* Appends a character-string in quoted presentation form. */
void emit_string(buf_t *b, const unsigned char *s, size_t n);

#endif
