#include "rdata.h"
#include "ttl.h"
#include "util.h"

#include <strings.h>

static const rrtype_t types[] = {
    { "A", TYPE_A, rr_a_parse, rr_a_format },
    { "NS", TYPE_NS, rr_name_parse, rr_name_format },
    { "CNAME", TYPE_CNAME, rr_name_parse, rr_name_format },
    { "SOA", TYPE_SOA, rr_soa_parse, rr_soa_format },
    { "PTR", TYPE_PTR, rr_name_parse, rr_name_format },
    { "MX", TYPE_MX, rr_mx_parse, rr_mx_format },
    { "TXT", TYPE_TXT, rr_txt_parse, rr_txt_format },
    { "AAAA", TYPE_AAAA, rr_aaaa_parse, rr_aaaa_format },
    { "SRV", TYPE_SRV, rr_srv_parse, rr_srv_format },
    { "ZONEMD", TYPE_ZONEMD, rr_zonemd_parse, rr_zonemd_format },
    { "CAA", TYPE_CAA, rr_caa_parse, rr_caa_format },
};

#define NTYPES (sizeof types / sizeof types[0])

const rrtype_t *rrtype_by_name(const char *name)
{
    for (size_t i = 0; i < NTYPES; i++)
        if (strcasecmp(types[i].name, name) == 0)
            return &types[i];
    return NULL;
}

const rrtype_t *rrtype_by_code(uint16_t code)
{
    for (size_t i = 0; i < NTYPES; i++)
        if (types[i].code == code)
            return &types[i];
    return NULL;
}

void rd_expect(const rdctx_t *cx, size_t n, size_t want)
{
    if (n != want)
        fail_at(cx->pos, "%s record needs %zu RDATA fields, got %zu", cx->type, want, n);
}

void rd_name(const rdctx_t *cx, const token_t *t, buf_t *rd)
{
    dname_t n;
    const char *err = NULL;
    if (t->quoted)
        fail_at(cx->pos, "quoted string where a domain name is expected");
    if (name_parse(t->text, cx->origin, &n, &err))
        fail_at(cx->pos, "%s: %s", t->text, err);
    buf_put(rd, n.wire, (size_t)n.len);
}

uint32_t rd_number(const rdctx_t *cx, const token_t *t, uint32_t max, const char *field)
{
    uint32_t v;
    if (t->quoted || parse_u32(t->text, max, &v))
        fail_at(cx->pos, "bad %s %s \"%s\"", cx->type, field, t->text);
    return v;
}

uint32_t rd_period(const rdctx_t *cx, const token_t *t, const char *field)
{
    uint32_t v;
    if (t->quoted || ttl_parse(t->text, &v))
        fail_at(cx->pos, "bad %s %s \"%s\"", cx->type, field, t->text);
    return v;
}

size_t rd_fmt_name(const unsigned char *rd, size_t len, size_t off, buf_t *out)
{
    dname_t n;
    size_t next = name_from_wire(rd, len, off, &n);
    if (!next) {
        buf_puts(out, "<bad-name>");
        return len;
    }
    name_format(&n, out);
    return next;
}

uint32_t rd_get16(const unsigned char *p)
{
    return ((uint32_t)p[0] << 8) | p[1];
}

uint32_t rd_get32(const unsigned char *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3];
}
