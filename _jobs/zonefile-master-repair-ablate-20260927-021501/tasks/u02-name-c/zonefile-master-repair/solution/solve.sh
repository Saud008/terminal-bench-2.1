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

# A record TTL never overrides the $TTL value in effect.
cat > src/ttl.c <<'ZONEC_TTL_C'
#include "ttl.h"

static uint32_t unit_seconds(char u)
{
    switch (u) {
    case 'w': case 'W': return 604800;
    case 'd': case 'D': return 86400;
    case 'h': case 'H': return 3600;
    case 'm': case 'M': return 60;
    case 's': case 'S': return 1;
    default: return 0;
    }
}

int ttl_parse(const char *text, uint32_t *out)
{
    uint64_t total = 0;
    const char *p = text;
    int units = 0;

    if (!*p)
        return -1;
    while (*p) {
        uint64_t v = 0;
        const char *start = p;
        while (*p >= '0' && *p <= '9') {
            v = v * 10 + (uint64_t)(*p - '0');
            if (v > TTL_MAX)
                return -1;
            p++;
        }
        if (p == start)
            return -1;
        if (*p == '\0') {
            if (units)
                return -1;
            total = v;
            break;
        }
        uint32_t mult = unit_seconds(*p);
        if (!mult)
            return -1;
        p++;
        units = 1;
        total += v * mult;
        if (total > TTL_MAX)
            return -1;
    }
    *out = (uint32_t)total;
    return 0;
}

void ttl_ctx_set_dollar(ttl_ctx_t *c, uint32_t v)
{
    c->has_dollar = 1;
    c->dollar = v;
}

void ttl_ctx_note_explicit(ttl_ctx_t *c, uint32_t v)
{
    c->has_last = 1;
    c->last = v;
}

int ttl_ctx_default(const ttl_ctx_t *c, uint32_t *out)
{
    if (c->has_dollar) {
        *out = c->dollar;
        return 1;
    }
    if (c->has_last) {
        *out = c->last;
        return 1;
    }
    return 0;
}
ZONEC_TTL_C

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

# Sort owners in RFC 4034 canonical order and give each RRset the TTL of its first record.
cat > src/zone.c <<'ZONEC_ZONE_C'
#include "zone.h"
#include "rdata.h"
#include "util.h"

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

make
