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
