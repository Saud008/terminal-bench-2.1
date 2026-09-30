#include "parser.h"
#include "rdata.h"
#include "util.h"
#include "zonemd.h"

#include <strings.h>

static int is_class_name(const char *t)
{
    return strcasecmp(t, "CH") == 0 || strcasecmp(t, "HS") == 0 ||
           strcasecmp(t, "CS") == 0 || strcasecmp(t, "ANY") == 0 ||
           strcasecmp(t, "NONE") == 0;
}

static void parse_rr(parse_ctx_t *ctx, const char *path, const lline_t *ll)
{
    srcpos_t pos = { path, ll->line };
    zone_t *z = ctx->zone;
    dname_t owner;
    size_t i = 0;
    int have_ttl = 0, have_class = 0;
    uint32_t ttl = 0;

    if (ll->indented) {
        if (!ctx->have_owner)
            fail_at(&pos, "no previous owner name");
        owner = ctx->owner;
    } else {
        const char *err = NULL;
        if (ll->v[0].quoted)
            fail_at(&pos, "quoted string where an owner name is expected");
        if (name_parse(ll->v[0].text, &ctx->origin, &owner, &err))
            fail_at(&pos, "%s: %s", ll->v[0].text, err);
        i = 1;
    }

    for (int k = 0; k < 2 && i < ll->n && !ll->v[i].quoted; k++) {
        const char *t = ll->v[i].text;
        if (t[0] >= '0' && t[0] <= '9') {
            if (have_ttl)
                fail_at(&pos, "TTL given twice");
            if (ttl_parse(t, &ttl))
                fail_at(&pos, "bad TTL \"%s\"", t);
            have_ttl = 1;
        } else if (strcasecmp(t, "IN") == 0) {
            if (have_class)
                fail_at(&pos, "class given twice");
            have_class = 1;
        } else if (is_class_name(t)) {
            fail_at(&pos, "class %s is not supported", t);
        } else {
            break;
        }
        i++;
    }

    if (i >= ll->n)
        fail_at(&pos, "missing record type");
    const rrtype_t *rt = ll->v[i].quoted ? NULL : rrtype_by_name(ll->v[i].text);
    if (!rt)
        fail_at(&pos, "unknown record type \"%s\"", ll->v[i].text);
    i++;

    if (!name_is_subdomain(&owner, &z->origin)) {
        buf_t t;
        buf_init(&t);
        name_format(&owner, &t);
        fail_at(&pos, "%s is outside the zone", buf_cstr(&t));
    }

    buf_t rd;
    rdctx_t cx = { &ctx->origin, &pos, rt->name };
    buf_init(&rd);
    rt->parse(&cx, ll->v + i, ll->n - i, &rd);

    if (rt->code == TYPE_SOA) {
        if (!name_equal(&owner, &z->origin))
            fail_at(&pos, "SOA record is not at the zone apex");
        if (z->have_soa)
            fail_at(&pos, "more than one SOA record");
        z->have_soa = 1;
        z->soa_serial = rr_soa_serial(rd.data, rd.len);
        z->soa_minimum = rr_soa_minimum(rd.data, rd.len);
    }

    if (rt->code == TYPE_ZONEMD && name_equal(&owner, &z->origin)) {
        if (rd.data[4] != ZONEMD_SCHEME_SIMPLE || rd.data[5] != ZONEMD_HASH_SHA384)
            fail_at(&pos, "unsupported ZONEMD scheme %u / hash algorithm %u", rd.data[4], rd.data[5]);
        if (z->have_zonemd)
            fail_at(&pos, "more than one ZONEMD record at the zone apex");
        z->have_zonemd = 1;
    }

    if (have_ttl)
        ttl_ctx_note_explicit(&ctx->ttl, ttl);
    else if (!ttl_ctx_default(&ctx->ttl, &ttl)) {
        if (!z->have_soa)
            fail_at(&pos, "no TTL specified");
        ttl = z->soa_minimum;
    }

    zone_add(z, &owner, rt->code, ttl, rd.data, rd.len);
    buf_free(&rd);

    ctx->owner = owner;
    ctx->have_owner = 1;
}

void parse_file(parse_ctx_t *ctx, const char *path, const srcpos_t *from)
{
    lexer_t *lx = lexer_open(path);
    lline_t ll;

    if (!lx) {
        if (from)
            fail_at(from, "cannot open %s", path);
        fail_file(path, "cannot open file");
    }

    lline_init(&ll);
    while (lexer_next(lx, &ll)) {
        if (!ll.indented && !ll.v[0].quoted && ll.v[0].text[0] == '$')
            parse_directive(ctx, lexer_path(lx), &ll);
        else
            parse_rr(ctx, lexer_path(lx), &ll);
    }
    lline_clear(&ll);
    free(ll.v);
    lexer_close(lx);
}
