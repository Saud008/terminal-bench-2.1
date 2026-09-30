#include "rdata.h"

/* NS, CNAME and PTR: a single domain name. */
void rr_name_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    rd_expect(cx, n, 1);
    rd_name(cx, &tok[0], rd);
}

void rr_name_format(const unsigned char *rd, size_t len, buf_t *out)
{
    rd_fmt_name(rd, len, 0, out);
}

void rr_mx_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    rd_expect(cx, n, 2);
    buf_put16(rd, rd_number(cx, &tok[0], 65535, "preference"));
    rd_name(cx, &tok[1], rd);
}

void rr_mx_format(const unsigned char *rd, size_t len, buf_t *out)
{
    buf_printf(out, "%u ", (unsigned)rd_get16(rd));
    rd_fmt_name(rd, len, 2, out);
}
