#include "rdata.h"
#include "util.h"

void rr_txt_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    if (n == 0)
        fail_at(cx->pos, "TXT record needs at least one character-string");
    for (size_t i = 0; i < n; i++) {
        unsigned char s[255];
        size_t len = 0;
        switch (decode_string(tok[i].text, s, sizeof s, &len)) {
        case DECODE_BAD_ESCAPE:
            fail_at(cx->pos, "bad escape in character-string");
        case DECODE_TOO_LONG:
            fail_at(cx->pos, "character-string longer than 255 octets");
        default:
            break;
        }
        buf_put8(rd, (unsigned)len);
        buf_put(rd, s, len);
    }
}

void rr_txt_format(const unsigned char *rd, size_t len, buf_t *out)
{
    size_t off = 0;
    while (off < len) {
        size_t n = rd[off];
        if (off + 1 + n > len)
            break;
        if (off)
            buf_put8(out, ' ');
        emit_string(out, rd + off + 1, n);
        off += 1 + n;
    }
}
