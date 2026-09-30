#include "rdata.h"
#include "util.h"

#include <string.h>

#define CAA_VALUE_MAX 1024

static int is_alnum(char c)
{
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
}

void rr_caa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    unsigned char value[CAA_VALUE_MAX];
    size_t vlen = 0;
    size_t tlen;

    rd_expect(cx, n, 3);
    buf_put8(rd, rd_number(cx, &tok[0], 255, "flags"));

    tlen = strlen(tok[1].text);
    if (tok[1].quoted || tlen == 0 || tlen > 15)
        fail_at(cx->pos, "bad CAA tag \"%s\"", tok[1].text);
    for (size_t i = 0; i < tlen; i++)
        if (!is_alnum(tok[1].text[i]))
            fail_at(cx->pos, "bad CAA tag \"%s\"", tok[1].text);
    buf_put8(rd, (unsigned)tlen);
    buf_put(rd, tok[1].text, tlen);

    switch (decode_string(tok[2].text, value, sizeof value, &vlen)) {
    case DECODE_BAD_ESCAPE:
        fail_at(cx->pos, "bad escape in CAA value");
    case DECODE_TOO_LONG:
        fail_at(cx->pos, "CAA value longer than %d octets", CAA_VALUE_MAX);
    default:
        break;
    }
    buf_put(rd, value, vlen);
}

void rr_caa_format(const unsigned char *rd, size_t len, buf_t *out)
{
    size_t tlen = rd[1];
    buf_printf(out, "%u ", rd[0]);
    buf_put(out, rd + 2, tlen);
    buf_put8(out, ' ');
    emit_string(out, rd + 2 + tlen, len - 2 - tlen);
}
