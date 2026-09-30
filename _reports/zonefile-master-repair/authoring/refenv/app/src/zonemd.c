#include "zonemd.h"
#include "rdata.h"
#include "sha384.h"
#include "util.h"

#include <string.h>

static int is_apex_zonemd(const zone_t *z, const rr_t *r)
{
    return r->type == TYPE_ZONEMD && name_equal(&r->owner, &z->origin);
}

static void hash_rr(sha384_ctx *h, const rr_t *r)
{
    buf_t w;

    buf_init(&w);
    buf_put(&w, r->owner.wire, (size_t)r->owner.len);
    buf_put16(&w, r->type);
    buf_put16(&w, 1);
    buf_put32(&w, r->ttl);
    buf_put16(&w, (unsigned)r->rdlen);
    buf_put(&w, r->rd, r->rdlen);
    sha384_update(h, w.data, w.len);
    buf_free(&w);
}

void zonemd_update(zone_t *z)
{
    rr_t *md = NULL;
    sha384_ctx h;
    unsigned char digest[SHA384_DIGEST_LEN];
    buf_t rd;

    for (size_t i = 0; i < z->n; i++)
        if (is_apex_zonemd(z, &z->v[i]))
            md = &z->v[i];
    if (!md)
        return;

    sha384_init(&h);
    for (size_t i = 0; i < z->n; i++) {
        if (is_apex_zonemd(z, &z->v[i]))
            continue;
        hash_rr(&h, &z->v[i]);
    }
    sha384_final(&h, digest);

    buf_init(&rd);
    buf_put32(&rd, z->soa_serial);
    buf_put8(&rd, ZONEMD_SCHEME_SIMPLE);
    buf_put8(&rd, ZONEMD_HASH_SHA384);
    buf_put(&rd, digest, sizeof digest);
    free(md->rd);
    md->rd = rd.data;
    md->rdlen = rd.len;
}
