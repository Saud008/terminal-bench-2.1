#ifndef ZONEC_SHA384_H
#define ZONEC_SHA384_H

#include <stddef.h>
#include <stdint.h>

#define SHA384_DIGEST_LEN 48

/* SHA-384 (FIPS 180-4): SHA-512 compression with its own initial values,
 * output truncated to six words. */
typedef struct {
    uint64_t h[8];
    unsigned char buf[128];
    size_t buflen;
    uint64_t total;
} sha384_ctx;

void sha384_init(sha384_ctx *c);
void sha384_update(sha384_ctx *c, const void *data, size_t n);
void sha384_final(sha384_ctx *c, unsigned char out[SHA384_DIGEST_LEN]);

#endif
