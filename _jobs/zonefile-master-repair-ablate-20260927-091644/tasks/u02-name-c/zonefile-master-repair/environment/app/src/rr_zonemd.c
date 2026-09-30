#include "rdata.h"

#include <string.h>

#define ZONEMD_DIGEST_MIN 12
#define ZONEMD_DIGEST_MAX 64

static int hexval(char c)
{
    if (c >= '0' && c <= '9')
        return c - '0';
    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;
    if (c >= 'A' && c <= 'F')
        return c - 'A' + 10;
    return -1;
}

/* serial scheme hash-algorithm digest; the digest may be split over
 * several hex tokens. */
void rr_zonemd_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    unsigned char digest[ZONEMD_DIGEST_MAX];
    size_t dlen = 0;
    int half = -1;

    if (n < 4)
        fail_at(cx->pos, "ZONEMD record needs serial, scheme, hash algorithm and digest");
    buf_put32(rd, rd_number(cx, &tok[0], 4294967295u, "serial"));
    buf_put8(rd, rd_number(cx, &tok[1], 255, "scheme"));
    buf_put8(rd, rd_number(cx, &tok[2], 255, "hash algorithm"));

    for (size_t i = 3; i < n; i++) {
        if (tok[i].quoted)
            fail_at(cx->pos, "bad ZONEMD digest");
        for (const char *p = tok[i].text; *p; p++) {
            int v = hexval(*p);
            if (v < 0)
                fail_at(cx->pos, "bad ZONEMD digest");
            if (half < 0) {
                half = v;
                continue;
            }
            if (dlen == ZONEMD_DIGEST_MAX)
                fail_at(cx->pos, "ZONEMD digest longer than %d octets", ZONEMD_DIGEST_MAX);
            digest[dlen++] = (unsigned char)(half << 4 | v);
            half = -1;
        }
    }
    if (half >= 0 || dlen < ZONEMD_DIGEST_MIN)
        fail_at(cx->pos, "bad ZONEMD digest");
    buf_put(rd, digest, dlen);
}

void rr_zonemd_format(const unsigned char *rd, size_t len, buf_t *out)
{
    buf_printf(out, "%u %u %u ", (unsigned)rd_get32(rd), rd[4], rd[5]);
    for (size_t i = 6; i < len; i++)
        buf_printf(out, "%02X", rd[i]);
}
