#include "rdata.h"

static const char *const periods[] = { "refresh", "retry", "expire", "minimum" };

void rr_soa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd)
{
    rd_expect(cx, n, 7);
    rd_name(cx, &tok[0], rd);
    rd_name(cx, &tok[1], rd);
    buf_put32(rd, rd_number(cx, &tok[2], 4294967295u, "serial"));
    for (int i = 0; i < 4; i++)
        buf_put32(rd, rd_period(cx, &tok[3 + i], periods[i]));
}

void rr_soa_format(const unsigned char *rd, size_t len, buf_t *out)
{
    size_t off = rd_fmt_name(rd, len, 0, out);
    buf_put8(out, ' ');
    off = rd_fmt_name(rd, len, off, out);
    for (int i = 0; i < 5 && off + 4 <= len; i++, off += 4)
        buf_printf(out, " %u", (unsigned)rd_get32(rd + off));
}

uint32_t rr_soa_minimum(const unsigned char *rd, size_t len)
{
    return rd_get32(rd + len - 4);
}

uint32_t rr_soa_serial(const unsigned char *rd, size_t len)
{
    return rd_get32(rd + len - 20);
}
