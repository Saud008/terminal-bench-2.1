#!/usr/bin/env bash
set -euo pipefail

cd /app

# Quoted strings are opaque: parentheses inside them neither open nor close a group.
cat > src/lexer.c <<'ZONEC_LEXER_C'
#include "lexer.h"
#include "buf.h"
#include "diag.h"
#include "util.h"

#include <stdio.h>
#include <string.h>
#include <sys/types.h>

struct lexer {
    FILE *fp;
    char *path;
    int lineno;
    char *line;
    size_t linecap;
};

lexer_t *lexer_open(const char *path)
{
    FILE *fp = fopen(path, "r");
    if (!fp)
        return NULL;
    lexer_t *lx = xmalloc(sizeof *lx);
    lx->fp = fp;
    lx->path = xstrdup(path);
    lx->lineno = 0;
    lx->line = NULL;
    lx->linecap = 0;
    return lx;
}

void lexer_close(lexer_t *lx)
{
    if (!lx)
        return;
    fclose(lx->fp);
    free(lx->path);
    free(lx->line);
    free(lx);
}

const char *lexer_path(const lexer_t *lx)
{
    return lx->path;
}

void lline_init(lline_t *ll)
{
    memset(ll, 0, sizeof *ll);
}

void lline_clear(lline_t *ll)
{
    for (size_t i = 0; i < ll->n; i++)
        free(ll->v[i].text);
    ll->n = 0;
    ll->line = 0;
    ll->indented = 0;
}

static void push(lline_t *ll, buf_t *cur, int quoted)
{
    if (ll->n == ll->cap) {
        ll->cap = ll->cap ? ll->cap * 2 : 8;
        ll->v = xrealloc(ll->v, ll->cap * sizeof *ll->v);
    }
    ll->v[ll->n].text = xstrdup(buf_cstr(cur));
    ll->v[ll->n].quoted = quoted;
    ll->n++;
    buf_reset(cur);
}

int lexer_next(lexer_t *lx, lline_t *ll)
{
    buf_t cur;
    int depth = 0;

    lline_clear(ll);
    buf_init(&cur);

    for (;;) {
        ssize_t got = getline(&lx->line, &lx->linecap, lx->fp);
        if (got < 0) {
            if (depth > 0) {
                srcpos_t pos = { lx->path, ll->line };
                fail_at(&pos, "unbalanced parentheses");
            }
            buf_free(&cur);
            return 0;
        }
        lx->lineno++;

        const char *s = lx->line;
        srcpos_t pos = { lx->path, lx->lineno };
        int intok = 0, inq = 0;

        if (depth == 0) {
            ll->line = lx->lineno;
            ll->indented = (s[0] == ' ' || s[0] == '\t');
        }

        for (size_t i = 0; s[i] && s[i] != '\n'; i++) {
            char c = s[i];

            if (c == '\r' && (s[i + 1] == '\n' || s[i + 1] == '\0'))
                continue;
            if (c == '\\') {
                if (s[i + 1] == '\0' || s[i + 1] == '\n')
                    fail_at(&pos, "backslash at end of line");
                buf_put8(&cur, '\\');
                buf_put8(&cur, (unsigned char)s[++i]);
                if (!inq)
                    intok = 1;
                continue;
            }
            if (inq) {
                if (c == '"') {
                    push(ll, &cur, 1);
                    inq = 0;
                } else {
                    buf_put8(&cur, (unsigned char)c);
                }
                continue;
            }
            if (c == '(' || c == ')') {
                if (intok)
                    push(ll, &cur, 0);
                intok = 0;
                if (c == '(')
                    depth++;
                else if (--depth < 0)
                    fail_at(&pos, "unbalanced parentheses");
                continue;
            }
            if (c == ';')
                break;
            if (c == ' ' || c == '\t') {
                if (intok)
                    push(ll, &cur, 0);
                intok = 0;
                continue;
            }
            if (c == '"') {
                if (intok)
                    push(ll, &cur, 0);
                intok = 0;
                inq = 1;
                continue;
            }
            buf_put8(&cur, (unsigned char)c);
            intok = 1;
        }

        if (inq)
            fail_at(&pos, "unterminated quoted string");
        if (intok)
            push(ll, &cur, 0);

        if (depth > 0)
            continue;
        if (ll->n > 0) {
            buf_free(&cur);
            return 1;
        }
    }
}
ZONEC_LEXER_C

# Label limits count decoded octets, and case folding runs on the decoded name so \DDD escapes fold too.
cat > src/name.c <<'ZONEC_NAME_C'
#include "name.h"

#include <string.h>

const dname_t name_root = { { 0 }, 1 };

static int is_digit(char c)
{
    return c >= '0' && c <= '9';
}

static void name_lower(dname_t *n)
{
    int i = 0;
    while (n->wire[i]) {
        int len = n->wire[i];
        for (int j = i + 1; j <= i + len; j++)
            if (n->wire[j] >= 'A' && n->wire[j] <= 'Z')
                n->wire[j] = (unsigned char)(n->wire[j] - 'A' + 'a');
        i += len + 1;
    }
}

int name_parse(const char *text, const dname_t *origin, dname_t *out, const char **err)
{
    unsigned char w[NAME_MAXWIRE];
    int wl = 0;
    int absolute = 0;
    const char *p = text;

    if (strcmp(text, "@") == 0) {
        *out = *origin;
        return 0;
    }
    if (strcmp(text, ".") == 0) {
        *out = name_root;
        return 0;
    }

    while (*p) {
        int lenpos = wl++;
        int lablen = 0;

        while (*p && *p != '.') {
            unsigned c;
            if (*p == '\\') {
                if (is_digit(p[1])) {
                    if (!is_digit(p[2]) || !is_digit(p[3])) {
                        *err = "bad escape in name";
                        return -1;
                    }
                    c = (unsigned)(p[1] - '0') * 100 + (unsigned)(p[2] - '0') * 10 + (unsigned)(p[3] - '0');
                    if (c > 255) {
                        *err = "bad escape in name";
                        return -1;
                    }
                    p += 4;
                } else if (p[1]) {
                    c = (unsigned char)p[1];
                    p += 2;
                } else {
                    *err = "bad escape in name";
                    return -1;
                }
            } else {
                c = (unsigned char)*p++;
            }
            if (lablen == LABEL_MAX) {
                *err = "label too long";
                return -1;
            }
            if (wl >= NAME_MAXWIRE - 1) {
                *err = "name too long";
                return -1;
            }
            w[wl++] = (unsigned char)c;
            lablen++;
        }
        if (lablen == 0) {
            *err = "empty label";
            return -1;
        }
        w[lenpos] = (unsigned char)lablen;
        if (*p == '.') {
            p++;
            if (*p == '\0')
                absolute = 1;
        }
    }

    if (absolute) {
        w[wl++] = 0;
    } else {
        if (wl + origin->len > NAME_MAXWIRE) {
            *err = "name too long";
            return -1;
        }
        memcpy(w + wl, origin->wire, (size_t)origin->len);
        wl += origin->len;
    }

    memcpy(out->wire, w, (size_t)wl);
    out->len = wl;
    name_lower(out);
    return 0;
}

size_t name_from_wire(const unsigned char *rd, size_t rdlen, size_t off, dname_t *out)
{
    int wl = 0;
    for (;;) {
        if (off >= rdlen)
            return 0;
        unsigned len = rd[off];
        if (len > LABEL_MAX || off + 1 + len > rdlen || wl + 1 + (int)len > NAME_MAXWIRE)
            return 0;
        memcpy(out->wire + wl, rd + off, len + 1);
        wl += (int)len + 1;
        off += len + 1;
        if (len == 0)
            break;
    }
    out->len = wl;
    return off;
}

int name_equal(const dname_t *a, const dname_t *b)
{
    return a->len == b->len && memcmp(a->wire, b->wire, (size_t)a->len) == 0;
}

static int label_offsets(const dname_t *n, int *off)
{
    int k = 0, i = 0;
    while (n->wire[i]) {
        off[k++] = i;
        i += n->wire[i] + 1;
    }
    return k;
}

int name_cmp_canonical(const dname_t *a, const dname_t *b)
{
    int oa[NAME_MAXWIRE / 2], ob[NAME_MAXWIRE / 2];
    int ka = label_offsets(a, oa);
    int kb = label_offsets(b, ob);

    while (ka > 0 && kb > 0) {
        const unsigned char *la = a->wire + oa[--ka];
        const unsigned char *lb = b->wire + ob[--kb];
        int n = la[0] < lb[0] ? la[0] : lb[0];
        int r = memcmp(la + 1, lb + 1, (size_t)n);
        if (r)
            return r < 0 ? -1 : 1;
        if (la[0] != lb[0])
            return la[0] < lb[0] ? -1 : 1;
    }
    if (ka)
        return 1;
    if (kb)
        return -1;
    return 0;
}

int name_is_subdomain(const dname_t *child, const dname_t *parent)
{
    int i = 0;
    for (;;) {
        if (child->len - i == parent->len &&
            memcmp(child->wire + i, parent->wire, (size_t)parent->len) == 0)
            return 1;
        if (child->wire[i] == 0)
            return 0;
        i += child->wire[i] + 1;
    }
}

void name_format(const dname_t *n, buf_t *out)
{
    int i = 0;
    if (n->wire[0] == 0) {
        buf_put8(out, '.');
        return;
    }
    while (n->wire[i]) {
        int len = n->wire[i];
        for (int j = i + 1; j <= i + len; j++) {
            unsigned char c = n->wire[j];
            if (strchr(".\\\"();@$", c) && c != '\0') {
                buf_put8(out, '\\');
                buf_put8(out, c);
            } else if (c <= 0x20 || c >= 0x7f) {
                buf_printf(out, "\\%03u", c);
            } else {
                buf_put8(out, c);
            }
        }
        buf_put8(out, '.');
        i += len + 1;
    }
}
ZONEC_NAME_C

# A record TTL never overrides the $TTL value in effect.

# $ORIGIN leaves the previous owner alone, includes restore the TTL state and resolve paths from the including file's directory.
cat > src/directives.c <<'ZONEC_DIRECTIVES_C'
#include "parser.h"
#include "util.h"

#include <string.h>
#include <strings.h>

/* Relative $INCLUDE paths are taken from the directory of the file that
 * contains the directive. */
static char *include_path(const char *including, const char *name)
{
    const char *slash;
    size_t dirlen;
    char *path;

    if (name[0] == '/')
        return xstrdup(name);
    slash = strrchr(including, '/');
    if (!slash)
        return xstrdup(name);
    dirlen = (size_t)(slash - including) + 1;
    path = xmalloc(dirlen + strlen(name) + 1);
    memcpy(path, including, dirlen);
    strcpy(path + dirlen, name);
    return path;
}

static void do_origin(parse_ctx_t *ctx, const srcpos_t *pos, const lline_t *ll)
{
    const char *err = NULL;
    dname_t origin;

    if (ll->n != 2 || ll->v[1].quoted)
        fail_at(pos, "$ORIGIN needs one domain name");
    if (name_parse(ll->v[1].text, &ctx->origin, &origin, &err))
        fail_at(pos, "%s: %s", ll->v[1].text, err);
    ctx->origin = origin;
}

static void do_ttl(parse_ctx_t *ctx, const srcpos_t *pos, const lline_t *ll)
{
    uint32_t v;

    if (ll->n != 2 || ll->v[1].quoted || ttl_parse(ll->v[1].text, &v))
        fail_at(pos, "$TTL needs one TTL value");
    ttl_ctx_set_dollar(&ctx->ttl, v);
}

static void do_include(parse_ctx_t *ctx, const char *path, const srcpos_t *pos,
                       const lline_t *ll)
{
    dname_t saved_origin = ctx->origin;
    dname_t saved_owner = ctx->owner;
    int saved_have_owner = ctx->have_owner;
    ttl_ctx_t saved_ttl = ctx->ttl;
    char *file;

    if (ll->n < 2 || ll->n > 3)
        fail_at(pos, "$INCLUDE needs a file name and an optional origin");
    if (ctx->depth >= INCLUDE_DEPTH_MAX)
        fail_at(pos, "$INCLUDE nested more than %d levels", INCLUDE_DEPTH_MAX);

    if (ll->n == 3) {
        const char *err = NULL;
        dname_t origin;
        if (ll->v[2].quoted || name_parse(ll->v[2].text, &ctx->origin, &origin, &err))
            fail_at(pos, "bad $INCLUDE origin \"%s\"", ll->v[2].text);
        ctx->origin = origin;
    }

    file = include_path(path, ll->v[1].text);
    ctx->depth++;
    parse_file(ctx, file, pos);
    ctx->depth--;
    free(file);

    ctx->origin = saved_origin;
    ctx->owner = saved_owner;
    ctx->have_owner = saved_have_owner;
    ctx->ttl = saved_ttl;
}

void parse_directive(parse_ctx_t *ctx, const char *path, const lline_t *ll)
{
    srcpos_t pos = { path, ll->line };
    const char *d = ll->v[0].text;

    if (strcasecmp(d, "$ORIGIN") == 0)
        do_origin(ctx, &pos, ll);
    else if (strcasecmp(d, "$TTL") == 0)
        do_ttl(ctx, &pos, ll);
    else if (strcasecmp(d, "$INCLUDE") == 0)
        do_include(ctx, path, &pos, ll);
    else
        fail_at(&pos, "unknown directive %s", d);
}
ZONEC_DIRECTIVES_C

# Sort owners in RFC 4034 canonical order, give each RRset the TTL of its first record, and digest the zone only once those TTLs are final.
cat > src/zone.c <<'ZONEC_ZONE_C'
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
ZONEC_ZONE_C

# Only the apex ZONEMD is left out of the digest, and it carries the SOA serial.
cat > src/zonemd.c <<'ZONEC_ZONEMD_C'
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
ZONEC_ZONEMD_C

# SHA-384 needs a second padding block whenever the 0x80 byte leaves less than 16 bytes for the 128-bit length.
cat > src/sha384.c <<'ZONEC_SHA384_C'
#include "sha384.h"

#include <string.h>

static const uint64_t K[80] = {
    0x428a2f98d728ae22ULL, 0x7137449123ef65cdULL, 0xb5c0fbcfec4d3b2fULL, 0xe9b5dba58189dbbcULL,
    0x3956c25bf348b538ULL, 0x59f111f1b605d019ULL, 0x923f82a4af194f9bULL, 0xab1c5ed5da6d8118ULL,
    0xd807aa98a3030242ULL, 0x12835b0145706fbeULL, 0x243185be4ee4b28cULL, 0x550c7dc3d5ffb4e2ULL,
    0x72be5d74f27b896fULL, 0x80deb1fe3b1696b1ULL, 0x9bdc06a725c71235ULL, 0xc19bf174cf692694ULL,
    0xe49b69c19ef14ad2ULL, 0xefbe4786384f25e3ULL, 0x0fc19dc68b8cd5b5ULL, 0x240ca1cc77ac9c65ULL,
    0x2de92c6f592b0275ULL, 0x4a7484aa6ea6e483ULL, 0x5cb0a9dcbd41fbd4ULL, 0x76f988da831153b5ULL,
    0x983e5152ee66dfabULL, 0xa831c66d2db43210ULL, 0xb00327c898fb213fULL, 0xbf597fc7beef0ee4ULL,
    0xc6e00bf33da88fc2ULL, 0xd5a79147930aa725ULL, 0x06ca6351e003826fULL, 0x142929670a0e6e70ULL,
    0x27b70a8546d22ffcULL, 0x2e1b21385c26c926ULL, 0x4d2c6dfc5ac42aedULL, 0x53380d139d95b3dfULL,
    0x650a73548baf63deULL, 0x766a0abb3c77b2a8ULL, 0x81c2c92e47edaee6ULL, 0x92722c851482353bULL,
    0xa2bfe8a14cf10364ULL, 0xa81a664bbc423001ULL, 0xc24b8b70d0f89791ULL, 0xc76c51a30654be30ULL,
    0xd192e819d6ef5218ULL, 0xd69906245565a910ULL, 0xf40e35855771202aULL, 0x106aa07032bbd1b8ULL,
    0x19a4c116b8d2d0c8ULL, 0x1e376c085141ab53ULL, 0x2748774cdf8eeb99ULL, 0x34b0bcb5e19b48a8ULL,
    0x391c0cb3c5c95a63ULL, 0x4ed8aa4ae3418acbULL, 0x5b9cca4f7763e373ULL, 0x682e6ff3d6b2b8a3ULL,
    0x748f82ee5defb2fcULL, 0x78a5636f43172f60ULL, 0x84c87814a1f0ab72ULL, 0x8cc702081a6439ecULL,
    0x90befffa23631e28ULL, 0xa4506cebde82bde9ULL, 0xbef9a3f7b2c67915ULL, 0xc67178f2e372532bULL,
    0xca273eceea26619cULL, 0xd186b8c721c0c207ULL, 0xeada7dd6cde0eb1eULL, 0xf57d4f7fee6ed178ULL,
    0x06f067aa72176fbaULL, 0x0a637dc5a2c898a6ULL, 0x113f9804bef90daeULL, 0x1b710b35131c471bULL,
    0x28db77f523047d84ULL, 0x32caab7b40c72493ULL, 0x3c9ebe0a15c9bebcULL, 0x431d67c49c100d4cULL,
    0x4cc5d4becb3e42b6ULL, 0x597f299cfc657e2aULL, 0x5fcb6fab3ad6faecULL, 0x6c44198c4a475817ULL,
};

static uint64_t ror(uint64_t x, unsigned n)
{
    return (x >> n) | (x << (64 - n));
}

static uint64_t load64(const unsigned char *p)
{
    uint64_t v = 0;
    for (int i = 0; i < 8; i++)
        v = (v << 8) | p[i];
    return v;
}

static void store64(unsigned char *p, uint64_t v)
{
    for (int i = 7; i >= 0; i--) {
        p[i] = (unsigned char)v;
        v >>= 8;
    }
}

static void compress(sha384_ctx *c, const unsigned char *block)
{
    uint64_t w[80], a, b, d, e, f, g, h, cc;

    for (int i = 0; i < 16; i++)
        w[i] = load64(block + 8 * i);
    for (int i = 16; i < 80; i++) {
        uint64_t s0 = ror(w[i - 15], 1) ^ ror(w[i - 15], 8) ^ (w[i - 15] >> 7);
        uint64_t s1 = ror(w[i - 2], 19) ^ ror(w[i - 2], 61) ^ (w[i - 2] >> 6);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }

    a = c->h[0]; b = c->h[1]; cc = c->h[2]; d = c->h[3];
    e = c->h[4]; f = c->h[5]; g = c->h[6]; h = c->h[7];
    for (int i = 0; i < 80; i++) {
        uint64_t S1 = ror(e, 14) ^ ror(e, 18) ^ ror(e, 41);
        uint64_t ch = (e & f) ^ (~e & g);
        uint64_t t1 = h + S1 + ch + K[i] + w[i];
        uint64_t S0 = ror(a, 28) ^ ror(a, 34) ^ ror(a, 39);
        uint64_t maj = (a & b) ^ (a & cc) ^ (b & cc);
        uint64_t t2 = S0 + maj;
        h = g; g = f; f = e; e = d + t1;
        d = cc; cc = b; b = a; a = t1 + t2;
    }
    c->h[0] += a; c->h[1] += b; c->h[2] += cc; c->h[3] += d;
    c->h[4] += e; c->h[5] += f; c->h[6] += g; c->h[7] += h;
}

void sha384_init(sha384_ctx *c)
{
    static const uint64_t iv[8] = {
        0xcbbb9d5dc1059ed8ULL, 0x629a292a367cd507ULL, 0x9159015a3070dd17ULL, 0x152fecd8f70e5939ULL,
        0x67332667ffc00b31ULL, 0x8eb44a8768581511ULL, 0xdb0c2e0d64f98fa7ULL, 0x47b5481dbefa4fa4ULL,
    };
    memcpy(c->h, iv, sizeof iv);
    c->buflen = 0;
    c->total = 0;
}

void sha384_update(sha384_ctx *c, const void *data, size_t n)
{
    const unsigned char *p = data;
    c->total += n;
    while (n > 0) {
        size_t take = 128 - c->buflen;
        if (take > n)
            take = n;
        memcpy(c->buf + c->buflen, p, take);
        c->buflen += take;
        p += take;
        n -= take;
        if (c->buflen == 128) {
            compress(c, c->buf);
            c->buflen = 0;
        }
    }
}

void sha384_final(sha384_ctx *c, unsigned char out[SHA384_DIGEST_LEN])
{
    uint64_t bits = c->total * 8;

    c->buf[c->buflen++] = 0x80;
    if (c->buflen > 112) {
        memset(c->buf + c->buflen, 0, 128 - c->buflen);
        compress(c, c->buf);
        c->buflen = 0;
    }
    /* The length field is 128 bits; the high half is always zero here. */
    memset(c->buf + c->buflen, 0, 120 - c->buflen);
    store64(c->buf + 120, bits);
    compress(c, c->buf);

    for (int i = 0; i < 6; i++)
        store64(out + 8 * i, c->h[i]);
}
ZONEC_SHA384_C

make
