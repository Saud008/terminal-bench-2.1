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
