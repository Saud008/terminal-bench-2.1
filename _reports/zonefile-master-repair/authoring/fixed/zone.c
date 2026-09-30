#include "zone.h"
#include "rdata.h"
#include "util.h"
#include "zonemd.h"

#include <stdlib.h>
#include <string.h>

void zone_init(zone_t *z, const dname_t *origin)
{
    memset(z, 0, sizeof *z);
    z->origin = *origin;
}

void zone_add(zone_t *z, const dname_t *owner, uint16_t type, uint32_t ttl,
              const unsigned char *rd, size_t rdlen)
{
    buf_t text;

    if (z->n == z->cap) {
        z->cap = z->cap ? z->cap * 2 : 32;
        z->v = xrealloc(z->v, z->cap * sizeof *z->v);
    }
    rr_t *r = &z->v[z->n];
    r->owner = *owner;
    buf_init(&text);
    name_format(owner, &text);
    r->owner_text = xstrdup(buf_cstr(&text));
    buf_free(&text);
    r->type = type;
    r->ttl = ttl;
    r->rd = xmalloc(rdlen);
    memcpy(r->rd, rd, rdlen);
    r->rdlen = rdlen;
    r->seq = z->n;
    z->n++;
}

static int rdata_cmp(const rr_t *a, const rr_t *b)
{
    size_t n = a->rdlen < b->rdlen ? a->rdlen : b->rdlen;
    int r = memcmp(a->rd, b->rd, n);
    if (r)
        return r;
    if (a->rdlen != b->rdlen)
        return a->rdlen < b->rdlen ? -1 : 1;
    return 0;
}

static int same_rrset(const rr_t *a, const rr_t *b)
{
    return a->type == b->type && name_equal(&a->owner, &b->owner);
}

/* Canonical order (RFC 4034 section 6): owner name, then type, then RDATA.
 * Input order breaks ties so duplicates keep their first occurrence. */
static int rr_cmp(const void *pa, const void *pb)
{
    const rr_t *a = pa, *b = pb;
    int r = name_cmp_canonical(&a->owner, &b->owner);
    if (r)
        return r;
    if (a->type != b->type)
        return a->type < b->type ? -1 : 1;
    r = rdata_cmp(a, b);
    if (r)
        return r;
    return a->seq < b->seq ? -1 : a->seq > b->seq;
}

void zone_finish(zone_t *z)
{
    size_t out = 0;

    qsort(z->v, z->n, sizeof *z->v, rr_cmp);

    for (size_t i = 0; i < z->n; i++) {
        if (out > 0 && same_rrset(&z->v[out - 1], &z->v[i]) &&
            rdata_cmp(&z->v[out - 1], &z->v[i]) == 0) {
            free(z->v[i].rd);
            free(z->v[i].owner_text);
            continue;
        }
        z->v[out++] = z->v[i];
    }
    z->n = out;

    for (size_t i = 0; i < z->n;) {
        size_t j = i, first = i;
        while (j < z->n && same_rrset(&z->v[i], &z->v[j])) {
            if (z->v[j].seq < z->v[first].seq)
                first = j;
            j++;
        }
        for (size_t k = i; k < j; k++)
            z->v[k].ttl = z->v[first].ttl;
        i = j;
    }

    zonemd_update(z);
}

void zone_emit(const zone_t *z, buf_t *out)
{
    for (size_t i = 0; i < z->n; i++) {
        const rr_t *r = &z->v[i];
        const rrtype_t *t = rrtype_by_code(r->type);
        buf_printf(out, "%s\t%u\tIN\t%s\t", r->owner_text, (unsigned)r->ttl, t->name);
        t->format(r->rd, r->rdlen, out);
        buf_put8(out, '\n');
    }
}
