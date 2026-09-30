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
    slash = strchr(including, '/');
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
    ctx->owner = origin;
    ctx->have_owner = 1;
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
