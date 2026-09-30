#include "rdata.h"

#include <arpa/inet.h>
#include <string.h>

void rr_a_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    unsigned char addr[4];
    const char *p;
    int part = 0;

    rd_expect(cx, n, 1);
    p = tok[0].text;
    if (tok[0].quoted)
        goto bad;
    for (;;) {
        unsigned v = 0;
        int digits = 0;
        while (*p >= '0' && *p <= '9') {
            v = v * 10 + (unsigned)(*p++ - '0');
            if (++digits > 3)
                goto bad;
        }
        if (!digits || v > 255)
            goto bad;
        addr[part++] = (unsigned char)v;
        if (part == 4)
            break;
        if (*p++ != '.')
            goto bad;
    }
    if (*p)
        goto bad;
    buf_put(rd, addr, 4);
    return;
bad:
    fail_at(cx->pos, "bad IPv4 address \"%s\"", tok[0].text);
}

void rr_a_format(const unsigned char *rd, size_t len, buf_t *out)
{
    (void)len;
    buf_printf(out, "%u.%u.%u.%u", rd[0], rd[1], rd[2], rd[3]);
}

void rr_aaaa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    unsigned char addr[16];
    rd_expect(cx, n, 1);
    if (tok[0].quoted || inet_pton(AF_INET6, tok[0].text, addr) != 1)
        fail_at(cx->pos, "bad IPv6 address \"%s\"", tok[0].text);
    buf_put(rd, addr, 16);
}

/* RFC 5952 text form: lowercase hex, no leading zeros, the longest run of
 * two or more zero groups (the first one on a tie) shortened to "::". */
void rr_aaaa_format(const unsigned char *rd, size_t len, buf_t *out)
{
    unsigned g[8];
    int best = -1, bestlen = 0;

    (void)len;
    for (int i = 0; i < 8; i++)
        g[i] = rd_get16(rd + 2 * i);
    for (int i = 0; i < 8;) {
        if (g[i] != 0) {
            i++;
            continue;
        }
        int j = i;
        while (j < 8 && g[j] == 0)
            j++;
        if (j - i > bestlen) {
            best = i;
            bestlen = j - i;
        }
        i = j;
    }
    if (bestlen < 2)
        best = -1;

    for (int i = 0; i < 8; i++) {
        if (i == best) {
            buf_puts(out, "::");
            i += bestlen - 1;
            continue;
        }
        if (i > 0 && i != best + bestlen)
            buf_put8(out, ':');
        buf_printf(out, "%x", g[i]);
    }
}
