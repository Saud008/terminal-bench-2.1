#include "rdata.h"

void rr_srv_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    rd_expect(cx, n, 4);
    buf_put16(rd, rd_number(cx, &tok[0], 65535, "priority"));
    buf_put16(rd, rd_number(cx, &tok[1], 65535, "weight"));
    buf_put16(rd, rd_number(cx, &tok[2], 65535, "port"));
    rd_name(cx, &tok[3], rd);
}

void rr_srv_format(const unsigned char *rd, size_t len, buf_t *out)
{
    buf_printf(out, "%u %u %u ", (unsigned)rd_get16(rd), (unsigned)rd_get16(rd + 2),
               (unsigned)rd_get16(rd + 4));
    rd_fmt_name(rd, len, 6, out);
}
