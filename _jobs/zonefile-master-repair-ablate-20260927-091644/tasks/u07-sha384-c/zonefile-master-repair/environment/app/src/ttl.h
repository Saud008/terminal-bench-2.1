#ifndef ZONEC_TTL_H
#define ZONEC_TTL_H

#include <stdint.h>

#define TTL_MAX 2147483647u

/* Parses "3600" or unit form such as "1h30m" (w, d, h, m, s; any case).
 * Returns 0 on success. */
int ttl_parse(const char *text, uint32_t *out);

/* Default-TTL state of a master file (see docs/master-files.md). */
typedef struct {
    int has_dollar;
    uint32_t dollar;   /* value of the $TTL directive in effect */
    int has_last;
    uint32_t last;     /* last TTL written explicitly on a record */
} ttl_ctx_t;

void ttl_ctx_set_dollar(ttl_ctx_t *c, uint32_t v);
void ttl_ctx_note_explicit(ttl_ctx_t *c, uint32_t v);

/* Default TTL for a record written without one. Returns 0 if the file
 * gives no default. */
int ttl_ctx_default(const ttl_ctx_t *c, uint32_t *out);

#endif
